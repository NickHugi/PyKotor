from __future__ import annotations

from typing import Any

from toolset.gui.widgets.settings.editor_settings.git import GITSettings


class LYTEditorSettings(GITSettings):
    def __init__(self):
        super().__init__()
        # Add any LYT-specific settings here
        self.grid_size: float = 1.0
        self.show_grid: bool = True
        self.show_room_labels: bool = True
        self.show_door_hook_labels: bool = True

    def load(self):
        # Load LYT-specific settings
        self.grid_size = self.value("grid_size", 1.0)
        self.show_grid = self.value("show_grid", True)
        self.show_room_labels = self.value("show_room_labels", True)
        self.show_door_hook_labels = self.value("show_door_hook_labels", True)

    def save(self):
        # Save LYT-specific settings
        self.setValue("grid_size", self.grid_size)
        self.setValue("show_grid", self.show_grid)
        self.setValue("show_room_labels", self.show_room_labels)
        self.setValue("show_door_hook_labels", self.show_door_hook_labels)

    def value(self, key: str, default: Any) -> Any:
        return self.settings.value(key, default)

    def setValue(self, key: str, value: Any):
        self.settings.setValue(key, value)
