from __future__ import annotations

import asyncio

from contextlib import suppress
from typing import TYPE_CHECKING

from qtpy.QtWidgets import QMessageBox

from toolset.gui.windows.tool_window import ToolWindow
from toolset.utils.temp import is_running_from_temp

if TYPE_CHECKING:
    from qtpy.QtWidgets import QApplication

def setup_main_window(app: QApplication):
    """Set up and show the main application window."""
    if is_running_from_temp():
        QMessageBox.critical(
            None,
            "Error",
            "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running."
        )
        return False

    tool_window = ToolWindow()
    tool_window.show()
    tool_window.update_manager.check_for_updates(silent=True)

    with suppress(ImportError):
        from qasync import QEventLoop  # pyright: ignore[reportMissingTypeStubs]
        asyncio.set_event_loop(QEventLoop(app))

    return True
