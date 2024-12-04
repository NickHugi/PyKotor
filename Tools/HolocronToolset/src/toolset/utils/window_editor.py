from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from toolset.gui.editor import Editor
from toolset.utils.window_base import add_window

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget
    pass

def create_editor_window(
    filepath: Path | str | None = None,
    parent: QWidget | None = None,
) -> Editor:
    """Create a new editor window."""
    editor: Editor = Editor(parent)
    if filepath is not None:
        editor.load_file(filepath)
    add_window(editor)
    editor.show()
    return editor

def get_editor_by_filepath(filepath: Path | str) -> Editor | None:
    """Get an editor window by its filepath."""
    from toolset.utils.window_base import TOOLSET_WINDOWS

    if isinstance(filepath, str):
        filepath = Path(filepath)
    for window in TOOLSET_WINDOWS:
        if isinstance(window, Editor) and window._filepath == filepath:  # noqa: SLF001
            return window
    return None

def get_editor_by_title(title: str) -> Editor | None:
    """Get an editor window by its title."""
    from toolset.utils.window_base import TOOLSET_WINDOWS

    for window in TOOLSET_WINDOWS:
        if isinstance(window, Editor) and window.windowTitle() == title:
            return window
    return None

def get_all_editors() -> list[Editor]:
    """Get all editor windows."""
    from toolset.utils.window_base import TOOLSET_WINDOWS
    return [window for window in TOOLSET_WINDOWS if isinstance(window, Editor)]

def close_all_editors():
    """Close all editor windows."""
    for editor in get_all_editors():
        editor.close()
