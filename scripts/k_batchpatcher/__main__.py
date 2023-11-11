from __future__ import annotations

import argparse
import cProfile
import pathlib
import sys
import traceback
from copy import deepcopy
from io import StringIO
from typing import TYPE_CHECKING

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.exists():
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.common.language import Language, LocalizedString
from pykotor.extract.capsule import Capsule
from pykotor.helpers.path import Path, PureWindowsPath
from pykotor.resource.formats.gff import (
    GFF,
    GFFContent,
    GFFFieldType,
    GFFList,
    GFFStruct,
    bytes_gff,
    read_gff,
    write_gff,
)
from pykotor.resource.formats.tlk import TLK, read_tlk, write_tlk
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.path import CaseAwarePath
from scripts.k_batchpatcher.translate.language_translator import (
    TranslationOption,
    Translator,
    get_language_code,
)

if TYPE_CHECKING:
    import os

    from pykotor.extract.file import FileResource


OUTPUT_LOG: Path
LOGGING_ENABLED: bool
pytranslator: Translator | None = None
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


def relative_path_from_to(src, dst) -> Path:
    src_parts = list(src.parts)
    dst_parts = list(dst.parts)

    common_length = next(
        (i for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts)) if src_part != dst_part),
        len(src_parts),
    )
    rel_parts = dst_parts[common_length:]
    return Path(*rel_parts)


def do_patch(
    gff_struct: GFFStruct,
    gff_content: GFFContent,
    current_path: PureWindowsPath | os.PathLike | str | None = None,
):
    current_path = current_path if isinstance(current_path, PureWindowsPath) else PureWindowsPath(current_path or "GFFRoot")
    for label, ftype, value in gff_struct:
        if label.lower() == "mod_name":
            continue
        child_path = current_path / label

        if ftype == GFFFieldType.Struct:
            assert isinstance(value, GFFStruct)  # noqa: S101
            if parser_args.set_unskippable and "Skippable" in value._fields:
                log_output(f"Setting '{child_path}' as unskippable")
                value._fields["Skippable"]._value = 0

            do_patch(value, gff_content, child_path)
            continue

        if ftype == GFFFieldType.List:
            assert isinstance(value, GFFList)  # noqa: S101
            recurse_through_list(value, gff_content, child_path)
            continue

        if ftype == GFFFieldType.LocalizedString and parser_args.translate:  # and gff_content.value == GFFContent.DLG.value:
            assert isinstance(value, LocalizedString)  # noqa: S101
            new_substrings = deepcopy(value._substrings)
            for lang, gender, text in value:
                if pytranslator is not None and text is not None and text.strip():
                    log_output_with_separator(f"Translating CExoLocString at {child_path}", above=True)
                    translated_text = pytranslator.translate(text, from_lang=lang)
                    log_output(f"Translated {text} --> {translated_text}")
                    substring_id = LocalizedString.substring_id(parser_args.to_lang, gender)
                    new_substrings[substring_id] = translated_text
            value._substrings = new_substrings


def recurse_through_list(gff_list: GFFList, gff_content: GFFContent, current_path: PureWindowsPath):
    current_path = current_path if isinstance(current_path, PureWindowsPath) else PureWindowsPath(current_path or "GFFListRoot")
    for list_index, gff_struct in enumerate(gff_list):
        do_patch(gff_struct, gff_content, current_path / str(list_index))


def log_output(*args, **kwargs) -> None:
    # Create an in-memory text stream
    buffer = StringIO()

    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg = buffer.getvalue()

    # Write the captured output to the file
    encoding = parser_args.to_lang.get_encoding() if parser_args.to_lang else "utf-8"
    with OUTPUT_LOG.open("a", encoding=encoding, errors="ignore") as f:
        f.write(msg)

    # Print the captured output to console
    print(*args, **kwargs)  # noqa: T201


