#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import os
import pathlib
import platform
import sys
import tempfile
import tkinter as tk
import traceback

from contextlib import suppress
from copy import deepcopy
from threading import Thread
from tkinter import (
    colorchooser,
    filedialog,
    font as tkfont,
    messagebox,
    ttk,
)
from typing import TYPE_CHECKING, Any

from pykotor.resource.formats.tpc.io_tpc import TPCBinaryReader, TPCBinaryWriter
from pykotor.resource.salvage import validate_capsule

if getattr(sys, "frozen", False) is False:

    def add_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    absolute_file_path = pathlib.Path(__file__).resolve()
    pykotor_font_path = absolute_file_path.parents[4] / "Libraries" / "PyKotorFont" / "src" / "pykotor"
    if pykotor_font_path.is_dir():
        add_sys_path(pykotor_font_path.parent)
    pykotor_path = absolute_file_path.parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.is_dir():
        add_sys_path(pykotor_path.parent)
    utility_path = absolute_file_path.parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.is_dir():
        add_sys_path(utility_path.parent)


from loggerplus import RobustLogger

from batchpatcher.translate.language_translator import TranslationOption, Translator
from pykotor.common.alien_sounds import ALIEN_SOUNDS
from pykotor.common.language import Language, LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule, LazyCapsule
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.font.draw import write_bitmap_fonts
from pykotor.resource.formats.erf.erf_auto import write_erf
from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.formats.gff import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct, read_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.rim.rim_auto import write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.resource.formats.tpc.io_tga import TPCTGAReader, TPCTGAWriter
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.generics.are import read_are, write_are
from pykotor.resource.generics.dlg import read_dlg, write_dlg
from pykotor.resource.generics.git import read_git, write_git
from pykotor.resource.generics.jrl import read_jrl, write_jrl
from pykotor.resource.generics.pth import read_pth, write_pth
from pykotor.resource.generics.utc import read_utc, write_utc
from pykotor.resource.generics.utd import read_utd, write_utd
from pykotor.resource.generics.ute import read_ute, write_ute
from pykotor.resource.generics.uti import read_uti, write_uti
from pykotor.resource.generics.utm import read_utm, write_utm
from pykotor.resource.generics.utp import read_utp, write_utp
from pykotor.resource.generics.uts import read_uts, write_uts
from pykotor.resource.generics.utt import read_utt, write_utt
from pykotor.resource.generics.utw import read_utw, write_utw
from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.misc import is_any_erf_type_file, is_capsule_file
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.tslpatcher.logger import LogType, PatchLog, PatchLogger
from utility.error_handling import universal_simplify_exception
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Literal

    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.formats.tlk.tlk_data import TLKEntry

APP: KOTORPatchingToolUI
OUTPUT_LOG: Path
LOGGING_ENABLED: bool
processed_files: set[Path] = set()

gff_types: list[str] = list(GFFContent.get_extensions())
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
    def __init__(self):
        self.always_backup: bool = True
        self.chosen_languages: list[Language] = []
        self.create_fonts: bool = False
        self.convert_tga: Literal["TPC to TGA", "TGA to TPC", None] = None
        self.k1_convert_gffs: bool = False
        self.tsl_convert_gffs: bool = False
        self.custom_scaling: float = 1.0
        self.draw_bounds: bool = False
        self.font_color: float
        self.font_path: Path
        self.install_running: bool = False
        self.install_thread: Thread
        self.max_threads: int = 2
        self.patchlogger = PatchLogger()
        self.path: Path
        self.pytranslator: Translator = Translator(Language.ENGLISH)
        self.resolution: int = 2048
        self.set_unskippable: bool = False
        self.translate: bool = False
        self.translation_applied = True

    def __setitem__(self, key, value):
        # Equivalent to setting an attribute
        setattr(self, key, value)

    def __getitem__(self, key):
        # Equivalent to getting an attribute, returns None if not found
        return self.__dict__.get(key, None)

    def is_patching(self):
        return bool(self.translate or self.set_unskippable or self.convert_tga or self.k1_convert_gffs or self.tsl_convert_gffs)


SCRIPT_GLOBALS = Globals()


def get_font_paths_linux() -> list[Path]:
    font_dirs: list[Path] = [Path("/usr/share/fonts/"), Path("/usr/local/share/fonts/"), Path.home() / ".fonts"]
    return [font for font_dir in font_dirs for font in font_dir.glob("**/*.ttf")]


def get_font_paths_macos() -> list[Path]:
    font_dirs: list[Path] = [Path("/Library/Fonts/"), Path("/System/Library/Fonts/"), Path.home() / "Library/Fonts"]
    return [font for font_dir in font_dirs for font in font_dir.glob("**/*.ttf")]


def get_font_paths_windows() -> list[Path]:
    import winreg

    font_registry_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    fonts_dir = Path("C:/Windows/Fonts")
    font_paths = set()

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, font_registry_path) as key:
        for i in range(winreg.QueryInfoKey(key)[1]):  # Number of values in the key
            value: tuple[str, Any, int] = winreg.EnumValue(key, i)
            font_path: Path = fonts_dir / value[1]
            if font_path.suffix.lower() == ".ttf":  # Filtering for .ttf files
                font_paths.add(font_path)
    for file in fonts_dir.safe_rglob("*"):
        if file.suffix.lower() == ".ttf" and file.safe_isfile():
            font_paths.add(file)

    return list(font_paths)


def get_font_paths() -> list[Path]:
    with suppress(Exception):
        os_str = platform.system()
        if os_str == "Linux":
            return get_font_paths_linux()
        if os_str == "Darwin":
            return get_font_paths_macos()
        if os_str == "Windows":
            return get_font_paths_windows()
    msg = "Unsupported operating system"
    raise NotImplementedError(msg)


