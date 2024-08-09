from __future__ import annotations

import argparse
import os
import pathlib
import sys

from copy import deepcopy

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.is_dir():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

from typing import TYPE_CHECKING, cast

from pykotor.resource.formats.gff import GFF, GFFContent, read_gff, write_gff
from pykotor.tools.path import CaseAwarePath
from utility.system.agnostics import askdirectory, askopenfilenames, askretrycancel, showinfo

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFList, GFFStruct

LOGGING_ENABLED = True
PARSER_ARGS: argparse.Namespace | None = None
TEST_MODE = False


ASPECT_RATIO_TO_RESOLUTION = {
    "16:9": [
        (3840, 2160),  # 4K UHD
        (2560, 1440),  # QHD
        (1920, 1080),  # FHD
        (1600, 900),
        (1366, 768),  # Common for laptops
        (1280, 720),  # HD
        (1024, 576),
        (960, 540),  # qHD
        (854, 480),
        (640, 360),
    ],
    "16:10": [
        (2560, 1600),  # WQXGA
        (1920, 1200),  # WUXGA
        (1680, 1050),  # WSXGA+
        (1440, 900),  # WXGA+
        (1280, 800),  # WXGA
        (1152, 720),
        (1024, 640),
        (768, 480),
        (640, 400),
        (512, 320),
    ],
    "4:3": [
        (1600, 1200),  # UXGA
        (1400, 1050),  # SXGA+
        (1280, 960),
        (1152, 864),  # XGA+
        (1024, 768),  # XGA
        (800, 600),  # SVGA
        (640, 480),  # VGA
        (512, 384),
        (400, 300),
        (320, 240),  # QVGA
    ],
    "5:4": [
        (1280, 1024),  # SXGA
        (2560, 2048),  # QSXGA
        (512, 409),
        (1024, 819),
        (2560, 2048),
        (1280, 1024),
        (640, 512),
        (320, 256),
        (256, 205),
        (128, 102),
    ],
    "21:9": [
        (5120, 2160),  # 5K UHD
        (3440, 1440),
        (2560, 1080),
        (1920, 810),
        (1680, 720),
        (1440, 612),
        (1280, 548),
        (1080, 460),
        (960, 408),
        (640, 272),
    ],
    # Adding more aspect ratios and resolutions as per common usage:
    "3:2": [
        (2160, 1440),
        (1920, 1280),
        (1440, 960),
        (1368, 912),
        (1280, 854),
        (1152, 768),
        (1080, 720),
        (1024, 682),
        (960, 640),
        (720, 480),
    ],
    "1:1": [
        (1024, 1024),
        (960, 960),
        (720, 720),
        (640, 640),
        (512, 512),
        (480, 480),
        (320, 320),
        (240, 240),
        (160, 160),
        (128, 128),
    ],
    # Other common ratios (especially for tablets, phones, or other devices) can be added as well.
}


def log(message: str):
    global PARSER_ARGS  # noqa: PLW0602
    assert PARSER_ARGS is not None
    global LOGGING_ENABLED  # noqa: PLW0602
    """Function to log messages both on console and to a file if logging is enabled."""
    print(message)
    if LOGGING_ENABLED:
        cast(CaseAwarePath, PARSER_ARGS.output).mkdir(parents=True, exist_ok=True)
        with PARSER_ARGS.output.joinpath("output.log").open("a", encoding="utf-8") as log_file:
            log_file.write(message + "\n")


def scale_value(value: float, scale_factor: float) -> int:
    return int(value * scale_factor)


def adjust_controls_for_resolution(gui_data: GFF, target_width: int, target_height: int) -> GFF:
    new_gff = GFF(GFFContent.GUI)
    new_gff.root = deepcopy(gui_data.root)

    # Determine the scaling factor from the root extent.
    root_extent_struct = new_gff.root.get_struct("EXTENT")
    width_scale_factor = target_width / (root_extent_struct.get_int32("WIDTH"))
    height_scale_factor = target_height / (root_extent_struct.get_int32("HEIGHT"))
    root_extent_struct.set_int32("WIDTH", target_width)
    root_extent_struct.set_int32("HEIGHT", target_height)

    controls_list: GFFList = new_gff.root.get_list("CONTROLS")
    for control_struct in controls_list:
        if control_struct.exists("SCROLLBAR"):
            scrollbar: GFFStruct = control_struct.get_struct("SCROLLBAR")
            scrollbar_extent: GFFStruct = scrollbar.get_struct("EXTENT")
            resize_extent_by_factor(scrollbar_extent, height_scale_factor, width_scale_factor)

        extent = control_struct.get_struct("EXTENT")
        resize_extent_by_factor(extent, height_scale_factor, width_scale_factor)
    return new_gff


