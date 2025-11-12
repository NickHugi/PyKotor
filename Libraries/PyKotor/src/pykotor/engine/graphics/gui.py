"""GUI management stubs for test purposes.

This module provides minimal GUI infrastructure for testing without full rendering backend.

References:
----------
    vendor/reone/src/libs/gui/gui.cpp - GUI system implementation
    vendor/reone/include/reone/gui/control.h - GUI control interface
    vendor/KotOR.js/src/gui/ - GUI control implementations
    vendor/KotOR-Unity/Assets/Scripts/UI/ - Unity GUI implementation
    vendor/KotOR-dotNET - C# GUI handling
    vendor/kotorblender - GUI mesh export
    Note: This is a minimal stub for testing; full GUI implementation would use a rendering backend
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class GUI:
    """Lightweight GUI representation for tests."""

    name: str
    visible: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)


class GUIManager:
    """Minimal GUI manager used by the GUI tests."""

    def __init__(self) -> None:
        self._guis: Dict[str, GUI] = {}
        self._active_dialogue: Optional[str] = None

    def load_gui(self, name: str) -> GUI:
        """Load (or retrieve) a GUI by name."""
        if not name:
            raise ValueError("GUI name cannot be empty.")
        gui = self._guis.get(name)
        if gui is None:
            gui = GUI(name=name)
            self._guis[name] = gui
        gui.visible = True
        return gui

    def hide_gui(self, gui: GUI) -> None:
        """Hide a GUI instance."""
        gui.visible = False

    def show_gui(self, gui: GUI) -> None:
        """Show a GUI instance."""
        gui.visible = True

    def start_dialogue(self, dialogue_id: str) -> None:
        """Mark a dialogue sequence as active."""
        if not dialogue_id:
            raise ValueError("Dialogue identifier cannot be empty.")
        self._active_dialogue = dialogue_id

    def end_dialogue(self, dialogue_id: str) -> None:
        """Finalize a dialogue sequence."""
        if self._active_dialogue != dialogue_id:
            raise ValueError(f"Dialogue {dialogue_id!r} is not active.")
        self._active_dialogue = None

    def remove_gui(self, gui: GUI) -> None:
        """Remove a GUI instance from management."""
        self._guis.pop(gui.name, None)

