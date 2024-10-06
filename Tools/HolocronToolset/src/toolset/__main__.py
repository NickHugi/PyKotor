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
    from inspect import FrameInfo

    from qtpy.QtCore import QSettings, QThread


def is_frozen() -> bool:
    """Check if the toolset is frozen in an executable file e.g. with PyInstaller.

    Returns:
        bool: True if the toolset is frozen, False otherwise.
    """
    return (
        getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", False)
        # or tempfile.gettempdir() in sys.executable
    )


def on_app_crash(
    etype: type[BaseException],
    exc: BaseException,
    tback: TracebackType | None,
):  # sourcery skip: extract-method
    """Handle uncaught exceptions.

    This function should be called when an uncaught exception occurs, set to sys.excepthook.
    """
    from loggerplus import RobustLogger

    if issubclass(etype, KeyboardInterrupt):
        sys.__excepthook__(etype, exc, tback)
        return
    if tback is None:
        with suppress(Exception):
            import inspect

            # Get the current stack frames
            current_stack: list[FrameInfo] = inspect.stack()
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
        os.chdir(toolset_path)


def fix_qt_env_var():
    """Fix the QT_API environment variable.

    This function should be called when the toolset is not frozen.
    """
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
    """Set the QT_API environment variable to the first available API.

    This function should only be called when the toolset is not frozen.
    """
    available_apis: list[str] = ["PyQt5", "PyQt6", "PySide2", "PySide6"]
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
        except ImportError:  # noqa: S112, PERF203
            continue
        else:
            os.environ["QT_API"] = api
            print(f"QT_API auto-resolved as '{api}'.")
            break


def is_running_from_temp() -> bool:
    """Check if the toolset is running from a temporary or zip directory.

    Returns:
        bool: True if the toolset is running from a temporary or zip directory, False otherwise.
    """
    app_path = pathlib.Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)


def qt_cleanup():
    """Cleanup so we can exit."""
    from loggerplus import RobustLogger
    from qtpy.QtCore import QThread

    from toolset.utils.window import TOOLSET_WINDOWS
    from utility.system.app_process.shutdown import terminate_child_processes

    RobustLogger().debug("Closing/destroy all windows from WINDOWS list, (%s to handle)...", len(TOOLSET_WINDOWS))
    for window in TOOLSET_WINDOWS:
        window.close()
        window.destroy()
    TOOLSET_WINDOWS.clear()
    gc.collect()
    for obj in gc.get_objects():
        with suppress(RuntimeError):  # wrapped C/C++ object of type QThread has been deleted
            if isinstance(obj, QThread) and obj.isRunning():
                RobustLogger().info(f"Terminating QThread obj with name: {obj.objectName()}")
                obj.terminate()
                # obj.wait()  # DO NOT UNCOMMENT THIS, causes a deadlock.
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


def _setup_pre_init_settings():
    """Setup pre-initialization settings for the Holocron Toolset.

    Call main_init() to get here.
    """
    from qtpy.QtWidgets import QApplication  # pylint: disable=redefined-outer-name

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
        QApplication.setAttribute(
            attr_value,
            settings_widget.settings.value(attr_name, QApplication.testAttribute(attr_value), bool),
        )


def main_init():
    """Initialize the Holocron Toolset.

    This function should be called before the QApplication is created.
    """
    sys.excepthook = on_app_crash
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
        # DO NOT USE `faulthandler` IN THIS TOOLSET!!
        # import faulthandler
        # https://bugreports.qt.io/browse/PYSIDE-2359
        # faulthandler.enable()


def setup_post_init_settings():
    """Set up post-initialization settings for the application.

    This function performs the following tasks:
    1. Imports necessary Qt modules and application settings.
    2. Retrieves the QApplication instance and sets the global font.
    3. Applies Qt attributes that require a restart to take effect.
    4. Sets miscellaneous settings that can be changed without restarting.

    The function uses the ApplicationSettings class to manage and apply various
    settings to the QApplication instance.
    """
    from qtpy.QtGui import QFont
    from qtpy.QtWidgets import QApplication

    from toolset.gui.widgets.settings.application import ApplicationSettings

    settings_widget = ApplicationSettings()
    toolset_qsettings: QSettings = settings_widget.settings
    app = QApplication.instance()
    assert app is not None, "QApplication instance not found."
    assert isinstance(app, QApplication), "QApplication instance not a QApplication type object."

    # Set the global font for the application
    app.setFont(toolset_qsettings.value("GlobalFont", QApplication.font(), QFont))

    # Apply Qt attributes that require a restart
    for attr_name, attr_value in settings_widget.__dict__.items():
        if attr_value is None:  # attr not available in this qt version.
            continue
        if attr_name.startswith("AA_"):
            QApplication.setAttribute(
                attr_value,
                toolset_qsettings.value(attr_name, QApplication.testAttribute(attr_value), bool),
            )

    # Set miscellaneous settings that can be changed without restarting
    for name, setting in settings_widget.MISC_SETTINGS.items():
        if toolset_qsettings.contains(name):
            qsetting_lookup_val = toolset_qsettings.value(name, setting.getter(), setting.setting_type)
            setting.setter(qsetting_lookup_val)


def setup_toolset_default_env():
    """Setup default environment variables for the toolset based on our recommendations.

    These can be configured in the toolset's Settings dialog.
    """
    from utility.misc import is_debug_mode

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation")
    if not is_debug_mode() or is_frozen():
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "0")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=false")  # Disable specific Qt debug output


if __name__ == "__main__":

    def main():
        """Main entry point for the Holocron Toolset.

        This block is ran when users run __main__.py directly.
        """
        try:
            from qasync import QEventLoop  # pyright: ignore[reportMissingTypeStubs]
        except ImportError:
            use_qasync = False
        else:
            use_qasync = True
        from loggerplus import RobustLogger
        from qtpy.QtCore import QThread  # pylint: disable=no-name-in-module
        from qtpy.QtGui import QIcon
        from qtpy.QtWidgets import QApplication, QMessageBox  # pylint: disable=no-name-in-module

        from toolset.config import CURRENT_VERSION

        _setup_pre_init_settings()

        app = QApplication(sys.argv)
        app.setApplicationName("HolocronToolset")
        app.setOrganizationName("PyKotor")
        app.setOrganizationDomain("github.com/NickHugi/PyKotor")
        app.setApplicationVersion(CURRENT_VERSION)
        app.setQuitOnLastWindowClosed(True)
        icon_path = ":/images/icons/sith.ico"
        if QIcon(icon_path).isNull():
            RobustLogger().warning(f"Warning: Main application icon not found at '{icon_path}'")
        else:
            icon = QIcon(icon_path)
            app.setWindowIcon(icon)
        main_gui_thread: QThread | None = app.thread()
        assert main_gui_thread is not None, "Main GUI thread should not be None"
        main_gui_thread.setPriority(QThread.Priority.HighestPriority)
        app.aboutToQuit.connect(qt_cleanup)

        setup_post_init_settings()
        setup_toolset_default_env()

        if is_running_from_temp():
            # Show error message using PyQt5's QMessageBox
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText("This application cannot be run from within a zip or temporary directory.  Please extract it to a permanent location before running.")
            msg_box.exec()
            sys.exit("Exiting: Application was run from a temporary or zip directory.")

        from toolset.gui.windows.main import ToolWindow

        tool_window = ToolWindow()
        tool_window.show()
        tool_window.check_for_updates(silent=True)

        if use_qasync:
            loop = QEventLoop(app)
            asyncio.set_event_loop(loop)
            with loop:
                loop.run_forever()
        else:
            sys.exit(app.exec())

    main_init()
    main()