def resize_extent_by_factor(
    extent_struct: GFFStruct,
    height_scale_factor: float,
    width_scale_factor: float,
):
    extent_struct.set_int32("TOP", int(extent_struct.get_int32("TOP") * height_scale_factor))
    extent_struct.set_int32("HEIGHT", int(extent_struct.get_int32("HEIGHT") * height_scale_factor))
    extent_struct.set_int32("LEFT", int(extent_struct.get_int32("LEFT") * width_scale_factor))
    extent_struct.set_int32("WIDTH", int(extent_struct.get_int32("WIDTH") * width_scale_factor))


def process_file(
    gui_file: CaseAwarePath,
    output_dir: CaseAwarePath,
    resolutions: list[tuple[int, int]],
):
    global PARSER_ARGS  # noqa: PLW0602
    assert PARSER_ARGS is not None
    if gui_file.suffix.lower() != ".gui":
        print(f"Invalid GUI file: '{gui_file}'")
        return

    gui_data: GFF | None = read_gff(gui_file)
    log(f"Processing GUI file: '{gui_file}'")

    if PARSER_ARGS.resolution.upper() == "ALL":
        for aspect_ratio in ASPECT_RATIO_TO_RESOLUTION:
            aspect_ratio_dir: CaseAwarePath = output_dir / aspect_ratio.replace(":", "x")

            for width, height in ASPECT_RATIO_TO_RESOLUTION[aspect_ratio]:
                adjusted_gui_data = adjust_controls_for_resolution(gui_data, width, height)
                output_path: CaseAwarePath = aspect_ratio_dir / f"{width}x{height}" / gui_file.name
                output_path.parent.mkdir(exist_ok=True, parents=True)
                log(f"Created directory for aspect ratio {aspect_ratio} at {output_path}")
                write_gff(adjusted_gui_data, output_path)
                log(f"Processed and wrote GUI data for resolution {width}x{height} at {output_path}")
    else:
        for width, height in resolutions:
            adjusted_gui_data = adjust_controls_for_resolution(gui_data, width, height)
            output_path: CaseAwarePath = output_dir / f"{width}x{height}" / gui_file.name
            output_path.parent.mkdir(exist_ok=True, parents=True)
            write_gff(adjusted_gui_data, output_path)
            log(f"Processed and wrote GUI data for resolution {width}x{height} at {output_path}")


def main():
    global LOGGING_ENABLED  # noqa: PLW0602
    global PARSER_ARGS  # noqa: PLW0602, PLW0603
    global TEST_MODE  # noqa: PLW0602

    if TEST_MODE:
        input_dir = CaseAwarePath(os.path.expandvars("%USERPROFILE%\\Documents\\k1 mods\\k1hrm-1.5\\16-by-10\\gui.1280x800"))
        input_files = list(input_dir.rglob("*.gui"))
        PARSER_ARGS = argparse.Namespace(
            input=input_files,
            output=CaseAwarePath(os.path.expandvars("%USERPROFILE%\\Documents\\k1 mods\\k1hrm-1.5\\16-by-9-test")),
            output_log=None,
            logging=True,
            resolution="1280x720",
        )
    else:
        PARSER_ARGS = _parse_user_arg_inputs()

    input_paths: list[CaseAwarePath] = PARSER_ARGS.input
    resolution_arg: str = PARSER_ARGS.resolution
    resolutions_to_process = []

    if resolution_arg.upper() == "ALL":
        for aspect_resolutions in ASPECT_RATIO_TO_RESOLUTION.values():
            resolutions_to_process.extend(aspect_resolutions)
    else:
        try:
            width, height = map(int, resolution_arg.lower().split("x"))
            resolutions_to_process.append((width, height))
        except ValueError:
            print(f"Invalid resolution format: {resolution_arg}. Please use 'WIDTHxHEIGHT' format or 'ALL'.")
            return

    processed_files_count = 0
    for input_path in input_paths:
        if input_path.safe_isfile():
            process_file(input_path, PARSER_ARGS.output, resolutions_to_process)
            processed_files_count += 1

        elif input_path.safe_isdir():
            files_to_process = list(input_path.safe_rglob("*.gui"))
            if not files_to_process:
                print(f"Error: no .gui files to process in input path '{input_path}'", file=sys.stderr)
            for gui_file in files_to_process:
                new_output_dir: CaseAwarePath = PARSER_ARGS.output / gui_file.relative_to(input_path).parent
                new_output_dir.mkdir(parents=True, exist_ok=True)
                process_file(gui_file, new_output_dir, resolutions_to_process)
                processed_files_count += 1

        else:
            print(f"Invalid input: '{input_path}'. It's neither a file nor a directory.")
            return

    if TEST_MODE:
        comparison_dir = CaseAwarePath(os.path.expandvars(r"%USERPROFILE%\Documents\k1 mods\k1hrm-1.5\16-by-9\gui.1280x720"))
        assert compare_directories(PARSER_ARGS.output / "1280x720", comparison_dir), "Test directories do not match."

    # Display a summary info dialog after processing is complete
    summary_message = f"GUI conversions complete!\nTotal files processed: {processed_files_count}"
    showinfo("Processing Complete", summary_message)



