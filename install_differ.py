from __future__ import annotations

import argparse

from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff
from pykotor.resource.formats.tlk import read_tlk
from pykotor.resource.formats.twoda import read_2da
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.diff.gff import DiffGFF
from pykotor.tslpatcher.diff.tlk import DiffTLK
from pykotor.tslpatcher.diff.twoda import Diff2DA

parser = argparse.ArgumentParser(description="Finds differences between two KOTOR installations")

parser.add_argument("--install1", type=str, help="Path to the first K1/TSL install")
parser.add_argument("--install2", type=str, help="Path to the second K1/TSL install")
args, unknown = parser.parse_known_args()

if len(unknown) > 1 and not args.install1:
    args.install1 = unknown[0]
if len(unknown) > 2 and not args.install2:
    args.install2 = unknown[1]
if not args.install1 and not args.install2:
    parser.print_help()
    print("Using defaults")
    #sys.exit()  # noqa: ERA001

tslpatcher_path = args.install1 or "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II"
pykotor_path = args.install2 or "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II - PyKotor"

def relative_path_from_to(src, dst):
    src_parts = list(src.parts)
    dst_parts = list(dst.parts)

    common_length = next(
        (i for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts)) if src_part != dst_part),
        len(src_parts),
    )
    # ".." for each diverging part of src, and then the remaining parts of dst
    rel_parts = [".."] * (len(src_parts) - common_length) + dst_parts[common_length:]
    return CaseAwarePath(*rel_parts)


def visual_length(s: str, tab_length=8):
    # Split the string at tabs, sum the lengths of the substrings,
    # and add the necessary spaces to account for the tab stops.
    parts = s.split("\t")
    vis_length = sum(len(part) for part in parts)
    for part in parts[:-1]:  # all parts except the last one
        vis_length += tab_length - (len(part) % tab_length)
    return vis_length


gff_types = [x.value.lower().strip() for x in GFFContent]

pykotor_dialogtlk_file = CaseAwarePath(pykotor_path, "dialog.tlk")
tslpatcher_dialogtlk_file = CaseAwarePath(tslpatcher_path, "dialog.tlk")
pykotor_dialogtlk_exists = pykotor_dialogtlk_file.exists()
tslpatcher_dialogtlk_exists = tslpatcher_dialogtlk_file.exists()
if not pykotor_dialogtlk_exists:
    message = "Missing PyKotor dialog.tlk"
    print(message)
    print(len(message) * "-")
if not tslpatcher_dialogtlk_exists:
    message = "Missing TSLPatcher dialog.tlk"
    print(message)
    print(len(message) * "-")
if pykotor_dialogtlk_exists and tslpatcher_dialogtlk_exists:
    print(f"Loading TLK '{pykotor_dialogtlk_file}'")
    pykotor_tlk = read_tlk(pykotor_dialogtlk_file)
    print(f"Loading TLK '{tslpatcher_dialogtlk_file}'")
    tslpatcher_tlk = read_tlk(tslpatcher_dialogtlk_file)
    if not pykotor_tlk and tslpatcher_tlk:
        message = "PyKotor TLK resource missing in memory"
        print(message)
        print(len(message) * "-")
    elif pykotor_tlk and not tslpatcher_tlk:
        message = "TSLPatcher TLK resource missing in memory"
        print(message)
        print(len(message) * "-")
    elif not pykotor_tlk and not tslpatcher_tlk:
        message = "Both TLK resources missing in memory."
        print(message)
        print(len(message) * "-")
    else:
        print("Diffing dialog.tlk files...")
        same = DiffTLK(tslpatcher_tlk, pykotor_tlk).is_same()
        print("dialog.tlk files match") if same else print("^ in dialog.tlk")
        print("--------------------")