def relative_path_from_to(
    src: PurePath,
    dst: PurePath,
) -> Path:
    src_parts = list(src.parts)
    dst_parts = list(dst.parts)

    common_length = next(
        (i for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts)) if src_part != dst_part),
        len(src_parts),
    )
    rel_parts: list[str] = dst_parts[common_length:]
    return Path(*rel_parts)


def log_output(*args, **kwargs):
    # Create an in-memory text stream
    # buffer = StringIO()

    # Print to the in-memory stream
    # print(*args, **kwargs, file=buffer)

    # Retrieve the printed content
    # msg: str = buffer.getvalue()

    # Write the captured output to the file
    # with Path("log_batch_patcher.log").open("a", encoding="utf-8", errors="ignore") as f:
    #    f.write(msg)

    # Print the captured output to console
    # print(*args, **kwargs)
    SCRIPT_GLOBALS.patchlogger.add_note("\t".join(str(arg) for arg in args))


def visual_length(
    s: str,
    tab_length: int = 8,
) -> int:
    if "\t" not in s:
        return len(s)

    # Split the string at tabs, sum the lengths of the substrings,
    # and add the necessary spaces to account for the tab stops.
    parts: list[str] = s.split("\t")
    vis_length: int = sum(len(part) for part in parts)
    for part in parts[:-1]:  # all parts except the last one
        vis_length += tab_length - (len(part) % tab_length)
    return vis_length


def log_output_with_separator(
    message,
    below=True,
    above=False,
    surround=False,
):
    if above or surround:
        log_output(visual_length(message) * "-")
    log_output(message)
    if (below and not above) or surround:
        log_output(visual_length(message) * "-")


def patch_nested_gff(
    gff_struct: GFFStruct,
    gff_content: GFFContent,
    gff: GFF,
    current_path: PurePath | Path = None,  # type: ignore[pylance, assignment]
    made_change: bool = False,
    alien_vo_count: int = -1,
) -> tuple[bool, int]:
    if gff_content != GFFContent.DLG and not SCRIPT_GLOBALS.translate:
        # print(f"Skipping file at '{current_path}', translate not set.")
        return False, alien_vo_count
    if gff_content == GFFContent.DLG and SCRIPT_GLOBALS.set_unskippable:
        sound: ResRef | None = gff_struct.acquire("Sound", None, ResRef)
        sound_str = "" if sound is None else str(sound).strip().lower()
        if sound and sound_str.strip() and sound_str in ALIEN_SOUNDS:
            alien_vo_count += 1

    current_path = PurePath.pathify(current_path or "GFFRoot")
    for label, ftype, value in gff_struct:
        if label.lower() == "mod_name":
            continue
        child_path: PurePath = current_path / label

        if ftype == GFFFieldType.Struct:
            assert isinstance(value, GFFStruct), f"Not a GFFStruct instance: {value.__class__.__name__}: {value}"  # noqa: S101
            result_made_change, alien_vo_count = patch_nested_gff(value, gff_content, gff, child_path, made_change, alien_vo_count)
            made_change |= result_made_change
            continue

        if ftype == GFFFieldType.List:
            assert isinstance(value, GFFList), f"Not a GFFList instance: {value.__class__.__name__}: {value}"  # noqa: S101
            result_made_change, alien_vo_count = recurse_through_list(value, gff_content, gff, child_path, made_change, alien_vo_count)
            made_change |= result_made_change
            continue

        if ftype == GFFFieldType.LocalizedString and SCRIPT_GLOBALS.translate:
            assert isinstance(value, LocalizedString), f"{value.__class__.__name__}: {value}"  # noqa: S101
            log_output_with_separator(f"Translating CExoLocString at {child_path} to {SCRIPT_GLOBALS.pytranslator.to_lang.name}", above=True)
            made_change |= translate_locstring(value)
    return made_change, alien_vo_count


def recurse_through_list(
    gff_list: GFFList,
    gff_content: GFFContent,
    gff: GFF,
    current_path: PurePath | Path = None,  # type: ignore[pylance, assignment]
    made_change: bool = False,
    alien_vo_count: int = -1,
) -> tuple[bool, int]:
    current_path = PurePath.pathify(current_path or "GFFListRoot")
    for list_index, gff_struct in enumerate(gff_list):
        result_made_change, alien_vo_count = patch_nested_gff(gff_struct, gff_content, gff, current_path / str(list_index), made_change, alien_vo_count)
        made_change |= result_made_change
    return made_change, alien_vo_count


def fix_encoding(text: str, encoding: str) -> str:
    return text.encode(encoding=encoding, errors="ignore").decode(encoding=encoding, errors="ignore").strip()


