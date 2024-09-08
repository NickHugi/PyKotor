class ModuleDesignerSettings:
    # ... existing code ...
    def __init__(self):
        # ... existing code ...
        self.lytEditorSettings = LYTEditorSettings()

class LYTEditorSettings:
    def __init__(self):
        self.gridSize = 10
        self.snapToGrid = True
        self.showGrid = True
        self.layerVisibility = {"Rooms": True, "Tracks": True, "Obstacles": True, "DoorHooks": True}