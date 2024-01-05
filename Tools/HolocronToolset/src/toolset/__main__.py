from __future__ import annotations

import multiprocessing
import os
import pathlib
import sys
import tempfile
from typing import TYPE_CHECKING

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

if TYPE_CHECKING:
    from types import TracebackType


def onAppCrash(etype: type[BaseException], e: BaseException, tback: TracebackType):
    from utility.error_handling import format_exception_with_variables
    with pathlib.Path("errorlog.txt").open("a") as file:
        file.writelines(format_exception_with_variables(e, etype, tback))
        file.write("\n----------------------\n")
    raise e

def is_frozen() -> bool:  # sourcery skip: assign-if-exp, boolean-if-exp-identity, reintroduce-else, remove-unnecessary-cast
    # Check for sys.frozen attribute
    if getattr(sys, "frozen", False):
        return True
    # Check if the executable is in a temp directory (common for frozen apps)
    if tempfile.gettempdir() in sys.executable:
        return True
    return False

def fix_sys_and_cwd_path():
    """Fixes sys.path and current working directory for PyKotor.

    This function will determine whether they have the source files downloaded for pykotor in the expected directory. If they do, we
    insert the source path to pykotor to the beginning of sys.path so it'll have priority over pip's pykotor package if that is installed.
    If the toolset dir exists, change directory to that of the toolset. Allows users to do things like `python -m toolset`
    This function should never be used in frozen code.
    This function also ensures a user can run toolset/__main__.py directly.

    Processing Logic:
    ----------------
        - Checks if PyKotor package exists in parent directory of calling file.
        - If exists, removes parent directory from sys.path and adds to front.
        - Also checks for toolset package and changes cwd to that directory if exists.
        - This ensures packages and scripts can be located correctly on import.
    """
    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)

    pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    pykotor_gl_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if pykotor_gl_path.exists():
        update_sys_path(pykotor_gl_path.parent)
    utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        update_sys_path(utility_path)
    toolset_path = pathlib.Path(__file__).parents[1] / "toolset"
    if toolset_path.exists():
        update_sys_path(toolset_path.parent)
        os.chdir(toolset_path)

if __name__ == "__main__":
    if is_frozen() is False:
        fix_sys_and_cwd_path()

    from utility.misc import is_debug_mode

    os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
    os.environ["QT_DEBUG_PLUGINS"] = "1"

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    # os.environ["QT_SCALE_FACTOR"] = "1"

    if not is_debug_mode() or is_frozen():
        multiprocessing.freeze_support()


    app = QApplication(sys.argv)

    # font = app.font()
    # font.setPixelSize(15)
    # app.setFont(font)
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app.thread().setPriority(QThread.HighestPriority)

    sys.excepthook = onAppCrash

    from toolset.gui.windows.main import ToolWindow

    window = ToolWindow()
    window.show()
    app.exec_()
