from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff
from pykotor.resource.formats.tlk import read_tlk
from pykotor.resource.formats.twoda import read_2da
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.diff.gff import DiffGFF
from pykotor.tslpatcher.diff.tlk import DiffTLK
from pykotor.tslpatcher.diff.twoda import Diff2DA


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
tslpatcher_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor"
pykotor_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor_pykotor"

pykotor_file = CaseAwarePath(pykotor_path) / "dialog.tlk"
tslpatcher_file = CaseAwarePath(tslpatcher_path) / "dialog.tlk"

if not pykotor_file.exists():
    message = "Missing PyKotor dialog.tlk"
    print(message)
    print(len(message) * "-")
if not tslpatcher_file.exists():
    message = "Missing TSLPatcher dialog.tlk"
    print(message)
    print(len(message) * "-")
pykotor_tlk = read_tlk(pykotor_file)
tslpatcher_tlk = read_tlk(tslpatcher_file)
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
    diff = DiffTLK(tslpatcher_tlk, pykotor_tlk).is_same()


def override():
    print("Finding differences in the override folders...")
    tslpatcher_dir = CaseAwarePath(tslpatcher_path).joinpath("override")
    pykotor_dir = CaseAwarePath(pykotor_path).joinpath("override")

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
            pykotor_gff: GFF = read_gff(pykotor_file)
            tslpatcher_gff: GFF = read_gff(tslpatcher_file)
            if not pykotor_gff and tslpatcher_gff:
                message = f"PyKotor {ext.upper()} resource missing in memory:", pykotor_file_rel
                print(message)
                print(visual_length(message) * "-")
            elif pykotor_gff and not tslpatcher_gff:
                message = f"TSLPatcher {ext.upper()} resource missing in memory:", tslpatcher_file_rel
                print(message)
                print(visual_length(message) * "-")
            elif not pykotor_gff and not tslpatcher_gff:
                message = f"Both {ext.upper()} resources missing for both in memory."
                print(message)
                print(len(message) * "-")
            else:
                diff = DiffGFF(tslpatcher_gff, pykotor_gff)
                if not diff.is_same():
                    message = f"^ {pykotor_file.name} is different ^"
                    print(message)
                    print("-" * len(message))

        elif ext == "2da":
            pykotor_2da = read_2da(pykotor_file)
            tslpatcher_2da = read_2da(tslpatcher_file)
            if not pykotor_2da and tslpatcher_2da:
                message = "PyKotor 2DA resource missing in memory:", pykotor_file_rel
                print(message)
                print(visual_length(message) * "-")
            elif pykotor_2da and not tslpatcher_2da:
                message = "TSLPatcher 2DA resource missing in memory:", tslpatcher_file_rel
                print(message)
                print(visual_length(message) * "-")
            elif not pykotor_2da and not tslpatcher_2da:
                message = "Both 2DA resources missing in memory."
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
    tslpatcher_dir = CaseAwarePath(tslpatcher_path).joinpath("modules")
    pykotor_dir = CaseAwarePath(pykotor_path).joinpath("modules")

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
            message = "Missing PyKotor file:", pykotor_file_rel
            print(message)
            print(visual_length(message) * "-")
            continue
        if not tslpatcher_file.exists():
            message = "Missing TSLPatcher file:", tslpatcher_file_rel
            print(message)
            print(visual_length(message) * "-")
            continue

        pykotor_mod = read_erf(pykotor_file)
        tslpatcher_mod = read_erf(tslpatcher_file)

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

                diff = DiffGFF(tslpatcher_gff, pykotor_gff)
                if not diff.is_same():
                    message = f"    in {filename}\t{resref}\t{tsl_res.restype.extension.upper()}"
                    print(message)
                    print("-" * visual_length(message))


print()
override()
modules()
