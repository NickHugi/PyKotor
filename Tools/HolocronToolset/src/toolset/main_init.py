from __future__ import annotations

import atexit
import faulthandler
import importlib
import multiprocessing
import os
import pathlib
import sys
import tempfile

from typing import TYPE_CHECKING

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from types import TracebackType


def is_frozen() -> bool:
    """Check if the toolset is frozen in an executable file e.g. with PyInstaller.

    Returns:
        bool: True if the toolset is frozen, False otherwise.
    """
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
    )


def on_app_crash(
    etype: type[BaseException],
    exc: BaseException,
    tback: TracebackType | None,
):  # sourcery skip: extract-method
    """Handle uncaught exceptions.

    This function should be called when an uncaught exception occurs, set to sys.excepthook.
    """
    if issubclass(etype, KeyboardInterrupt):
        sys.__excepthook__(etype, exc, tback)
        return
    logger = RobustLogger()
    logger.critical("Uncaught exception", exc_info=(etype, exc, tback))


def fix_sys_and_cwd_path():
    """Fixes sys.path and current working directory for PyKotor.

    It makes no sense to call this function in frozen code.
    This function ensures a user can run toolset/__main__.py directly.
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
    return str(pathlib.Path(sys.executable)).startswith(tempfile.gettempdir())


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
        RobustLogger().debug("App is frozen - calling multiprocessing.freeze_support()")
        multiprocessing.freeze_support()
        if is_main_process:
            set_qt_api()
    else:
        fix_sys_and_cwd_path()
        fix_qt_env_var()
    # Do not use `faulthandler.enable()` in the toolset!
    # https://bugreports.qt.io/browse/PYSIDE-2359
    faulthandler.enable()


def last_resort_cleanup():
    """Prevents the toolset from running in the background after sys.exit is called.

    This function should be registered with atexit as early as possible.
    """
    from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]

    from utility.system.app_process.shutdown import gracefully_shutdown_threads, start_shutdown_process

    RobustLogger().info("Fully shutting down Holocron Toolset...")
    gracefully_shutdown_threads()
    RobustLogger().debug("Starting new shutdown process...")
    start_shutdown_process()
    RobustLogger().debug("Shutdown process started...")