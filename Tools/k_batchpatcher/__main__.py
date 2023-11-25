from __future__ import annotations

import argparse
import concurrent.futures
import cProfile
import os
import pathlib
import sys
import tkinter as tk
import traceback
from copy import deepcopy
from io import StringIO
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import TYPE_CHECKING, Any, Callable

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        if pykotor_path in sys.path:
            sys.path.remove(str(pykotor_path))
        sys.path.insert(0, str(pykotor_path.parent))


from pykotor.common.language import Language, LocalizedString
from pykotor.common.stream import BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import FileResource
from pykotor.extract.installation import Installation
from pykotor.resource.formats.erf.erf_auto import write_erf
from pykotor.resource.formats.erf.erf_data import ERF
from pykotor.resource.formats.gff import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct, read_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.rim.rim_auto import write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tlk import TLK, read_tlk, write_tlk
from pykotor.resource.formats.tpc.txi_data import write_bitmap_fonts
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.utility.path import Path, PurePath, PureWindowsPath
from tools.k_batchpatcher.translate.language_translator import TranslationOption, Translator

if TYPE_CHECKING:

    from pykotor.resource.formats.tlk.tlk_data import TLKEntry

APP: KOTORPatchingToolUI
OUTPUT_LOG: Path
LOGGING_ENABLED: bool
processed_files: set[Path] = set()

gff_types = [x.value.lower().strip() for x in GFFContent]
fieldtype_to_fieldname: dict[GFFFieldType, str] = {
    GFFFieldType.UInt8: "Byte",
    GFFFieldType.Int8: "Char",
    GFFFieldType.UInt16: "Word",
    GFFFieldType.Int16: "Short",
    GFFFieldType.UInt32: "DWORD",
    GFFFieldType.Int32: "Int",
    GFFFieldType.Int64: "Int64",
    GFFFieldType.Single: "Float",
    GFFFieldType.Double: "Double",
    GFFFieldType.String: "ExoString",
    GFFFieldType.ResRef: "ResRef",
    GFFFieldType.LocalizedString: "ExoLocString",
    GFFFieldType.Vector3: "Position",
    GFFFieldType.Vector4: "Orientation",
    GFFFieldType.Struct: "Struct",
    GFFFieldType.List: "List",
}

class Globals:
    def __init__(self) -> None:
        # Initialize with an empty dictionary to store attributes
        self._attributes: dict[str, Any] = {}

    def __setattr__(self, key, value):
        # If the key is '_attributes', handle it as a normal attribute assignment
        # This is necessary to avoid recursion during initialization
        if key == "_attributes":
            super().__setattr__(key, value)
        else:
            self._attributes[key] = value

    def __getattr__(self, item):
        return self._attributes.get(item, None)

    def __setitem__(self, key, value):
        self._attributes[key] = value

    def __getitem__(self, key):
        return self._attributes.get(key, None)

SCRIPT_GLOBALS = Globals()
SCRIPT_GLOBALS.pytranslator: Translator = None

def relative_path_from_to(src, dst) -> Path:
    src_parts = list(src.parts)
    dst_parts = list(dst.parts)

    common_length = next(
        (i for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts)) if src_part != dst_part),
        len(src_parts),
    )
    rel_parts = dst_parts[common_length:]
    return Path(*rel_parts)


def log_output(*args, **kwargs) -> None:
    # Create an in-memory text stream
    buffer = StringIO()

    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg = buffer.getvalue()

    # Write the captured output to the file
    with Path("log_batch_patcher.log").open("a", errors="ignore") as f:
        f.write(msg)

    # Print the captured output to console
    print(*args, **kwargs)  # noqa: T201
    SCRIPT_GLOBALS.patchlogger.add_note("\t".join(args))


def visual_length(s: str, tab_length=8) -> int:
    if "\t" not in s:
        return len(s)

    # Split the string at tabs, sum the lengths of the substrings,
    # and add the necessary spaces to account for the tab stops.
    parts = s.split("\t")
    vis_length = sum(len(part) for part in parts)
    for part in parts[:-1]:  # all parts except the last one
        vis_length += tab_length - (len(part) % tab_length)
    return vis_length


def log_output_with_separator(message, below=True, above=False, surround=False) -> None:
    if above or surround:
        log_output(visual_length(message) * "-")
    log_output(message)
    if below and not above or surround:
        log_output(visual_length(message) * "-")


