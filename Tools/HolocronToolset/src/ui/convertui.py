from __future__ import annotations

import os

from pykotor.tools.path import CaseAwarePath
from utility.path import Path

# working dir should always be 'toolset' when running this script.
this_script_path = Path(__file__)
if this_script_path.parent.name.lower() != "toolset":
    os.chdir(Path(__file__).parents[1])


UI_TARGET_DIR = "../toolset/uic/"
QRC_TARGET_DIR = "../toolset/"


def get_ui_files() -> list[CaseAwarePath]:
    return list(CaseAwarePath(".").safe_rglob("*.ui"))


def compile_ui(ignore_timestamp: bool = False):
    for ui_source in get_ui_files():
        directory: str = ui_source.parent.name
        filename: str = ui_source.with_suffix(ui_source.suffix.lower().replace(".ui", ".py")).name
        subdir_ui_target = Path(UI_TARGET_DIR, directory)
        ui_target: Path = subdir_ui_target / filename

        if not subdir_ui_target.safe_exists():
            subdir_ui_target.mkdir(exist_ok=True, parents=True)
            print("mkdir", subdir_ui_target)

        # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
        source_timestamp: float = ui_source.stat().st_mtime
        target_timestamp: float = ui_target.stat().st_mtime if ui_target.safe_exists() else 0.0

        # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
        if source_timestamp > target_timestamp or ignore_timestamp:
            command = f"pyuic5 {ui_source} -o {ui_target}"
            os.system(command)  # noqa: S605
            print(command)


def compile_qrc(ignore_timestamp: bool = False):
    qrc_source: Path = Path("../resources/resources.qrc").resolve()
    qrc_target = Path(QRC_TARGET_DIR, "resources_rc.py")

    # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
    source_timestamp: float = qrc_source.stat().st_mtime
    target_timestamp: float = qrc_target.stat().st_mtime if qrc_target.safe_exists() else 0.0

    # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
    if source_timestamp > target_timestamp or ignore_timestamp:
        command = f"pyrcc5 {qrc_source} -o {qrc_target}"
        os.system(command)  # noqa: S605
        print(command)


if __name__ == "__main__":
    compile_ui()
    compile_qrc()
