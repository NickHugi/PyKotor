from __future__ import annotations

import os
import pathlib
import sys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Literal

def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()
utility_path = file_absolute_path.parents[4] / "Libraries" / "Utility" / "src"
if utility_path.exists():
    update_sys_path(utility_path)

from pathlib import Path  # noqa: E402

# Working dir should always be 'toolset' when running this script.
TOOLSET_DIR = Path(file_absolute_path.parents[1], "toolset")
if not TOOLSET_DIR.is_dir():
    while len(TOOLSET_DIR.parts) > 1 and TOOLSET_DIR.name.lower() != "toolset":
        TOOLSET_DIR = TOOLSET_DIR.parent
    if TOOLSET_DIR.name.lower() != "toolset":
        raise RuntimeError("Could not find the toolset folder! Please ensure this script is ran somewhere inside the toolset folder or a subdirectory.")

if __name__ == "__main__":
    os.chdir(TOOLSET_DIR)

UI_SOURCE_DIR = Path("../ui/")
UI_TARGET_DIR = Path("../toolset/uic/")
QRC_SOURCE_PATH = Path("../resources/resources.qrc")
QRC_TARGET_PATH = Path("..")


def get_available_qt_version() -> Literal["PyQt5", "PyQt6", "PySide6", "PySide2"]:
    qt_versions = ["PyQt5", "PyQt6", "PySide6", "PySide2"]
    for qt_version in qt_versions:
        try:
            if qt_version.startswith("PyQt"):
                __import__(qt_version)
            else:
                __import__(qt_version.replace("Side", ""))
        except ImportError:  # noqa: PERF203, S112
            continue
        else:
            return qt_version  # pyright: ignore[reportReturnType]
    raise RuntimeError("No supported Qt binding found. Please install PyQt6, PySide6, PyQt5, or PySide2.")


def compile_ui(
    qt_version: str, *,
    ignore_timestamp: bool = False,
    debug: bool = False,
):
    ui_compiler: str = {"PySide2": "pyside2-uic", "PySide6": "pyside6-uic", "PyQt5": "pyuic5", "PyQt6": "pyuic6"}[qt_version]
    for ui_file in Path(UI_SOURCE_DIR).rglob("*.ui"):
        if ui_file.is_dir():
            print(f"Skipping {ui_file}, not a file.")
            continue
        relpath: Path = ui_file.relative_to(UI_SOURCE_DIR)
        subdir_ui_target: Path = Path(UI_TARGET_DIR, "qtpy", relpath).resolve()
        ui_target: Path = subdir_ui_target.with_suffix(".py")

        if not ui_target.is_file():
            print("mkdir", ui_target.parent)
            ui_target.parent.mkdir(exist_ok=True, parents=True)
            temp_path: Path = ui_target.parent
            new_init_file: Path = temp_path.joinpath("__init__.py")
            while not new_init_file.is_file() and temp_path.resolve() != UI_TARGET_DIR.resolve():
                print(f"touch {new_init_file}")
                new_init_file.touch()
                temp_path: Path = temp_path.parent
                new_init_file: Path = temp_path.joinpath("__init__.py")

        # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
        source_timestamp: float = ui_file.stat().st_mtime
        target_timestamp: float = ui_target.stat().st_mtime if ui_target.exists() else 0.0

        # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
        if source_timestamp > target_timestamp or ignore_timestamp:
            command = f'{ui_compiler} "{ui_file}" -o "{ui_target}"'
            if debug:
                command += " -d"
            print(command)
            os.system(command)  # noqa: S605
            filedata: str = ui_target.read_text(encoding="utf-8")
            new_filedata: str = filedata.replace(f"from {qt_version}", "from qtpy").replace(f"import {qt_version}", "import qtpy")
            if filedata != new_filedata:
                ui_target.write_text(new_filedata, encoding="utf-8")


def compile_qrc(
    qt_version: str,
    *,
    ignore_timestamp: bool = False,
):
    qrc_source: Path = QRC_SOURCE_PATH.resolve()
    qrc_target: Path = Path(QRC_TARGET_PATH, "resources_rc.py").resolve()

    if not qrc_target.parent.is_dir():
        print("mkdir", qrc_target.parent)
        qrc_target.parent.mkdir(exist_ok=True, parents=True)

    # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
    source_timestamp: float = qrc_source.stat().st_mtime
    target_timestamp: float = qrc_target.stat().st_mtime if qrc_target.is_file() else 0.0

    if source_timestamp > target_timestamp or ignore_timestamp:
        rc_compiler: str = {
            "PyQt5": "pyrcc5",
            "PyQt6": "pyside6-rcc",
            "PySide2": "pyside2-rcc",
            "PySide6": "pyside6-rcc",
        }[qt_version]
        command: str = f'{rc_compiler} "{qrc_source}" -o "{qrc_target}"'
        os.system(command)  # noqa: S605
        print(command)
        filedata: str = qrc_target.read_text(encoding="utf-8")
        new_filedata: str = filedata.replace(f"from {qt_version}", "from qtpy").replace(f"import {qt_version}", "import qtpy")
        if filedata != new_filedata:
            qrc_target.write_text(new_filedata)


if __name__ == "__main__":
    qt_version = get_available_qt_version()
    compile_ui(qt_version, ignore_timestamp=False, debug=False)
    compile_qrc(qt_version, ignore_timestamp=False)
    print("All ui compilations completed in", TOOLSET_DIR)