def convert_gff_game(
    from_game: Game,
    resource: FileResource,
):
    to_game = Game.K2 if from_game.is_k1() else Game.K1
    new_name = resource.filename()
    converted_data: Path | bytearray = bytearray()
    if not resource.inside_capsule:
        new_name = f"{resource.resname()}_{to_game.name!s}.{resource.restype()!s}" if SCRIPT_GLOBALS.always_backup else resource.filename()
        converted_data = resource.filepath().with_name(new_name)
        savepath = converted_data
    else:
        # TODO(th3w1zard1): define this up the stack
        #savepath = (
        #    resource.filepath().with_name(f"{resource.filepath().stem}_{to_game.name!s}{resource.filepath().suffix}")
        #    if SCRIPT_GLOBALS.always_backup
        #    else resource.filepath()
        #)
        savepath = resource.filepath()
    log_output(f"Converting {resource.path_ident().parent}/{resource.path_ident().name} to {to_game.name}")
    generic: Any
    try:
        if resource.restype() is ResourceType.ARE:
            generic = read_are(resource.data(), offset=0, size=resource.size())
            write_are(generic, converted_data, to_game)

        elif resource.restype() is ResourceType.DLG:
            generic = read_dlg(resource.data(), offset=0, size=resource.size())
            write_dlg(generic, converted_data, to_game)

        elif resource.restype() is ResourceType.GIT:
            generic = read_git(resource.data(), offset=0, size=resource.size())
            write_git(generic, converted_data, to_game)

        elif resource.restype() is ResourceType.JRL:
            generic = read_jrl(resource.data(), offset=0, size=resource.size())
            write_jrl(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.PTH:
            generic = read_pth(resource.data(), offset=0, size=resource.size())
            write_pth(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTC:
            generic = read_utc(resource.data(), offset=0, size=resource.size())
            write_utc(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTD:
            generic = read_utd(resource.data(), offset=0, size=resource.size())
            write_utd(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTE:
            generic = read_ute(resource.data(), offset=0, size=resource.size())
            write_ute(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTI:
            generic = read_uti(resource.data(), offset=0, size=resource.size())
            write_uti(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTM:
            generic = read_utm(resource.data(), offset=0, size=resource.size())
            write_utm(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTP:
            generic = read_utp(resource.data(), offset=0, size=resource.size())
            write_utp(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTS:
            generic = read_uts(resource.data(), offset=0, size=resource.size())
            write_uts(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTT:
            generic = read_utt(resource.data(), offset=0, size=resource.size())
            write_utt(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTW:
            generic = read_utw(resource.data(), offset=0, size=resource.size())
            write_utw(generic, converted_data, game=to_game)

        else:
            log_output(f"Unsupported gff: {resource.identifier()}")
    except (OSError, ValueError):
        RobustLogger().error(f"Corrupted GFF: '{resource.path_ident()}', skipping...", exc_info=False)
        if not resource.inside_capsule:
            log_output(f"Corrupted GFF: '{resource.path_ident()}', skipping...")
            return
        log_output(f"Corrupted GFF: '{resource.path_ident()}', will start validation process of '{resource.filepath().name}'...")
        new_erfrim = validate_capsule(resource.filepath(), strict=True, game=to_game)
        if isinstance(new_erfrim, ERF):
            log_output(f"Saving salvaged ERF to '{savepath}'")
            write_erf(new_erfrim, savepath)
            return
        if isinstance(new_erfrim, RIM):
            log_output(f"Saving salvaged RIM to '{savepath}'")
            write_rim(new_erfrim, savepath)
            return
        log_output(f"Whole erf/rim is corrupt: {resource!r}")
        return

    if isinstance(converted_data, bytearray):
        log_output(f"Saving conversions in ERF/RIM at '{savepath}'")
        lazy_capsule = LazyCapsule(savepath, create_nonexisting=True)
        lazy_capsule.delete(resource.resname(), resource.restype())
        lazy_capsule.add(resource.resname(), resource.restype(), converted_data)


def translate_locstring(locstring: LocalizedString) -> bool:
    made_change = False
    new_substrings: dict[int, str] = deepcopy(locstring._substrings)  # noqa: SLF001
    for lang, gender, text in locstring:
        if SCRIPT_GLOBALS.pytranslator is not None and text is not None and text.strip():
            translated_text = SCRIPT_GLOBALS.pytranslator.translate(text, from_lang=lang)
            log_output(f"Translated {text} --> {translated_text}")
            substring_id = LocalizedString.substring_id(SCRIPT_GLOBALS.pytranslator.to_lang, gender)
            new_substrings[substring_id] = str(translated_text)
            made_change = True
    locstring._substrings = new_substrings  # noqa: SLF001
    return made_change


def process_translations(tlk: TLK, from_lang: Language):
    def translate_entry(tlkentry: TLKEntry, from_lang: Language) -> tuple[str, str]:
        text = tlkentry.text
        if not text.strip() or text.isdigit():
            return text, ""
        if "Do not translate this text" in text:
            return text, text
        if "actual text to be translated" in text:
            return text, text
        return text, SCRIPT_GLOBALS.pytranslator.translate(text, from_lang=from_lang)
    with concurrent.futures.ThreadPoolExecutor(max_workers=SCRIPT_GLOBALS.max_threads) as executor:
        # Create a future for each translation task
        future_to_strref: dict[concurrent.futures.Future[tuple[str, str]], int] = {
            executor.submit(translate_entry, tlkentry, from_lang): strref for strref, tlkentry in tlk
        }

        for future in concurrent.futures.as_completed(future_to_strref):
            strref: int = future_to_strref[future]
            try:
                original_text, translated_text = future.result()
                if translated_text.strip():
                    translated_text = fix_encoding(translated_text, SCRIPT_GLOBALS.pytranslator.to_lang.get_encoding())
                    tlk.replace(strref, translated_text)
                    log_output(f"#{strref} Translated {original_text} --> {translated_text}")
            except Exception as exc:  # pylint: disable=W0718  # noqa: BLE001
                RobustLogger().exception(f"tlk strref {strref} generated an exception")
                log_output(f"tlk strref {strref} generated an exception: {universal_simplify_exception(exc)}")
                log_output(traceback.format_exc())


def patch_resource(resource: FileResource) -> GFF | TPC | None:

    if resource.restype().extension.lower() == "tlk" and SCRIPT_GLOBALS.translate and SCRIPT_GLOBALS.pytranslator:
        tlk: TLK | None = None
        log_output(f"Loading TLK '{resource.filepath()}'")
        try:
            tlk = read_tlk(resource.data())
        except Exception:  # pylint: disable=W0718  # noqa: BLE001
            RobustLogger().exception(f"[Error] loading TLK '{resource.identifier()}' at '{resource.filepath()}'!")
            log_output(traceback.format_exc())
            return None

        from_lang: Language = tlk.language
        new_filename_stem = f"{resource.resname()}_" + (SCRIPT_GLOBALS.pytranslator.to_lang.get_bcp47_code() or "UNKNOWN")
        new_file_path = resource.filepath().parent / f"{new_filename_stem}.{resource.restype().extension}"
        tlk.language = SCRIPT_GLOBALS.pytranslator.to_lang
        log_output(f"Translating TalkTable resource at {resource.filepath()} to {SCRIPT_GLOBALS.pytranslator.to_lang.name}")
        process_translations(tlk, from_lang)
        write_tlk(tlk, new_file_path)
        processed_files.add(new_file_path)

    if resource.restype().extension.lower() == "tga" and SCRIPT_GLOBALS.convert_tga == "TGA to TPC":
        log_output(f"Converting TGA at {resource.path_ident()} to TPC...")
        try:
            return TPCTGAReader(resource.data()).load()
        except Exception:  # pylint: disable=W0718  # noqa: BLE001
            RobustLogger().exception(f"[Error] loading TGA '{resource.identifier()}' at '{resource.filepath()}'!")
            log_output(traceback.format_exc())
            return None

    if resource.restype().extension.lower() == "tpc" and SCRIPT_GLOBALS.convert_tga == "TPC to TGA":
        log_output(f"Converting TPC at {resource.path_ident()} to TGA...")
        try:
            return TPCBinaryReader(resource.data()).load()
        except Exception:  # pylint: disable=W0718  # noqa: BLE001
            RobustLogger().exception(f"[Error] loading TPC '{resource.identifier()}' at '{resource.filepath()}'!")
            log_output(traceback.format_exc())
            return None


    if resource.restype().name.upper() in {x.name for x in GFFContent}:
        if SCRIPT_GLOBALS.k1_convert_gffs and not resource.inside_capsule:
            convert_gff_game(Game.K2, resource)
        if SCRIPT_GLOBALS.tsl_convert_gffs and not resource.inside_capsule:
            convert_gff_game(Game.K1, resource)
        gff: GFF | None = None
        try:
            # log_output(f"Loading {resource.resname()}.{resource.restype().extension} from '{resource.filepath().name}'")
            gff = read_gff(resource.data())
            alien_owner: str | None = None
            if gff.content is GFFContent.DLG and SCRIPT_GLOBALS.set_unskippable:
                skippable = gff.root.acquire("Skippable", None)
                if skippable not in {0, "0"}:
                    conversationtype = gff.root.acquire("ConversationType", None)
                    if conversationtype not in {"1", 1}:
                        alien_owner = gff.root.acquire("AlienRaceOwner", None)  # TSL only
            made_change, alien_vo_count = patch_nested_gff(
                gff.root,
                gff.content,
                gff,
                resource.path_ident(),  # noqa: SLF001
            )
            if (
                SCRIPT_GLOBALS.set_unskippable
                and alien_owner in {0, "0", None}
                and alien_vo_count != -1
                and alien_vo_count < 3
                and gff.content is GFFContent.DLG
            ):
                skippable = gff.root.acquire("Skippable", None)
                if skippable not in {0, "0"}:
                    conversationtype = gff.root.acquire("ConversationType", None)
                    if conversationtype not in {"1", 1}:
                        print(
                            "Skippable",
                            skippable,
                            "alien_vo_count",
                            alien_vo_count,
                            "ConversationType",
                            conversationtype
                        )
                        log_output(f"Setting dialog {resource.path_ident()} as unskippable")
                        made_change |= True
                        gff.root.set_uint8("Skippable", 0)
            if made_change:
                return gff
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            log_output(f"[Error] cannot load corrupted GFF '{resource.path_ident()}'!")
            if not isinstance(e, (OSError, ValueError)):
                RobustLogger().exception(f"[Error] loading GFF '{resource.path_ident()}'!")
                log_output(traceback.format_exc())
            # raise
            return None
    return None


def patch_and_save_noncapsule(
    resource: FileResource,
    savedir: Path | None = None,
):
    patched_data: GFF | TPC | None = patch_resource(resource)
    if patched_data is None:
        return
    capsule = Capsule(resource.filepath()) if resource.inside_capsule else None

    if isinstance(patched_data, GFF):
        new_data = bytes_gff(patched_data)

        new_gff_filename = resource.filename()
        if SCRIPT_GLOBALS.translate:
            new_gff_filename = f"{resource.resname()}_{SCRIPT_GLOBALS.pytranslator.to_lang.get_bcp47_code()}.{resource.restype().extension}"

        new_path = (savedir or resource.filepath().parent) / new_gff_filename
        if new_path.exists() and savedir:
            log_output(f"Skipping '{new_gff_filename}', already exists on disk")
        else:
            log_output(f"Saving patched gff to '{new_path}'")
            BinaryWriter.dump(new_path, new_data)
    elif isinstance(patched_data, TPC):
        if capsule is None:
            txi_file = resource.filepath().with_suffix(".txi")
            if txi_file.is_file():
                print("Embedding TXI information...")
                data: bytes = BinaryReader.load_file(txi_file)
                txi_text: str = decode_bytes_with_fallbacks(data)
                patched_data.txi = txi_text
        else:
            txi_data = capsule.resource(resource.resname(), ResourceType.TXI)
            if txi_data is not None:
                print("Embedding TXI information from resource found in capsule...")
                txi_text = decode_bytes_with_fallbacks(txi_data)
                patched_data.txi = txi_text

        new_path = (savedir or resource.filepath().parent) / resource.resname()
        if SCRIPT_GLOBALS.convert_tga == "TGA to TPC":
            new_path = new_path.with_suffix(".tpc")
            writer = TPCBinaryWriter
        else:
            new_path = new_path.with_suffix(".tga")
            writer = TPCTGAWriter
        if new_path.exists():
            log_output(f"Skipping '{new_path}', already exists on disk")
        else:
            log_output(f"Saving converted tpc to '{new_path}'")
            writer(patched_data, new_path).write()


def patch_capsule_file(c_file: Path):
    new_data: bytes
    log_output(f"Load {c_file.name}")
    try:
        file_capsule = Capsule(c_file)
    except ValueError as e:
        RobustLogger().exception(f"Could not load '{c_file}'")
        log_output(f"Could not load '{c_file}'. Reason: {universal_simplify_exception(e)}")
        return

    new_filepath: Path = c_file
    if SCRIPT_GLOBALS.translate:
        new_filepath = c_file.parent / f"{c_file.stem}_{SCRIPT_GLOBALS.pytranslator.to_lang.get_bcp47_code()}{c_file.suffix}"

    new_resources: list[tuple[str, ResourceType, bytes]] = []
    omitted_resources: list[ResourceIdentifier] = []
    for resource in file_capsule:
        if SCRIPT_GLOBALS.is_patching():
            patched_data: GFF | TPC | None = patch_resource(resource)
            if isinstance(patched_data, GFF):
                new_data = bytes_gff(patched_data) if patched_data else resource.data()
                log_output(f"Adding patched GFF resource '{resource.identifier()}' to capsule {new_filepath.name}")
                new_resources.append((resource.resname(), resource.restype(), new_data))
                omitted_resources.append(resource.identifier())

            elif isinstance(patched_data, TPC):
                txi_resource = file_capsule.resource(resource.resname(), ResourceType.TXI)
                if txi_resource is not None:
                    patched_data.txi = txi_resource.decode("ascii", errors="ignore")
                    omitted_resources.append(ResourceIdentifier(resource.resname(), ResourceType.TXI))

                new_data = bytes_tpc(patched_data)
                log_output(f"Adding patched TPC resource '{resource.identifier()}' to capsule {new_filepath.name}")
                new_resources.append((resource.resname(), ResourceType.TPC, new_data))
                omitted_resources.append(resource.identifier())

    if SCRIPT_GLOBALS.is_patching():
        erf_or_rim: ERF | RIM = ERF(ERFType.from_extension(new_filepath)) if is_any_erf_type_file(c_file) else RIM()
        for resource in file_capsule:
            if resource.identifier() not in omitted_resources:
                erf_or_rim.set_data(resource.resname(), resource.restype(), resource.data())
        for resinfo in new_resources:
            erf_or_rim.set_data(*resinfo)

        log_output(f"Saving back to {new_filepath.name}")
        if is_any_erf_type_file(c_file):
            write_erf(erf_or_rim, new_filepath)  # type: ignore[arg-type, reportArgumentType]
        else:
            write_rim(erf_or_rim, new_filepath)  # type: ignore[arg-type, reportArgumentType]


def patch_erf_or_rim(
    resources: list[FileResource],
    filename: str,
    erf_or_rim: RIM | ERF,
) -> PurePath:
    omitted_resources: list[ResourceIdentifier] = []
    new_filename = PurePath(filename)
    if SCRIPT_GLOBALS.translate:
        new_filename = PurePath(f"{new_filename.stem}_{SCRIPT_GLOBALS.pytranslator.to_lang.name}{new_filename.suffix}")

    for resource in resources:
        patched_data: GFF | TPC | None = patch_resource(resource)
        if isinstance(patched_data, GFF):
            log_output(f"Adding patched GFF resource '{resource.identifier()}' to {new_filename}")
            new_data: bytes = bytes_gff(patched_data) if patched_data else resource.data()
            erf_or_rim.set_data(resource.resname(), resource.restype(), new_data)
            omitted_resources.append(resource.identifier())

        elif isinstance(patched_data, TPC):
            log_output(f"Adding patched TPC resource '{resource.resname()}' to {new_filename}")
            txi_resource: FileResource | None = next(
                (res for res in resources if res.resname() == resource.resname() and res.restype() is ResourceType.TXI),
                None,
            )
            if txi_resource:
                patched_data.txi = txi_resource.data().decode("ascii", errors="ignore")
                omitted_resources.append(txi_resource.identifier())

            new_data = bytes_tpc(patched_data)
            erf_or_rim.set_data(resource.resname(), ResourceType.TPC, new_data)
            omitted_resources.append(resource.identifier())
    for resource in resources:
        if resource.identifier() not in omitted_resources:
            try:
                erf_or_rim.set_data(resource.resname(), resource.restype(), resource.data())
            except (OSError, ValueError):
                RobustLogger().error(f"Corrupted resource: {resource!r}, skipping...", exc_info=True)
                log_output(f"Corrupted resource: {resource!r}, skipping...")
            except Exception:
                RobustLogger().exception(f"Unexpected exception occurred for resource {resource!r}")
    return new_filename


def patch_file(file: os.PathLike | str):
    c_file = Path.pathify(file)
    if c_file in processed_files:
        return

    if is_capsule_file(c_file):
        patch_capsule_file(c_file)

    elif SCRIPT_GLOBALS.is_patching():
        patch_and_save_noncapsule(FileResource.from_path(c_file))


def patch_folder(folder_path: os.PathLike | str):
    c_folderpath = Path.pathify(folder_path)
    log_output_with_separator(f"Recursing through resources in the '{c_folderpath.name}' folder...", above=True)
    for file_path in c_folderpath.safe_rglob("*"):
        patch_file(file_path)


def patch_install(install_path: os.PathLike | str):
    log_output()
    log_output_with_separator(f"Using install dir for operations:\t{install_path}", above=True)
    log_output("Note: Logging to this UI is extremely slow, this app will mostly use the .log files instead. Don't panic if there's no output on screen.")
    log_output()

    k_install = Installation(install_path)
    # k_install.reload_all()
    if SCRIPT_GLOBALS.is_patching():
        log_output_with_separator("Patching modules...")
        if SCRIPT_GLOBALS.k1_convert_gffs or SCRIPT_GLOBALS.tsl_convert_gffs:
            for module_name in k_install._modules:  # noqa: SLF001
                log_output(f"Validating ERF/RIM in the Modules folder: '{module_name}'")
                module_path = k_install.module_path().joinpath(module_name)
                to_game = Game.K2 if SCRIPT_GLOBALS.tsl_convert_gffs else Game.K1
                erf_or_rim = validate_capsule(module_path, strict=True, game=to_game)
                if isinstance(erf_or_rim, ERF):
                    write_erf(erf_or_rim, module_path)
                elif isinstance(erf_or_rim, RIM):
                    write_rim(erf_or_rim, module_path)
                else:
                    log_output(f"Unknown ERF/RIM: '{module_path.relative_to(k_install.path().parent)}'")
        k_install.load_modules()
        for module_name, resources in k_install._modules.items():  # noqa: SLF001
            res_ident = ResourceIdentifier.from_path(module_name)
            filename = str(res_ident)
            filepath = k_install.path().joinpath("Modules", filename)
            if res_ident.restype is ResourceType.RIM:
                if filepath.with_suffix(".mod").safe_isfile():
                    log_output(f"Skipping {filepath}, a .mod already exists at this path.")
                    continue
                new_rim = RIM()
                new_rim_filename = patch_erf_or_rim(resources, module_name, new_rim)
                log_output(f"Saving '{new_rim_filename}'")
                write_rim(new_rim, filepath.parent / new_rim_filename, res_ident.restype)

            elif res_ident.restype.name in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):
                new_erf = ERF(ERFType.from_extension(filepath.suffix))
                if res_ident.restype is ResourceType.SAV:
                    new_erf.is_save_erf = True
                new_erf_filename = patch_erf_or_rim(resources, module_name, new_erf)
                log_output(f"Saving '{new_erf_filename}'")
                write_erf(new_erf, filepath.parent / new_erf_filename, res_ident.restype)

            else:
                log_output("Unsupported module:", module_name, " - cannot patch")

    # nothing by the game uses these rims as far as I can tell
    # log_output_with_separator("Patching rims...")
    # for rim_name, resources in k_install._rims.items():
    #    new_rim = RIM()
    #    res_ident = ResourceIdentifier.from_path(module_name)
    #    filename = str(res_ident)
    #    filepath = k_install.path().joinpath("rims", filename)
    #    new_rim_filename = patch_erf_or_rim(resources, rim_name, new_rim)
    #    log_output(f"Patching {new_rim_filename} in the 'rims' folder ")
    #    write_rim(new_rim, filepath.parent / new_rim_filename)

    if SCRIPT_GLOBALS.is_patching():
        log_output_with_separator("Patching Override...")
    override_path = k_install.override_path()
    override_path.mkdir(exist_ok=True, parents=True)
    for folder in k_install.override_list():
        for resource in k_install.override_resources(folder):
            if SCRIPT_GLOBALS.is_patching():
                patch_and_save_noncapsule(resource)

    if SCRIPT_GLOBALS.is_patching():
        log_output_with_separator("Extract and patch BIF data, saving to Override (will not overwrite)")
    for resource in k_install.core_resources():
        if SCRIPT_GLOBALS.translate or SCRIPT_GLOBALS.set_unskippable:
            patch_and_save_noncapsule(resource, savedir=override_path)

    patch_file(k_install.path().joinpath("dialog.tlk"))


def is_kotor_install_dir(path: os.PathLike | str) -> bool:
    c_path: CaseAwarePath = CaseAwarePath(path)
    return bool(c_path.safe_isdir() and c_path.joinpath("chitin.key").safe_isfile())


def determine_input_path(path: Path) -> None:
    # sourcery skip: assign-if-exp, reintroduce-else
    if not path.safe_exists() or path.resolve() == Path.cwd().resolve():
        import errno

        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    if is_kotor_install_dir(path):
        return patch_install(path)

    if path.safe_isdir():
        return patch_folder(path)

    if path.safe_isfile():
        return patch_file(path)
    return None


def execute_patchloop_thread() -> str | None:
    try:
        SCRIPT_GLOBALS.install_running = True
        do_main_patchloop()
        SCRIPT_GLOBALS.install_running = False
    except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
        RobustLogger().exception("Unhandled exception during the patching process.")
        log_output(traceback.format_exc())
        SCRIPT_GLOBALS.install_running = False
        return messagebox.showerror("Error", f"An error occurred during patching\n{universal_simplify_exception(e)}")


def do_main_patchloop() -> str:
    # Validate args
    if not SCRIPT_GLOBALS.chosen_languages:
        if SCRIPT_GLOBALS.translate:
            return messagebox.showwarning("No language chosen", "Select a language first if you want to translate")
        if SCRIPT_GLOBALS.create_fonts:
            return messagebox.showwarning("No language chosen", "Select a language first to create fonts.")
    if SCRIPT_GLOBALS.create_fonts and (not Path(SCRIPT_GLOBALS.font_path).name or not Path(SCRIPT_GLOBALS.font_path).safe_isfile()):
        return messagebox.showwarning(f"Font path not found {SCRIPT_GLOBALS.font_path}", "Please set your font path to a valid TTF font file.")
    if SCRIPT_GLOBALS.translate and not SCRIPT_GLOBALS.translation_applied:
        return messagebox.showwarning(
            "Bad translation args",
            "Cannot start translation, you have not applied your translation options. (api key, db path, server url etc)",
        )

    # Patching logic
    has_action = False
    if SCRIPT_GLOBALS.create_fonts:
        for lang in SCRIPT_GLOBALS.chosen_languages:
            create_font_pack(lang)
        has_action = True
    if SCRIPT_GLOBALS.translate:
        has_action = True
        for lang in SCRIPT_GLOBALS.chosen_languages:
            main_translate_loop(lang)
    if SCRIPT_GLOBALS.is_patching():
        determine_input_path(Path(SCRIPT_GLOBALS.path))
        has_action = True
    if not has_action:
        return messagebox.showwarning("No options chosen", "Select what you want to do.")

    log_output(f"Completed batch patcher of {SCRIPT_GLOBALS.path}")
    return messagebox.showinfo("Patching complete!", "Check the log files for more information.")


def main_translate_loop(lang: Language):
    print(f"Translating to {lang.name}...")
    SCRIPT_GLOBALS.pytranslator.to_lang = lang
    determine_input_path(Path(SCRIPT_GLOBALS.path))


def create_font_pack(lang: Language):
    print(f"Creating font pack for '{lang.name}'...")
    write_bitmap_fonts(
        Path.cwd() / lang.name,
        SCRIPT_GLOBALS.font_path,
        (SCRIPT_GLOBALS.resolution, SCRIPT_GLOBALS.resolution),
        lang,
        SCRIPT_GLOBALS.draw_bounds,
        SCRIPT_GLOBALS.custom_scaling,
        font_color=SCRIPT_GLOBALS.font_color,
    )


def assign_to_globals(instance: KOTORPatchingToolUI):
    for attr, value in instance.__dict__.items():
        # Convert tkinter variables to their respective Python types
        if isinstance(value, tk.StringVar):
            SCRIPT_GLOBALS[attr] = None if value.get() == "None" or value.get() == "" else value.get()
        elif isinstance(value, tk.BooleanVar):
            SCRIPT_GLOBALS[attr] = bool(value.get())
        elif isinstance(value, tk.IntVar):
            SCRIPT_GLOBALS[attr] = int(value.get())
        elif isinstance(value, tk.DoubleVar):
            SCRIPT_GLOBALS[attr] = float(value.get())
        else:
            # Directly assign if it's not a tkinter variable
            SCRIPT_GLOBALS[attr] = value
    SCRIPT_GLOBALS.font_path = Path(instance.font_path.get())
    SCRIPT_GLOBALS.path = Path(instance.path.get())


class KOTORPatchingToolUI:
    def __init__(self, root: tk.Tk):
        self.root: tk.Tk = root
        root.title("KOTOR BatchPatcher")

        self.path = tk.StringVar()
        self.set_unskippable = tk.BooleanVar(value=SCRIPT_GLOBALS.set_unskippable)
        self.translate = tk.BooleanVar(value=SCRIPT_GLOBALS.translate)
        self.create_fonts = tk.BooleanVar(value=SCRIPT_GLOBALS.create_fonts)
        self.font_path = tk.StringVar()
        self.resolution = tk.IntVar(value=SCRIPT_GLOBALS.resolution)
        self.custom_scaling = tk.DoubleVar(value=SCRIPT_GLOBALS.custom_scaling)
        self.font_color = tk.StringVar()
        self.draw_bounds = tk.BooleanVar(value=False)
        self.convert_tga = tk.StringVar(value="None")
        self.k1_convert_gffs = tk.BooleanVar(value=False)
        self.tsl_convert_gffs = tk.BooleanVar(value=False)

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

        self.initialize_logger()
        self.setup_ui()

    def write_log(self, log: PatchLog):
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
        self.description_text.insert(tk.END, log.formatted_message + os.linesep)
        self.description_text.see(tk.END)
        self.description_text.config(state=tk.DISABLED)

    def initialize_logger(self):
        SCRIPT_GLOBALS.patchlogger.verbose_observable.subscribe(self.write_log)
        SCRIPT_GLOBALS.patchlogger.note_observable.subscribe(self.write_log)
        SCRIPT_GLOBALS.patchlogger.warning_observable.subscribe(self.write_log)
        SCRIPT_GLOBALS.patchlogger.error_observable.subscribe(self.write_log)

    def on_gamepaths_chosen(self, event: tk.Event):
        """Adjust the combobox after a short delay."""
        self.root.after(10, lambda: self.move_cursor_to_end(event.widget))

    def move_cursor_to_end(self, combobox: ttk.Combobox):
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
        browse_folder_button = ttk.Button(self.root, text="Browse Folder", command=self.browse_source_folder)
        browse_folder_button.grid(row=row, column=3, padx=2)  # Stick to both sides within its cell
        browse_folder_button.config(width=15)
        browse_file_button = ttk.Button(self.root, text="Browse File", command=self.browse_source_file)
        browse_file_button.grid(row=row+1, column=3, padx=2)  # Stick to both sides within its cell
        browse_file_button.config(width=15)
        row += 1

        # Skippable
        ttk.Label(self.root, text="Make all dialog unskippable:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.set_unskippable).grid(row=row, column=1)
        row += 1

        # TGA <-> TPC
        ttk.Label(self.root, text="Convert TGAs to TPCs or TPCs to TGAs:").grid(row=row, column=0)
        self.convert_tga_combobox = ttk.Combobox(self.root, textvariable=self.convert_tga, state="readonly")
        self.convert_tga_combobox["values"] = ("None", "TGA to TPC", "TPC to TGA")
        self.convert_tga_combobox.grid(row=row, column=1)
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
        def on_value_change():
            SCRIPT_GLOBALS.max_threads = int(spinbox_value.get())

        ttk.Label(self.root, text="Max Translation Threads:").grid(row=row, column=0)
        spinbox_value = tk.StringVar(value=str(SCRIPT_GLOBALS.max_threads))
        self.spinbox = tk.Spinbox(root, from_=1, to=2, increment=1, command=on_value_change, textvariable=spinbox_value)
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

        # Convert GFFs to K1
        ttk.Label(self.root, text="Convert GFFs to K1").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.k1_convert_gffs).grid(row=row, column=1)
        row += 1

        # Convert GFFs to TSL
        ttk.Label(self.root, text="Convert GFFs to TSL").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.tsl_convert_gffs).grid(row=row, column=1)
        row += 1

        # Font Path
        ttk.Label(self.root, text="Font Path:").grid(row=row, column=0)
        font_paths = [str(path_str) for path_str in get_font_paths()]

        # Calculate the pixel width of the longest string in the list
        from tkinter.font import Font

        font = Font(family="TkDefaultFont")  # Use the default font and size used by ttk.Combobox
        max_width = max(font.measure(path) for path in font_paths)

        # Configure the Combobox to be wide enough for the longest string
        combobox = ttk.Combobox(self.root, textvariable=self.font_path, values=font_paths)
        combobox.grid(row=row, column=1)

        # Set the width of the Combobox in characters, not pixels
        # Find the average character width in pixels and divide max_width by this number
        avg_char_width = font.measure("0")  # '0' is typically used as an average character
        combobox_width = max_width // avg_char_width
        combobox.config(width=combobox_width)
        ttk.Button(self.root, text="Browse", command=self.browse_font_path).grid(row=row, column=2)
        row += 1

        # Font - Draw Rectangles
        ttk.Label(self.root, text="Draw borders:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, variable=self.draw_bounds).grid(row=row, column=1)
        row += 1

        # Font Resolution
        ttk.Label(self.root, text="Font Resolution:").grid(row=row, column=0)
        ttk.Entry(self.root, textvariable=self.resolution).grid(row=row, column=1)
        row += 1

        def choose_color():
            color_code: tuple[None, None] | tuple[tuple[float, float, float], str] = colorchooser.askcolor(title="Choose a color")
            if color_code[1]:
                self.font_color.set(color_code[1])

        # TODO: parse the .gui or wherever the actual color is stored.
        # self.font_color = tk.StringVar()
        # ttk.Label(self.root, text="Font Color:").grid(row=row, column=0)
        # ttk.Entry(self.root, textvariable=self.font_color).grid(row=row, column=1)
        # tk.Button(self.root, text="Choose Color", command=choose_color).grid(row=row, column=2)
        # row += 1

        # Font Scaling
        ttk.Label(self.root, text="Font Scaling:").grid(row=row, column=0)
        ttk.Entry(self.root, textvariable=self.custom_scaling).grid(row=row, column=1)
        row += 1

        # Logging Enabled
        # ttk.Label(self.root, text="Enable Logging:").grid(row=row, column=0)
        # ttk.Checkbutton(self.root, text="Yes", variable=self.logging_enabled).grid(row=row, column=1)
        # row += 1

        # Use Profiler
        # ttk.Label(self.root, text="Use Profiler:").grid(row=row, column=0)
        # ttk.Checkbutton(self.root, text="Yes", variable=self.use_profiler).grid(row=row, column=1)
        # row += 1

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

    def on_translation_option_chosen(self, event):
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
            ttk.Button(
                self.translation_options_frame,
                text="Apply Options",
                command=lambda: self.apply_translation_option(varname=varname, value=value),
            ).grid(row=row, column=2)
        else:
            self.translation_applied = True

    def apply_translation_option(
        self,
        varname: str,
        value: Any,
    ):
        setattr(SCRIPT_GLOBALS.pytranslator, varname, value)  # TODO: add all the variable names to __init__ of Translator class
        self.write_log(PatchLog(f"Applied Options for {self.translation_option.get()}: {varname} = {value}", LogType.NOTE))
        cur_toption: TranslationOption = TranslationOption.__members__[self.translation_option.get()]
        msg: str = cur_toption.validate_args(SCRIPT_GLOBALS.pytranslator)
        if msg:
            messagebox.showwarning("Invalid translation options", msg)
            return
        self.translation_applied = True

    def create_language_checkbuttons(self, row: int):
        # Show/Hide Languages
        self.show_hide_language = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.root, text="Show/Hide Languages:", command=lambda: self.toggle_language_frame(self.show_hide_language)).grid(row=row, column=1)
        row += 1

        # Middle area for text and scrollbar
        self.language_row = row
        self.language_frame = ttk.Frame(self.root)
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
        sorted_languages: list[Language] = sorted(Language, key=lambda lang: lang.name)

        # Create Checkbuttons for each language
        column = 0
        for lang in sorted_languages:
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

    def update_chosen_languages(
        self,
        lang: Language,
        lang_var: tk.BooleanVar,
    ):
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

    def browse_source_folder(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path.set(directory)

    def browse_source_file(self):
        directory = filedialog.askopenfilename()
        if directory:
            self.path.set(directory)

    def browse_font_path(self):
        file = filedialog.askopenfilename()
        if file:
            self.font_path.set(file)

    def start_patching(self) -> str | None:
        if SCRIPT_GLOBALS.install_running:
            return messagebox.showerror("Install already running", "Please wait for all operations to complete. Check the console/output for details.")
        self.install_button.config(state="normal")
        try:
            assign_to_globals(self)
            # Mapping UI input to script logic
            try:
                path = Path(SCRIPT_GLOBALS.path).resolve()
            except OSError as e:
                return messagebox.showerror("Error", f"Invalid path '{SCRIPT_GLOBALS.path}'\n{universal_simplify_exception(e)}")
            else:
                if not path.safe_exists():
                    return messagebox.showerror("Error", "Invalid path")
            SCRIPT_GLOBALS.pytranslator = Translator(Language.ENGLISH)
            SCRIPT_GLOBALS.pytranslator.translation_option = TranslationOption[self.translation_option.get()]
            self.toggle_output_frame(tk.BooleanVar(value=False))

            SCRIPT_GLOBALS.install_thread = Thread(target=execute_patchloop_thread, name="Patchloop_Thread")
            SCRIPT_GLOBALS.install_thread.start()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            RobustLogger().exception("Unhandled exception during the patching process.")
            messagebox.showerror("Unhandled exception", str(universal_simplify_exception(e) + "\n" + traceback.format_exc()))
            SCRIPT_GLOBALS.install_running = False
            self.install_button.config(state=tk.DISABLED)
        return None


def is_running_from_temp() -> bool:
    app_path = Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)


if __name__ == "__main__":
    if is_running_from_temp():
        messagebox.showerror("Error", "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        sys.exit("Exiting: Application was run from a temporary or zip directory.")
    try:
        root = tk.Tk()
        APP = KOTORPatchingToolUI(root)
        root.mainloop()
    except Exception:  # pylint: disable=W0718  # noqa: BLE001, RUF100
        RobustLogger().exception("Unhandled main exception")
        log_output(traceback.format_exc())
        raise
