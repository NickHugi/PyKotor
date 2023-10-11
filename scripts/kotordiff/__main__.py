from __future__ import annotations

import argparse
import cProfile
import hashlib
import io
import os
import pathlib
import sys

# Ensure the directory of the script is in sys.path
script_dir = pathlib.Path(__file__).parent.resolve()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))
from settings import setup_environment

setup_environment()

from pykotor.resource.formats.erf import ERFResource, read_erf
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff
from pykotor.resource.formats.lip import LIP, read_lip
from pykotor.resource.formats.rim import RIMResource, read_rim
from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.resource.formats.twoda import read_2da
from pykotor.tools.misc import is_capsule_file, is_erf_or_mod_file, is_rim_file
from pykotor.tools.path import CaseAwarePath, Path, PureWindowsPath
from pykotor.tslpatcher.diff.gff import DiffGFF
from pykotor.tslpatcher.diff.lip import DiffLIP
from pykotor.tslpatcher.diff.tlk import DiffTLK
from pykotor.tslpatcher.diff.twoda import Diff2DA

OUTPUT_LOG: Path


def log_output(*args, **kwargs) -> None:
    # Create an in-memory text stream
    buffer = io.StringIO()

    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg = buffer.getvalue()

    # Write the captured output to the file
    with OUTPUT_LOG.open("a") as f:
        f.write(msg)

    # Print the captured output to console
    print(*args, **kwargs)  # noqa: T201


def compute_sha256(where: os.PathLike | str | bytes):
    """Compute the SHA-256 hash of the data."""
    if isinstance(where, bytes):
        return compute_sha256_from_bytes(where)
    if isinstance(where, (os.PathLike | str)):
        file_path = CaseAwarePath(where)
        return compute_sha256_from_path(file_path)
    return None


def compute_sha256_from_path(file_path: CaseAwarePath) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as f:
        while True:
            data = f.read(0x10000)  # read in 64k chunks
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest()


