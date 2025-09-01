#!/usr/bin/env python3
from __future__ import annotations

import cProfile
import os
import pathlib
import sys

from argparse import ArgumentParser
from io import StringIO
from typing import TYPE_CHECKING, Callable

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

from pathlib import Path, PureWindowsPath

from pykotor.extract.capsule import Capsule
from pykotor.resource.formats import gff, lip, tlk, twoda
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.path import CaseAwarePath
from utility.error_handling import universal_simplify_exception
from utility.misc import generate_hash

# Protected imports for dialog functions
try:
    from utility.system.agnostics import askdirectory, askopenfilename
    DIALOGS_AVAILABLE = True
except ImportError:
    DIALOGS_AVAILABLE = False
    askdirectory = None
    askopenfilename = None

if os.name == "nt":
    try:
        from utility.system.win32.com.windialogs import open_file_and_folder_dialog
        WIN32_DIALOGS_AVAILABLE = True
    except ImportError:
        WIN32_DIALOGS_AVAILABLE = False
        open_file_and_folder_dialog = None
else:
    WIN32_DIALOGS_AVAILABLE = False
    open_file_and_folder_dialog = None

if TYPE_CHECKING:
    from pathlib import PurePath

    from pykotor.extract.file import FileResource

CURRENT_VERSION = "1.0.0b1"
OUTPUT_LOG: Path | None = None
LOGGING_ENABLED: bool | None = None

PARSER_ARGS = None
PARSER = None


def log_output(*args, **kwargs):
    global OUTPUT_LOG  # noqa: PLW0603
    # Create an in-memory text stream
    buffer = StringIO()

    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg = buffer.getvalue()

    # Print the captured output to console
    print(*args, **kwargs)  # noqa: T201

    if not LOGGING_ENABLED or not PARSER_ARGS or not PARSER:
        return

    if not OUTPUT_LOG:
        chosen_log_file_path: str = "log_install_differ.log"
        OUTPUT_LOG = Path(chosen_log_file_path).resolve()
        if not OUTPUT_LOG.parent.is_dir():
            while True:
                chosen_log_file_path: str = PARSER_ARGS.output_log or input("Filepath of the desired output logfile: ").strip() or "log_install_differ.log"
                OUTPUT_LOG = Path(chosen_log_file_path).resolve()
                if OUTPUT_LOG.parent.is_dir():
                    break
                print("Invalid path:", OUTPUT_LOG)
                PARSER.print_help()

    # Write the captured output to the file
    with OUTPUT_LOG.open("a", encoding="utf-8") as f:
        f.write(msg)


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


