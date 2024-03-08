from __future__ import annotations

import os
import pathlib
import sys


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()
utility_path = file_absolute_path.parents[4] / "Libraries" / "Utility" / "src"
if utility_path.exists():
    update_sys_path(utility_path)

from utility.system.path import Path  # noqa: E402

# working dir should always be 'toolset' when running this script.
this_script_path = Path(__file__).absolute()
HERE = this_script_path.parent
if this_script_path.parent.name.lower() != "toolset":
    HERE = Path(__file__).parents[1]
    os.chdir(HERE)

UI_SOURCE_DIR = Path("../src/ui/").absolute()
UI_TARGET_DIR = Path("../src/toolset/uic/").absolute()
QRC_SOURCE_PATH = Path("../src/resources/resources.qrc").absolute()
QRC_TARGET_PATH = Path("../src/resources_rc.py").absolute()


def get_ui_files() -> list[Path]:
    return list(Path(UI_SOURCE_DIR).safe_rglob("*.ui"))


def compile_ui(*, ignore_timestamp: bool = False):
    for ui_file in get_ui_files():
        if ui_file.safe_isdir():
            print(f"Skipping {ui_file}, not a file.")
            continue
        relpath = ui_file.relative_to(UI_SOURCE_DIR)
        subdir_ui_target = Path(UI_TARGET_DIR, relpath)
        ui_target: Path = subdir_ui_target.with_suffix(".py")

        if not ui_target.safe_isfile():
            print("mkdir", ui_target.parent)
            ui_target.parent.mkdir(exist_ok=True, parents=True)

        # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
        source_timestamp: float = ui_file.stat().st_mtime
        target_timestamp: float = ui_target.stat().st_mtime if ui_target.safe_exists() else 0.0

        # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
        if source_timestamp > target_timestamp or ignore_timestamp:
            command = f"pyuic5 {ui_file.relative_to(HERE)} -o {ui_target}"
            print(command)
            os.system(command)  # noqa: S605


def compile_qrc(*, ignore_timestamp: bool = False):
    qrc_source: Path = Path(QRC_SOURCE_PATH).resolve()
    qrc_target = Path(QRC_TARGET_PATH).resolve()

    # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
    source_timestamp: float = qrc_source.stat().st_mtime
    target_timestamp: float = qrc_target.stat().st_mtime if qrc_target.safe_isfile() else 0.0

    # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
    if source_timestamp > target_timestamp or ignore_timestamp:
        command = f"pyrcc5 {qrc_source} -o {qrc_target}"
        os.system(command)  # noqa: S605
        print(command)


if __name__ == "__main__":
    compile_ui(ignore_timestamp=False)
    compile_qrc(ignore_timestamp=True)
