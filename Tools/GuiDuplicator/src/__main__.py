from __future__ import annotations

import argparse
import pathlib
import sys
from copy import deepcopy
from fractions import Fraction

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)

from pykotor.resource.formats.gff import GFF, GFFContent, read_gff, write_gff
from pykotor.tools.path import CaseAwarePath

parser = argparse.ArgumentParser(description="Finds differences between two KOTOR installations")
parser.add_argument("--input", type=str, help="Path to the K1/TSL GUI file.")
parser.add_argument("--output", type=str, help="Output directory")
parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
parser.add_argument("--logging", type=bool, help="Whether to log the results to a file or not (default is enabled)")

parser_args, unknown = parser.parse_known_args()
LOGGING_ENABLED = parser_args.logging
if LOGGING_ENABLED is None:
    LOGGING_ENABLED = True
while True:
    parser_args.input = CaseAwarePath(
        parser_args.input or (unknown[0] if len(unknown) > 0 else None) or input("Path to the K1/TSL GUI file: "),
    ).resolve()
    if parser_args.input.exists():
        break
    print("Invalid path:", parser_args.input)
    parser.print_help()
    parser_args.input = None
while True:
    parser_args.output = CaseAwarePath(
        parser_args.output or (unknown[0] if len(unknown) > 0 else None) or input("Output directory: "),
    ).resolve()
    if parser_args.output.parent.exists():
        parser_args.output.mkdir(exist_ok=True, parents=True)
        break
    print("Invalid path:", parser_args.output)
    parser.print_help()
    parser_args.output = None


def log(message: str):
    """Function to log messages both on console and to a file if logging is enabled."""
    print(message)
    if LOGGING_ENABLED:
        with parser_args.output.joinpath("output.log").open("a") as log_file:
            log_file.write(message + "\n")


def scale_value(value, scale_factor):
    return int(value * scale_factor)


def adjust_controls_for_resolution(gui_data: GFF, target_width, target_height):
    new_gff = GFF(GFFContent.GUI)
    new_gff.root._fields = deepcopy(gui_data.root._fields)

    width_scale_factor = target_width / (new_gff.root._fields["EXTENT"]._value.get_int32("WIDTH"))
    height_scale_factor = target_height / (new_gff.root._fields["EXTENT"]._value.get_int32("HEIGHT"))

    new_gff.root._fields["EXTENT"]._value.set_int32("WIDTH", target_width)
    new_gff.root._fields["EXTENT"]._value.set_int32("HEIGHT", target_height)

    for i, control_struct in enumerate(gui_data.root._fields["CONTROLS"]._value):
        if new_gff.root._fields["CONTROLS"]._value._structs[i]._fields.get("SCROLLBAR"):
            new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["SCROLLBAR"]._value._fields[
                "EXTENT"]._value.set_int32(
                "TOP",
                scale_value(control_struct._fields["SCROLLBAR"]._value._fields["EXTENT"]._value["TOP"],
                            height_scale_factor),
            )
            new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["SCROLLBAR"]._value._fields[
                "EXTENT"]._value.set_int32(
                "LEFT",
                scale_value(control_struct._fields["SCROLLBAR"]._value._fields["EXTENT"]._value["LEFT"],
                            width_scale_factor),
            )
            new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["SCROLLBAR"]._value._fields[
                "EXTENT"]._value.set_int32(
                "HEIGHT",
                scale_value(control_struct._fields["SCROLLBAR"]._value._fields["EXTENT"]._value["HEIGHT"],
                            height_scale_factor),
            )
            new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["SCROLLBAR"]._value._fields[
                "EXTENT"]._value.set_int32(
                "WIDTH",
                scale_value(control_struct._fields["SCROLLBAR"]._value._fields["EXTENT"]._value["WIDTH"],
                            width_scale_factor),
            )
        new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["EXTENT"]._value.set_int32(
            "TOP", scale_value(control_struct._fields["EXTENT"]._value["TOP"], height_scale_factor),
        )
        new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["EXTENT"]._value.set_int32(
            "LEFT", scale_value(control_struct._fields["EXTENT"]._value["LEFT"], width_scale_factor),
        )
        new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["EXTENT"]._value.set_int32(
            "HEIGHT", scale_value(control_struct._fields["EXTENT"]._value["HEIGHT"], height_scale_factor),
        )
        new_gff.root._fields["CONTROLS"]._value._structs[i]._fields["EXTENT"]._value.set_int32(
            "WIDTH", scale_value(control_struct._fields["EXTENT"]._value["WIDTH"], width_scale_factor),
        )

    return new_gff


# Define a normalization function
def normalize_aspect_ratio(width, height):
    aspect_ratio = Fraction(width, height).limit_denominator(1000)  # Ensure it does not reduce too much

    # Normalization rules for known non-standard aspect ratios
    normalization = {
        Fraction(1366, 768): Fraction(16, 9),
        Fraction(1536, 864): Fraction(16, 9),
        Fraction(1440, 900): Fraction(16, 10),
        Fraction(8, 5): Fraction(16, 10),
    }

    return normalization.get(aspect_ratio, aspect_ratio)


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


def process_file(gui_file: CaseAwarePath, output_dir: CaseAwarePath):
    if gui_file.suffix.lower() != ".gui":
        print(f"Invalid GUI file: {gui_file!s}")
        return

    gui_data: GFF | None = read_gff(gui_file)
    if not gui_data:
        print(f"Could not read GUI file: {gui_file!s}")
        return

    log(f"Processing GUI file: {gui_file!s}")

    # Processing and saving the resolutions based on the ASPECT_RATIO_TO_RESOLUTION dictionary
    for aspect_ratio in ASPECT_RATIO_TO_RESOLUTION:
        aspect_ratio_dir: CaseAwarePath = output_dir / aspect_ratio.replace(":", "x")
        aspect_ratio_dir.mkdir(exist_ok=True, parents=True)
        log(f"Created directory for aspect ratio {aspect_ratio} at {aspect_ratio_dir!s}")

        for width, height in ASPECT_RATIO_TO_RESOLUTION[aspect_ratio]:
            adjusted_gui_data = adjust_controls_for_resolution(gui_data, width, height)
            output_filename = f"{width}x{height}.gui"
            output_path: CaseAwarePath = aspect_ratio_dir / output_filename
            output_path.touch(exist_ok=True)
            write_gff(adjusted_gui_data, output_path)
            log(f"Processed and wrote GUI data for resolution {width}x{height} at {output_path!s}")


def main():
    input_path: CaseAwarePath = parser_args.input

    if input_path.is_file():
        process_file(input_path, parser_args.output)

    elif input_path.is_dir():
        for gui_file in input_path.rglob("*.gui"):
            relative_path = gui_file.relative_to(input_path)
            new_output_dir = parser_args.output / relative_path.parent / gui_file.stem
            new_output_dir.mkdir(parents=True, exist_ok=True)
            process_file(gui_file, new_output_dir)

    else:
        print(f"Invalid input: {input_path!s}. It's neither a file nor a directory.")
        return


if __name__ == "__main__":
    main()
