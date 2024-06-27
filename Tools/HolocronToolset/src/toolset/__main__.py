from __future__ import annotations

import atexit
import cProfile
import gc
import multiprocessing
import os
import pathlib
import sys
import tempfile

from contextlib import suppress
from types import TracebackType


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        # or tempfile.gettempdir() in sys.executable
    )


def onAppCrash(
    etype: type[BaseException],
    exc: BaseException,
    tback: TracebackType | None,
):
    from utility.logger_util import RobustRootLogger

    if issubclass(etype, KeyboardInterrupt):
        sys.__excepthook__(etype, exc, tback)
        return
    if tback is None:
        with suppress(Exception):
            import inspect

            # Get the current stack frames
            current_stack = inspect.stack()
            if current_stack:
                # Reverse the stack to have the order from caller to callee
                current_stack = current_stack[1:][::-1]
                fake_traceback = None
                for frame_info in current_stack:
                    frame = frame_info.frame
                    fake_traceback = TracebackType(fake_traceback, frame, frame.f_lasti, frame.f_lineno)
                exc = exc.with_traceback(fake_traceback)
                # Now exc has a traceback :)
                tback = exc.__traceback__
    logger = RobustRootLogger()
    logger.critical("Uncaught exception", exc_info=(etype, exc, tback))


def fix_sys_and_cwd_path():
    """Fixes sys.path and current working directory for PyKotor.

    This function should never be used in frozen code.
    This function also ensures a user can run toolset/__main__.py directly.
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
    # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    available_apis = ["PyQt5", "PyQt6", "PySide2", "PySide6"]
    for api in available_apis:
        try:
            if api == "PyQt5":
                __import__("PyQt5.QtCore")
            elif api == "PyQt6":
                __import__("PyQt6.QtCore")
            elif api == "PySide2":
                __import__("PySide2.QtCore")
            elif api == "PySide6":
                __import__("PySide6.QtCore")
        except (ImportError, ModuleNotFoundError):  # noqa: S112, PERF203
            continue
        else:
            os.environ["QT_API"] = api
            print(f"QT_API auto-resolved as '{api}'.")
            break


def is_running_from_temp() -> bool:
    app_path = pathlib.Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)

def qt_cleanup():
    """Cleanup so we can exit."""
    from toolset.utils.window import WINDOWS
    from utility.logger_util import RobustRootLogger
    from utility.system.os_helper import terminate_child_processes

    RobustRootLogger().debug("Closing/destroy all windows from WINDOWS list, (%s to handle)...", len(WINDOWS))
    for window in WINDOWS:
        window.close()
        window.destroy()
    WINDOWS.clear()
    gc.collect()
    for obj in gc.get_objects():
        if isinstance(obj, QThread) and obj.isRunning():
            RobustRootLogger().debug(f"Terminating QThread: {obj}")
            obj.terminate()
            obj.wait()
    terminate_child_processes()

def last_resort_cleanup():
    """Prevents the toolset from running in the background after sys.exit is called..."""
    from utility.logger_util import RobustRootLogger
    from utility.system.os_helper import gracefully_shutdown_threads, start_shutdown_process

    RobustRootLogger().info("Fully shutting down Holocron Toolset...")
    # kill_self_pid()
    gracefully_shutdown_threads()
    RobustRootLogger().debug("Starting new shutdown process...")
    start_shutdown_process()
    RobustRootLogger().debug("Shutdown process started...")

def main_init():
    sys.excepthook = onAppCrash
    if multiprocessing.current_process() == "MainProcess":
        multiprocessing.set_start_method("spawn")  # 'spawn' is default on windows, linux/mac defaults to some other start method (probably 'fork') which breaks the updater.

    if is_frozen():
        from utility.logger_util import RobustRootLogger

        RobustRootLogger().debug("App is frozen - calling multiprocessing.freeze_support()")
        multiprocessing.freeze_support()
        set_qt_api()
    else:
        fix_sys_and_cwd_path()
        qtpy_case_map: dict[str, str] = {
            "pyqt5": "PyQt5",
            "pyqt6": "PyQt6",
            "pyside2": "PySide2",
            "pyside6": "PySide6",
        }
        case_api_name = qtpy_case_map.get(os.environ.get("QT_API", "").lower().strip())
        if case_api_name in ("PyQt5", "PyQt6", "PySide2", "PySide6"):
            print(f"QT_API manually set by user to '{case_api_name}'.")
            os.environ["QT_API"] = case_api_name
        else:
            set_qt_api()

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation")

    from utility.misc import is_debug_mode
    if not is_debug_mode() or is_frozen():
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "0")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=false")  # Disable specific Qt debug output
    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    # os.environ["QT_SCALE_FACTOR"] = "1"


if __name__ == "__main__":
    main_init()

    from qtpy.QtCore import QThread, Qt
    from qtpy.QtGui import QFont
    from qtpy.QtWidgets import QApplication, QMessageBox

    from toolset.gui.widgets.settings.application import ApplicationSettings

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling, False)
    # Some application settings must be set before the app starts.
    # These ones are accessible through the in-app settings window widget.
    settings_widget = ApplicationSettings()
    for attr_name, attr_value in settings_widget.REQUIRES_RESTART.items():
        QApplication.setAttribute(attr_value, settings_widget.settings.value(attr_name, QApplication.testAttribute(attr_value), bool))

    app = QApplication(sys.argv)
    # app.setAttribute(Qt.ApplicationAttribute.AA_ForceRasterWidgets, False)  # this breaks gl!

    for attr_name, attr_value in settings_widget.__dict__.items():
        if not attr_name.startswith("AA_"):
            continue
        QApplication.setAttribute(attr_value, settings_widget.settings.value(attr_name, QApplication.testAttribute(attr_value), bool))
    app.setFont(QFont("Roboto", 13))
    app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app.setApplicationName("HolocronToolsetV3")
    app.setOrganizationName("PyKotor")
    app.setOrganizationDomain("github.com/NickHugi/PyKotor")

    app.thread().setPriority(QThread.Priority.HighestPriority)

    if is_running_from_temp():
        # Show error message using PyQt5's QMessageBox
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.setWindowTitle("Error")
        msgBox.setText("This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        msgBox.exec_()
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    app.aboutToQuit.connect(qt_cleanup)
    atexit.register(last_resort_cleanup)

    from toolset.gui.windows.main import ToolWindow

    profiler: bool | cProfile.Profile = False  # Set to False or None to disable profiler
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    window = ToolWindow()
    window.show()
    window.checkForUpdates(silent=True)

    # Start main app loop.
    app.exec_()

    if profiler:
        profiler.disable()
        profiler.dump_stats(str(pathlib.Path("profiler_output.pstat")))
