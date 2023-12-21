import argparse  # noqa: INP001
import pathlib
import sys
import traceback

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)

from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from utility.path import Path

parser = argparse.ArgumentParser(description="Extracts MDL/MDX in ASCII format, whatever that means")
parser.add_argument("--input", type=str, help="Path to the MDL/MDX file/folder of MDL files")
parser.add_argument("--output", type=str, help="Output directory")
parser.add_argument("--compile", action="store_true", help="Should compile or decompile")
parser_args, unknown = parser.parse_known_args()
parser.print_help()
while True:
    parser_args.input = Path(
        parser_args.input
        or (unknown[0] if len(unknown) > 0 else None)
        or input("Path to the MDL/MDX file/folder of MDL files: "),
    ).resolve()
    if parser_args.input.exists():
        break
    print("Invalid path:", parser_args.input)
    parser.print_help()
    parser_args.input = None
while True:
    parser_args.output = Path(
        parser_args.output or (unknown[1] if len(unknown) > 1 else None) or input("Output directory: "),
    ).resolve()
    if parser_args.output.parent.exists():
        parser_args.output.mkdir(exist_ok=True, parents=True)
        break
    print("Invalid path:", parser_args.output)
    parser.print_help()
    parser_args.output = None
while True:
    parser_args.compile = str(
        parser_args.compile
        or (unknown[2] if len(unknown) > 2 else None)
        or input("Would you like to compile or decompile? (enter 'c', 'compile' 'd', or 'decompile'): "),
    )
    if parser_args.compile.lower().strip() in {"compile", "c"}:
        parser_args.compile = True
        break
    elif parser_args.compile.lower().strip() in ("decompile", "d"):
        parser_args.compile = False
        break
    else:
        print("Invalid input: enter 'compile' or 'decompile'")
        parser_args.compile = None


def process_file(mdl_file: Path, output_path: Path, should_compile: bool):
    model = read_mdl(mdl_file)
    if should_compile:
        write_mdl(
            model,  # type: ignore[None]
            output_path / f"{mdl_file.stem}.mdl",
            ResourceType.MDL,
        )
        print("Compiled some ascii model thing to: ", output_path / f"{mdl_file.stem}.mdl")
    else:
        write_mdl(
            model,  # type: ignore[None]
            output_path / f"{mdl_file.stem}.ascii_output",
            ResourceType.MDL_ASCII,
        )
        print("Extracted some ascii model thing to: ", output_path / f"{mdl_file.stem}.ascii_output")


def main():
    try:
        input_path: Path = parser_args.input

        if input_path.is_file():
            process_file(input_path, parser_args.output, parser_args.compile)

        elif input_path.is_dir():
            for gui_file in input_path.rglob("*.gui", case_sensitive=False):
                try:
                    relative_path = gui_file.relative_to(input_path)
                    new_output_dir = parser_args.output / relative_path.parent / gui_file.stem
                    new_output_dir.mkdir(parents=True, exist_ok=True)
                    process_file(gui_file, new_output_dir, parser_args.compile)
                except KeyboardInterrupt:  # noqa: PERF203
                    raise
                except Exception:
                    traceback.print_exc()

        else:
            print(f"Invalid input: {input_path}. It's neither a file nor a directory.")
            return
        print("Completed extractions")
    except KeyboardInterrupt:
        print("Goodbye")
    except Exception:
        traceback.print_exc()


main()
