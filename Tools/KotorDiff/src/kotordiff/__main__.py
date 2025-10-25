#!/usr/bin/env python3
from __future__ import annotations

import cProfile
import difflib
import io
import os
import pathlib
import sys
import traceback

from argparse import ArgumentParser
from contextlib import suppress
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, Any, Callable

import merge3

if getattr(sys, "frozen", False) is False:

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        update_sys_path(utility_path.parent)
    kotordiff_path = pathlib.Path(__file__).parent
    if kotordiff_path.exists():
        update_sys_path(kotordiff_path.parent)

from kotordiff.diff_analyzers import DiffAnalyzerFactory
from kotordiff.diff_objects import DiffFormat
from kotordiff.formatters import FormatterFactory
from kotordiff.ini_serializer import TSLPatcherINISerializer
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats import gff, lip, tlk, twoda
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.path import CaseAwarePath
from utility.error_handling import universal_simplify_exception
from utility.misc import generate_hash
from utility.system.path import Path, PurePath, PureWindowsPath

# Import the new logging and diff systems
try:
    from kotordiff.logger import LogLevel, OutputMode, setup_logger
except ImportError:
    # Fallback for when running as script
    LogLevel = None  # type: ignore[assignment, misc]
    OutputMode = None  # type: ignore[assignment, misc]
    setup_logger = None  # type: ignore[assignment, misc]
    DiffFormat = None  # type: ignore[assignment, misc]
    FormatterFactory = None  # type: ignore[assignment, misc]

if TYPE_CHECKING:
    from pykotor.extract.file import (
        FileResource,
        FileResource as CapsuleResource,
    )
    from pykotor.resource.formats.tlk.tlk_data import TLK

CURRENT_VERSION = "1.0.0"


@dataclass
class GlobalConfig:
    """Global configuration state for KotorDiff."""

    output_log: Path | None = None
    logging_enabled: bool | None = None
    parser_args: Any = None
    parser: Any = None


# Global configuration instance
_global_config = GlobalConfig()


@dataclass
class DiffContext:
    """Context for diff operations, grouping related file paths."""

    file1_rel: Path
    file2_rel: Path
    ext: str
    resname: str | None = None
    skip_nss: bool = False  # Skip .nss files when comparing installations

    @property
    def where(self) -> PureWindowsPath | str:
        """Get the display name for the resource being compared."""
        if self.resname:
            return PureWindowsPath(self.file1_rel.name, f"{self.resname}.{self.ext}")
        return self.file1_rel.name


@dataclass
class IniGenerationConfig:
    """Configuration for INI generation (changes.ini) for both 2-way and 3-way diffs."""

    generate_ini: bool = True
    out_ini: Path | None = None


@dataclass
class ModificationsByType:
    """Typed collection of modifications grouped by format type."""

    twoda: list[Any]  # List[Modifications2DA]
    gff: list[Any]  # List[ModificationsGFF]
    tlk: list[Any]  # List[ModificationsTLK]
    ssf: list[Any]  # List[ModificationsSSF]
    install: list[tuple[str, list[str]]]  # List[(folder, [filenames])]

    @classmethod
    def create_empty(cls) -> ModificationsByType:
        """Create an empty ModificationsByType instance."""
        return cls(twoda=[], gff=[], tlk=[], ssf=[], install=[])


def log_output(*args, **kwargs):
    # Create an in-memory text stream
    buffer = StringIO()

    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg = buffer.getvalue()

    # Print the captured output to console with Unicode error handling
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode with error handling for Windows console
        # Replace unencodable characters with ? or similar
        try:
            safe_msg = msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(safe_msg, **kwargs)
        except Exception:  # noqa: BLE001
            # Last resort: use ASCII with backslashreplace
            safe_msg = msg.encode("ascii", errors="backslashreplace").decode("ascii")
            print(safe_msg, **kwargs)

    if not _global_config.logging_enabled or not _global_config.parser_args or not _global_config.parser:
        return

    if not _global_config.output_log:
        chosen_log_file_path: str = "log_install_differ.log"
        _global_config.output_log = Path(chosen_log_file_path).resolve()
        assert _global_config.output_log is not None
        if not _global_config.output_log.parent.safe_isdir():
            while True:
                chosen_log_file_path = _global_config.parser_args.output_log or input("Filepath of the desired output logfile: ").strip() or "log_install_differ.log"
                _global_config.output_log = Path(chosen_log_file_path).resolve()
                assert _global_config.output_log is not None
                if _global_config.output_log.parent.safe_isdir():
                    break
                print("Invalid path:", _global_config.output_log)
                _global_config.parser.print_help()

    # Write the captured output to the file (always use UTF-8 for file)
    with _global_config.output_log.open("a", encoding="utf-8") as f:
        f.write(msg)


def find_module_root(filename: str) -> str:
    """Extract the root name from a module filename.

    This replicates the logic from Module.find_root without importing pykotor.common.module.
    For example: "tat_m18ac.rim" -> "tat_m18ac", "tat_m18ac_s.rim" -> "tat_m18ac"
    """
    root = Path(filename).stem
    lower_root = root.lower()
    if lower_root.endswith("_s"):
        root = root[:-2]
    elif lower_root.endswith("_dlg"):
        root = root[:-4]
    return root


def should_use_composite_for_file(file_path: Path, other_file_path: Path) -> bool:
    """Determine if composite module loading should be used for a specific file.

    Only use composite loading for .rim files when comparing against .mod files.
    """
    # Check if this file is a .rim file (not in rims folder)
    if not is_capsule_file(file_path.name):
        return False
    if file_path.parent.name.lower() == "rims":
        return False
    if file_path.suffix.lower() != ".rim":
        return False

    # Check if the other file is a .mod file (not in rims folder)
    if not is_capsule_file(other_file_path.name):
        return False
    if other_file_path.parent.name.lower() == "rims":
        return False
    return other_file_path.suffix.lower() == ".mod"


class ModuleCapsuleWrapper:
    """A wrapper that combines multiple module capsules into one iterable."""

    def __init__(self, module_path: Path):
        self.module_path: Path = module_path
        self.capsules: list[Capsule] = []

        # Manually find related module files that actually exist
        self._find_related_capsules()

    def _find_root(self, filename: str) -> str:
        """Extract the root name from a module filename (same logic as Module.find_root)."""
        return find_module_root(filename)

    def _find_related_capsules(self):
        """Find related module files based on module.py logic, but only include files that exist."""
        # Get the root name (e.g., "tat_m18ac" from "tat_m18ac.rim")
        root = self._find_root(self.module_path.name)
        module_dir = self.module_path.parent

        # Possible related files in order of priority
        related_files = [
            f"{root}.rim",  # Main RIM
            f"{root}_s.rim",  # Data RIM
            f"{root}_dlg.erf",  # Dialog ERF (TSL only, but check anyway)
        ]

        found_files = []
        for filename in related_files:
            file_path = module_dir / filename
            if file_path.safe_isfile():
                found_files.append(filename)
                try:
                    self.capsules.append(Capsule(file_path))
                except Exception as e:  # noqa: BLE001
                    log_output(f"Failed to load {filename}: {e}")

        if found_files:
            log_output(f"Combined module capsules for {self.module_path.name}: {found_files}")
        else:
            # Fallback to just the original file
            log_output(f"No related files found for {self.module_path.name}, using single capsule")
            try:
                self.capsules = [Capsule(self.module_path)]
            except Exception as e:  # noqa: BLE001
                log_output(f"Failed to load {self.module_path.name}: {e}")
                self.capsules = []

    def __iter__(self):
        """Iterate over all resources from all capsules."""
        for capsule in self.capsules:
            yield from capsule


def relative_path_from_to(src: PurePath, dst: PurePath) -> Path:
    src_parts = list(src.parts)
    dst_parts = list(dst.parts)

    common_length = next(
        (i for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts)) if src_part != dst_part),
        len(src_parts),
    )
    rel_parts = dst_parts[common_length:]
    return Path(*rel_parts)


def visual_length(s: str, tab_length: int = 8) -> int:
    if "\t" not in s:
        return len(s)

    # Split the string at tabs, sum the lengths of the substrings,
    # and add the necessary spaces to account for the tab stops.
    parts: list[str] = s.split("\t")
    vis_length: int = sum(len(part) for part in parts)
    for part in parts[:-1]:  # all parts except the last one
        vis_length += tab_length - (len(part) % tab_length)
    return vis_length


gff_types: list[str] = list(gff.GFFContent.get_extensions())


def _is_text_content(data: bytes) -> bool:
    """Heuristically determine if data is text content."""
    if len(data) == 0:
        return True

    with suppress(UnicodeDecodeError):
        # Try to decode as UTF-8 first
        data.decode("utf-8")
        return True

    with suppress(UnicodeDecodeError):
        # Try Windows-1252 (common for KOTOR text files)
        data.decode("windows-1252")
        return True

    # Check for high ratio of printable ASCII characters
    # ASCII printable range: 32-126, plus tab(9), LF(10), CR(13)
    PRINTABLE_ASCII_MIN = 32
    PRINTABLE_ASCII_MAX = 126
    TEXT_THRESHOLD = 0.7

    printable_count = sum(1 for b in data if PRINTABLE_ASCII_MIN <= b <= PRINTABLE_ASCII_MAX or b in (9, 10, 13))
    return printable_count / len(data) > TEXT_THRESHOLD