def diff_data(
    data1: bytes | Path,
    data2: bytes | Path,
    file1_rel: Path,
    file2_rel: Path,
    ext: str,
    resname: str | None = None,
) -> bool | None:
    where: PureWindowsPath | str = PureWindowsPath(file1_rel.name, f"{resname}.{ext}") if resname else file1_rel.name

    if not data1 and data2:
        return log_output(f"[Error] Cannot determine data for '{where}' in '{file1_rel}'")  # type: ignore[func-returns-value]
    if data1 and not data2:
        return log_output(f"[Error] Cannot determine data for '{where}' in '{file2_rel}'")  # type: ignore[func-returns-value]
    if not data1 and not data2:  # sourcery skip: extract-duplicate-method
        # message = f"No data for either resource: '{where}'"  # noqa: ERA001
        # log_output(message)  # noqa: ERA001
        return True

    assert PARSER_ARGS
    if ext == "tlk" and PARSER_ARGS.ignore_tlk:
        return True
    if ext == "lip" and PARSER_ARGS.ignore_lips:
        return True

    if ext in gff_types:
        gff1: gff.GFF | None = None
        gff2: gff.GFF | None = None
        try:
            gff1 = gff.read_gff(data1)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"[Error] loading GFF {file1_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        try:
            gff2 = gff.read_gff(data2)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"[Error] loading GFF {file2_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        if gff1 and not gff2:
            return log_output(f"GFF resource missing in memory:\t'{file1_rel.parent / where}'")  # type: ignore[func-returns-value]
        if not gff1 and gff2:
            return log_output(f"GFF resource missing in memory:\t'{file2_rel.parent / where}'")  # type: ignore[func-returns-value]
        if not gff1 and not gff2:
            return log_output(f"Both GFF resources missing in memory:\t'{where}'")  # type: ignore[func-returns-value]
        if gff1 and gff2 and not gff1.compare(gff2, log_output, PureWindowsPath(where)):
            log_output_with_separator(f"^ '{where}': GFF is different ^")
            return False
        return True

    if ext == "2da":
        twoda1: twoda.TwoDA | None = None
        twoda2: twoda.TwoDA | None = None
        try:
            twoda1 = twoda.read_2da(data1)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            if file1_rel.parent.name.lower() == "rims" and file1_rel.name.lower() in {"global.rim", "miniglobal.rim"}:
                return True
            return log_output(f"Error loading 2DA {file1_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        try:
            twoda2 = twoda.read_2da(data2)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            if file1_rel.parent.name.lower() == "rims" and file1_rel.name.lower() in {"global.rim", "miniglobal.rim"}:
                return True
            return log_output(f"Error loading 2DA {file2_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        if twoda1 and not twoda2:
            message = f"2DA resource missing in memory:\t'{file1_rel.parent / where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if not twoda1 and twoda2:
            message = f"2DA resource missing in memory:\t'{file2_rel.parent / where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if not twoda1 and not twoda2:
            message = f"Both 2DA resources missing in memory:\t'{where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if twoda1 and twoda2 and not twoda1.compare(twoda2, log_output):
            log_output_with_separator(f"^ '{where}': 2DA is different ^")
            return False
        return True

    if ext == "tlk":
        tlk1: tlk.TLK | None = None
        tlk2: tlk.TLK | None = None
        try:
            log_output(f"Loading TLK '{file1_rel.parent / where}'")
            tlk1 = tlk.read_tlk(data1)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"Error loading TLK {file1_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        try:
            log_output(f"Loading TLK '{file2_rel.parent / where}'")
            tlk2 = tlk.read_tlk(data2)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"Error loading TLK {file2_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        if tlk1 and not tlk2:
            message = f"TLK resource missing in memory:\t'{file1_rel.parent / where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if not tlk1 and tlk2:
            message = f"TLK resource missing in memory:\t'{file2_rel.parent / where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if not tlk1 and not tlk2:
            message = f"Both TLK resources missing in memory:\t'{where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if tlk1 and tlk2 and not tlk1.compare(tlk2, log_output):
            log_output_with_separator(f"^ '{where}': TLK is different ^", surround=True)
            return False
        return True

    if ext == "lip":
        lip1: lip.LIP | None = None
        lip2: lip.LIP | None = None
        try:
            lip1 = lip.read_lip(data1)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"Error loading LIP {file1_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        try:
            lip2 = lip.read_lip(data2)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            return log_output(f"Error loading LIP {file2_rel.parent / where}!\n{universal_simplify_exception(e)}")  # type: ignore[func-returns-value]
        if lip1 and not lip2:
            message = f"LIP resource missing in memory:\t'{file1_rel.parent / where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if not lip1 and lip2:
            message = f"LIP resource missing in memory:\t'{file2_rel.parent / where}'"
            return log_output(message)  # type: ignore[func-returns-value]
        if not lip1 and not lip2:
            message = f"Both LIP resources missing in memory:\t'{where}'"
            log_output(message)
            log_output(len(message) * "-")
            return True
        if lip1 and lip2 and not lip1.compare(lip2, log_output):
            message = f"^ '{where}': LIP is different ^"
            return log_output_with_separator(message)
        return True

    if PARSER_ARGS.compare_hashes and generate_hash(data1) != generate_hash(data2):
        log_output(f"'{where}': SHA256 is different")
        return False
    return True


def log_output_with_separator(message, *, below=True, above=False, surround=False):
    if above or surround:
        log_output(visual_length(message) * "-")
    log_output(message)
    if (below and not above) or surround:
        log_output(visual_length(message) * "-")


def diff_files(file1: os.PathLike | str, file2: os.PathLike | str) -> bool | None:
    c_file1 = Path(file1).resolve()
    c_file2 = Path(file2).resolve()
    c_file1_rel: Path = relative_path_from_to(c_file2, c_file1)
    c_file2_rel: Path = relative_path_from_to(c_file1, c_file2)
    is_same_result: bool | None = True

    if not c_file1.is_file():
        log_output(f"Missing file:\t{c_file1_rel}")
        return False
    if not c_file2.is_file():
        log_output(f"Missing file:\t{c_file2_rel}")
        return False

    if is_capsule_file(c_file1_rel.name):
        try:
            file1_capsule = Capsule(file1)
        except ValueError as e:
            log_output(f"Could not load '{c_file1_rel}'. Reason: {universal_simplify_exception(e)}")
            return None
        try:
            file2_capsule = Capsule(file2)
        except ValueError as e:
            log_output(f"Could not load '{c_file2_rel}'. Reason: {universal_simplify_exception(e)}")
            return None

        # Build dict of resources
        capsule1_resources: dict[str, FileResource] = {res.resname(): res for res in file1_capsule}
        capsule2_resources: dict[str, FileResource] = {res.resname(): res for res in file2_capsule}

        # Identifying missing resources
        missing_in_capsule1: set[str] = capsule2_resources.keys() - capsule1_resources.keys()
        missing_in_capsule2: set[str] = capsule1_resources.keys() - capsule2_resources.keys()
        for resref in missing_in_capsule1:
            message = f"Capsule1 resource missing\t{c_file1_rel}\t{resref}\t{capsule2_resources[resref].restype().extension.upper()}"
            log_output(message)

        for resref in missing_in_capsule2:
            message = f"Capsule2 resource missing\t{c_file2_rel}\t{resref}\t{capsule1_resources[resref].restype().extension.upper()}"
            log_output(message)

        # Checking for differences
        common_resrefs: set[str] = capsule1_resources.keys() & capsule2_resources.keys()  # Intersection of keys
        for resref in common_resrefs:
            res1: FileResource = capsule1_resources[resref]
            res2: FileResource = capsule2_resources[resref]
            ext: str = res1.restype().extension.lower()
            result: bool | None = diff_data(res1.data(), res2.data(), c_file1_rel, c_file2_rel, ext, resref) and is_same_result
            is_same_result = None if result is None else result and is_same_result
        return is_same_result
    return diff_data(c_file1, c_file2, c_file1_rel, c_file2_rel, c_file1_rel.suffix.lower()[1:])


def diff_directories(dir1: os.PathLike | str, dir2: os.PathLike | str) -> bool | None:
    c_dir1 = Path(dir1).resolve()
    c_dir2 = Path(dir2).resolve()

    log_output_with_separator(f"Finding differences in the '{c_dir1.name}' folders...", above=True)

    # Store relative paths instead of just filenames
    files_path1: set[str] = {f.relative_to(c_dir1).as_posix().lower() for f in c_dir1.rglob("*") if f.is_file()}
    files_path2: set[str] = {f.relative_to(c_dir2).as_posix().lower() for f in c_dir2.rglob("*") if f.is_file()}

    # Merge both sets to iterate over unique relative paths
    all_files: set[str] = files_path1.union(files_path2)

    is_same_result: bool | None = True
    for rel_path in all_files:
        result: bool | None = diff_files(c_dir1 / rel_path, c_dir2 / rel_path)
        is_same_result = None if result is None else result and is_same_result

    return is_same_result


def diff_installs(install_path1: os.PathLike | str, install_path2: os.PathLike | str) -> bool | None:
    # TODO(th3w1zard1): use pykotor.extract.installation
    rinstall_path1: CaseAwarePath = CaseAwarePath(install_path1).resolve()
    rinstall_path2: CaseAwarePath = CaseAwarePath(install_path2).resolve()
    log_output()
    log_output((max(len(str(rinstall_path1)) + 29, len(str(rinstall_path2)) + 30)) * "-")
    log_output("Searching first install dir:", rinstall_path1)
    log_output("Searching second install dir:", rinstall_path2)
    log_output()

    is_same_result = diff_files(rinstall_path1.joinpath("dialog.tlk"), rinstall_path2 / "dialog.tlk")
    modules_path1: CaseAwarePath = rinstall_path1 / "Modules"
    modules_path2: CaseAwarePath = rinstall_path2 / "Modules"
    is_same_result = diff_directories(modules_path1, modules_path2) and is_same_result

    override_path1: CaseAwarePath = rinstall_path1 / "Override"
    override_path2: CaseAwarePath = rinstall_path2 / "Override"
    is_same_result = diff_directories(override_path1, override_path2) and is_same_result

    rims_path1: CaseAwarePath = rinstall_path1 / "rims"
    rims_path2: CaseAwarePath = rinstall_path2 / "rims"
    is_same_result = diff_directories(rims_path1, rims_path2) and is_same_result

    lips_path1: CaseAwarePath = rinstall_path1 / "Lips"
    lips_path2: CaseAwarePath = rinstall_path2 / "Lips"
    is_same_result = diff_directories(lips_path1, lips_path2) and is_same_result

    streamwaves_path1: CaseAwarePath = (
        rinstall_path1.joinpath("streamwaves")
        if rinstall_path1.joinpath("streamwaves").is_dir()
        else rinstall_path1.joinpath("streamvoice")
    )
    streamwaves_path2: CaseAwarePath = (
        rinstall_path2.joinpath("streamwaves")
        if rinstall_path2.joinpath("streamwaves").is_dir()
        else rinstall_path2.joinpath("streamvoice")
    )
    is_same_result = diff_directories(streamwaves_path1, streamwaves_path2) and is_same_result
    return is_same_result  # noqa: RET504


def is_kotor_install_dir(path: os.PathLike | str) -> bool | None:
    c_path: CaseAwarePath = CaseAwarePath(path)
    return c_path.is_dir() and c_path.joinpath("chitin.key").is_file()


def run_differ_from_args(path1: Path, path2: Path) -> bool | None:
    if not path1.exists():
        log_output(f"--path1='{path1}' does not exist on disk, cannot diff")
        return None
    if not path2.exists():
        log_output(f"--path2='{path2}' does not exist on disk, cannot diff")
        return None
    if is_kotor_install_dir(path1) and is_kotor_install_dir(path2):
        return diff_installs(path1, path2)
    if path1.is_dir() and path2.is_dir():
        return diff_directories(path1, path2)
    if path1.is_file() and path2.is_file():
        return diff_files(path1, path2)
    msg = f"--path1='{path1.name}' and --path2='{path2.name}' must be the same type"
    raise ValueError(msg)


def main():
    print(f"KotorDiff version {CURRENT_VERSION}")
    global PARSER_ARGS
    global PARSER  # noqa: PLW0603
    global LOGGING_ENABLED  # noqa: PLW0603
    PARSER = ArgumentParser(description="Finds differences between two KOTOR installations")
    PARSER.add_argument("--path1", type=str, help="Path to the first K1/TSL install, file, or directory to diff.")
    PARSER.add_argument("--path2", type=str, help="Path to the second K1/TSL install, file, or directory to diff.")
    PARSER.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
    PARSER.add_argument("--compare-hashes", type=bool, help="Compare hashes of any unsupported file/resource type (default is True)")
    PARSER.add_argument("--ignore-rims", type=bool, help="Whether to compare RIMS (default is False)")
    PARSER.add_argument("--ignore-tlk", type=bool, help="Whether to compare TLK files (default is False)")
    PARSER.add_argument("--ignore-lips", type=bool, help="Whether to compare LIPS (default is False)")
    PARSER.add_argument("--logging", type=bool, help="Whether to log the results to a file or not (default is True)")
    PARSER.add_argument("--use-profiler", type=bool, default=False, help="Use cProfile to find where most of the execution time is taking place in source code.")


    PARSER_ARGS, unknown = PARSER.parse_known_args()
    
    LOGGING_ENABLED = bool(PARSER_ARGS.logging is None or PARSER_ARGS.logging)

    lookup_function: Callable[[str], str] | None = None  # pyright: ignore[reportRedeclaration, reportAssignmentType]

    def get_lookup_function() -> Callable[[str], str]:
        nonlocal lookup_function
        if lookup_function is not None:
            return lookup_function
        
        if not DIALOGS_AVAILABLE:
            def lookup_function(title: str) -> str:
                return input(f"{title}: ").strip()
            return lookup_function
            
        if os.name == "nt" and WIN32_DIALOGS_AVAILABLE:
            def lookup_function(title: str) -> str:
                result = open_file_and_folder_dialog(title=title)
                return result[0] if result else ""
        else:
            choice = input("Do you want to pick a path using a ui-based file/directory picker? (y/N)").strip().lower()
            if not choice or choice == "y":
                file_or_dir_choice = input("Do you want to pick a file? (No for directory) (y/N)").strip().lower()
                if file_or_dir_choice == "yes":
                    def lookup_function(title: str) -> str:
                        return askopenfilename(title=title) if askopenfilename else input(f"{title}: ").strip()
                else:
                    def lookup_function(title: str) -> str:
                        return askdirectory(title=title) if askdirectory else input(f"{title}: ").strip()
            else:
                def lookup_function(title: str) -> str:
                    return input(f"{title}: ").strip()
        return lookup_function

    while True:
        PARSER_ARGS.path1 = Path(
            PARSER_ARGS.path1
            or (unknown[0] if len(unknown) > 0 else None)
            or get_lookup_function()("Path to the first K1/TSL install, file, or directory to diff."),
        ).resolve()
        if PARSER_ARGS.path1.exists():
            break
        print("Invalid path:", PARSER_ARGS.path1)
        PARSER.print_help()
        PARSER_ARGS.path1 = None
    while True:
        PARSER_ARGS.path2 = Path(
            PARSER_ARGS.path2
            or (unknown[1] if len(unknown) > 1 else None)
            or get_lookup_function()("Path to the second K1/TSL install, file, or directory to diff."),
        ).resolve()
        if PARSER_ARGS.path2.exists():
            break
        print("Invalid path:", PARSER_ARGS.path2)
        PARSER.print_help()
        PARSER_ARGS.path2 = None

    PARSER_ARGS.ignore_rims = bool(PARSER_ARGS.ignore_rims)
    PARSER_ARGS.ignore_lips = bool(PARSER_ARGS.ignore_lips)
    PARSER_ARGS.ignore_tlk = bool(PARSER_ARGS.ignore_tlk)
    PARSER_ARGS.use_profiler = bool(PARSER_ARGS.use_profiler)
    PARSER_ARGS.compare_hashes = not bool(PARSER_ARGS.compare_hashes)

    log_output()
    log_output(f"Using --path1='{PARSER_ARGS.path1}'")
    log_output(f"Using --path2='{PARSER_ARGS.path2}'")
    log_output(f"Using --ignore-rims={PARSER_ARGS.ignore_rims}")
    log_output(f"Using --ignore-tlk={PARSER_ARGS.ignore_tlk}")
    log_output(f"Using --ignore-lips={PARSER_ARGS.ignore_lips}")
    log_output(f"Using --compare-hashes={PARSER_ARGS.compare_hashes}")
    log_output(f"Using --use-profiler={PARSER_ARGS.use_profiler}")

    profiler = None
    try:
        if PARSER_ARGS.use_profiler:
            profiler = cProfile.Profile()
            profiler.enable()

        comparison: bool | None = run_differ_from_args(
            PARSER_ARGS.path1,
            PARSER_ARGS.path2,
        )

        if profiler is not None:
            _stop_profiler(profiler)
        if comparison is not None:
            log_output(
                f"'{relative_path_from_to(PARSER_ARGS.path2, PARSER_ARGS.path1)}'",
                " MATCHES " if comparison else " DOES NOT MATCH ",
                f"'{relative_path_from_to(PARSER_ARGS.path1, PARSER_ARGS.path2)}'",
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
