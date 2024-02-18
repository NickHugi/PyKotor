from __future__ import annotations

import cProfile
import multiprocessing
import os
import pathlib
import sys
import tempfile
import traceback

from typing import TYPE_CHECKING

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

if TYPE_CHECKING:
    from types import TracebackType


def onAppCrash(etype: type[BaseException], e: BaseException, tback: TracebackType | None):
    from utility.error_handling import format_exception_with_variables  # noqa: PLC0415
    with pathlib.Path("errorlog.txt").open("a", encoding="utf-8") as file:
        try:  # sourcery skip: do-not-use-bare-except
            file.writelines(format_exception_with_variables(e, etype, tback))
        except:  # noqa: E722
            file.writelines(str(e))
        file.write("\n----------------------\n")
    # Mimic default behavior by printing the traceback to stderr
    traceback.print_exception(etype, e, tback)


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
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    file_absolute_path = pathlib.Path(__file__).resolve()

    pykotor_path = file_absolute_path.parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    pykotor_gl_path = file_absolute_path.parents[4] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if pykotor_gl_path.exists():
        update_sys_path(pykotor_gl_path.parent)
    utility_path = file_absolute_path.parents[4] / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        update_sys_path(utility_path)
    toolset_path = file_absolute_path.parents[1] / "toolset"
    if toolset_path.exists():
        update_sys_path(toolset_path.parent)
        os.chdir(toolset_path)

if __name__ == "__main__":

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
    os.environ["QT_DEBUG_PLUGINS"] = "1"

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    # os.environ["QT_SCALE_FACTOR"] = "1"

    if is_frozen():
        print("App is frozen - doing multiprocessing.freeze_support()")
        multiprocessing.freeze_support()
    else:
        fix_sys_and_cwd_path()
    from utility.system.path import Path

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


    profiler = True  # Set to False or None to disable profiler
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    app.exec_()

    if profiler:
        profiler.disable()
        profiler.dump_stats(str(Path("profiler_output.pstat")))
