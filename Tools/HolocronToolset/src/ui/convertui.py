from __future__ import annotations

import os
import pathlib
import re
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

# Working dir should always be 'toolset' when running this script.
TOOLSET_DIR = Path(file_absolute_path.parents[1], "toolset")
if not TOOLSET_DIR.safe_isdir():
    while len(TOOLSET_DIR.parts) > 1 and TOOLSET_DIR.name.lower() != "toolset":
        TOOLSET_DIR = TOOLSET_DIR.parent
    if TOOLSET_DIR.name.lower() != "toolset":
        raise RuntimeError("Could not find the toolset folder! Please ensure this script is ran somewhere inside the toolset folder or a subdirectory.")

os.chdir(TOOLSET_DIR)

UI_SOURCE_DIR = Path("../ui/")
UI_TARGET_DIR = Path("../toolset/uic/")
QRC_SOURCE_PATH = Path("../resources/resources.qrc")
QRC_TARGET_PATH = Path("../toolset/rcc")


def compile_ui(qt_version: str, *, ignore_timestamp: bool = False):
    ui_compiler = {
        "pyside2": "pyside2-uic",
        "pyside6": "pyside6-uic",
        "pyqt5": "pyuic5",
        "pyqt6": "pyuic6"
    }[qt_version]
    for ui_file in Path(UI_SOURCE_DIR).safe_rglob("*.ui"):
        if ui_file.safe_isdir():
            print(f"Skipping {ui_file}, not a file.")
            continue
        relpath = ui_file.relative_to(UI_SOURCE_DIR)
        subdir_ui_target = Path(UI_TARGET_DIR, qt_version, relpath).safe_relative_to(TOOLSET_DIR)
        ui_target: Path = subdir_ui_target.with_suffix(".py")

        if not ui_target.safe_isfile():
            print("mkdir", ui_target.parent)
            ui_target.parent.mkdir(exist_ok=True, parents=True)
            temp_path = ui_target.parent
            new_init_file = temp_path.joinpath("__init__.py")
            while not new_init_file.safe_isfile() and temp_path.resolve() != UI_TARGET_DIR.resolve():
                print(f"touch {new_init_file}")
                new_init_file.touch()
                temp_path = temp_path.parent
                new_init_file = temp_path.joinpath("__init__.py")

        # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
        source_timestamp: float = ui_file.stat().st_mtime
        target_timestamp: float = ui_target.stat().st_mtime if ui_target.safe_exists() else 0.0

        # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
        if source_timestamp > target_timestamp or ignore_timestamp:
            command = f"{ui_compiler} {ui_file.safe_relative_to(TOOLSET_DIR)} -o {ui_target}"
            print(command)
            os.system(command)  # noqa: S605
            # Post-processing: Fix importing resources_rc
            with ui_target.open("r", encoding="utf-8") as file:
                filedata = file.read()
            new_filedata = re.sub(r"^import resources_rc.*\n?", f"from toolset.rcc import resources_rc_{qt_version}", filedata, flags=re.MULTILINE)
            new_filedata = re.sub(r"^from resources_rc.*\n?", f"from toolset.rcc.resources_rc_{qt_version}", new_filedata, flags=re.MULTILINE)
            if (
                new_filedata == filedata
                and re.search(f"from toolset.rcc import resources_rc_{qt_version}", new_filedata) is None
            ):
                new_filedata += f"\nfrom toolset.rcc import resources_rc_{qt_version}\n"
            with ui_target.open("w", encoding="utf-8") as file:
                file.write(new_filedata)


def compile_qrc(qt_version: str, *, ignore_timestamp: bool = False):
    qrc_source: Path = QRC_SOURCE_PATH.resolve()
    qrc_target = Path(QRC_TARGET_PATH, f"resources_rc_{qt_version}.py").resolve()

    if not qrc_target.parent.safe_isdir():
        print("mkdir", qrc_target.parent)
        qrc_target.parent.mkdir(exist_ok=True, parents=True)

    # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
    source_timestamp: float = qrc_source.stat().st_mtime
    target_timestamp: float = qrc_target.stat().st_mtime if qrc_target.safe_isfile() else 0.0

    if source_timestamp > target_timestamp or ignore_timestamp:
        rc_compiler = {
            "pyqt5": "pyrcc5",
            "pyqt6": "pyside6-rcc",
            "pyside2": "pyside2-rcc",
            "pyside6": "pyside6-rcc",
        }[qt_version]
        command = f"{rc_compiler} {qrc_source} -o {qrc_target}"
        os.system(command)  # noqa: S605
        print(command)


if __name__ == "__main__":
    qt_versions = ["pyqt5", "pyqt6", "pyside6", "pyside2"]
    qt_versions_to_run: list[str] | None = None
    if len(sys.argv) > 1:
        qt_version = sys.argv[1]
        if qt_version in qt_versions:
            qt_versions_to_run = [qt_version]
        else:
            print(f"Invalid Qt version specified. Please choose from [{qt_versions}].")
            sys.exit(1)
    else:
        qt_versions_to_run = qt_versions

    for qt_version in qt_versions_to_run:
        compile_ui(qt_version, ignore_timestamp=False)
        compile_qrc(qt_version, ignore_timestamp=False)
    print("All ui compilations completed")
