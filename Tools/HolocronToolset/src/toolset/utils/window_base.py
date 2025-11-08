from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QDialog, QMainWindow


TOOLSET_WINDOWS: list[QDialog | QMainWindow] = []
"""TODO: Remove this implementation, there's better ways to keep windows from being garbage collected."""

_UNIQUE_SENTINEL = object()


def add_window(
    window: QDialog | QMainWindow,
) -> None:
    """Prevents Qt's garbage collection by keeping a reference to the window."""
    original_closeEvent = window.closeEvent

    def new_close_event(
        event: QCloseEvent | None = _UNIQUE_SENTINEL,  # pyright: ignore[reportArgumentType]
        *args,
        **kwargs,
    ):
        from toolset.gui.editor import Editor

        if isinstance(window, Editor) and window._filepath is not None:  # noqa: SLF001
            add_recent_file(window._filepath)  # noqa: SLF001
        if window in TOOLSET_WINDOWS:
            TOOLSET_WINDOWS.remove(window)
        if event is _UNIQUE_SENTINEL:  # Make event arg optional just in case the class has the wrong definition.
            original_closeEvent(*args, **kwargs)
        else:
            original_closeEvent(event, *args, **kwargs)  # pyright: ignore[reportArgumentType]

    window.closeEvent = new_close_event  # pyright: ignore[reportAttributeAccessIssue]
    TOOLSET_WINDOWS.append(window)


def add_recent_file(
    file: Path,
) -> None:
    """Update the list of recent files."""
    settings = GlobalSettings()
    recent_files: list[str] = [str(fp) for fp in {Path(p) for p in settings.recentFiles} if fp.is_file()]
    recent_files.insert(0, str(file))
    if len(recent_files) > 15:  # noqa: PLR2004
        recent_files.pop()
    settings.recentFiles = recent_files
