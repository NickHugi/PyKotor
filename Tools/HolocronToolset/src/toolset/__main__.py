from __future__ import annotations

import atexit
import cProfile
import multiprocessing
import os
import pathlib
import sys
import tempfile

from typing import TYPE_CHECKING

from qtpy.QtCore import QThread
from qtpy.QtWidgets import QApplication, QMessageBox

if TYPE_CHECKING:
    from types import TracebackType


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        or tempfile.gettempdir() in sys.executable
    )


def onAppCrash(
    etype: type[BaseException],
    e: BaseException,
    tback: TracebackType | None,
):
    from utility.logger_util import get_root_logger
    if issubclass(etype, KeyboardInterrupt):
        sys.__excepthook__(etype, e, tback)
        return
    logger = get_root_logger()
    logger.critical("Uncaught exception", exc_info=(etype, e, tback))


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


def set_qt_api():
    available_apis = ["pyqt5", "pyqt6", "pyside2", "pyside6"]
    for api in available_apis:
        try:
            if api == "pyqt5":
                __import__("PyQt5.QtCore")
            elif api == "pyqt6":
                __import__("PyQt6.QtCore")
            elif api == "pyside2":
                __import__("PySide2.QtCore")
            elif api == "pyside6":
                __import__("PySide6.QtCore")
            os.environ["QT_API"] = api
            print(f"QT_API set to '{api}'.")
            break
        except (ImportError, ModuleNotFoundError):  # noqa: S112
            continue


def is_running_from_temp():
    app_path = Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)


if __name__ == "__main__":
    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
    os.environ["QT_DEBUG_PLUGINS"] = "1"

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    # os.environ["QT_SCALE_FACTOR"] = "1"

    multiprocessing.set_start_method("spawn")  # 'spawn' is default on windows, linux/mac defaults to some other start method which breaks the updater.
    if is_frozen():
        from utility.logger_util import get_root_logger
        get_root_logger().debug("App is frozen - calling multiprocessing.freeze_support()")
        multiprocessing.freeze_support()
        set_qt_api()
    else:
        fix_sys_and_cwd_path()
        os.environ["QT_API"] = os.environ.get("QT_API", "")  # supports pyqt5, pyqt6, pyside2, pyside6
        if not os.environ["QT_API"]:
            set_qt_api()

    try:
        import qtpy
        print(f"Using Qt bindings: {qtpy.API_NAME}")
    except ImportError as e:
        print(e)
        sys.exit("QtPy is not available. Ensure QtPy is installed and accessible.")

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
    os.environ["QT_DEBUG_PLUGINS"] = "1"

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    # os.environ["QT_SCALE_FACTOR"] = "1"

    from qtpy.QtCore import QThread
    from qtpy.QtWidgets import QApplication

    from utility.system.path import Path

    app = QApplication(sys.argv)

    import ui.stylesheet_resources as stylesheet_resources  # noqa: F401

    # set stylesheet
    #file = QFile(":/dark/stylesheet.qss")
    #file.open(QFile.ReadOnly | QFile.Text)
    #stream = QTextStream(file)
    #app.setStyleSheet(stream.readAll())

    # font = app.font()
    # font.setPixelSize(15)
    # app.setFont(font)
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app.thread().setPriority(QThread.HighestPriority)

    sys.excepthook = onAppCrash
    if is_running_from_temp():
        # Show error message using PyQt5's QMessageBox
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setWindowTitle("Error")
        msgBox.setText("This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        msgBox.exec_()
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    from toolset.gui.windows.main import ToolWindow

    profiler = False  # Set to False or None to disable profiler
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    window = ToolWindow()
    window.show()
    window.checkForUpdates(silent=True)
    def qt_cleanup():
        """Cleanup so we can exit."""
        from toolset.utils.window import WINDOWS
        from utility.logger_util import get_root_logger
        get_root_logger().debug("Closing/destroy all windows from WINDOWS list, (%s to handle)...", len(WINDOWS))
        for window in WINDOWS:
            window.close()
            window.destroy()
        WINDOWS.clear()

    def last_resort_cleanup():
        """Prevents the toolset from running in the background after sys.exit is called..."""
        from utility.logger_util import get_root_logger
        from utility.system.os_helper import kill_self_pid
        get_root_logger().info("Fully shutting down Holocron Toolset...")
        kill_self_pid()

    app.aboutToQuit.connect(qt_cleanup)
    atexit.register(last_resort_cleanup)

    # Start main app loop.
    app.exec_()

    if profiler:
        profiler.disable()
        profiler.dump_stats(str(Path("profiler_output.pstat")))