def compare_directories(dir1: CaseAwarePath, dir2: CaseAwarePath) -> bool:
    dir1_files = {str(f.relative_to(dir1)).replace("\\", "/"): f for f in dir1.rglob("*.gui")}
    dir2_files = {str(f.relative_to(dir2)).replace("\\", "/"): f for f in dir2.rglob("*.gui")}

    all_relative_paths = set(dir1_files.keys()).union(set(dir2_files.keys()))

    all_files_match = True

    for relative_path in all_relative_paths:
        file_in_dir1 = relative_path in dir1_files
        file_in_dir2 = relative_path in dir2_files

        if not file_in_dir1:
            print(f"File {relative_path} found in {dir2} but not in {dir1}.")
            all_files_match = False
            continue

        if not file_in_dir2:
            print(f"File {relative_path} found in {dir1} but not in {dir2}.")
            all_files_match = False
            continue

        gff1 = read_gff(dir1_files[relative_path])
        gff2 = read_gff(dir2_files[relative_path])

        if not gff1.compare(gff2):
            print(f"Files differ: {dir1_files[relative_path]} and {dir2_files[relative_path]}")
            all_files_match = False

    return all_files_match




def _parse_user_arg_inputs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finds differences between two KOTOR installations")
    parser.add_argument("--input", type=str, help="Path to the K1/TSL GUI file.")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
    parser.add_argument("--logging", type=bool, help="Whether to log the results to a file or not (default is enabled)")
    parser.add_argument("--resolution", type=str, help="Specific resolution (e.g., 1920x1080) or 'ALL' for all resolutions")

    result, unknown = parser.parse_known_args()
    while True:
        result.input = result.input or (unknown if len(unknown) > 0 else None) or askopenfilenames(title="Select K1/TSL GUI file(s) to convert")
        if not result.input or not any(result.input):
            if not askretrycancel("error: You cancelled the browse file dialog.", "You must choose at least one .gui file!"):
                sys.exit()
            result.input = None
            continue
        result.input = [CaseAwarePath(path).resolve() for path in result.input]
        if all(path.exists() for path in result.input):
            break
        print("Invalid path(s):", result.input)
        parser.print_help()
        result.input = None
    while True:
        result.output = result.output or (unknown[0] if len(unknown) > 0 else None) or askdirectory(title="Select the output directory:")
        if not result.output or not result.output.strip():
            if not askretrycancel("error: You cancelled the browse folder dialog.", "You must choose a path to save your input .ui file(s)!"):
                sys.exit()
            result.output = None
            continue
        result.output = CaseAwarePath(result.output).resolve()
        if result.output.parent.exists():
            result.output.mkdir(exist_ok=True, parents=True)
            break
        print("Invalid path:", result.output)
        parser.print_help()
        result.output = None
    while True:
        result.resolution = result.resolution or input("Resolution (e.g., 1920x1080) or 'ALL': ")
        if result.resolution.upper() == "ALL":
            break
        try:
            width, height = map(int, result.resolution.split("x"))
            if width > 0 and height > 0:
                break
        except ValueError:
            ...
        print("Invalid resolution:", result.resolution)
        parser.print_help()
        result.resolution = None
    return result


if __name__ == "__main__":
    main()