def patch_nested_gff(
    gff_struct: GFFStruct,
    gff_content: GFFContent,
    current_path: PureWindowsPath | os.PathLike | str | None = None,
    made_change: bool = False,
) -> bool:
    if gff_content != GFFContent.DLG and not SCRIPT_GLOBALS.translate:
        print("Skipping file, translate not set.")
        return False
    current_path = current_path if isinstance(current_path, PureWindowsPath) else PureWindowsPath(current_path or "GFFRoot")
    for label, ftype, value in gff_struct:
        if label.lower() == "mod_name":
            continue
        child_path = current_path / label

        if ftype == GFFFieldType.Struct:
            assert isinstance(value, GFFStruct)  # noqa: S101
            if SCRIPT_GLOBALS.set_unskippable and gff_content == GFFContent.DLG and current_path.parent == "RepliesList":
                log_output(f"Setting '{child_path}' as unskippable")
                value.set_uint32("Skippable", 0)
                made_change = True
            patch_nested_gff(value, gff_content, child_path, made_change)
            continue

        if ftype == GFFFieldType.List:
            assert isinstance(value, GFFList)  # noqa: S101
            recurse_through_list(value, gff_content, child_path, made_change)
            continue

        if ftype == GFFFieldType.LocalizedString and SCRIPT_GLOBALS.translate:  # and gff_content.value == GFFContent.DLG.value:
            assert isinstance(value, LocalizedString)  # noqa: S101
            new_substrings = deepcopy(value._substrings)
            for lang, gender, text in value:
                if SCRIPT_GLOBALS.pytranslator is not None and text is not None and text.strip():
                    log_output_with_separator(f"Translating CExoLocString at {child_path} to {SCRIPT_GLOBALS.to_lang.name}", above=True)
                    translated_text = SCRIPT_GLOBALS.pytranslator.translate(text, from_lang=lang)
                    log_output(f"Translated {text} --> {translated_text}")
                    substring_id = LocalizedString.substring_id(SCRIPT_GLOBALS.to_lang, gender)
                    new_substrings[substring_id] = translated_text
                    made_change = True
            value._substrings = new_substrings
    return made_change


def recurse_through_list(gff_list: GFFList, gff_content: GFFContent, current_path: PureWindowsPath, made_change: bool):
    current_path = current_path if isinstance(current_path, PureWindowsPath) else PureWindowsPath(current_path or "GFFListRoot")
    for list_index, gff_struct in enumerate(gff_list):
        patch_nested_gff(gff_struct, gff_content, current_path / str(list_index), made_change)


def patch_resource(resource: FileResource) -> GFF | None:
    def translate_entry(strref, tlkentry, from_lang):
        text = tlkentry.text
        if not text.strip() or text.isdigit():
            return strref, None
        translated_text = SCRIPT_GLOBALS.pytranslator.translate(text, from_lang=from_lang)
        return strref, translated_text

    def process_translations(tlk, from_lang) -> list[TLKEntry]:
        new_entries: list[TLKEntry] = deepcopy(tlk.entries)
        with concurrent.futures.ThreadPoolExecutor(max_workers=SCRIPT_GLOBALS.max_threads) as executor:
            # Create a future for each translation task
            future_to_strref = {executor.submit(translate_entry, strref, tlkentry, from_lang): strref for strref, tlkentry in tlk}

            for future in concurrent.futures.as_completed(future_to_strref):
                strref = future_to_strref[future]
                try:
                    log_output_with_separator(f"Translating TLK text at {resource.filepath()!s}", above=True)
                    translated_text = future.result()
                    if translated_text:
                        new_entries[strref].text = translated_text[1]
                        log_output(f"#{strref} Translated {tlk[strref].text} --> {translated_text[1]}")
                except Exception as exc:
                    print(f"{strref} generated an exception: {exc!r}")
        return new_entries
    if resource.restype().extension.lower() == "tlk" and SCRIPT_GLOBALS.translate and SCRIPT_GLOBALS.pytranslator:
        tlk: TLK | None = None
        try:
            log_output(f"Loading TLK '{resource.filepath()}'")
            tlk = read_tlk(resource.data())
        except Exception as e:  # noqa: BLE001
            log_output(f"Error loading TLK {resource.filepath()}! {e!r}")
            return None
        if not tlk:
            message = f"TLK resource missing in memory:\t'{resource.filepath()}'"
            log_output(message)
            return None

        from_lang: Language = tlk.language
        new_filename_stem = f"{resource.resname()}_" + (SCRIPT_GLOBALS.to_lang.get_bcp47_code() or "UNKNOWN")
        new_file_path = resource.filepath().parent / (new_filename_stem + resource.restype().extension)
        tlk.language = SCRIPT_GLOBALS.to_lang
        tlk.entries = process_translations(tlk, from_lang)
        write_tlk(tlk, new_file_path)
        processed_files.add(new_file_path)
    if resource.restype().extension.lower() in gff_types or f"{resource.restype().name.upper()} " in GFFContent.get_valid_types():
        gff: GFF | None = None
        try:
            #log_output(f"Loading {resource.resname()}.{resource.restype().extension} from '{resource.filepath().name}'")
            gff = read_gff(resource.data())
            if patch_nested_gff(
                gff.root,
                gff.content,
                f"{resource.resname()}.{resource.restype().extension}",
            ):
                return gff
        except Exception as e:  # noqa: BLE001
            log_output(f"[Error] loading GFF {resource.resname()} at {resource.filepath()}! {e!r}")
            #raise
            return None

        if not gff:
            log_output(f"GFF resource {resource.resname()} missing in memory:\t'{resource.filepath()}'")
            return None
    return None


def patch_and_save_noncapsule(resource: FileResource):
    gff: GFF | None = patch_resource(resource)
    new_data: bytes = resource.data()
    if gff is not None:
        new_data = bytes_gff(gff)

    new_path = resource.filepath()
    new_gff_filename = resource.filename()
    if SCRIPT_GLOBALS.translate:
        new_gff_filename = f"{resource.resname()}_{SCRIPT_GLOBALS.to_lang.get_bcp47_code()}{resource.restype().extension}"
    new_path = new_path.parent / new_gff_filename

    BinaryWriter.dump(new_path, new_data)


