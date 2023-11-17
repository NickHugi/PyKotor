import multiprocessing
import os
import pathlib
import sys
from types import TracebackType

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication


def onAppCrash(e: BaseException, value: str, tback: TracebackType):
    from pykotor.helpers.error_handling import format_exception_with_variables
    with pathlib.Path("errorlog.txt").open("a") as file:
        file.writelines(format_exception_with_variables(e, value, tback))
        file.write("\n----------------------\n")
    raise e

def is_frozen() -> bool:
    return getattr(sys, "frozen", False)

def is_debug_mode() -> bool:
    ret = False
    if os.getenv("PYTHONDEBUG", None):
        ret = True
    if os.getenv("DEBUG_MODE", "0") == "1":
        ret = True
    if hasattr(sys, "gettrace") and sys.gettrace() is not None:
        ret = True
    print(f"DEBUG MODE: {ret!s}")
    return ret

def fix_sys_and_cwd_path():
    """Fixes sys.path and current working directory for PyKotor.

    This function will determine whether they have the source files downloaded for pykotor in the expected directory. If they do, we
    insert the source path to pykotor to the beginning of sys.path so it'll have priority over pip's pykotor package if that is installed.
    If the toolset dir exists, change directory to that of the toolset. Allows users to do things like `python -m toolset`
    This function should never be used in frozen code.
    This function also ensures a user can run toolset/__main__.py directly.

    Processing Logic:
    - Checks if PyKotor package exists in parent directory of calling file.
    - If exists, removes parent directory from sys.path and adds to front.
    - Also checks for toolset package and changes cwd to that directory if exists.
    - This ensures packages and scripts can be located correctly on import.
    """
    pykotor_path = pathlib.Path(__file__).parents[1] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)
    toolset_path = pathlib.Path(__file__).parents[1] / "toolset"
    if toolset_path.joinpath("__init__.py").exists():
        os.chdir(toolset_path)

if __name__ == "__main__":
    if is_frozen() is False:
        fix_sys_and_cwd_path()

    os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
    os.environ["QT_DEBUG_PLUGINS"] = "1"

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    # os.environ["QT_SCALE_FACTOR"] = "1"

    if not is_debug_mode() or is_frozen():
        multiprocessing.freeze_support()

    from toolset.gui.windows.main import ToolWindow

    app = QApplication(sys.argv)

    # font = app.font()
    # font.setPixelSize(15)
    # app.setFont(font)
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app.thread().setPriority(QThread.HighestPriority)  # type: ignore[reportGeneralTypeIssues]

    sys.excepthook = onAppCrash
    window = ToolWindow()
    window.show()
    app.exec_()
