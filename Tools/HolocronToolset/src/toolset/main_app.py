from __future__ import annotations

import asyncio
import sys

from contextlib import suppress

from loggerplus import RobustLogger
from qtpy.QtCore import QThread
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QMessageBox

import resources_rc  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import

from toolset.config import CURRENT_VERSION
from toolset.gui.windows.main import ToolWindow
from toolset.main_init import is_running_from_temp
from toolset.main_settings import setup_post_init_settings, setup_pre_init_settings, setup_toolset_default_env
from toolset.utils.window import TOOLSET_WINDOWS
from utility.system.app_process.shutdown import terminate_child_processes


def qt_cleanup():
    """Cleanup so we can exit."""
    RobustLogger().debug("Closing/destroy all windows from WINDOWS list, (%s to handle)...", len(TOOLSET_WINDOWS))
    for window in TOOLSET_WINDOWS:
        window.close()
        window.destroy()

    TOOLSET_WINDOWS.clear()
    terminate_child_processes()


def main():
    """Main entry point for the Holocron Toolset.

    This block is ran when users run __main__.py directly.
    """
    setup_pre_init_settings()

    app = QApplication(sys.argv)
    app.setApplicationName("HolocronToolset")
    app.setOrganizationName("PyKotor")
    app.setOrganizationDomain("github.com/NickHugi/PyKotor")
    app.setApplicationVersion(CURRENT_VERSION)
    app.setDesktopFileName("com.pykotor.toolset")
    app.setApplicationDisplayName("Holocron Toolset")
    icon_path = ":/images/icons/sith.png"
    icon = QIcon(icon_path)
    if icon.isNull():
        RobustLogger().warning(f"Warning: Main application icon not found at '{icon_path}'")
    else:
        app.setWindowIcon(icon)
    main_gui_thread: QThread | None = app.thread()
    assert main_gui_thread is not None, "Main GUI thread should not be None"
    main_gui_thread.setPriority(QThread.Priority.HighestPriority)
    app.aboutToQuit.connect(qt_cleanup)

    setup_post_init_settings()
    setup_toolset_default_env()

    if is_running_from_temp():
        QMessageBox.critical(
            None,
            "Error",
            "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running."
        )
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    tool_window = ToolWindow()
    tool_window.show()
    tool_window.update_manager.check_for_updates(silent=True)
    with suppress(ImportError):
        from qasync import QEventLoop  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
        asyncio.set_event_loop(QEventLoop(app))
    sys.exit(app.exec())