def patch_file(file: os.PathLike | str) -> None:
    c_file = file if isinstance(file, Path) else Path(file).resolve()
    if c_file in processed_files:
        return

    new_data: bytes
    gff: GFF | None

    if is_capsule_file(c_file):
        log_output(f"Load {c_file.name}")
        try:
            file_capsule = Capsule(file)
        except ValueError as e:
            log_output(f"Could not load '{c_file!s}'. Reason: {e!r}")
            return

        new_filepath: Path = c_file.parent / f"{c_file.name}_{SCRIPT_GLOBALS.to_lang.get_bcp47_code()}"
        new_capsule = Capsule(new_filepath, create_nonexisting=True)
        for resource in file_capsule:
            gff = patch_resource(resource)
            new_data = resource.data()
            if gff is not None:
                new_data = bytes_gff(gff)
            new_capsule.add(resource.resname(), resource.restype(), new_data)
    else:
        ext = c_file.suffix.lower()[1:]
        resource = FileResource(
            c_file.name,
            ResourceType.from_extension(ext),
            c_file.stat().st_size,
            0,
            c_file,
        )
        patch_and_save_noncapsule(resource)

def patch_folder(folder_path: os.PathLike | str) -> None:
    c_folderpath = folder_path if isinstance(folder_path, Path) else Path(folder_path).resolve()
    log_output_with_separator(f"Recursing through resources in the '{c_folderpath.name}' folder...", above=True)
    for file_path in c_folderpath.safe_rglob("*"):
        patch_file(file_path)

def patch_capsule_resources(resources: list[FileResource], filename: str, erf_or_rim: RIM | ERF) -> PurePath:
    for resource in resources:
        gff: GFF | None = patch_resource(resource)
        new_data: bytes = bytes_gff(gff) if gff else resource.data()
        erf_or_rim.set_data(resource.resname(), resource.restype(), new_data)

    new_filename = PurePath(filename)
    if SCRIPT_GLOBALS.translate:
        new_filename = PurePath(f"{new_filename.stem}_{SCRIPT_GLOBALS.to_lang.get_bcp47_code()}{new_filename.suffix}")
    return new_filename

def patch_install(install_path: os.PathLike | str) -> None:
    log_output()
    log_output_with_separator(f"Patching install dir:\t{install_path}", above=True)
    log_output()

    log_output_with_separator("Patching modules...")
    k_install = Installation(install_path, SCRIPT_GLOBALS.patchlogger)

    # Patch modules...
    for module_name, resources in k_install._modules.items():
        restype = ResourceType.from_extension(PurePath(module_name).suffix[1:])
        if restype == ResourceType.RIM:
            new_rim = RIM()
            new_rim_filename = patch_capsule_resources(resources, module_name, new_rim)
            write_rim(new_rim, k_install.path() / new_rim_filename)
        elif restype in [ResourceType.MOD, ResourceType.ERF]:
            new_erf = ERF()
            new_erf_filename = patch_capsule_resources(resources, module_name, new_erf)
            write_erf(new_erf, k_install.path() / new_erf_filename, restype)
        else:
            log_output("Unsupported module:", module_name, " - cannot patch")

    # Patch rims...
    for rim_name, resources in k_install._rims.items():
        new_rim = RIM()
        new_rim_filename = patch_capsule_resources(resources, rim_name, new_rim)
        write_rim(new_rim, k_install.path() / new_rim_filename)

    # Patch Override...
    for folder in k_install.override_list():
        for resource in k_install.override_resources(folder):
            patch_and_save_noncapsule(resource)

    patch_file(k_install.path().joinpath("dialog.tlk"))


def is_kotor_install_dir(path: os.PathLike | str) -> bool:
    c_path: CaseAwarePath = CaseAwarePath(path)
    return c_path.safe_isdir() and c_path.joinpath("chitin.key").exists()


def determine_input_path(path: Path):
    if not path.safe_exists() or path.resolve() == Path.cwd().resolve():
        msg = "Path does not exist"
        raise FileNotFoundError(msg)

    if is_kotor_install_dir(path):
        return patch_install(path)

    if path.is_dir():
        return patch_folder(path)

    if path.is_file():
        return patch_file(path)
    return None


def execute_patchloop_thread():
    try:
        SCRIPT_GLOBALS.install_running = True
        do_main_patchloop()
        SCRIPT_GLOBALS.install_running = False
    except Exception as e:  # noqa: BLE001
        log_output("Unhandled exception during the patching process.")
        log_output(traceback.format_exc())
        SCRIPT_GLOBALS.install_running = False
        return messagebox.showerror("Error", f"An error occurred during patching\n{e!r}")