def handle_restype_and_patch(
    file_path: Path,
    bytes_data: bytes | None = None,
    ext: str | None = None,
    resref: FileResource | None = None,
    capsule: Capsule | None = None,
) -> None:
    # sourcery skip: extract-method
    data: bytes | Path = file_path if bytes_data is None else bytes_data
    if ext == "tlk":
        tlk: TLK | None = None
        try:
            log_output(f"Loading TLK '{file_path}'")
            tlk = read_tlk(data)
        except Exception as e:  # noqa: BLE001
            log_output(f"Error loading TLK {file_path}! {e!r}")
            return
        if not tlk:
            message = f"TLK resource missing in memory:\t'{file_path}'"
            log_output(message)
            return

        if pytranslator is not None:
            new_entries = deepcopy(tlk.entries)
            from_lang = tlk.language
            tlk.language = parser_args.to_lang
            new_file_path = file_path.parent / (
                f"{file_path.stem}_" + (get_language_code(parser_args.to_lang) or "UNKNOWN") + file_path.suffix
            )
            for strref, tlkentry in tlk:
                text = tlkentry.text
                if not text.strip() or text.isdigit():
                    continue
                log_output_with_separator(f"Translating TLK text at {file_path!s}", above=True)
                translated_text = pytranslator.translate(text, from_lang=from_lang)
                log_output(f"Translated {text} --> {translated_text}")
                new_entries[strref].text = translated_text
            tlk.entries = new_entries
            write_tlk(tlk, new_file_path)
            processed_files.add(new_file_path)
    if ext in gff_types:
        gff: GFF | None = None
        try:
            gff = read_gff(data)
        except Exception as e:  # noqa: BLE001
            log_output(f"[Error] loading GFF {file_path}! {e!r}")
            return

        if not gff:
            log_output(f"GFF resource missing in memory:\t'{file_path}'")
            return

        # TODO: Don't write files that are unchanged.
        if capsule is not None and resref is not None:
            do_patch(
                gff.root,
                gff.content,
                Path(
                    resref.filepath(),
                    f"{resref.identifier().resname}.{resref.identifier().restype.extension}",
                ),
            )
            new_file_path = file_path.parent / (
                f"{file_path.stem}_" + (get_language_code(parser_args.to_lang) or "UNKNOWN") + file_path.suffix
            )
            new_capsule = Capsule(
                new_file_path,
                create_nonexisting=True,
            )
            new_capsule._resources = deepcopy(capsule._resources)
            new_capsule.add(resref.resname(), resref.restype(), bytes_gff(gff))
            processed_files.add(new_capsule.path())
        else:
            do_patch(gff.root, gff.content, file_path.name)
            new_file_path = file_path.parent / (
                f"{file_path.stem}_" + (get_language_code(parser_args.to_lang) or "UNKNOWN") + file_path.suffix
            )
            write_gff(gff, new_file_path)
            processed_files.add(new_file_path)
        return

    return


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


def handle_capsule_and_patch(file: os.PathLike | str) -> None:
    c_file = file if isinstance(file, Path) else Path(file).resolve()
    if c_file in processed_files:
        return

    if not c_file.exists():
        log_output(f"Missing file:\t{c_file!s}")
        return

    if is_capsule_file(c_file.name):
        try:
            file_capsule = Capsule(file)
        except ValueError as e:
            log_output(f"Could not load '{c_file!s}'. Reason: {e!r}")
            return

        for resref in file_capsule:
            ext = resref.restype().extension.lower()
            handle_restype_and_patch(c_file, resref.data(), ext, resref, file_capsule)
    else:
        ext = c_file.suffix.lower()[1:]
        handle_restype_and_patch(c_file, ext=ext)


def recurse_directories(folder_path: os.PathLike | str) -> None:
    c_folderpath = folder_path if isinstance(folder_path, Path) else Path(folder_path).resolve()
    log_output_with_separator(f"Recursing through resources in the '{c_folderpath.name}' folder...", above=True)
    for file_path in c_folderpath.safe_rglob("*"):
        handle_capsule_and_patch(file_path)


# TODO: Use the Installation class
def patch_install(install_path: os.PathLike | str) -> None:
    install_path = install_path if isinstance(install_path, Path) else Path(install_path).resolve()
    log_output()
    log_output_with_separator(f"Patching install dir:\t{install_path}", above=True)
    log_output()

    handle_capsule_and_patch(install_path.joinpath("dialog.tlk"))
    modules_path: Path = install_path / "Modules"
    recurse_directories(modules_path)

    override_path: Path = install_path / "Override"
    recurse_directories(override_path)

    rims_path: Path = install_path / "rims"
    recurse_directories(rims_path)


