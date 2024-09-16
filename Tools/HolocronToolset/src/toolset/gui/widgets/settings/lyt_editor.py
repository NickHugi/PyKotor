from __future__ import annotations

from toolset.gui.widgets.settings.git import GITSettings


class LYTEditorSettings(GITSettings):
    def __init__(self):
        super().__init__()
        # Add any LYT-specific settings here
        self.gridSize = 1.0
        self.snapToGrid = True
        self.showRoomLabels = True
        self.showDoorHookLabels = True

    def load(self):
        super().load()
        # Load LYT-specific settings
        self.gridSize = self.value("gridSize", 1.0)
        self.snapToGrid = self.value("snapToGrid", True)
        self.showRoomLabels = self.value("showRoomLabels", True)
        self.showDoorHookLabels = self.value("showDoorHookLabels", True)

    def save(self):
        super().save()
        # Save LYT-specific settings
        self.setValue("gridSize", self.gridSize)
        self.setValue("snapToGrid", self.snapToGrid)
        self.setValue("showRoomLabels", self.showRoomLabels)
        self.setValue("showDoorHookLabels", self.showDoorHookLabels)