def _get_resource_reader_function(ext: str) -> Callable[[bytes], Any] | None:
    """Dynamically get the appropriate resource reader function for an extension."""
    # Map extensions to their reader functions
    reader_map = {
        "gff": gff.read_gff,
        "2da": twoda.read_2da,
        "tlk": tlk.read_tlk,
        "lip": lip.read_lip,
        "erf": lambda data: __import__("pykotor.resource.formats.erf.erf_auto", fromlist=["read_erf"]).read_erf(data),
        "rim": lambda data: __import__("pykotor.resource.formats.rim.rim_auto", fromlist=["read_rim"]).read_rim(data),
        "mod": lambda data: __import__("pykotor.resource.formats.erf.erf_auto", fromlist=["read_erf"]).read_erf(data),
        "sav": lambda data: __import__("pykotor.resource.formats.erf.erf_auto", fromlist=["read_erf"]).read_erf(data),
        "ssf": lambda data: __import__("pykotor.resource.formats.ssf.ssf_auto", fromlist=["read_ssf"]).read_ssf(data),
        "mdl": lambda data: __import__("pykotor.resource.formats.mdl.mdl_auto", fromlist=["read_mdl"]).read_mdl(data),
        "ncs": lambda data: __import__("pykotor.resource.formats.ncs.ncs_auto", fromlist=["read_ncs"]).read_ncs(data),
        "wok": lambda data: __import__("pykotor.resource.formats.bwm.bwm_auto", fromlist=["read_bwm"]).read_bwm(data),
        "pwk": lambda data: __import__("pykotor.resource.formats.bwm.bwm_auto", fromlist=["read_bwm"]).read_bwm(data),
        "dwk": lambda data: __import__("pykotor.resource.formats.bwm.bwm_auto", fromlist=["read_bwm"]).read_bwm(data),
        "ltr": lambda data: __import__("pykotor.resource.formats.ltr.ltr_auto", fromlist=["read_ltr"]).read_ltr(data),
        "lyt": lambda data: __import__("pykotor.resource.formats.lyt.lyt_auto", fromlist=["read_lyt"]).read_lyt(data),
        "vis": lambda data: __import__("pykotor.resource.formats.vis.vis_auto", fromlist=["read_vis"]).read_vis(data),
    }

    return reader_map.get(ext.lower(), read_unknown_resource)


def read_unknown_resource(data: bytes) -> Any:
    """Read an unknown resource from data - returns raw bytes for unknown formats."""
    return data


def _has_comparable_interface(obj: Any) -> bool:
    """Check if an object has a compare method (ComparableMixin interface)."""
    return hasattr(obj, "compare") and callable(obj.compare)


class InstallationLogger:
    """Logger that captures installation search output to a string."""

    def __init__(self):
        self.log_buffer: list[str] = []
        self.current_resource: str | None = None
        self.resource_logs: dict[str, list[str]] = {}

    def __call__(self, message: str) -> None:
        """Log a message and store it in the buffer."""
        self.log_buffer.append(message)

        # If this is a new resource being processed, start a new log entry
        if message.startswith("Processing resource: "):
            self.current_resource = message.split(": ", 1)[1].strip()
            self.resource_logs[self.current_resource] = []
        elif self.current_resource:
            self.resource_logs[self.current_resource].append(message)

    def get_resource_log(self, resource_name: str) -> str:
        """Get the log output for a specific resource."""
        if resource_name in self.resource_logs:
            return "\n".join(self.resource_logs[resource_name])
        return ""

    def clear(self) -> None:
        """Clear the log buffer."""
        self.log_buffer.clear()
        self.resource_logs.clear()
        self.current_resource = None


def _compare_text_content(data1: bytes, data2: bytes, where: str) -> bool:
    """Compare text content using line-by-line diffing."""
    MAX_LINE_LENGTH = 200  # Maximum characters to display per line

    try:
        # Try UTF-8 first
        text1 = data1.decode("utf-8", errors="ignore")
        text2 = data2.decode("utf-8", errors="ignore")
    except (UnicodeDecodeError, AttributeError):
        try:
            # Fallback to Windows-1252
            text1 = data1.decode("windows-1252", errors="ignore")
            text2 = data2.decode("windows-1252", errors="ignore")
        except (UnicodeDecodeError, AttributeError):
            # Last resort - treat as binary
            return data1 == data2

    if text1 == text2:
        return True

    # Use difflib for detailed text comparison
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    diff = difflib.unified_diff(lines1, lines2, fromfile=f"(old){where}", tofile=f"(new){where}", lineterm="")

    diff_lines = list(diff)
    if diff_lines:
        log_output_with_separator(f"^ '{where}': Text content differs ^")
        for line in diff_lines:
            # Truncate excessively long lines (likely binary data that slipped through)
            if len(line) > MAX_LINE_LENGTH:
                truncated = line[:MAX_LINE_LENGTH] + f"... (truncated, {len(line)} chars total)"
                log_output(truncated)
            else:
                log_output(line.rstrip())
        return False

    return True


