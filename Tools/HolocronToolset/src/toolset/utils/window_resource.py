from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from toolset.utils.window_editor import create_editor_window, get_editor_by_filepath

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.gui.editor import Editor


def get_resource_type(filepath: Path | str) -> str | None:
    """Get the resource type from a filepath."""
    if isinstance(filepath, str):
        filepath = Path(filepath)
    return filepath.suffix[1:].lower() if filepath.suffix else None


def open_resource(
    filepath: Path | str,
    parent: QWidget | None = None,
) -> Editor | None:
    """Open a resource file in the appropriate editor."""
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if not filepath.is_file():
        RobustLogger().warning(f"File not found: {filepath}")
        return None

    existing_editor = get_editor_by_filepath(filepath)
    if existing_editor is not None:
        existing_editor.activateWindow()
        return existing_editor

    return create_editor_window(filepath, parent)


def open_resources(
    filepaths: list[Path | str],
    parent: QWidget | None = None,
) -> list[Editor]:
    """Open multiple resource files."""
    editors: list[Editor] = []
    for filepath in filepaths:
        editor = open_resource(filepath, parent)
        if editor is not None:
            editors.append(editor)
    return editors
