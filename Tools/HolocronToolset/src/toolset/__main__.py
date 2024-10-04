#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import atexit
import faulthandler
import gc
import importlib
import multiprocessing
import os
import pathlib
import sys
import tempfile

from contextlib import suppress
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qtpy.QtCore import QSettings


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
):  # sourcery skip: extract-method
    from loggerplus import RobustLogger

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
    logger = RobustLogger()
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
        if __name__ == "__main__":
            os.chdir(toolset_path)


def fix_qt_env_var():
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


def set_qt_api():
    available_apis = ["PyQt5", "PyQt6", "PySide2", "PySide6"]
    for api in available_apis:
        try:
            if api == "PyQt5":
                importlib.import_module("PyQt5.QtCore")
            elif api == "PyQt6":
                importlib.import_module("PyQt6.QtCore")
            elif api == "PySide2":
                importlib.import_module("PySide2.QtCore")
            elif api == "PySide6":
                importlib.import_module("PySide6.QtCore")
        except (ImportError):  # noqa: S112, PERF203
            continue
        else:
            os.environ["QT_API"] = api
            print(f"QT_API auto-resolved as '{api}'.")
            break


def is_running_from_temp() -> bool:
    app_path = pathlib.Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)

def qt_cleanup(app_close_event: asyncio.Event):
    """Cleanup so we can exit."""
    from loggerplus import RobustLogger

    from toolset.utils.window import WINDOWS
    from utility.system.app_process.shutdown import terminate_child_processes

    RobustLogger().debug("Closing/destroy all windows from WINDOWS list, (%s to handle)...", len(WINDOWS))
    for window in WINDOWS:
        window.close()
        window.destroy()
    WINDOWS.clear()
    gc.collect()
    for obj in gc.get_objects():
        with suppress(RuntimeError):  # wrapped C/C++ object of type QThread has been deleted
            if isinstance(obj, QThread) and obj.isRunning():
                RobustLogger().info(f"Terminating QThread obj with name: {obj.objectName()}")
                obj.terminate()
                obj.wait()
            elif isinstance(obj, multiprocessing.Process):
                RobustLogger().info(f"Terminating multiprocessing.Process obj with pid: {obj.pid}")
                obj.terminate()
                obj.join()
    app_close_event.set()
    terminate_child_processes()

def last_resort_cleanup():
    """Prevents the toolset from running in the background after sys.exit is called.

    This function should be registered with atexit as early as possible.
    """
    from loggerplus import RobustLogger

    from utility.system.app_process.shutdown import (
        gracefully_shutdown_threads,
        start_shutdown_process,
    )

    RobustLogger().info("Fully shutting down Holocron Toolset...")
    gracefully_shutdown_threads()
    RobustLogger().debug("Starting new shutdown process...")
    start_shutdown_process()
    RobustLogger().debug("Shutdown process started...")


def setupPreInitSettings():
    from qtpy.QtWidgets import QApplication

    from toolset.gui.widgets.settings.application import ApplicationSettings

    # Some application settings must be set before the app starts.
    # These ones are accessible through the in-app settings window widget.
    settings_widget = ApplicationSettings()
    environment_variables: dict[str, str] = settings_widget.app_env_variables
    for key, value in environment_variables.items():
        os.environ[key] = os.environ.get(key, value)  # Use os.environ.get to prioritize the existing env.
    for attr_name, attr_value in settings_widget.REQUIRES_RESTART.items():
        if attr_value is None:  # attr not available in this qt version.
            continue
        QApplication.setAttribute(attr_value, settings_widget.settings.value(attr_name, QApplication.testAttribute(attr_value), bool))


def main_init():
    sys.excepthook = onAppCrash
    is_main_process: bool = multiprocessing.current_process() == "MainProcess"
    if is_main_process:
        multiprocessing.set_start_method("spawn")  # 'spawn' is default on windows, linux/mac defaults to most likely 'fork' which breaks the built-in updater.
        atexit.register(last_resort_cleanup)  # last_resort_cleanup already handles child processes.

    if is_frozen():
        from loggerplus import RobustLogger

        RobustLogger().debug("App is frozen - calling multiprocessing.freeze_support()")
        multiprocessing.freeze_support()
        if is_main_process:
            set_qt_api()
        faulthandler.disable()
    else:
        fix_sys_and_cwd_path()
        fix_qt_env_var()
        # If you run into bugs, consider disabling faulthandler.
        # https://bugreports.qt.io/browse/PYSIDE-2359
        faulthandler.enable()


def setupPostInitSettings():
    from qtpy.QtGui import QFont

    from toolset.gui.widgets.settings.application import ApplicationSettings
    settings_widget = ApplicationSettings()
    toolset_qsettings: QSettings = settings_widget.settings
    app.setFont(toolset_qsettings.value("GlobalFont", QApplication.font(), QFont))

    for attr_name, attr_value in settings_widget.__dict__.items():
        if attr_value is None:  # attr not available in this qt version.
            continue
        if attr_name.startswith("AA_"):
            QApplication.setAttribute(attr_value, toolset_qsettings.value(attr_name, QApplication.testAttribute(attr_value), bool))

    for name, setting in settings_widget.MISC_SETTINGS.items():
        if toolset_qsettings.contains(name):
            qsetting_lookup_val = toolset_qsettings.value(name, setting.getter(), setting.setting_type)
            setting.setter(qsetting_lookup_val)


def setupToolsetDefaultEnv():
    from utility.misc import is_debug_mode

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation")
    if not is_debug_mode() or is_frozen():
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "0")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=false")  # Disable specific Qt debug output


if __name__ == "__main__":
    main_init()

    from qasync import QEventLoop  # pyright: ignore[reportMissingTypeStubs]
    from qtpy.QtCore import QThread
    from qtpy.QtWidgets import QApplication, QMessageBox

    setupPreInitSettings()

    app = QApplication(sys.argv)
    app.setApplicationName("HolocronToolsetV3")
    app.setOrganizationName("PyKotor")
    app.setOrganizationDomain("github.com/NickHugi/PyKotor")
    #app.thread().setPriority(QThread.Priority.HighestPriority)  # pyright: ignore[reportOptionalMemberAccess]
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(lambda: qt_cleanup(app_close_event))

    setupPostInitSettings()
    setupToolsetDefaultEnv()

    if is_running_from_temp():
        # Show error message using PyQt5's QMessageBox
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.setWindowTitle("Error")
        msgBox.setText("This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        msgBox.exec_()  # pyright: ignore[reportAttributeAccessIssue]
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    from toolset.gui.windows.main import ToolWindow

    toolWindow = ToolWindow()
    toolWindow.show()

    toolWindow.checkForUpdates(silent=True)

    use_qasync = False
    if use_qasync:
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        with loop:
            loop.run_forever()
    else:
        sys.exit(app.exec())