def do_main_patchloop():
    # Validate args
    if not SCRIPT_GLOBALS.chosen_languages:
        if SCRIPT_GLOBALS.translate:
            return messagebox.showwarning("No language chosen", "Select a language first if you want to translate")
        if SCRIPT_GLOBALS.create_fonts:
            return messagebox.showwarning("No language chosen", "Select a language first to create fonts.")
    if SCRIPT_GLOBALS.create_fonts and (not Path(SCRIPT_GLOBALS.font_path).name or not Path(SCRIPT_GLOBALS.font_path).safe_exists()):
        return messagebox.showwarning(f"Font path not found {SCRIPT_GLOBALS.font_path}", "Please set your font path to a valid TTF font file.")
    if SCRIPT_GLOBALS.translate and not SCRIPT_GLOBALS.translation_applied:
        return messagebox.showwarning("Bad translation args", "Cannot start translation, you have not applied your translation options. (api key, db path, server url etc)")

    # Patching logic
    has_action = False
    if SCRIPT_GLOBALS.create_fonts:
        for lang in SCRIPT_GLOBALS.chosen_languages:
            create_font_pack(lang)
        has_action = True
    if SCRIPT_GLOBALS.translate:
        has_action = True
        for lang in SCRIPT_GLOBALS.chosen_languages:
            main_patchloop_logic(lang)
    if SCRIPT_GLOBALS.set_unskippable:
        determine_input_path(Path(SCRIPT_GLOBALS.path))
        has_action = True
    if not has_action:
        return messagebox.showwarning("No options chosen", "Select what you want to do.")

    log_output(f"Completed batch patcher of {SCRIPT_GLOBALS.path}")
    return messagebox.showinfo("Patching complete!", "Check the log file log_batch_patcher.log for more information.")


def main_patchloop_logic(lang):
    print(f"Translating to {lang.name}...")
    if SCRIPT_GLOBALS.pytranslator is None:
        SCRIPT_GLOBALS.pytranslator = Translator(lang)
    else:
        SCRIPT_GLOBALS.pytranslator.to_lang = lang
    SCRIPT_GLOBALS.to_lang = lang
    SCRIPT_GLOBALS.pytranslator.translation_option = SCRIPT_GLOBALS.translation_option  # type: ignore[assignment]
    determine_input_path(Path(SCRIPT_GLOBALS.path))

def create_font_pack(lang: Language):
    print(f"Creating font pack for '{lang.name}'...")
    write_bitmap_fonts(
        Path.cwd() / lang.name,
        SCRIPT_GLOBALS.font_path,
        (SCRIPT_GLOBALS.resolution, SCRIPT_GLOBALS.resolution),
        lang,
        SCRIPT_GLOBALS.draw_bounds,
    )


def assign_to_globals(instance):
    for attr, value in instance.__dict__.items():
        # Convert tkinter variables to their respective Python types
        if isinstance(value, tk.StringVar):
            SCRIPT_GLOBALS[attr] = value.get()
        elif isinstance(value, tk.BooleanVar):
            SCRIPT_GLOBALS[attr] = bool(value.get())
        elif isinstance(value, tk.IntVar):
            SCRIPT_GLOBALS[attr] = int(value.get())
        else:
            # Directly assign if it's not a tkinter variable
            SCRIPT_GLOBALS[attr] = value