def override():
    print("Finding differences in the override folders...")
    tslpatcher_dir = CaseAwarePath(tslpatcher_path).joinpath("override")
    pykotor_dir = CaseAwarePath(pykotor_path).joinpath("override")

    print("Searching first install dir:", tslpatcher_dir)
    print("Searching second install dir:", pykotor_dir)
    print((max(len(str(tslpatcher_dir))+29, len(str(pykotor_dir))+30)) * "-")

    # Create sets of filenames for both directories
    tslpatcher_files = {f.name.lower() for f in tslpatcher_dir.iterdir()}
    pykotor_files = {f.name.lower() for f in pykotor_dir.iterdir()}

    # Merge both sets to iterate over unique filenames
    all_files = tslpatcher_files.union(pykotor_files)

    for filename in all_files:
        tslpatcher_file = tslpatcher_dir / filename
        pykotor_file = pykotor_dir / filename

        tslpatcher_file_rel = relative_path_from_to(pykotor_file, tslpatcher_file)
        pykotor_file_rel = relative_path_from_to(tslpatcher_file, pykotor_file)

        if not pykotor_file.exists():
            message = f"Missing file:\t{pykotor_file_rel}"
            print(message)
            print(visual_length(message) * "-")
            continue
        if not tslpatcher_file.exists():
            message = f"Missing file:\t{tslpatcher_file_rel}"
            print(message)
            print(visual_length(message) * "-")
            continue

        ext = tslpatcher_file.suffix.lower()[1:]

        if ext in gff_types:
            pykotor_gff: GFF | None = read_gff(pykotor_file)
            tslpatcher_gff: GFF | None = read_gff(tslpatcher_file)
            if not pykotor_gff and tslpatcher_gff:
                message = f"PyKotor {ext.upper()} resource missing in memory:\t{pykotor_file_rel}"
                print(message)
                print(visual_length(message) * "-")
            elif pykotor_gff and not tslpatcher_gff:
                message = f"TSLPatcher {ext.upper()} resource missing in memory:\t{tslpatcher_file_rel}"
                print(message)
                print(visual_length(message) * "-")
            elif not pykotor_gff and not tslpatcher_gff:
                message = f"Both {ext.upper()} resources missing for both in memory:\t{pykotor_file_rel}"
                print(message)
                print(len(message) * "-")
            elif pykotor_gff and tslpatcher_gff:
                diff = DiffGFF(tslpatcher_gff, pykotor_gff)
                if not diff.is_same():
                    message = f"^ {pykotor_file.name} is different ^"
                    print(message)
                    print("-" * len(message))

        elif ext == "2da":
            pykotor_2da = read_2da(pykotor_file)
            tslpatcher_2da = read_2da(tslpatcher_file)
            if not pykotor_2da and tslpatcher_2da:
                message = f"PyKotor 2DA resource missing in memory:\t{pykotor_file_rel}"
                print(message)
                print(visual_length(message) * "-")
            elif pykotor_2da and not tslpatcher_2da:
                message = f"TSLPatcher 2DA resource missing in memory:\t{tslpatcher_file_rel}"
                print(message)
                print(visual_length(message) * "-")
            elif not pykotor_2da and not tslpatcher_2da:
                message = f"Both 2DA resources missing in memory:\t{pykotor_file_rel}"
                print(message)
                print(len(message) * "-")
            else:
                diff = Diff2DA(tslpatcher_2da, pykotor_2da)
                if not diff.is_same():
                    message = f"^ {pykotor_file.name}: 2DA is different ^"
                    print(message)
                    print("-" * len(message))


