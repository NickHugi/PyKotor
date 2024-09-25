from __future__ import annotations

import os
import sys

from pathlib import Path

# Change the current working directory to the directory of this script
HERE = Path(__file__).parent.parent.absolute()
if __name__ == "__main__":
    print("chdir", HERE)
    os.chdir(HERE)

UI_SOURCE_DIR = HERE / "ui"
UI_TARGET_DIR = HERE / "uic"
print(UI_SOURCE_DIR)
print(UI_TARGET_DIR)
QRC_SOURCE_PATH = Path("./resources/resources.qrc")
QRC_TARGET_PATH = Path("./rcc")


def compile_ui(qt_version: str, *, ignore_timestamp: bool = False):
    ui_compiler = {
        "pyside2": "pyside2-uic",
        "pyside6": "pyside6-uic",
        "pyqt5": "pyuic5",
        "pyqt6": "pyuic6"
    }[qt_version]
    for ui_file in UI_SOURCE_DIR.rglob("*.ui"):
        if ui_file.is_dir():
            print(f"Skipping {ui_file}, not a file.")
            continue
        relpath = ui_file.relative_to(UI_SOURCE_DIR)
        subdir_ui_target = Path(UI_TARGET_DIR, qt_version, relpath).relative_to(Path.cwd())
        ui_target: Path = subdir_ui_target.with_suffix(".py")

        if not ui_target.is_file():
            print("mkdir", ui_target.parent)
            ui_target.parent.mkdir(exist_ok=True, parents=True)
            temp_path = ui_target.parent
            new_init_file = temp_path.joinpath("__init__.py")
            while not new_init_file.is_file() and temp_path.resolve() != UI_TARGET_DIR.resolve():
                print(f"touch {new_init_file}")
                new_init_file.touch()
                temp_path = temp_path.parent
                new_init_file = temp_path.joinpath("__init__.py")

        # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
        source_timestamp: float = ui_file.stat().st_mtime
        target_timestamp: float = ui_target.stat().st_mtime if ui_target.exists() else 0.0

        # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
        if source_timestamp > target_timestamp or ignore_timestamp:
            command = f"{ui_compiler} {ui_file.relative_to(Path.cwd())} -o {ui_target}"
            print(command)
            os.system(command)  # noqa: S605


def compile_qrc(qt_version: str, *, ignore_timestamp: bool = False):
    qrc_source: Path = QRC_SOURCE_PATH.resolve()
    qrc_target = Path(QRC_TARGET_PATH, f"resources_rc_{qt_version}.py").resolve()

    if not qrc_target.parent.is_dir():
        print("mkdir", qrc_target.parent)
        qrc_target.parent.mkdir(exist_ok=True, parents=True)

    # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
    source_timestamp: float = qrc_source.stat().st_mtime
    target_timestamp: float = qrc_target.stat().st_mtime if qrc_target.is_file() else 0.0

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
        try:
            compile_ui(qt_version, ignore_timestamp=True)
        except Exception as e:  # noqa: BLE001, PERF203
            print("compile_ui", f"{qt_version}", e)

    for qt_version in qt_versions_to_run:
        try:
            compile_qrc(qt_version, ignore_timestamp=False)
        except Exception as e:  # noqa: BLE001, PERF203
            print("compile_qrc", f"{qt_version}", e)
    print("All ui compilations completed")