def compute_sha256_from_bytes(data: bytes) -> str:
    """Compute the SHA-256 hash of bytes data."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()


def relative_path_from_to(src, dst) -> CaseAwarePath:
    src_parts = list(src.parts)
    dst_parts = list(dst.parts)

    common_length = next(
        (i for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts)) if src_part != dst_part),
        len(src_parts),
    )
    rel_parts = dst_parts[common_length:]
    return CaseAwarePath(*rel_parts)


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


gff_types = [x.value.lower().strip() for x in GFFContent]


def diff_data(
    data1: bytes | CaseAwarePath,
    data2: bytes | CaseAwarePath,
    file1_rel: CaseAwarePath,
    file2_rel: CaseAwarePath,
    ext: str,
    resname: str | None = None,
) -> bool | None:
    where = PureWindowsPath(file1_rel.name, f"{resname}.{ext}") if resname else file1_rel.name

    if not data1 and data2:
        return log_output_with_separator(f"Cannot determine data for '{where}' in '{file1_rel}'")
    if data1 and not data2:
        return log_output_with_separator(f"Cannot determine data for '{where}' in '{file2_rel}'")
    if not data1 and not data2:
        # message = f"No data for either resource: '{where}'"  # noqa: ERA001
        # log_output(message)  # noqa: ERA001
        # log_output(len(message) * "-")  # noqa: ERA001
        return True

    if ext == "tlk" and parser_args.ignore_tlk:
        return True
    if ext == "lip" and parser_args.ignore_lips:
        return True

    if ext in gff_types:
        gff1: GFF | None = read_gff(data1)
        gff2: GFF | None = read_gff(data2)
        if gff1 and not gff2:
            return log_output_with_separator(f"GFF resource missing in memory:\t'{file1_rel.parent / where}'")
        if not gff1 and gff2:
            return log_output_with_separator(f"GFF resource missing in memory:\t'{file2_rel.parent / where}'")
        if not gff1 and not gff2:
            return log_output_with_separator(f"Both GFF resources missing in memory:\t'{where}'")
        if gff1 and gff2:
            diff = DiffGFF(gff1, gff2, log_output)
            if not diff.is_same(current_path=where):
                log_output_with_separator(f"^ '{where}': GFF is different ^")
                return False
        return True

    if ext == "2da":
        twoda1 = read_2da(data1)
        twoda2 = read_2da(data2)
        if twoda1 and not twoda2:
            message = f"TSLPatcher 2DA resource missing in memory:\t'{file1_rel.parent / where}'"
            return log_output_with_separator(message)
        if not twoda1 and twoda2:
            message = f"2DA resource missing in memory:\t'{file2_rel.parent / where}'"
            return log_output_with_separator(message)
        if not twoda1 and not twoda2:
            message = f"Both 2DA resources missing in memory:\t'{where}'"
            return log_output_with_separator(message)
        if twoda1 and twoda2:
            diff = Diff2DA(twoda2, twoda1, log_output)
            if not diff.is_same():
                log_output_with_separator(f"^ '{where}': 2DA is different ^")
                return False
        return True

    if ext == "tlk":
        log_output(f"Loading TLK '{file1_rel.parent / where}'")
        tlk1: TLK = read_tlk(data1)
        log_output(f"Loading TLK '{file2_rel.parent / where}'")
        tlk2: TLK = read_tlk(data2)
        if tlk1 and not tlk2:
            message = f"TLK resource missing in memory:\t'{file1_rel.parent / where}'"
            return log_output_with_separator(message)
        if not tlk1 and tlk2:
            message = f"TLK resource missing in memory:\t'{file2_rel.parent / where}'"
            return log_output_with_separator(message)
        if not tlk1 and not tlk2:
            message = f"Both TLK resources missing in memory:\t'{where}'"
            return log_output_with_separator(message)
        if tlk1 and tlk2:
            diff = DiffTLK(tlk1, tlk2, log_output)
            if not diff.is_same():
                log_output_with_separator(f"^ '{where}': TLK is different ^")
                return False
        return True

    if ext == "lip":
        lip1: LIP | None = read_lip(data1) if isinstance(data1, bytes) or data1.stat().st_size > 0 else None
        lip2: LIP | None = read_lip(data2) if isinstance(data2, bytes) or data2.stat().st_size > 0 else None
        if lip1 and not lip2:
            message = f"LIP resource missing in memory:\t'{file1_rel.parent / where}'"
            return log_output_with_separator(message)
        if not lip1 and lip2:
            message = f"LIP resource missing in memory:\t'{file2_rel.parent / where}'"
            return log_output_with_separator(message)
        if not lip1 and not lip2:
            # message = f"Both LIP resources missing in memory:\t'{where}'"  # noqa: ERA001
            # log_output(message)  # noqa: ERA001
            # log_output(len(message) * "-")  # noqa: ERA001
            return True
        if lip1 and lip2:
            diff = DiffLIP(lip1, lip2, log_output)
            if not diff.is_same():
                message = f"^ '{where}': LIP is different ^"
                return log_output_with_separator(message)
        return True

    if parser_args.compare_hashes and compute_sha256(data1) != compute_sha256(data2):
        log_output(f"'{where}': SHA256 is different")
        return False
    return True


def log_output_with_separator(message):
    log_output(message)
    log_output(visual_length(message) * "-")


def diff_files(file1: os.PathLike | str, file2: os.PathLike | str) -> bool | None:
    c_file1 = CaseAwarePath(file1)
    c_file2 = CaseAwarePath(file2)
    c_file1_rel: CaseAwarePath = relative_path_from_to(c_file2, c_file1)
    c_file2_rel: CaseAwarePath = relative_path_from_to(c_file1, c_file2)
    is_same_result = True

    if not c_file1.exists():
        log_output_with_separator(f"Missing file:\t{c_file1_rel}")
        return False
    if not c_file2.exists():
        log_output_with_separator(f"Missing file:\t{c_file2_rel}")
        return False

    ext = c_file1_rel.suffix.lower()[1:]

    if is_capsule_file(c_file1_rel.name):
        if is_erf_or_mod_file(c_file1_rel.name):
            try:
                file1_capsule = read_erf(file1)
            except ValueError as e:
                log_output_with_separator(f"Could not load '{c_file1_rel}'. Reason: {e}")
                return None
            try:
                file2_capsule = read_erf(file2)
            except ValueError as e:
                log_output_with_separator(f"Could not load '{c_file2_rel}'. Reason: {e}")
                return None
        elif is_rim_file(c_file1_rel.name) and parser_args.ignore_rims is False:
            try:
                file1_capsule = read_rim(file1)
            except ValueError as e:
                log_output_with_separator(f"Could not load '{c_file1_rel}'. Reason: {e}")
                return None
            try:
                file2_capsule = read_rim(file2)
            except ValueError as e:
                log_output_with_separator(f"Could not load '{c_file2_rel}'. Reason: {e}")
                return None
        else:
            return True
        capsule1_resources: dict[str, ERFResource | RIMResource] = {str(res.resref): res for res in file1_capsule}
        capsule2_resources: dict[str, ERFResource | RIMResource] = {str(res.resref): res for res in file2_capsule}

        # Identifying missing resources
        missing_in_capsule1 = capsule2_resources.keys() - capsule1_resources.keys()
        missing_in_capsule2 = capsule1_resources.keys() - capsule2_resources.keys()

        for resref in missing_in_capsule1:
            message = (
                f"Capsule1 resource missing\t{c_file1_rel}\t{resref}\t{capsule2_resources[resref].restype.extension.upper()}"
            )
            log_output_with_separator(message)

        for resref in missing_in_capsule2:
            message = (
                f"Capsule2 resource missing\t{c_file2_rel}\t{resref}\t{capsule1_resources[resref].restype.extension.upper()}"
            )
            log_output_with_separator(message)

        # Checking for differences
        common_resrefs = capsule1_resources.keys() & capsule2_resources.keys()  # Intersection of keys
        for resref in common_resrefs:
            res1: ERFResource | RIMResource = capsule1_resources[resref]
            res2: ERFResource | RIMResource = capsule2_resources[resref]
            ext = res1.restype.extension
            is_same_result = diff_data(res1.data, res2.data, c_file1_rel, c_file2_rel, ext, resref) and is_same_result
        return is_same_result
    return diff_data(c_file1, c_file2, c_file1_rel, c_file2_rel, ext)


def diff_directories(dir1: os.PathLike | str, dir2: os.PathLike | str) -> bool | None:
    c_dir1 = CaseAwarePath(dir1)
    c_dir2 = CaseAwarePath(dir2)

    log_output_with_separator(f"Finding differences in the '{c_dir1.name}' folders...")

    # Store relative paths instead of just filenames
    files_path1 = {f.relative_to(c_dir1).as_posix().lower() for f in c_dir1.rglob("*") if f.is_file()}
    files_path2 = {f.relative_to(c_dir2).as_posix().lower() for f in c_dir2.rglob("*") if f.is_file()}

    # Merge both sets to iterate over unique relative paths
    all_files = files_path1.union(files_path2)

    is_same_result = True
    for rel_path in all_files:
        is_same_result = diff_files(c_dir1 / rel_path, c_dir2 / rel_path) and is_same_result

    return is_same_result


def diff_installs(install_path1: os.PathLike | str, install_path2: os.PathLike | str) -> bool | None:
    install_path1 = CaseAwarePath(install_path1)
    install_path2 = CaseAwarePath(install_path2)
    log_output()
    log_output("Searching first install dir:", install_path1)
    log_output("Searching second install dir:", install_path2)
    log_output((max(len(str(install_path1)) + 29, len(str(install_path2)) + 30)) * "-")
    log_output()

    is_same_result = diff_files(install_path1.joinpath("dialog.tlk"), install_path2 / "dialog.tlk")
    override_path1: CaseAwarePath = install_path1 / "Override"
    override_path2: CaseAwarePath = install_path2 / "Override"
    is_same_result = diff_directories(override_path1, override_path2) and is_same_result

    modules_path1: CaseAwarePath = install_path1 / "Modules"
    modules_path2: CaseAwarePath = install_path2 / "Modules"
    is_same_result = diff_directories(modules_path1, modules_path2) and is_same_result

    lips_path1: CaseAwarePath = install_path1 / "Lips"
    lips_path2: CaseAwarePath = install_path2 / "Lips"
    is_same_result = diff_directories(lips_path1, lips_path2) and is_same_result

    streamwaves_path1: CaseAwarePath = (
        install_path1.joinpath("streamwaves")
        if install_path1.joinpath("streamwaves").exists()
        else install_path1.joinpath("streamvoice")
    )
    streamwaves_path2: CaseAwarePath = (
        install_path2.joinpath("streamwaves")
        if install_path2.joinpath("streamwaves").exists()
        else install_path2.joinpath("streamvoice")
    )
    is_same_result = diff_directories(streamwaves_path1, streamwaves_path2) and is_same_result
    return is_same_result  # noqa: RET504


def is_kotor_install_dir(path: os.PathLike | str) -> bool:
    c_path: CaseAwarePath = CaseAwarePath(path)
    return c_path.is_dir() and c_path.joinpath("chitin.key").exists()


def run_differ_from_args(path1: CaseAwarePath, path2: CaseAwarePath) -> bool | None:
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


parser = argparse.ArgumentParser(description="Finds differences between two KOTOR installations")
parser.add_argument("--path1", type=str, help="Path to the first K1/TSL install, file, or directory to diff.")
parser.add_argument("--path2", type=str, help="Path to the second K1/TSL install, file, or directory to diff.")
parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
parser.add_argument("--compare-hashes", type=bool, help="Compare hashes of any unsupported file/resource")
parser.add_argument("--ignore-rims", type=bool, help="Whether to compare RIMS (default is ignored)")
parser.add_argument("--ignore-tlk", type=bool, help="Whether to compare dialog.TLK (default is not ignored)")
parser.add_argument("--ignore-lips", type=bool, help="Whether to compare dialog.TLK (default is not ignored)")
parser.add_argument(
    "--use-profiler",
    type=bool,
    default=False,
    help="Use cProfile to find where most of the execution time is taking place in source code.",
)

parser_args, unknown = parser.parse_known_args()
while True:
    parser_args.path1 = CaseAwarePath(
        parser_args.path1
        or (unknown[0] if len(unknown) > 0 else None)
        or input("Path to the first K1/TSL install, file, or directory to diff: ")
        or "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II",
    ).resolve()
    if parser_args.path1.exists():
        break
    print("Invalid path:", parser_args.path1)
    parser.print_help()
    parser_args.path1 = None
while True:
    parser_args.path2 = CaseAwarePath(
        parser_args.path2
        or (unknown[1] if len(unknown) > 1 else None)
        or input("Path to the second K1/TSL install, file, or directory to diff: ")
        or "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II - PyKotor",
    ).resolve()
    if parser_args.path2.exists():
        break
    print("Invalid path:", parser_args.path2)
    parser.print_help()
    parser_args.path2 = None
while True:
    OUTPUT_LOG = CaseAwarePath(
        parser_args.output_log
        or (unknown[2] if len(unknown) > 2 else None)
        or input("Filepath of the desired output logfile: ")
        or "log_install_differ.log",
    ).resolve()
    if OUTPUT_LOG.parent.exists():
        break
    print("Invalid path:", OUTPUT_LOG)
    parser.print_help()

parser_args.ignore_rims = bool(parser_args.ignore_rims)
parser_args.ignore_lips = bool(parser_args.ignore_lips)
parser_args.ignore_tlk = bool(parser_args.ignore_tlk)
parser_args.use_profiler = bool(parser_args.use_profiler)
parser_args.compare_hashes = not bool(parser_args.compare_hashes)

log_output()
log_output(f"Using --path1='{parser_args.path1}'")
log_output(f"Using --path2='{parser_args.path2}'")
log_output(f"Using --output-log='{parser_args.output_log}'")
log_output(f"Using --ignore-rims={parser_args.ignore_rims!s}")
log_output(f"Using --ignore-tlk={parser_args.ignore_tlk!s}")
log_output(f"Using --ignore-lips={parser_args.ignore_lips!s}")
log_output(f"Using --compare-hashes={parser_args.compare_hashes!s}")
log_output(f"Using --use-profiler={parser_args.use_profiler!s}")

profiler = None
try:
    if parser_args.use_profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    comparison: bool | None = run_differ_from_args(
        parser_args.path1,
        parser_args.path2,
    )

    if profiler is not None:
        profiler.disable()
        profiler_output_file = Path("profiler_output.pstat").resolve()
        profiler.dump_stats(str(profiler_output_file))
        log_output(f"Profiler output saved to: {profiler_output_file}")
    if comparison is not None:
        log_output(
            f"'{relative_path_from_to(parser_args.path2, parser_args.path1)}'",
            " MATCHES " if comparison else " DOES NOT MATCH ",
            f"'{relative_path_from_to(parser_args.path1, parser_args.path2)}'",
        )
    if comparison is None:
        log_output("Error during comparison")
except KeyboardInterrupt:
    if profiler is not None:
        profiler.disable()
        profiler_output_file = Path("profiler_output.pstat").resolve()
        profiler.dump_stats(str(profiler_output_file))
        log_output(f"Profiler output saved to: {profiler_output_file}")