def modules():
    print("Finding differences in the modules folders...")
    tslpatcher_dir = CaseAwarePath(tslpatcher_path, "modules")
    pykotor_dir = CaseAwarePath(pykotor_path, "modules")

    print("Searching first install dir:", tslpatcher_dir)
    print("Searching second install dir:", pykotor_dir)
    print((max(len(str(tslpatcher_dir)), len(str(pykotor_dir))) + 29) * "-")

    # Create sets of filenames for both directories
    tslpatcher_files = {f.name.lower() for f in tslpatcher_dir.iterdir()}
    pykotor_files = {f.name.lower() for f in pykotor_dir.iterdir()}

    # Merge both sets to iterate over unique filenames
    all_files = tslpatcher_files.union(pykotor_files)

    for filename in all_files:
        tslpatcher_file = tslpatcher_dir / filename
        pykotor_file = pykotor_dir / filename

        tslpatcher_file_rel = relative_path_from_to(pykotor_file, tslpatcher_file)
        pykotor_file_rel = relative_path_from_to(tslpatcher_file, pykotor_file)

        if tslpatcher_file.suffix.lower() == ".rim":
            continue

        if not pykotor_file.exists():
            message = f"Missing PyKotor file:\t{pykotor_file_rel}"
            print(message)
            print(visual_length(message) * "-")
            continue
        if not tslpatcher_file.exists():
            message = f"Missing TSLPatcher file:\t{tslpatcher_file_rel}"
            print(message)
            print(visual_length(message) * "-")
            continue

        try:
            pykotor_mod = read_erf(pykotor_file)
        except ValueError as e:
            message = f"Could not load {pykotor_file_rel}. Reason: {e}"
            print(message)
            print(visual_length(message) * "-")
            continue
        try:
            tslpatcher_mod = read_erf(tslpatcher_file)
        except ValueError as e:
            message = f"Could not load {tslpatcher_file_rel}. Reason: {e}"
            print(message)
            print(visual_length(message) * "-")
            continue

        tslpatcher_resources = {str(res.resref): res for res in tslpatcher_mod}
        pykotor_resources = {str(res.resref): res for res in pykotor_mod}

        # Identifying missing resources
        missing_in_pykotor = tslpatcher_resources.keys() - pykotor_resources.keys()
        missing_in_tslpatcher = pykotor_resources.keys() - tslpatcher_resources.keys()

        for resref in missing_in_pykotor:
            message = f"PyKotor resource missing\t{pykotor_file_rel}\t{resref}\t{tslpatcher_resources[resref].restype.extension.upper()}"
            print(message)
            print(visual_length(message) * "-")

        for resref in missing_in_tslpatcher:
            message = f"TSLPatcher resource missing\t{tslpatcher_file_rel}\t{resref}\t{pykotor_resources[resref].restype.extension.upper()}"
            print(message)
            print(visual_length(message) * "-")

        # Checking for differences
        common_resrefs = tslpatcher_resources.keys() & pykotor_resources.keys()  # Intersection of keys
        for resref in common_resrefs:
            tsl_res = tslpatcher_resources[resref]
            pyk_res = pykotor_resources[resref]

            if tsl_res.restype.extension in gff_types:
                pykotor_gff = read_gff(pyk_res.data)
                tslpatcher_gff = read_gff(tsl_res.data)
                if not pykotor_gff and tslpatcher_gff:
                    message = f"PyKotor {tsl_res.restype.extension.upper()} resource missing in memory:\t{pykotor_file_rel}"
                    print(message)
                    print(visual_length(message) * "-")
                    continue

                if pykotor_gff and not tslpatcher_gff:
                    message = f"TSLPatcher {tsl_res.restype.extension.upper()} resource missing in memory:\t{tslpatcher_file_rel}"
                    print(message)
                    print(visual_length(message) * "-")
                    continue

                if not pykotor_gff and not tslpatcher_gff:
                    message = (
                        f"Both {tsl_res.restype.extension.upper()} resources missing for both in memory:\t{pykotor_file_rel}"
                    )
                    print(message)
                    print(len(message) * "-")
                    continue

                if pykotor_gff and tslpatcher_gff:
                    diff = DiffGFF(tslpatcher_gff, pykotor_gff)
                    if not diff.is_same():
                        message = f"\tin {filename}\t{resref}\t{tsl_res.restype.extension.upper()}"
                        print(message)
                        print("-" * visual_length(message))


print()
override()
modules()