class KOTORPatchingToolUI:
    def __init__(self, root, parser_args) -> None:
        self.root = root
        root.title("KOTOR Translate Tool")

        self.path = tk.StringVar(value=parser_args.path or None)
        self.output_log = "log_batch_patcher.log"
        self.set_unskippable = tk.BooleanVar(value=parser_args.set_unskippable)
        self.logging_enabled = tk.BooleanVar(value=parser_args.logging or True)
        self.translate = tk.BooleanVar(value=parser_args.translate or True)
        self.to_lang = tk.StringVar(value=parser_args.to_lang)
        self.create_fonts = tk.BooleanVar(value=parser_args.create_fonts)
        self.font_path = tk.StringVar(value=parser_args.font_path)
        self.resolution = tk.IntVar(value=parser_args.resolution or 512)
        self.use_profiler = tk.BooleanVar(value=parser_args.use_profiler)
        self.draw_bounds = tk.BooleanVar(value=False)

        # Middle area for text and scrollbar
        self.output_frame = tk.Frame(self.root)
        self.output_frame.grid_remove()

        self.description_text = tk.Text(self.output_frame, wrap=tk.WORD)
        font_obj = tkfont.Font(font=self.description_text.cget("font"))
        font_obj.configure(size=9)
        self.description_text.configure(font=font_obj)
        self.description_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(self.output_frame, command=self.description_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.lang_vars: dict[Language, tk.BooleanVar] = {}
        self.language_row: int
        self.install_running = False
        self.install_button: ttk.Button
        self.language_frame = ttk.Frame(root)  # Frame to contain language checkboxes
        self.translation_applied: bool = True
        SCRIPT_GLOBALS.chosen_languages = []

        self.setup_ui()

    def write_log(self, message: str) -> None:
        """Writes a message to the log.

        Args:
        ----
            message (str): The message to write to the log.

        Returns:
        -------
            None
        Processes the log message by:
            - Setting the description text widget to editable
            - Inserting the message plus a newline at the end of the text
            - Scrolling to the end of the text
            - Making the description text widget not editable again.
        """
        self.description_text.config(state=tk.NORMAL)
        self.description_text.insert(tk.END, message + os.linesep)
        self.description_text.see(tk.END)
        self.description_text.config(state=tk.DISABLED)

    def initialize_logger(self):
        self.logger = PatchLogger()
        SCRIPT_GLOBALS.patchlogger = self.logger
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

    def on_gamepaths_chosen(self, event: tk.Event) -> None:
        """Adjust the combobox after a short delay."""
        self.root.after(10, lambda: self.move_cursor_to_end(event.widget))

    def move_cursor_to_end(self, combobox: ttk.Combobox) -> None:
        """Shows the rightmost portion of the specified combobox as that's the most relevant."""
        combobox.focus_set()
        position: int = len(combobox.get())
        combobox.icursor(position)
        combobox.xview(position)
        self.root.focus_set()

    def setup_ui(self):
        row = 0
        # Path to K1/TSL install
        ttk.Label(self.root, text="Path to K1/TSL install:").grid(row=row, column=0)
        # Gamepaths Combobox
        self.gamepaths = ttk.Combobox(self.root, textvariable=self.path)
        self.gamepaths.grid(row=row, column=1, columnspan=2, sticky="ew")
        self.gamepaths["values"] = [str(path) for game in find_kotor_paths_from_default().values() for path in game]
        self.gamepaths.bind("<<ComboboxSelected>>", self.on_gamepaths_chosen)

        # Browse button
        browse_button = ttk.Button(self.root, text="Browse", command=self.browse_path)
        browse_button.grid(row=row, column=3, padx=2)  # Stick to both sides within its cell
        browse_button.config(width=15)

        row += 1

        # Skippable
        ttk.Label(self.root, text="Make all dialog unskippable:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.set_unskippable).grid(row=row, column=1)
        row += 1

        # Translate
        ttk.Label(self.root, text="Translate:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.translate).grid(row=row, column=1)
        row += 1

        # Translation Option
        ttk.Label(self.root, text="Translation Option:").grid(row=row, column=0)
        self.translation_option = ttk.Combobox(self.root)
        self.translation_option.grid(row=row, column=1)
        self.translation_option["values"] = [v.name for v in TranslationOption.get_available_translators()]
        self.translation_option.set("GOOGLE_TRANSLATE")
        self.translation_option.bind("<<ComboboxSelected>>", self.on_translation_option_chosen)
        row += 1

        # Max threads
        SCRIPT_GLOBALS.max_threads = 3
        def on_value_change():
            SCRIPT_GLOBALS.max_threads = int(spinbox_value.get())
        ttk.Label(self.root, text="Max Translation Threads:").grid(row=row, column=0)
        spinbox_value = tk.StringVar(value=str(SCRIPT_GLOBALS.max_threads))
        self.spinbox = tk.Spinbox(root, from_=1, to=5, increment=1, command=on_value_change, textvariable=spinbox_value)
        self.spinbox.grid(row=row, column=1)
        row += 1

        # Upper area for the translation options
        self.translation_ui_options_row = row
        self.translation_options_frame = tk.Frame(self.root)
        self.translation_options_frame.grid(row=row, column=0, sticky="nsew")
        self.translation_options_frame.grid_rowconfigure(0, weight=1)
        self.translation_options_frame.grid_columnconfigure(0, weight=1)
        row += 1

        # Create Fonts
        ttk.Label(self.root, text="Create Fonts:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.create_fonts).grid(row=row, column=1)
        row += 1

        # Font Path
        ttk.Label(self.root, text="Font Path:").grid(row=row, column=0)
        ttk.Entry(self.root, textvariable=self.font_path).grid(row=row, column=1)
        ttk.Button(self.root, text="Browse", command=self.browse_font_path).grid(row=row, column=2)
        row += 1

        # Draw bounds
        ttk.Label(self.root, text="Draw bounds:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, variable=self.draw_bounds).grid(row=row, column=1)
        row += 1

        # Resolution
        ttk.Label(self.root, text="Resolution:").grid(row=row, column=0)
        ttk.Entry(self.root, textvariable=self.resolution).grid(row=row, column=1)
        row += 1

        # Logging Enabled
        #ttk.Label(self.root, text="Enable Logging:").grid(row=row, column=0)
        #ttk.Checkbutton(self.root, text="Yes", variable=self.logging_enabled).grid(row=row, column=1)
        #row += 1

        # Use Profiler
        #ttk.Label(self.root, text="Use Profiler:").grid(row=row, column=0)
        #ttk.Checkbutton(self.root, text="Yes", variable=self.use_profiler).grid(row=row, column=1)
        #row += 1

        # Show/Hide output window
        self.show_hide_output = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.root, text="Show Output:", command=lambda: self.toggle_output_frame(self.show_hide_output)).grid(row=row, column=1)
        row += 1

        # To Language
        self.create_language_checkbuttons(row)
        row += len(Language)
        self.output_frame = tk.Frame(self.root)
        self.output_frame.grid(row=self.language_row, column=0, sticky="nsew")
        self.output_frame.grid_rowconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_remove()

        self.description_text = tk.Text(self.output_frame, wrap=tk.WORD)
        font_obj = tkfont.Font(font=self.description_text.cget("font"))
        font_obj.configure(size=9)
        self.description_text.configure(font=font_obj)
        self.description_text.grid(row=0, column=0, sticky="nsew")

        # Start Patching Button
        self.install_button = ttk.Button(self.root, text="Run All Operations", command=self.start_patching)
        self.install_button.grid(row=row, column=1)

    def on_translation_option_chosen(self, event) -> None:
        """Create Checkbuttons for each translator option and assign them to the translator.
        Needs rewriting or cleaning, difficult readability lies ahead if you're reading this.
        """
        for widget in self.translation_options_frame.winfo_children():
            widget.destroy()  # remove controls from a different translationoption before adding new ones below

        row = self.translation_ui_options_row
        t_option = TranslationOption.__members__[self.translation_option.get()]
        ui_lambdas_dict: dict[str, Callable[[tk.Frame], ttk.Combobox | ttk.Label | ttk.Checkbutton | ttk.Entry]] = t_option.get_specific_ui_controls()
        varname = None
        value = None
        for varname, ui_control_lambda in ui_lambdas_dict.items():
            ui_control: ttk.Combobox | ttk.Label | ttk.Checkbutton | ttk.Entry = ui_control_lambda(self.translation_options_frame)
            if varname.startswith("descriptor_label") or isinstance(ui_control, ttk.Label):
                ui_control.grid(row=row, column=1)
                continue
            value = ui_control.instate(["selected"]) if isinstance(ui_control, ttk.Checkbutton) else ui_control.get()
            ui_control.grid(row=row, column=2)
            row += 1

        if value is not None and varname is not None:
            self.translation_applied = False
            ttk.Button(self.translation_options_frame, text="Apply Options", command=lambda: self.apply_translation_option(varname=varname, value=value)).grid(row=row, column=2)
        else:
            self.translation_applied = True

    def apply_translation_option(self, varname, value) -> None:
        setattr(SCRIPT_GLOBALS.pytranslator, varname, value)  # TODO: add all the variable names to __init__ of Translator class
        self.write_log(f"Applied Options for {self.translation_option.get()}: {varname} = {value}")
        cur_toption: TranslationOption = TranslationOption.__members__[self.translation_option.get()]
        msg: str = cur_toption.validate_args(SCRIPT_GLOBALS.pytranslator)
        if msg:
            messagebox.showwarning("Invalid translation options", msg)
            return
        self.translation_applied = True

    def create_language_checkbuttons(self, row) -> None:

        # Show/Hide Languages
        self.show_hide_language = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.root, text="Show/Hide Languages:", command=lambda: self.toggle_language_frame(self.show_hide_language)).grid(row=row, column=1)
        row += 1

        # Middle area for text and scrollbar
        self.language_row = row
        self.language_frame = tk.Frame(self.root)
        self.language_frame.grid(row=row, column=0, sticky="nsew")
        self.language_frame.grid_rowconfigure(0, weight=1)
        self.language_frame.grid_columnconfigure(0, weight=1)
        self.language_frame.grid_remove()
        row += 1

        # Create a Checkbutton for "ALL"
        all_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.language_frame,
            text="ALL",
            variable=all_var,
            command=lambda: self.toggle_all_languages(all_var),
        ).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        # Sort the languages in alphabetical order
        sorted_languages = sorted(Language, key=lambda lang: lang.name)

        # Create Checkbuttons for each language
        column = 0
        for lang in sorted_languages:
            if not lang.is_8bit_encoding():
                continue
            lang_var = tk.BooleanVar()
            self.lang_vars[lang] = lang_var  # Store reference to the language variable
            ttk.Checkbutton(
                self.language_frame,
                text=lang.name,
                variable=lang_var,
                command=lambda lang=lang, lang_var=lang_var: self.update_chosen_languages(lang, lang_var),
            ).grid(row=row, column=column, sticky="w")

            # Alternate between columns
            column = (column + 1) % 4
            if column == 0:
                row += 1

    def update_chosen_languages(self, lang: Language, lang_var: tk.BooleanVar):
        if lang_var.get():
            SCRIPT_GLOBALS.chosen_languages.append(lang)
        else:
            SCRIPT_GLOBALS.chosen_languages.remove(lang)

    def toggle_all_languages(self, all_var: tk.BooleanVar):
        all_value = all_var.get()
        for lang, lang_var in self.lang_vars.items():
            lang_var.set(all_value)  # Set each language variable to the state of the "ALL" checkbox
            if all_value:
                if lang not in SCRIPT_GLOBALS.chosen_languages:
                    SCRIPT_GLOBALS.chosen_languages.append(lang)
            elif lang in SCRIPT_GLOBALS.chosen_languages:
                SCRIPT_GLOBALS.chosen_languages.remove(lang)

    def toggle_language_frame(self, show_var: tk.BooleanVar):
        show_var.set(not show_var.get())
        if show_var.get():
            self.language_frame.grid(row=self.language_row, column=0, columnspan=4, sticky="ew")
        else:
            self.language_frame.grid_remove()  # Hide the frame

    def toggle_output_frame(self, show_var: tk.BooleanVar):
        show_var.set(not show_var.get())
        if show_var.get():
            self.output_frame.grid(row=self.language_row, column=0, columnspan=4, sticky="ew")
        else:
            self.output_frame.grid_remove()  # Hide the frame

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path.set(directory)

    def browse_font_path(self):
        file = filedialog.askopenfilename()
        if file:
            self.font_path.set(file)

    def start_patching(self):
        if SCRIPT_GLOBALS.install_running:
            return messagebox.showerror("Install already running", "Please wait for all operations to complete. Check the console/output for details.")
        self.install_button.config(state="normal")
        try:
            assign_to_globals(self)
            # Mapping UI input to script logic
            try:
                path = Path(SCRIPT_GLOBALS.path).resolve()
            except OSError as e:
                return messagebox.showerror("Error", f"Invalid path '{SCRIPT_GLOBALS.path}'\n{e!r}")
            else:
                if not path.exists():
                    return messagebox.showerror("Error", "Invalid path")
            SCRIPT_GLOBALS.translation_option = TranslationOption[self.translation_option.get()]
            self.toggle_output_frame(tk.BooleanVar(value=False))
            self.initialize_logger()

            SCRIPT_GLOBALS.install_thread = Thread(target=execute_patchloop_thread)
            SCRIPT_GLOBALS.install_thread.start()
        except Exception as e:
            messagebox.showerror(f"Unhandled exception: {e}")
            SCRIPT_GLOBALS.install_running = False
            self.install_button.config(state=tk.DISABLED)
        return None

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Finds differences between two KOTOR installations")
    parser.add_argument("--path", type=str, help="Path to the first K1/TSL install, file, or directory to patch.")
    parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
    parser.add_argument("--logging", type=bool, help="Whether to log the results to a file or not (default is enabled)")
    parser.add_argument("--set-unskippable", type=str, help="Makes all dialog unskippable. (y/N)")
    parser.add_argument("--translate", type=str, help="Should we ai translate the TLK and all GFF locstrings? (y/N)")
    parser.add_argument("--to-lang", type=str, help="The language to translate the files to")
    parser.add_argument("--from-lang", type=str, help="The language the files are written in (defaults to auto if available)")
    parser.add_argument("--create-fonts", type=str, help="Create font packs for the selected language(s) (y/N).")
    parser.add_argument("--font-path", type=str, help="Path to the font file to use for the font pack creation (must be a file that ends in .ttk)")
    parser.add_argument("--resolution", type=int, help="A single number representing the resolution Y x Y. Must be divisible by 256. The single number entered will be used for both the height and width, as it must be a square.")
    parser.add_argument("--start", action="store_true", help="Start patching immediately, doesn't show a UI at all, exits when done.")
    parser.add_argument(
        "--use-profiler",
        type=bool,
        default=False,
        help="Use cProfile to find where most of the execution time is taking place in source code.",
    )
    parser_args, unknown = parser.parse_known_args()
    SCRIPT_GLOBALS.start = parser_args.start
    if not SCRIPT_GLOBALS.start:
        try:
            root = tk.Tk()
            APP = KOTORPatchingToolUI(root, parser_args)
            root.mainloop()
        except Exception:  # noqa: BLE001
            log_output(traceback.format_exc())
            raise
    else:
        LOGGING_ENABLED = bool(parser_args.logging is None or parser_args.logging)
        while True:
            parser_args.path = Path(
                parser_args.path
                or input("Path to the K1/TSL install, file, or directory to patch: ")
                or "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II",
            ).resolve()
            if parser_args.path.exists():
                break
            print("Invalid path:", parser_args.path)
            parser.print_help()
            parser_args.path = None
        while True:
            parser_args.set_unskippable = parser_args.set_unskippable or input("Would you like to make all dialog unskippable? (y/N): ")
            if parser_args.set_unskippable.lower() in ["y", "yes"]:  # type: ignore[attr-defined]
                parser_args.set_unskippable = True
            elif parser_args.set_unskippable.lower() in ["n", "no"]:  # type: ignore[attr-defined]
                parser_args.set_unskippable = False
            if not isinstance(parser_args.set_unskippable, bool):
                print("Invalid input, please enter yes or no")
                parser_args.set_unskippable = None
                parser.print_help()
                continue
            break
        while True:
            parser_args.translate = parser_args.translate or input(
                "Would you like to translate all CExoLocStrings and TLK entries to another language? (y/N): ",
            )
            if parser_args.translate.lower() in ["y", "yes"]:  # type: ignore[attr-defined]
                parser_args.translate = True
            elif parser_args.translate.lower() in ["n", "no"]:  # type: ignore[attr-defined]
                parser_args.translate = False
            if not isinstance(parser_args.translate, bool):
                print("Invalid input, please enter yes or no")
                parser_args.translate = None
                parser.print_help()
                continue
            break
        if LOGGING_ENABLED:
            while True:
                OUTPUT_LOG = Path(
                    parser_args.output_log
                    or "./log_batch_patcher.log",
                ).resolve()
                if OUTPUT_LOG.parent.exists():
                    break
                print("Invalid path:", OUTPUT_LOG)
                parser.print_help()
        SCRIPT_GLOBALS.translation_option: str = None  # type: ignore[assignment]
        if parser_args.translate:
            while True:
                print("Languages: ", *Language.__members__)
                parser_args.to_lang = parser_args.to_lang or input("Choose a language to translate to: ").upper()
                try:
                    if parser_args.to_lang == "ALL":
                        break
                    # Convert the string representation to the enum member, and then get its value
                    parser_args.to_lang = Language[parser_args.to_lang]
                except KeyError:
                    # Handle the case where the input is not a valid name in Language
                    parser.print_help()
                    msg = f"{parser_args.to_lang.upper()} is not a valid Language."  # type: ignore[union-attr, reportGeneralTypeIssues]
                    print(msg)
                    parser_args.to_lang = None
                    continue
                break
            while True:
                parser_args.create_fonts = parser_args.create_fonts or input(
                    "Would you like to create font packs for your language(s)? (y/N): ",
                )
                if parser_args.create_fonts.lower() in ["y", "yes"]:  # type: ignore[attr-defined]
                    SCRIPT_GLOBALS.create_fonts = True
                elif parser_args.create_fonts.lower() in ["n", "no"]:  # type: ignore[attr-defined]
                    SCRIPT_GLOBALS.create_fonts = False
                if not isinstance(parser_args.create_fonts, bool):
                    parser_args.create_fonts = None
                    parser.print_help()
                    print("Invalid input, please enter yes or no")
                    continue
                break
            if parser_args.create_fonts:
                while True:
                    SCRIPT_GLOBALS.font_path = Path(
                        parser_args.font_path
                        or input("Path to your TTF font file: "),
                    ).resolve()
                    if SCRIPT_GLOBALS.font_path.exists() and SCRIPT_GLOBALS.font_path.suffix.lower() == ".ttf":
                        break
                    parser.print_help()
                    print("Invalid font path:", parser_args.font_path)
                    parser_args.font_path = None
                while True:
                    SCRIPT_GLOBALS.resolution = (
                        parser_args.resolution
                        or input("Choose the desired resolution (single number - must be a square, and probably a multiple of 256): ").upper()
                    )
                    try:
                        val = int(SCRIPT_GLOBALS.resolution)
                        if val % 256 != 0:
                            msg = "not an int of required value"
                            raise ValueError(msg)
                        SCRIPT_GLOBALS.resolution = val
                    except Exception:
                        msg = f"{SCRIPT_GLOBALS.resolution.upper()} is not a resolution. Must be an int cleanly divisible by 256 (single number)."  # type: ignore[union-attr, reportGeneralTypeIssues]
                        print(msg)
                        parser_args.resolution = None
                        continue
                    break
            while True:
                print(*TranslationOption.__members__)
                SCRIPT_GLOBALS.translation_option = input("Choose a preferred translator library: ")
                try:
                    # Convert the string representation to the enum member, and then get its value
                    SCRIPT_GLOBALS.translation_option = TranslationOption[SCRIPT_GLOBALS.translation_option]  # type: ignore[assignment]
                except KeyError:
                    msg = f"{SCRIPT_GLOBALS.translation_option} is not a valid translation option. Please choose one of [{TranslationOption.__members__}]"  # type: ignore[union-attr, reportGeneralTypeIssues]
                    continue
                break
        SCRIPT_GLOBALS.use_profiler = bool(parser_args.use_profiler)
        input("Parameters have been set! Press [Enter] to start the patching process, or Ctrl+C to exit.")
        profiler = None
        execute_patchloop_thread()
        if SCRIPT_GLOBALS.translation_option is not None and SCRIPT_GLOBALS.to_lang != "ALL":
            SCRIPT_GLOBALS.pytranslator = Translator(SCRIPT_GLOBALS.to_lang)
            SCRIPT_GLOBALS.pytranslator.translation_option = SCRIPT_GLOBALS.translation_option  # type: ignore[assignment]
        try:
            if SCRIPT_GLOBALS.use_profiler:
                profiler = cProfile.Profile()
                profiler.enable()
            for lang in SCRIPT_GLOBALS.chosen_languages:
                print(f"Translating to {lang.name}...")
                enum_member_lang = Language[lang]
                if SCRIPT_GLOBALS.create_fonts:
                    create_font_pack(enum_member_lang)
                SCRIPT_GLOBALS.to_lang = enum_member_lang
                SCRIPT_GLOBALS.pytranslator = Translator(SCRIPT_GLOBALS.to_lang)
                SCRIPT_GLOBALS.pytranslator.translation_option = SCRIPT_GLOBALS.translation_option  # type: ignore[assignment]
                comparison: bool | None = determine_input_path(SCRIPT_GLOBALS.path)
            if SCRIPT_GLOBALS.create_fonts:
                create_font_pack(SCRIPT_GLOBALS.to_lang)
            comparison = determine_input_path(SCRIPT_GLOBALS.path)
            if profiler is not None:
                profiler.disable()
                profiler_output_file = Path("profiler_output.pstat").resolve()
                profiler.dump_stats(str(profiler_output_file))
                log_output(f"Profiler output saved to: {profiler_output_file}")
            log_output(f"Completed batch patcher of {SCRIPT_GLOBALS.path}")
            sys.exit(0)
        except KeyboardInterrupt:
            raise
        except Exception:  # noqa: BLE001
            log_output("Unhandled exception during the batchpatch process.")
            log_output(traceback.format_exc())
            input("The program must shut down. Press Enter to close.")
        finally:
            if profiler is not None:
                profiler.disable()
                profiler_output_file = Path("profiler_output.pstat").resolve()
                profiler.dump_stats(str(profiler_output_file))
                log_output(f"Profiler output saved to: {profiler_output_file}")