def is_kotor_install_dir(path: os.PathLike | str) -> bool:
    c_path: CaseAwarePath = CaseAwarePath(path)
    return c_path.safe_isdir() and c_path.joinpath("chitin.key").exists()


def run_patches(path: Path):
    if not path.exists():
        log_output(f"--path1='{path}' does not exist on disk, cannot diff")
        return

    if is_kotor_install_dir(path):
        patch_install(path)
        return

    if path.is_dir():
        recurse_directories(path)
        return

    if path.is_file():
        handle_capsule_and_patch(path)


parser = argparse.ArgumentParser(description="Finds differences between two KOTOR installations")
parser.add_argument("--path", type=str, help="Path to the first K1/TSL install, file, or directory to patch.")
parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
parser.add_argument("--logging", type=bool, help="Whether to log the results to a file or not (default is enabled)")
parser.add_argument("--set-unskippable", type=str, help="Makes all dialog unskippable.")
parser.add_argument("--translate", type=str, help="Should we ai translate the TLK and all GFF locstrings?")
parser.add_argument("--to-lang", type=str, help="The language to translate the files to")
parser.add_argument("--from-lang", type=str, help="The language the files are written in (defaults to auto if available)")
parser.add_argument(
    "--use-profiler",
    type=bool,
    default=False,
    help="Use cProfile to find where most of the execution time is taking place in source code.",
)

parser_args, unknown = parser.parse_known_args()
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
            or "./log_batch_patcher.log"  # noqa: SIM222
            or input("Filepath of the desired output logfile: "),
        ).resolve()
        if OUTPUT_LOG.parent.exists():
            break
        print("Invalid path:", OUTPUT_LOG)
        parser.print_help()
translation_option: str = None  # type: ignore[assignment]
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
            msg = f"{parser_args.to_lang.upper()} is not a valid Language."  # type: ignore[union-attr, reportGeneralTypeIssues]
            parser_args.to_lang = None
            continue
        break
    while True:
        print(*TranslationOption.__members__)
        translation_option = input("Choose a preferred translator library: ")
        try:
            # Convert the string representation to the enum member, and then get its value
            translation_option = TranslationOption[translation_option]  # type: ignore[assignment]
        except KeyError:
            msg = f"{translation_option} is not a valid translation option. Please choose one of [{TranslationOption.__members__}]"  # type: ignore[union-attr, reportGeneralTypeIssues]
            translation_option = None  # type: ignore[assignment]
            continue
        break

parser_args.use_profiler = bool(parser_args.use_profiler)
input("Parameters have been set! Press [Enter] to start the patching process, or Ctrl+C to exit.")
profiler = None


if translation_option is not None and parser_args.to_lang != "ALL":
    pytranslator = Translator(parser_args.to_lang)
    pytranslator.translation_option = translation_option  # type: ignore[assignment]
try:
    if parser_args.use_profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    if parser_args.to_lang == "ALL":
        for lang in Language.__members__:
            print(f"Translating to {lang}...")
            enum_member_lang = Language[lang]
            parser_args.to_lang = enum_member_lang
            pytranslator = Translator(parser_args.to_lang)
            pytranslator.translation_option = translation_option  # type: ignore[assignment]
            comparison = run_patches(parser_args.path)
    else:
        comparison: bool | None = run_patches(parser_args.path)

    if profiler is not None:
        profiler.disable()
        profiler_output_file = Path("profiler_output.pstat").resolve()
        profiler.dump_stats(str(profiler_output_file))
        log_output(f"Profiler output saved to: {profiler_output_file}")

    log_output(f"Completed batch patcher of {parser_args.path}")
    sys.exit(0)
except KeyboardInterrupt:
    if profiler is not None:
        profiler.disable()
        profiler_output_file = Path("profiler_output.pstat").resolve()
        profiler.dump_stats(str(profiler_output_file))
        log_output(f"Profiler output saved to: {profiler_output_file}")
    raise
except Exception:  # noqa: BLE001
    log_output("Unhandled exception during the batchpatch process.")
    log_output(traceback.format_exc())
    input("The program must shut down. Press Enter to close.")