def diff_data(  # noqa: C901, PLR0911, PLR0912, PLR0915
    data1: bytes | Path,
    data2: bytes | Path,
    context: DiffContext,
) -> bool | None:
    """Compare two resources with appropriate format-specific handling.

    Complexity is unavoidable due to many file formats and fallback strategies.
    """
    where = context.where

    if not data1 and data2:
        return log_output(f"[Error] Cannot determine data for '{where}' in '{context.file1_rel}'")  # type: ignore[func-returns-value]
    if data1 and not data2:
        return log_output(f"[Error] Cannot determine data for '{where}' in '{context.file2_rel}'")  # type: ignore[func-returns-value]
    if not data1 and not data2:
        # message = f"No data for either resource: '{where}'"
        # log_output(message)
        return True

    # Skip .nss source files when comparing installations (they're dev files, not game data)
    if context.skip_nss and context.ext == "nss":
        return True  # Skip silently

    assert _global_config.parser_args

    # Fast path: For large binary files (audio, video), check file size first before reading
    LARGE_BINARY_FORMATS = {"wav", "mp3", "bik", "mve", "tga", "tpc"}
    if context.ext in LARGE_BINARY_FORMATS and isinstance(data1, Path) and isinstance(data2, Path):
        # Check file sizes first - if different, no need to read the files
        try:
            size1 = data1.stat().st_size
            size2 = data2.stat().st_size
            if size1 != size2:
                if _global_config.parser_args.compare_hashes:
                    log_output(f"'{context.where}': File sizes differ ({size1} vs {size2} bytes)")
                    return False
                return True  # Sizes differ but not comparing hashes
        except Exception:  # noqa: BLE001, S110
            pass  # Fall through to normal comparison

    # Convert Path to bytes if needed
    if isinstance(data1, Path):
        data1 = data1.read_bytes()
    if isinstance(data2, Path):
        data2 = data2.read_bytes()

    # Check if this is a GFF type (handled specially for backwards compatibility)
    if context.ext in gff_types:
        gff1: gff.GFF | None = None
        gff2: gff.GFF | None = None
        try:
            gff1 = gff.read_gff(data1)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"[Error] loading GFF {context.file1_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        try:
            gff2 = gff.read_gff(data2)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"[Error] loading GFF {context.file2_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        if gff1 and not gff2:
            return log_output(f"GFF resource missing in memory:\t'{context.file1_rel.parent / where}'")  # type: ignore[func-returns-value]
        if not gff1 and gff2:
            return log_output(f"GFF resource missing in memory:\t'{context.file2_rel.parent / where}'")  # type: ignore[func-returns-value]
        if not gff1 and not gff2:
            return log_output(f"Both GFF resources missing in memory:\t'{context.where}'")  # type: ignore[func-returns-value]
        if gff1 and gff2 and not gff1.compare(gff2, log_output, PureWindowsPath(context.where)):
            log_output_with_separator(f"^ '{context.where}': GFF is different ^")
            return False
        return True

    # Define known binary formats that should never be treated as text
    BINARY_FORMATS = {
        # Scripts and models
        "ncs", "mdl", "mdx",
        # Walkmesh formats
        "wok", "pwk", "dwk",
        # Textures
        "tga", "tpc", "txi",
        # Audio/Video
        "wav", "mp3", "bik", "mve",
        # Capsule formats (should be handled by capsule reader, but fallback to binary if parsing fails)
        "erf", "rim", "mod", "sav",
        # All GFF-based formats (already handled above, but listed here for completeness in case of parse failure)
        "are", "git", "ifo", "utc", "utd", "ute",
        "uti", "utm", "utp", "uts", "utt", "utw",
        "dlg", "gui", "jrl", "fac", "ssf", "bic",
    }

    # Try to get a resource reader function for this extension
    reader_func = _get_resource_reader_function(context.ext)

    if reader_func:
        try:
            # Try to parse both resources
            obj1 = reader_func(data1)
            obj2 = reader_func(data2)

            # Check if the parsed objects have ComparableMixin interface
            if _has_comparable_interface(obj1) and _has_comparable_interface(obj2):
                # Special handling for NCS files - provide summary instead of exhaustive diff
                if context.ext == "ncs":
                    # Capture comparison output to summarize it
                    comparison_lines = []

                    def capture_log(*args, **kwargs):
                        buffer = StringIO()
                        print(*args, file=buffer, **kwargs)
                        comparison_lines.append(buffer.getvalue())

                    is_same = obj1.compare(obj2, capture_log)

                    if not is_same:
                        # Provide a summary of differences
                        log_output("NCS scripts differ:")
                        log_output(f"  Old: {len(obj1.instructions)} instructions")
                        log_output(f"  New: {len(obj2.instructions)} instructions")

                        # Show first few differences only
                        MAX_DIFF_LINES = 20
                        if len(comparison_lines) > MAX_DIFF_LINES:
                            for line in comparison_lines[:MAX_DIFF_LINES]:
                                log_output(line.rstrip())
                            log_output(f"  ... ({len(comparison_lines) - MAX_DIFF_LINES} more difference lines omitted)")
                        else:
                            for line in comparison_lines:
                                log_output(line.rstrip())

                        log_output_with_separator(f"^ '{context.where}': {context.ext.upper()} is different ^")
                        return False
                    return True

                # Use the structured compare method for other files
                if not obj1.compare(obj2, log_output):
                    log_output_with_separator(f"^ '{context.where}': {context.ext.upper()} is different ^")
                    return False
                return True
            # Objects don't have compare method, fall through to other methods

        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            # Parsing failed, fall through to other comparison methods
            log_output(f"[Warning] Could not parse {context.ext.upper()} for structured comparison at '{context.where}'")
            log_output(f"  Exception: {type(e).__name__}: {e}")
            # Show the original cause if available (for chained exceptions)
            if e.__cause__:
                log_output(f"  Caused by: {type(e.__cause__).__name__}: {e.__cause__}")
            # Only show full traceback if verbose mode enabled
            if os.environ.get("KOTORDIFF_VERBOSE"):
                log_output("  Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_output(f"    {line}")

            # For known binary formats, skip text comparison and go straight to hash
            if context.ext.lower() in BINARY_FORMATS:
                log_output("  Falling back to hash comparison")
                if _global_config.parser_args.compare_hashes and generate_hash(data1) != generate_hash(data2):
                    log_output(f"'{context.where}': SHA256 is different")
                    return False
                return True

    # Check if content appears to be text (but skip for known binary formats)
    if context.ext.lower() not in BINARY_FORMATS and _is_text_content(data1) and _is_text_content(data2):
        return _compare_text_content(data1, data2, str(context.where))

    # Fallback to hash comparison for binary content
    if _global_config.parser_args.compare_hashes and generate_hash(data1) != generate_hash(data2):
        log_output(f"'{context.where}': SHA256 is different")
        return False

    return True


def log_output_with_separator(message, *, below=True, above=False, surround=False):
    if above or surround:
        log_output(visual_length(message) * "-")
    log_output(message)
    if (below and not above) or surround:
        log_output(visual_length(message) * "-")


# --------------
# Unified diff helpers and diff3 support
# --------------


def _read_text_lines(filepath: Path) -> list[str]:
    try:
        return filepath.read_bytes().decode("utf-8", errors="ignore").splitlines(True)  # noqa: FBT003
    except Exception:  # noqa: BLE001
        try:
            return filepath.read_bytes().decode("windows-1252", errors="ignore").splitlines(True)  # noqa: FBT003
        except Exception:  # noqa: BLE001
            return []


def _print_udiff(from_file: Path, to_file: Path, label_from: str, label_to: str):
    a = _read_text_lines(from_file)
    b = _read_text_lines(to_file)
    if not a and not b:
        return
    diff = difflib.unified_diff(
        a,
        b,
        fromfile=str(label_from),
        tofile=str(label_to),
        lineterm="",
    )
    for line in diff:
        log_output(line)


def _walk_files(root: Path) -> set[str]:
    if not root.safe_exists():
        return set()
    if root.safe_isfile():
        return {root.name.casefold()}
    return {f.relative_to(root).as_posix().casefold() for f in root.safe_rglob("*") if f.safe_isfile()}


def _ext_of(path: Path) -> str:
    s = path.suffix.casefold()
    return s[1:] if s.startswith(".") else s


def _should_skip_rel(_rel: str) -> bool:
    """Check if a relative path should be skipped.

    Note: Currently unused but kept for future filtering capabilities.
    """
    return False


def _diff3_files_udiff(  # noqa: C901, PLR0911, PLR0912, PLR0915
    mine: Path,
    older: Path,
    yours: Path,
):
    """Print a diff3-style output: show conflicts and changes between three files (older, mine, yours).

    Uses merge3 for all supported formats, including text, TLK, and capsule-contained text resources.
    """
    ext = _ext_of(yours)

    if is_capsule_file(yours.name):
        try:
            cap_old = Capsule(older)
            cap_mine = Capsule(mine)
            cap_new = Capsule(yours)
        except (ValueError, OSError) as e:
            log_output(f"[Error] diff3 capsule: {universal_simplify_exception(e)}")
            return
        old_dict = {res.resname(): res for res in cap_old}
        mine_dict = {res.resname(): res for res in cap_mine}
        new_dict = {res.resname(): res for res in cap_new}
        keys = sorted(set(old_dict) | set(mine_dict) | set(new_dict))
        for k in keys:
            r_old = old_dict.get(k)
            r_mine = mine_dict.get(k)
            r_new = new_dict.get(k)
            log_output(f"==== {yours.name}/{k} ====")
            # If all three are missing, skip
            if r_old is None and r_mine is None and r_new is None:
                continue
            # If only present in one, print addition/removal
            if r_old is None and r_mine is not None and r_new is None:
                log_output(f"Only in mine: {mine.name}/{k}")
                continue
            if r_old is None and r_mine is None and r_new is not None:
                log_output(f"Only in yours: {yours.name}/{k}")
                continue
            if r_old is not None and r_mine is None and r_new is None:
                log_output(f"Only in older: {older.name}/{k}")
                continue

            # For all other cases, treat as text and use merge3
            # Try to decode as text, fallback to empty if not present
            def _res_lines(res: CapsuleResource | FileResource | None) -> list[str]:
                if res is None:
                    return []
                try:
                    return res.data().decode("utf-8", errors="ignore").splitlines(True)  # noqa: FBT003
                except Exception:  # noqa: BLE001
                    try:
                        return res.data().decode("windows-1252", errors="ignore").splitlines(True)  # noqa: FBT003
                    except Exception:  # noqa: BLE001
                        return []

            a = _res_lines(r_old)
            b = _res_lines(r_mine)
            c = _res_lines(r_new)
            try:
                m3 = merge3.Merge3(a, b, c, is_cherrypick=True, sequence_matcher=difflib.SequenceMatcher)
                for line in m3.merge_lines():
                    log_output(line if isinstance(line, str) else line.decode("utf-8", errors="ignore"))
            except Exception as e:  # noqa: BLE001
                log_output(f"[Error] merge3 failed for {k}: {universal_simplify_exception(e)}")
        return

    # Non-capsule files
    if ext in {"txt", "nss", "utp", "uti", "utc", "dlg"}:
        a = _read_text_lines(older)
        b = _read_text_lines(mine)
        c = _read_text_lines(yours)
        try:
            m3 = merge3.Merge3(a, b, c)
            for line in m3.merge_lines():
                log_output(line if isinstance(line, str) else line.decode("utf-8", errors="ignore"))
        except Exception as e:  # noqa: BLE001
            log_output(f"[Error] merge3 unavailable/failure ({universal_simplify_exception(e)})")
        return
    if ext == "2da":
        # Always use typed TwoDA compare to avoid treating as binary/text
        try:
            twoda_old = twoda.read_2da(older)
            twoda_mine = twoda.read_2da(mine)
            twoda_new = twoda.read_2da(yours)
        except Exception as e:  # noqa: BLE001
            log_output(f"[Error] reading 2DA: {universal_simplify_exception(e)}")
            return
        log_output(f"--- (old){older}")
        log_output(f"+++ (mine){mine}")
        twoda_old.compare(twoda_mine, log_output)
        log_output(f"--- (old){older}")
        log_output(f"+++ (new){yours}")
        twoda_old.compare(twoda_new, log_output)
        return

    if ext in gff_types:
        # For GFF, we can't do a line-based merge, so just show both diffs as before
        try:
            gff_old = gff.read_gff(older)
            gff_mine = gff.read_gff(mine)
            gff_new = gff.read_gff(yours)
        except Exception as e:  # noqa: BLE001
            log_output(f"[Error] reading GFF: {universal_simplify_exception(e)}")
            return
        log_output(f"--- (old){older}")
        log_output(f"+++ (mine){mine}")
        gff_old.compare(gff_mine, log_output, PureWindowsPath(mine.name))
        log_output(f"--- (old){older}")
        log_output(f"+++ (new){yours}")
        gff_old.compare(gff_new, log_output, PureWindowsPath(yours.name))
        return

    if ext == "tlk":
        try:
            tlk_old = tlk.read_tlk(older)
            tlk_mine = tlk.read_tlk(mine)
            tlk_new = tlk.read_tlk(yours)
        except Exception as e:  # noqa: BLE001
            log_output(f"[Error] reading TLK: {universal_simplify_exception(e)}")
            return

        def tlk_lines(tlk: TLK) -> list[str]:
            lines = []
            for i in range(len(tlk)):
                try:
                    e = tlk.get(i)
                    lines.append(f"{i}\t{e.text}\t{e.voiceover}\n") if e else lines.append(f"{i}\t\n")
                except Exception as e:  # noqa: BLE001, PERF203
                    log_output(f"[Error] reading TLK: {universal_simplify_exception(e)}")
                    lines.append(f"{i}\t\n")
            return lines

        a = tlk_lines(tlk_old)
        b = tlk_lines(tlk_mine)
        c = tlk_lines(tlk_new)
        try:
            m3 = merge3.Merge3(a, b, c)
            for line in m3.merge_lines():
                log_output(line if isinstance(line, str) else line.decode("utf-8", errors="ignore"))
        except Exception as e:  # noqa: BLE001
            log_output(f"[Error] merge3 unavailable/failure ({universal_simplify_exception(e)})")
        return

    # Fallback to raw text diff3 using merge3
    a = _read_text_lines(older)
    b = _read_text_lines(mine)
    c = _read_text_lines(yours)
    try:
        m3 = merge3.Merge3(a, b, c)
        for line in m3.merge_lines():
            log_output(line if isinstance(line, str) else line.decode("utf-8", errors="ignore"))
    except Exception as e:  # noqa: BLE001
        log_output(f"[Error] merge3 unavailable/failure ({universal_simplify_exception(e)})")


def _generate_changes_ini(  # noqa: C901, PLR0912, PLR0915
    mine_root: Path,  # noqa: ARG001
    older_root: Path,
    yours_root: Path,
    *,
    out_path: Path,
):
    """Generate a comprehensive TSLPatcher-compatible changes.ini from directory differences.

    This unified generator:
    1. Uses diff analyzers to create precise PatcherModifications for supported formats
    2. Falls back to [InstallList] for unsupported files
    3. Stages all necessary files
    """
    log_output_with_separator("Generating TSLPatcher changes.ini", above=True)

    # Collect all files
    older_files = {str(f.relative_to(older_root)): f for f in older_root.rglob("*") if f.is_file()} if older_root.safe_isdir() else {}
    yours_files = {str(f.relative_to(yours_root)): f for f in yours_root.rglob("*") if f.is_file()} if yours_root.safe_isdir() else {}
    all_rel = sorted(set(older_files.keys()) | set(yours_files.keys()))

    # Track modifications by type
    modifications_by_type = ModificationsByType.create_empty()

    # Map casefolded rel -> actual rel from 'yours' for correct casing
    yours_rel_map: dict[str, str] = {}
    for rel in yours_files:
        yours_rel_map[rel.casefold()] = rel

    # Analyze each file
    for rel in all_rel:
        if _should_skip_rel(rel):
            continue

        older_file = older_files.get(rel)
        yours_file = yours_files.get(rel)

        # Skip if only in one location
        if older_file is None or yours_file is None:
            continue

        # Check if different
        older_data = older_file.read_bytes()
        yours_data = yours_file.read_bytes()

        if older_data == yours_data:
            continue

        # Try to analyze with diff analyzers
        ext = _ext_of(Path(rel))
        analyzer = DiffAnalyzerFactory.get_analyzer(ext)

        if analyzer:
            try:
                log_output(f"Analyzing {rel}...")
                modifications = analyzer.analyze(older_data, yours_data, Path(rel).name)

                if modifications:
                    # Successfully analyzed - add to appropriate list
                    if ext.lower() in ("2da", "twoda"):
                        modifications_by_type.twoda.append(modifications)
                    elif ext.lower() in gff_types:
                        modifications_by_type.gff.append(modifications)
                    elif ext.lower() == "tlk":
                        modifications_by_type.tlk.append(modifications)
                    elif ext.lower() == "ssf":
                        modifications_by_type.ssf.append(modifications)
                continue
            except Exception as e:  # noqa: BLE001
                log_output(f"[Warning] Failed to analyze {rel}: {universal_simplify_exception(e)}")

        # Fallback to InstallList for this file
        actual_rel = yours_rel_map.get(rel.casefold(), rel)
        dest_folder = str(Path(actual_rel).parent)
        filename = Path(actual_rel).name
        # Find or create entry for this folder
        folder_entry = next((entry for entry in modifications_by_type.install if entry[0] == dest_folder), None)
        if folder_entry is None:
            folder_entry = (dest_folder, [])
            modifications_by_type.install.append(folder_entry)
        folder_entry[1].append(filename)

    # Stage files
    import shutil  # noqa: PLC0415

    stage_root = out_path.parent
    stage_root.mkdir(exist_ok=True, parents=True)

    # Stage files for InstallList
    for folder, files in modifications_by_type.install:
        for fname in files:
            src_rel = Path(folder) / fname if folder != "." else Path(fname)
            src_abs = yours_root / src_rel if yours_root.safe_isdir() else yours_root
            dst_dir = stage_root / folder if folder != "." else stage_root
            dst_dir.mkdir(exist_ok=True, parents=True)
            dst_abs = dst_dir / fname
            try:
                shutil.copy2(src_abs, dst_abs)
            except Exception as e:  # noqa: BLE001
                log_output(f"[Warning] Failed to stage '{src_abs}' → '{dst_abs}': {universal_simplify_exception(e)}")

    # Generate INI content using the expert serializer
    serializer = TSLPatcherINISerializer()
    ini_content = serializer.serialize(modifications_by_type)

    # Write the INI file
    out_path.write_text(ini_content, encoding="utf-8")
    log_output(f"Successfully generated changes.ini at: {out_path}")
    log_output(f"  - 2DA patches: {len(modifications_by_type.twoda)}")
    log_output(f"  - GFF patches: {len(modifications_by_type.gff)}")
    log_output(f"  - TLK patches: {len(modifications_by_type.tlk)}")
    log_output(f"  - SSF patches: {len(modifications_by_type.ssf)}")
    log_output(f"  - Install files: {sum(len(files) for _, files in modifications_by_type.install)}")


def run_differ3_from_args(
    mine: Path,
    older: Path,
    yours: Path,
    config: IniGenerationConfig,
):
    # Print header
    log_output()
    log_output("3-way diff (mine → older → yours)")
    log_output(f"mine:   {mine}")
    log_output(f"older:  {older}")
    log_output(f"yours:  {yours}")
    log_output()

    # Print udiff for older -> yours
    if mine.safe_isfile() and older.safe_isfile() and yours.safe_isfile():
        _diff3_files_udiff(mine, older, yours)
    elif mine.safe_isdir() and older.safe_isdir() and yours.safe_isdir():
        files_old: set[str] = _walk_files(older)
        files_new: set[str] = _walk_files(yours)
        for rel in sorted(files_old | files_new):
            if _should_skip_rel(rel):
                continue
            _diff3_files_udiff(mine / rel, older / rel, yours / rel)
    else:
        msg = "--mine, --older, --yours must all be files or all be directories"
        raise ValueError(msg)

    if config.generate_ini:
        out_path: Path = config.out_ini if config.out_ini is not None else Path("changes.ini").resolve()
        _generate_changes_ini(mine, older, yours, out_path=out_path)


def _load_capsule(
    file_path: Path,
    *,
    use_composite: bool,
) -> Capsule | ModuleCapsuleWrapper | None:
    """Load a capsule file, either as a simple Capsule or ModuleCapsuleWrapper."""
    try:
        if use_composite:
            return ModuleCapsuleWrapper(file_path)
        return Capsule(file_path)
    except ValueError as e:
        log_output(f"Could not load '{file_path}'. Reason: {universal_simplify_exception(e)}")
        return None


def _report_missing_resources(
    missing_in_capsule1: set[str],
    missing_in_capsule2: set[str],
    *,
    capsule1_resources: dict[str, FileResource],
    capsule2_resources: dict[str, FileResource],
    file_paths: tuple[Path, Path],
) -> None:
    """Report missing resources between two capsules."""
    c_file1_rel, c_file2_rel = file_paths
    for resref in sorted(missing_in_capsule1):
        message = f"Capsule1 resource missing\t{c_file1_rel}\t{resref}\t{capsule2_resources[resref].restype().extension.upper()}"
        log_output(message)

    for resref in sorted(missing_in_capsule2):
        message = f"Capsule2 resource missing\t{c_file2_rel}\t{resref}\t{capsule1_resources[resref].restype().extension.upper()}"
        log_output(message)


def _diff_capsule_files(
    c_file1: Path,
    c_file2: Path,
    c_file1_rel: Path,
    c_file2_rel: Path,
    *,
    skip_nss: bool = False,
) -> bool | None:
    """Handle diffing of capsule files."""
    # Check if we should use composite module loading for each file individually
    use_composite_file1 = should_use_composite_for_file(c_file1, c_file2)
    use_composite_file2 = should_use_composite_for_file(c_file2, c_file1)

    if use_composite_file1:
        log_output(f"Using composite module loading for {c_file1_rel.name} (RIM + _s.rim + _dlg.erf)")
    if use_composite_file2:
        log_output(f"Using composite module loading for {c_file2_rel.name} (RIM + _s.rim + _dlg.erf)")

    # Load capsules
    file1_capsule = _load_capsule(c_file1, use_composite=use_composite_file1)
    if file1_capsule is None:
        return None

    file2_capsule = _load_capsule(c_file2, use_composite=use_composite_file2)
    if file2_capsule is None:
        return None

    # Build dict of resources
    capsule1_resources: dict[str, FileResource] = {res.resname(): res for res in file1_capsule}
    capsule2_resources: dict[str, FileResource] = {res.resname(): res for res in file2_capsule}

    # Identify missing resources
    missing_in_capsule1: set[str] = capsule2_resources.keys() - capsule1_resources.keys()
    missing_in_capsule2: set[str] = capsule1_resources.keys() - capsule2_resources.keys()

    _report_missing_resources(
        missing_in_capsule1,
        missing_in_capsule2,
        capsule1_resources=capsule1_resources,
        capsule2_resources=capsule2_resources,
        file_paths=(c_file1_rel, c_file2_rel),
    )

    # Check for differences in common resources
    is_same_result: bool | None = True
    common_resrefs: set[str] = capsule1_resources.keys() & capsule2_resources.keys()
    for resref in sorted(common_resrefs):
        res1: FileResource = capsule1_resources[resref]
        res2: FileResource = capsule2_resources[resref]
        ext: str = res1.restype().extension.casefold()
        ctx = DiffContext(c_file1_rel, c_file2_rel, ext, resref, skip_nss=skip_nss)
        result: bool | None = diff_data(res1.data(), res2.data(), ctx)
        is_same_result = None if result is None else (result and is_same_result)

    return is_same_result


def diff_files(
    file1: os.PathLike | str,
    file2: os.PathLike | str,
    *,
    skip_nss: bool = False,
) -> bool | None:
    c_file1: Path = Path.pathify(file1).resolve()
    c_file2: Path = Path.pathify(file2).resolve()
    c_file1_rel: Path = relative_path_from_to(c_file2, c_file1)
    c_file2_rel: Path = relative_path_from_to(c_file1, c_file2)

    if not c_file1.safe_isfile():
        log_output(f"Missing file:\t{c_file1_rel}")
        return False
    if not c_file2.safe_isfile():
        log_output(f"Missing file:\t{c_file2_rel}")
        return False

    # Prefer udiff output by default for text-like files (exclude 2DA; use TwoDA.compare)
    ext = c_file1_rel.suffix.casefold()[1:]
    if ext in {"txi"}:
        _print_udiff(c_file1, c_file2, f"(old){c_file1}", f"(new){c_file2}")

    if is_capsule_file(c_file1_rel.name):
        return _diff_capsule_files(c_file1, c_file2, c_file1_rel, c_file2_rel, skip_nss=skip_nss)

    ctx = DiffContext(c_file1_rel, c_file2_rel, c_file1_rel.suffix.casefold()[1:], skip_nss=skip_nss)
    return diff_data(c_file1, c_file2, ctx)


def diff_directories(
    dir1: os.PathLike | str,
    dir2: os.PathLike | str,
    *,
    filters: list[str] | None = None,
    skip_nss: bool = False,
) -> bool | None:
    c_dir1 = Path.pathify(dir1).resolve()
    c_dir2 = Path.pathify(dir2).resolve()

    log_output_with_separator(f"Finding differences in the '{c_dir1.name}' folders...", above=True)

    # Store relative paths instead of just filenames
    files_path1: set[str] = {f.relative_to(c_dir1).as_posix().casefold() for f in c_dir1.safe_rglob("*") if f.safe_isfile()}
    files_path2: set[str] = {f.relative_to(c_dir2).as_posix().casefold() for f in c_dir2.safe_rglob("*") if f.safe_isfile()}

    # Merge both sets to iterate over unique relative paths
    all_files: set[str] = files_path1.union(files_path2)

    # Skip .nss files if requested (for installation comparisons)
    if skip_nss:
        all_files = {f for f in all_files if not f.lower().endswith(".nss")}

    # Apply filters if provided
    if filters:
        filtered_files = {f for f in all_files if should_include_in_filtered_diff(f, filters)}
        if filtered_files != all_files:
            log_output(f"Applying filters: {filters}")
            log_output(f"Filtered from {len(all_files)} to {len(filtered_files)} files")
        all_files = filtered_files

    # Show progress for large directories
    PROGRESS_FILE_THRESHOLD = 100  # Minimum files to show progress updates

    total_files = len(all_files)
    if total_files > PROGRESS_FILE_THRESHOLD:
        log_output(f"Comparing {total_files} files...")

    is_same_result: bool | None = True
    for idx, rel_path in enumerate(sorted(all_files), 1):
        # Show progress every PROGRESS_FILE_THRESHOLD files for large directories
        if total_files > PROGRESS_FILE_THRESHOLD and idx % PROGRESS_FILE_THRESHOLD == 0:
            log_output(f"Progress: {idx}/{total_files} files processed...")
        result: bool | None = diff_files(c_dir1 / rel_path, c_dir2 / rel_path, skip_nss=skip_nss)
        is_same_result = None if result is None else result and is_same_result

    if total_files > PROGRESS_FILE_THRESHOLD:
        log_output(f"Completed: {total_files}/{total_files} files processed.")

    return is_same_result


def diff_installs(
    install_path1: os.PathLike | str,
    install_path2: os.PathLike | str,
    *,
    filters: list[str] | None = None,
) -> bool | None:
    """Compare two KOTOR installations by diffing their standard directories.

    Note: This function walks installation directories directly. For more advanced
    resource resolution (using chitin.key, module loading, etc.), use diff_installs_with_objects
    or the Installation-aware comparison functions.

    TODO: https://github.com/NickHugi/PyKotor/issues/XXX - Fully utilize Installation objects for resource resolution
    """
    rinstall_path1: CaseAwarePath = CaseAwarePath.pathify(install_path1).resolve()
    rinstall_path2: CaseAwarePath = CaseAwarePath.pathify(install_path2).resolve()
    log_output()
    log_output((max(len(str(rinstall_path1)) + 29, len(str(rinstall_path2)) + 30)) * "-")
    log_output("Searching first install dir:", rinstall_path1)
    log_output("Searching second install dir:", rinstall_path2)
    if filters:
        log_output(f"Using filters: {filters}")
    log_output()

    is_same_result: bool | None = True

    # Only compare dialog.tlk if no specific filters or if TLK files are explicitly requested
    if not filters or any("dialog.tlk" in f.lower() or "tlk" in f.lower() for f in filters):
        is_same_result = diff_files(rinstall_path1.joinpath("dialog.tlk"), rinstall_path2 / "dialog.tlk") and is_same_result

    modules_path1: CaseAwarePath = rinstall_path1 / "Modules"
    modules_path2: CaseAwarePath = rinstall_path2 / "Modules"
    is_same_result = diff_directories(modules_path1, modules_path2, filters=filters, skip_nss=True) and is_same_result

    override_path1: CaseAwarePath = rinstall_path1 / "Override"
    override_path2: CaseAwarePath = rinstall_path2 / "Override"
    is_same_result = diff_directories(override_path1, override_path2, filters=filters, skip_nss=True) and is_same_result

    lips_path1: CaseAwarePath = rinstall_path1 / "Lips"
    lips_path2: CaseAwarePath = rinstall_path2 / "Lips"
    is_same_result = diff_directories(lips_path1, lips_path2, filters=filters, skip_nss=True) and is_same_result

    streamwaves_path1: CaseAwarePath = (
        rinstall_path1.joinpath("streamwaves")
        if rinstall_path1.joinpath("streamwaves").safe_isdir()
        else rinstall_path1.joinpath("streamvoice")
    )
    streamwaves_path2: CaseAwarePath = (
        rinstall_path2.joinpath("streamwaves")
        if rinstall_path2.joinpath("streamwaves").safe_isdir()
        else rinstall_path2.joinpath("streamvoice")
    )
    is_same_result = (
        diff_directories(
            streamwaves_path1,
            streamwaves_path2,
            filters=filters,
            skip_nss=True,
        )
        and is_same_result
    )
    return is_same_result


def diff_installs_with_objects(
    installation1: Installation,
    installation2: Installation,
    *,
    filters: list[str] | None = None,
) -> bool | None:
    """Compare two installations using already loaded Installation objects."""
    log_output("Comparing installations using loaded objects...")
    if filters:
        log_output(f"Using filters: {filters}")

    # For now, just delegate to the old function
    # In the future, this could be optimized to use the loaded objects directly
    return diff_installs(installation1.path(), installation2.path(), filters=filters)


def is_kotor_install_dir(path: os.PathLike | str) -> bool | None:
    c_path: CaseAwarePath = CaseAwarePath.pathify(path)
    return c_path.safe_isdir() and c_path.joinpath("chitin.key").safe_isfile()


def resolve_resource_with_installation(
    installation: Installation,
    resource_name: str,
    resource_type: ResourceType,
    *,
    module_root: str | None = None,
    installation_logger: InstallationLogger | None = None,
) -> tuple[bytes | None, str, str]:
    """Resolve a resource using an already-loaded Installation instance.

    Args:
    ----
        installation: Already loaded Installation instance
        resource_name: Name of the resource (without extension)
        resource_type: Resource type
        module_root: Optional module root to constrain search to specific module
        installation_logger: Logger to capture installation search output

    Returns:
    -------
        Tuple of (resource_data, resolution_path, search_log) where resolution_path describes where it was found
    """
    try:
        # Create a logger that captures the search output
        if installation_logger is None:
            installation_logger = InstallationLogger()

        # Log the resource being processed
        installation_logger(f"Processing resource: {resource_name}.{resource_type.extension}")
        installation_logger(f"Resolving resource '{resource_name}.{resource_type.extension}' in installation...")

        # Use Installation's resource method with the logger
        resource_result = installation.resource(
            resource_name,
            resource_type,
            module_root=module_root,
            logger=installation_logger,
        )

        if resource_result is not None:
            search_log = installation_logger.get_resource_log(f"{resource_name}.{resource_type.extension}")
            return resource_result.data, f"{resource_result.filepath}", search_log

        installation_logger(f"Resource '{resource_name}.{resource_type.extension}' not found in any location")
        search_log = installation_logger.get_resource_log(f"{resource_name}.{resource_type.extension}")

    except Exception as e:  # noqa: BLE001
        error_msg = f"Error resolving resource: {universal_simplify_exception(e)}"
        if installation_logger:
            installation_logger(error_msg)
            search_log = installation_logger.get_resource_log(f"{resource_name}.{resource_type.extension}")
        else:
            search_log = ""
        return None, error_msg, search_log
    else:
        return None, "Not found in installation", search_log


def _parse_resource_name_and_type(
    resource_name: str,
    resource_type: ResourceType | None,
) -> tuple[str | None, ResourceType, str | None]:
    """Parse resource name and determine resource type.

    Returns:
        Tuple of (name_part, resource_type, error_message)
        If error_message is not None, the parsing failed.
    """
    if "." in resource_name and resource_type is None:
        name_part, ext_part = resource_name.rsplit(".", 1)
        try:
            resource_type = ResourceType.from_extension(ext_part)
        except ValueError:
            error_msg = f"Unknown extension: {ext_part}"
            log_output(f"Unknown resource type extension: {ext_part}")
            return None, ResourceType.INVALID, error_msg
        else:
            return name_part, resource_type, None
    elif resource_type is None:
        error_msg = "Cannot determine resource type"
        log_output(f"Cannot determine resource type for: {resource_name}")
        return None, ResourceType.INVALID, error_msg
    else:
        return resource_name, resource_type or ResourceType.INVALID, None


def _determine_source_location(filepath: str) -> str:
    """Determine the source location string for logging based on filepath."""
    if "Override" in filepath:
        return f"Override: {filepath}"
    if "Modules" in filepath:
        return f"Module: {filepath}"
    if "rims" in filepath:
        return f"RIM: {filepath}"
    if "chitin.key" in filepath or "data" in filepath.lower():
        return f"Chitin: {filepath}"
    return f"Other: {filepath}"


def resolve_resource_in_installation(
    installation_path: Path,
    resource_name: str,
    resource_type: ResourceType | None = None,
) -> tuple[bytes | None, str]:
    """Resolve a resource using KOTOR installation priority order.

    Args:
    ----
        installation_path: Path to the KOTOR installation
        resource_name: Name of the resource (with or without extension)
        resource_type: Optional resource type if not inferrable from name

    Returns:
    -------
        Tuple of (resource_data, resolution_path) where resolution_path describes where it was found
    """
    try:
        installation = Installation(installation_path)

        # Parse resource name and type
        name_part, resource_type, error_msg = _parse_resource_name_and_type(resource_name, resource_type)
        if error_msg is not None or name_part is None or resource_type is None:
            return None, error_msg or "Failed to parse resource name and type"

        # Search with priority order
        search_order = [
            SearchLocation.OVERRIDE,
            SearchLocation.CUSTOM_MODULES,
            SearchLocation.MODULES,
            SearchLocation.CHITIN,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.TEXTURES_TPB,
            SearchLocation.TEXTURES_TPC,
            SearchLocation.RIMS,
            SearchLocation.LIPS,
        ]

        log_output(f"Resolving resource '{name_part}.{resource_type.extension}' in installation...")

        resource_result = installation.resource(name_part, resource_type, search_order)

        if resource_result is None:
            log_output(f"Resource '{name_part}.{resource_type.extension}' not found in installation")
            return None, "Not found in installation"

        data = resource_result.data
        filepath = str(resource_result.filepath)
        source = _determine_source_location(filepath)

        log_output(f"Found '{name_part}.{resource_type.extension}' at: {source}")

    except Exception as e:  # noqa: BLE001
        error_msg = f"Error resolving resource: {universal_simplify_exception(e)}"
        log_output(error_msg)
        return None, error_msg
    else:
        return data, source


def should_include_in_filtered_diff(
    file_path: str,
    filters: list[str] | None,
) -> bool:
    """Check if a file should be included based on filter criteria.

    Args:
    ----
        file_path: Relative path of the file being checked
        filters: List of filter patterns to match against

    Returns:
    -------
        True if file should be included, False otherwise
    """
    if not filters:
        return True  # No filters means include everything

    file_path_lower = file_path.lower()

    for filter_pattern in filters:
        filter_lower = filter_pattern.lower()

        # Direct filename match
        if filter_lower in file_path_lower:
            return True

        # Module name match (for .rim/.mod files)
        if file_path_lower.endswith((".rim", ".mod", ".erf")):
            # Extract module root from file path
            filename = Path(file_path).name
            try:
                root = find_module_root(filename)
                if filter_lower == root.lower():
                    return True
            except Exception:  # noqa: BLE001, S110, S112
                continue

    return False


def _validate_paths(
    path1: Path,
    path2: Path,
) -> bool | None:
    """Validate that both paths exist. Returns None if validation fails."""
    if not path1.safe_exists():
        log_output(f"--path1='{path1}' does not exist on disk, cannot diff")
        return None
    if not path2.safe_exists():
        log_output(f"--path2='{path2}' does not exist on disk, cannot diff")
        return None
    return True


def _load_installations(
    path1: Path,
    path2: Path,
) -> tuple[Installation | None, Installation | None]:
    """Load installations if the paths are KOTOR install directories."""
    installation1 = None
    installation2 = None

    if is_kotor_install_dir(path1):
        log_output(f"Loading installation from: {path1}")
        try:
            installation1 = Installation(path1)
        except Exception as e:  # noqa: BLE001
            log_output(f"Error loading installation '{path1}': {universal_simplify_exception(e)}")
            return None, None

    if is_kotor_install_dir(path2):
        log_output(f"Loading installation from: {path2}")
        try:
            installation2 = Installation(path2)
        except Exception as e:  # noqa: BLE001
            log_output(f"Error loading installation '{path2}': {universal_simplify_exception(e)}")
            return None, None

    return installation1, installation2


def _handle_special_comparisons(
    path1: Path,
    path2: Path,
    installation1: Installation | None,
    installation2: Installation | None,
    filters: list[str] | None,
) -> bool | None:
    """Handle special comparison cases (container vs installation, resource vs installation, etc.)."""
    # Handle container vs installation comparison
    if path1.safe_isfile() and is_capsule_file(path1.name) and installation2:
        return diff_container_vs_installation(path1, installation2, container_first=True)
    if installation1 and path2.safe_isfile() and is_capsule_file(path2.name):
        return diff_container_vs_installation(path2, installation1, container_first=False)

    # Handle single resource vs installation comparison
    if path1.safe_isfile() and not is_capsule_file(path1.name) and installation2:
        return diff_resource_vs_installation(path1, installation2, resource_first=True)
    if installation1 and path2.safe_isfile() and not is_capsule_file(path2.name):
        return diff_resource_vs_installation(path2, installation1, resource_first=False)

    # Handle installation vs installation comparison
    if installation1 and installation2:
        return diff_installs_with_objects(installation1, installation2, filters=filters)

    return None  # Indicates no special case was handled


def run_differ_from_args(
    path1: Path,
    path2: Path,
    *,
    filters: list[str] | None = None,
) -> bool | None:
    # Validate paths
    validation_result = _validate_paths(path1, path2)
    if validation_result is None:
        return None

    # Load installations if needed
    installation1, installation2 = _load_installations(path1, path2)
    if installation1 is None and is_kotor_install_dir(path1):
        return None  # Installation loading failed
    if installation2 is None and is_kotor_install_dir(path2):
        return None  # Installation loading failed

    # Handle special comparison cases
    result = _handle_special_comparisons(path1, path2, installation1, installation2, filters)
    if result is not None:  # Special case was handled
        return result

    # Handle standard comparisons
    if path1.safe_isdir() and path2.safe_isdir():
        return diff_directories(path1, path2, filters=filters)

    if path1.safe_isfile() and path2.safe_isfile():
        return diff_files(path1, path2)

    # If we get here, the paths are incompatible
    msg: str = f"--path1='{path1.name}' and --path2='{path2.name}' must be the same type or one must be a resource and the other an installation"
    raise ValueError(msg)


def _determine_composite_loading(container_path: Path) -> tuple[bool, list[Path], str]:
    """Determine if composite loading should be used and find related files."""
    module_root = find_module_root(container_path.name)
    container_dir = container_path.parent
    related_files = []

    for ext in [".mod", ".rim", "_s.rim", "_dlg.erf"]:
        related_file = container_dir / f"{module_root}{ext}"
        if related_file.safe_exists():
            related_files.append(related_file)

    use_composite = len(related_files) > 1
    return use_composite, related_files, module_root


def _load_container_capsule(container_path: Path, *, use_composite: bool) -> Capsule | ModuleCapsuleWrapper | None:
    """Load container capsule with appropriate loading method."""
    try:
        if use_composite:
            log_output(f"Using composite module loading for {container_path.name}")
            return ModuleCapsuleWrapper(container_path)
        return Capsule(container_path)
    except Exception as e:  # noqa: BLE001
        log_output(f"Error loading container '{container_path}': {universal_simplify_exception(e)}")
        return None


def _process_container_resource(  # noqa: PLR0913
    resource: FileResource,
    container_path: Path,
    installation: Installation,
    *,
    container_first: bool,
    module_root: str | None,
    installation_logger: InstallationLogger | None = None,
) -> tuple[bool | None, bool]:
    """Process a single resource from the container.

    Returns:
        Tuple of (comparison_result, should_continue)
        comparison_result: True if same, False if different, None if error
        should_continue: True if processing should continue, False if there was an error
    """
    resname = resource.resname()
    restype = resource.restype()
    resource_identifier = f"{resname}.{restype.extension}"

    # Get resource data from container
    try:
        container_data = resource.data()
    except Exception as e:  # noqa: BLE001
        log_output(f"Error reading resource '{resource_identifier}' from container: {universal_simplify_exception(e)}")
        return None, True  # Error, but continue processing

    # Resolve resource in installation
    installation_data, resolution_info, search_log = resolve_resource_with_installation(
        installation,
        resname,
        restype,
        module_root=module_root,
        installation_logger=installation_logger,
    )

    if installation_data is None:
        log_output(f"Resource '{resource_identifier}' not found in installation - container only")
        return False, True  # Different, continue processing

    # Compare the resources
    container_name = container_path.name
    container_rel = Path(f"{container_name}/{resource_identifier}")
    installation_rel = Path(f"installation/{resource_identifier}")

    try:
        if container_first:
            ctx = DiffContext(container_rel, installation_rel, restype.extension.casefold(), skip_nss=True)
            result = diff_data(container_data, installation_data, ctx)
        else:
            ctx = DiffContext(installation_rel, container_rel, restype.extension.casefold(), skip_nss=True)
            result = diff_data(installation_data, container_data, ctx)
    except Exception as e:  # noqa: BLE001
        log_output(f"Error comparing '{resource_identifier}': {universal_simplify_exception(e)}")
        return None, True  # Error, continue processing
    else:
        # Only show installation search logs if a diff was found
        if result is False and search_log:
            log_output(search_log)
        return result, True  # Continue processing


def diff_container_vs_installation(
    container_path: Path,
    installation: Installation,
    *,
    container_first: bool = True,
) -> bool | None:
    """Compare all resources in a container against their resolved versions in an installation.

    Args:
    ----
        container_path: Path to the container file (RIM/MOD/ERF/SAV)
        installation: Already loaded Installation object
        container_first: True if container_path is path1, False if it's path2

    Returns:
    -------
        True if all identical, False if any different, None if error
    """
    container_name = container_path.name
    log_output(f"Comparing container '{container_name}' against installation resolution...")

    # Determine composite loading strategy
    use_composite, related_files, module_root = _determine_composite_loading(container_path)

    if use_composite:
        log_output(f"Found {len(related_files)} related module files for '{module_root}': {[f.name for f in related_files]}")

    # Load the container
    container_capsule = _load_container_capsule(container_path, use_composite=use_composite)
    if container_capsule is None:
        return None

    # Create installation logger to capture search output
    installation_logger = InstallationLogger()

    # Process all resources
    is_same_result: bool | None = True
    total_resources = 0
    compared_resources = 0

    # Determine module root for resource resolution
    resolution_module_root = None
    if is_capsule_file(container_path.name) and container_path.parent.name.lower() != "rims":
        resolution_module_root = find_module_root(container_path.name)
        log_output(f"Constraining search to module root '{resolution_module_root}'")

    for resource in container_capsule:
        total_resources += 1

        result, should_continue = _process_container_resource(
            resource,
            container_path,
            installation,
            container_first=container_first,
            module_root=resolution_module_root,
            installation_logger=installation_logger,
        )

        if result is None:
            is_same_result = None
        elif not result:
            is_same_result = False

        if should_continue:
            compared_resources += 1

    log_output(f"Container comparison complete: {compared_resources}/{total_resources} resources processed")
    return is_same_result


def diff_resource_vs_installation(
    resource_path: Path,
    installation: Installation,
    *,
    resource_first: bool = True,
) -> bool | None:
    """Compare a single resource file against its resolved version in an installation.

    Args:
    ----
        resource_path: Path to the single resource file
        installation: Already loaded Installation object
        resource_first: True if resource_path is path1, False if it's path2

    Returns:
    -------
        True if identical, False if different, None if error
    """
    resource_name = resource_path.name
    log_output(f"Comparing resource '{resource_name}' against installation resolution...")

    # Read the standalone resource
    try:
        resource_data = resource_path.read_bytes()
    except Exception as e:  # noqa: BLE001
        log_output(f"Error reading resource file '{resource_path}': {universal_simplify_exception(e)}")
        return None

    # Parse resource name and type
    if "." in resource_name:
        name_part, ext_part = resource_name.rsplit(".", 1)
        try:
            resource_type = ResourceType.from_extension(ext_part)
        except ValueError:
            log_output(f"Unknown resource type extension: {ext_part}")
            return False
    else:
        log_output(f"Cannot determine resource type for: {resource_name}")
        return False

    # Create installation logger to capture search output
    installation_logger = InstallationLogger()

    # Resolve the resource in the installation
    installation_data, resolution_info, search_log = resolve_resource_with_installation(
        installation,
        name_part,
        resource_type,
        installation_logger=installation_logger,
    )

    if installation_data is None:
        log_output(f"Resource '{resource_name}' not found in installation")
        return False

    # Perform the comparison
    resource_rel = Path(resource_path.name)
    installation_rel = Path(f"installation/{resource_name}")

    ext = resource_path.suffix.casefold()[1:] if resource_path.suffix else ""

    if resource_first:
        ctx = DiffContext(resource_rel, installation_rel, ext, skip_nss=True)
        result = diff_data(resource_data, installation_data, ctx)
    else:
        ctx = DiffContext(installation_rel, resource_rel, ext, skip_nss=True)
        result = diff_data(installation_data, resource_data, ctx)

    # Only show installation search logs if a diff was found
    if result is False and search_log:
        log_output(search_log)

    return result


def _normalize_path_arg(path_str: str | None) -> str | None:
    """Normalize a path argument by stripping quotes and handling Windows path issues."""
    if not path_str:
        return None

    # Strip leading/trailing whitespace
    path_str = path_str.strip()

    if not path_str:
        return None

    # Handle Windows PowerShell quote escaping issues where trailing backslash escapes the quote
    # This manifests as paths like: C:\Program Files (x86)\Steam\steamapps\common\swkotor" C:\Program
    # We need to detect and fix this by finding where the actual path likely ends

    # Check if we have what looks like a mangled path (has a quote in the middle followed by space and more path)
    if '"' in path_str and " " in path_str:
        # Try to find the actual path end - look for the quote followed by space
        quote_space_idx = path_str.find('" ')
        if quote_space_idx > 0:
            # Take everything before the quote as the path
            path_str = path_str[:quote_space_idx]

    # Strip quotes if present (handles both single and double quotes)
    if (path_str.startswith('"') and path_str.endswith('"')) or (path_str.startswith("'") and path_str.endswith("'")):
        path_str = path_str[1:-1]

    # Remove any remaining quotes that might be embedded
    path_str = path_str.replace('"', "").replace("'", "")

    # Strip trailing backslashes that may have been used before quotes
    path_str = path_str.rstrip("\\").rstrip("/")

    # Final cleanup
    path_str = path_str.strip()

    return path_str if path_str else None


def main():  # noqa: C901, PLR0912, PLR0915
    """Main entry point for KotorDiff."""
    # Configure console for UTF-8 output to handle Unicode characters
    # This prevents UnicodeEncodeError on Windows when outputting text diffs
    if sys.platform == "win32":
        try:
            # Try to reconfigure stdout/stderr to use UTF-8 with error handling
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",  # Replace unencodable chars with ?
                line_buffering=True,
            )
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:  # noqa: BLE001, S110
            # If reconfiguration fails, the error handling in log_output will catch it
            pass

    print(f"KotorDiff version {CURRENT_VERSION}")

    # Debug: Show what arguments we actually received from PowerShell
    debug_mode = os.environ.get("KOTORDIFF_DEBUG")

    if debug_mode:
        print("DEBUG: Original sys.argv:")
        for idx, arg in enumerate(sys.argv):
            print(f"  [{idx}] {arg!r}")

    # Pre-process sys.argv to fix Windows PowerShell quote escaping issues
    # This must happen BEFORE argparse sees the arguments

    # First, detect if arguments are severely mangled (e.g., --path1="..\" causes --path2 to be in same arg)
    reconstructed_argv = [sys.argv[0]]  # Keep the script name
    i = 1

    while i < len(sys.argv):
        arg = sys.argv[i]

        # Check if this arg contains multiple option flags (sign of mangling)
        # Example: '--path1=C:\path\" --path2=C:\other'
        if arg.startswith("--") and '" --' in arg:
            # This is severely mangled - split it back up
            parts = arg.split('" --')

            # First part is complete (before the split)
            reconstructed_argv.append(parts[0])

            # Second part needs to be reassembled from fragments
            # The path is split across multiple argv elements
            for idx in range(1, len(parts)):
                part = "--" + parts[idx]  # Add back the -- prefix

                # Now we need to collect fragments until we find a closing quote or another --
                path_fragments = [part]
                i += 1

                # Collect fragments until we hit a closing quote or another option
                while i < len(sys.argv):
                    next_fragment = sys.argv[i]

                    # Stop if we hit another option flag
                    if next_fragment.startswith("--"):
                        i -= 1  # Back up so we process this in the outer loop
                        break

                    # Add this fragment
                    path_fragments.append(next_fragment)

                    # Stop if this fragment ends with a quote
                    if next_fragment.endswith('"'):
                        break

                    i += 1

                # Reconstruct the full argument by joining fragments with spaces
                full_arg = " ".join(path_fragments)
                reconstructed_argv.append(full_arg)
        else:
            reconstructed_argv.append(arg)

        i += 1

    # Debug: Show reconstructed argv
    if debug_mode:
        print("\nDEBUG: Reconstructed sys.argv:")
        for idx, arg in enumerate(reconstructed_argv):
            print(f"  [{idx}] {arg!r}")

    # Now normalize the reconstructed arguments
    fixed_argv = []
    i = 0
    while i < len(reconstructed_argv):
        arg = reconstructed_argv[i]
        # Check if this is a path argument that might need normalization
        if arg.startswith(("--path", "--mine", "--older", "--yours")):
            # Check if it uses = syntax (--path1=value)
            if "=" in arg:
                key, value = arg.split("=", 1)
                normalized = _normalize_path_arg(value)
                if normalized:
                    fixed_argv.append(f"{key}={normalized}")
                else:
                    fixed_argv.append(arg)
            else:
                # Space-separated syntax (--path1 value)
                fixed_argv.append(arg)
                if i + 1 < len(reconstructed_argv):
                    i += 1
                    next_arg = reconstructed_argv[i]
                    # Normalize the value
                    normalized = _normalize_path_arg(next_arg)
                    if normalized:
                        fixed_argv.append(normalized)
                    else:
                        fixed_argv.append(next_arg)
        # Not a path argument, but might be a positional path
        # Try to normalize it in case
        elif i > 0 and not arg.startswith("-"):  # Positional argument (not a flag)
            normalized = _normalize_path_arg(arg)
            if normalized:
                fixed_argv.append(normalized)
            else:
                fixed_argv.append(arg)
        else:
            fixed_argv.append(arg)
        i += 1

    # Replace sys.argv with fixed version
    sys.argv = fixed_argv

    # Debug: Show what arguments we have after normalization
    if debug_mode:
        print("\nDEBUG: Fixed sys.argv:")
        for idx, arg in enumerate(sys.argv):
            print(f"  [{idx}] {arg!r}")
        print()

    _global_config.parser = ArgumentParser(description="Finds differences between KOTOR files/dirs. Supports 2-way and 3-way (diff3) comparisons.")
    # Legacy two-path args
    _global_config.parser.add_argument("--path1", type=str, help="Path to the first K1/TSL install, file, or directory to diff.")
    _global_config.parser.add_argument("--path2", type=str, help="Path to the second K1/TSL install, file, or directory to diff.")
    # New three-way args
    _global_config.parser.add_argument("--mine", type=str, help="Path to 'mine' (target to patch).")
    _global_config.parser.add_argument("--older", type=str, help="Path to 'older' (common ancestor/baseline).")
    _global_config.parser.add_argument("--yours", type=str, help="Path to 'yours' (desired final state).")
    _global_config.parser.add_argument(
        "--format",
        type=str,
        default="default",
        choices=["default", "unified", "context", "side_by_side"],
        help="Output format (default: default)",
    )
    _global_config.parser.add_argument(
        "--out-ini",
        nargs="?",
        const="changes.ini",
        default=None,
        help="Generate changes.ini for TSLPatcher. Optionally specify output path (default: changes.ini). For 3-way diffs, defaults to 'changes.ini' if not specified.",
    )
    _global_config.parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
    _global_config.parser.add_argument(
        "--log-level", type=str, default="info", choices=["debug", "info", "warning", "error", "critical"], help="Logging level (default: info)"
    )
    _global_config.parser.add_argument(
        "--output-mode",
        type=str,
        default="full",
        choices=["full", "diff_only", "quiet"],
        help="Output mode: full (all logs), diff_only (only diff results), quiet (minimal) (default: full)",
    )
    _global_config.parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    _global_config.parser.add_argument(
        "--compare-hashes",
        type=bool,
        default=True,
        help="Compare hashes of any unsupported file/resource type (default is True)",
    )
    _global_config.parser.add_argument(
        "--filter",
        action="append",
        help="Filter specific files/modules for installation-wide diffs (can be used multiple times). "
        "Examples: 'tat_m18ac' for module, 'some_character.utc' for specific resource",
    )
    _global_config.parser.add_argument(
        "--logging",
        type=bool,
        default=True,
        help="Whether to log the results to a file or not (default is True)",
    )
    _global_config.parser.add_argument(
        "--use-profiler",
        type=bool,
        default=False,
        help="Use cProfile to find where most of the execution time is taking place in source code.",
    )

    # Use parse_known_args to capture positional arguments without adding them to help
    _global_config.parser_args, unknown_args = _global_config.parser.parse_known_args()
    _global_config.logging_enabled = bool(_global_config.parser_args.logging is None or _global_config.parser_args.logging)

    # Normalize all path arguments
    _global_config.parser_args.path1 = _normalize_path_arg(_global_config.parser_args.path1)
    _global_config.parser_args.path2 = _normalize_path_arg(_global_config.parser_args.path2)
    _global_config.parser_args.mine = _normalize_path_arg(_global_config.parser_args.mine)
    _global_config.parser_args.older = _normalize_path_arg(_global_config.parser_args.older)
    _global_config.parser_args.yours = _normalize_path_arg(_global_config.parser_args.yours)

    # Handle Windows PowerShell quote escaping in unknown args
    # If we have multiple unknown args that look like they were split incorrectly, try to reassemble
    cleaned_unknown = []
    i = 0
    while i < len(unknown_args):
        current = unknown_args[i]
        # Check if this looks like the start of a path that was split (ends with quote and space)
        if i + 1 < len(unknown_args) and ('" ' in current or "' " in current):
            # Try to reassemble - take everything up to the quote
            normalized = _normalize_path_arg(current)
            if normalized:
                cleaned_unknown.append(normalized)
            i += 1
            # Skip the mangled continuation
            continue
        normalized = _normalize_path_arg(current)
        if normalized:
            cleaned_unknown.append(normalized)
        i += 1

    unknown_args = cleaned_unknown

    # Set up the new logging system if available
    if setup_logger is not None and LogLevel is not None and OutputMode is not None:
        log_level = getattr(LogLevel, _global_config.parser_args.log_level.upper())
        output_mode = getattr(OutputMode, _global_config.parser_args.output_mode.upper())
        use_colors = not _global_config.parser_args.no_color

        # Set up output file if specified
        output_file = None
        if _global_config.parser_args.output_log:
            try:
                output_file = Path(_global_config.parser_args.output_log).open("w", encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                print(f"Warning: Could not open log file {_global_config.parser_args.output_log}: {e}")

        setup_logger(log_level, output_mode, use_colors, output_file)

    def prompt_for_path(title: str) -> str:
        """Prompt the user for a path input."""
        user_input = input(f"{title}: ").strip()
        return _normalize_path_arg(user_input) or ""

    def print_path_error_with_help(path: Path) -> None:
        """Print error message for invalid path with helpful quoting guidance."""
        print("Invalid path:", path)
        # Detect if this might be a quoting issue
        path_str = str(path)
        if '"' in path_str or not path.parent.safe_exists():
            print("\nNote: If using paths with spaces and trailing backslashes in PowerShell:")
            print('  - Remove trailing backslash: --path1="C:\\Program Files\\folder"')
            print('  - Or double the backslash: --path1="C:\\Program Files\\folder\\\\"')
            print('  - Or use forward slashes: --path1="C:/Program Files/folder/"')
        if _global_config.parser:
            _global_config.parser.print_help()

    # Decide between 2-way and 3-way usage
    # Prefer explicit args, fallback to positional args
    mine_arg: str | None = _global_config.parser_args.mine or (unknown_args[0] if len(unknown_args) > 0 else None)
    older_arg: str | None = _global_config.parser_args.older or (unknown_args[1] if len(unknown_args) > 1 else None)
    yours_arg: str | None = _global_config.parser_args.yours or (unknown_args[2] if len(unknown_args) > 2 else None)  # noqa: PLR2004

    is_three_way: bool = bool(mine_arg and older_arg and yours_arg)

    if is_three_way:
        _global_config.parser_args.mine = Path(mine_arg).resolve()
        _global_config.parser_args.older = Path(older_arg).resolve()
        _global_config.parser_args.yours = Path(yours_arg).resolve()
        for _label, p in (("--mine", _global_config.parser_args.mine), ("--older", _global_config.parser_args.older), ("--yours", _global_config.parser_args.yours)):
            if not p.safe_exists():
                print("Invalid path:", p)
                _global_config.parser.print_help()
                sys.exit(2)
    else:
        # Handle 2-way comparison
        # Priority: --path1 > positional arg > prompt
        # Get initial path1 from explicit arg or positional arg
        initial_path1 = _global_config.parser_args.path1 or (unknown_args[0] if len(unknown_args) > 0 else None)

        while True:
            if initial_path1:
                path1_str = initial_path1
                initial_path1 = None  # Only use once
            else:
                path1_str = prompt_for_path("Path to the first K1/TSL install, file, or directory to diff.")

            if not path1_str:
                print("Path cannot be empty")
                continue

            _global_config.parser_args.path1 = Path(path1_str).resolve()

            if _global_config.parser_args.path1.safe_exists():
                break

            # Check if this could be a module name by trying to find related module files
            potential_module_files = []
            base_name = _global_config.parser_args.path1.name
            parent_dir = _global_config.parser_args.path1.parent

            for ext in [".mod", ".rim", "_s.rim", "_dlg.erf"]:
                module_file = parent_dir / f"{base_name}{ext}"
                if module_file.safe_exists():
                    potential_module_files.append(module_file)

            if potential_module_files:
                # Found module files, use the first one as the representative path
                # The composite loading logic will handle finding all related files
                _global_config.parser_args.path1 = potential_module_files[0]
                log_output(f"Resolved module name '{base_name}' to: {_global_config.parser_args.path1}")
                break

            print_path_error_with_help(_global_config.parser_args.path1)

        # Priority: --path2 > positional arg > prompt
        # Get initial path2 from explicit arg or positional arg
        initial_path2 = _global_config.parser_args.path2 or (unknown_args[1] if len(unknown_args) > 1 else None)

        while True:
            if initial_path2:
                path2_str = initial_path2
                initial_path2 = None  # Only use once
            else:
                path2_str = prompt_for_path("Path to the second K1/TSL install, file, or directory to diff.")

            if not path2_str:
                print("Path cannot be empty")
                continue

            _global_config.parser_args.path2 = Path(path2_str).resolve()

            if _global_config.parser_args.path2.safe_exists():
                break

            # Check if this could be a module name by trying to find related module files
            potential_module_files = []
            base_name = _global_config.parser_args.path2.name
            parent_dir = _global_config.parser_args.path2.parent

            for ext in [".mod", ".rim", "_s.rim", "_dlg.erf"]:
                module_file = parent_dir / f"{base_name}{ext}"
                if module_file.safe_exists():
                    potential_module_files.append(module_file)

            if potential_module_files:
                # Found module files, use the first one as the representative path
                # The composite loading logic will handle finding all related files
                _global_config.parser_args.path2 = potential_module_files[0]
                log_output(f"Resolved module name '{base_name}' to: {_global_config.parser_args.path2}")
                break

            print_path_error_with_help(_global_config.parser_args.path2)

    _global_config.parser_args.use_profiler = bool(_global_config.parser_args.use_profiler)
    _global_config.parser_args.compare_hashes = not bool(_global_config.parser_args.compare_hashes)

    log_output()
    if is_three_way:
        log_output(f"Using --mine='{_global_config.parser_args.mine}'")
        log_output(f"Using --older='{_global_config.parser_args.older}'")
        log_output(f"Using --yours='{_global_config.parser_args.yours}'")
    else:
        log_output(f"Using --path1='{_global_config.parser_args.path1}'")
        log_output(f"Using --path2='{_global_config.parser_args.path2}'")
    log_output(f"Using --compare-hashes={_global_config.parser_args.compare_hashes}")
    log_output(f"Using --use-profiler={_global_config.parser_args.use_profiler}")

    profiler = None
    try:
        if _global_config.parser_args.use_profiler:
            profiler = cProfile.Profile()
            profiler.enable()

        if is_three_way:
            # For 3-way diffs, generate INI by default to "changes.ini" unless --out-ini is not provided
            # If --out-ini is provided (with or without path), use that value
            out_ini_path: Path | None
            if _global_config.parser_args.out_ini is not None:
                # --out-ini was provided (either with path or without, in which case it's "changes.ini")
                out_ini_path = Path(_global_config.parser_args.out_ini).resolve()
            else:
                # Default behavior for 3-way: generate to "changes.ini"
                out_ini_path = Path("changes.ini").resolve()

            assert isinstance(_global_config.parser_args.mine, Path)
            assert isinstance(_global_config.parser_args.older, Path)
            assert isinstance(_global_config.parser_args.yours, Path)
            config = IniGenerationConfig(
                generate_ini=True,
                out_ini=out_ini_path,
            )
            run_differ3_from_args(
                _global_config.parser_args.mine,
                _global_config.parser_args.older,
                _global_config.parser_args.yours,
                config,
            )
            comparison = None
        else:
            assert isinstance(_global_config.parser_args.path1, Path)
            assert isinstance(_global_config.parser_args.path2, Path)
            comparison = run_differ_from_args(
                _global_config.parser_args.path1,
                _global_config.parser_args.path2,
                filters=_global_config.parser_args.filter,
            )

            # Generate changes.ini only if --out-ini is explicitly provided for 2-way diffs
            if _global_config.parser_args.out_ini is not None:
                ini_out: Path = Path(_global_config.parser_args.out_ini).resolve()
                log_output(f"Generating changes.ini and staging files at: {ini_out.parent}")
                try:
                    _generate_changes_ini(
                        _global_config.parser_args.path1,  # mine (target to patch)
                        _global_config.parser_args.path1,  # older baseline same as mine in 2-way mode
                        _global_config.parser_args.path2,  # yours (desired state)
                        out_path=ini_out,
                    )
                except Exception as e:  # noqa: BLE001
                    log_output(f"[Error] Failed to generate changes.ini: {universal_simplify_exception(e)}")

        if profiler is not None:
            _stop_profiler(profiler)
        if comparison is not None:
            assert isinstance(_global_config.parser_args.path1, PurePath)
            assert isinstance(_global_config.parser_args.path2, PurePath)
            log_output(
                f"'{relative_path_from_to(_global_config.parser_args.path2, _global_config.parser_args.path1)}'",
                " MATCHES " if comparison else " DOES NOT MATCH ",
                f"'{relative_path_from_to(_global_config.parser_args.path1, _global_config.parser_args.path2)}'",
            )
            if comparison is True:
                sys.exit(0)
            if comparison is False:
                sys.exit(2)
        if comparison is None:
            log_output("Completed with errors found during comparison")
            sys.exit(3)
    except KeyboardInterrupt:
        log_output("KeyboardInterrupt - KotorDiff was cancelled by user.")
        raise
    finally:
        if profiler is not None:
            _stop_profiler(profiler)


def _stop_profiler(profiler: cProfile.Profile):
    profiler.disable()
    profiler_output_file = Path("profiler_output.pstat")
    profiler.dump_stats(str(profiler_output_file))
    log_output(f"Profiler output saved to: {profiler_output_file}")


if __name__ == "__main__":
    main()
