from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt

from pykotor.common.misc import Color
from toolset.data.settings import Settings

if TYPE_CHECKING:
    from toolset.data.settings import SettingsProperty


class GITSettings(Settings):
    def __init__(self):
        super().__init__("GITEditor")

    def resetMaterialColors(self):
        for setting in dir(self):
            if not setting.endswith("Colour"):
                continue
            self.reset_setting(setting)

    def resetControls(self):
        for setting in dir(self):
            if not setting.endswith("Bind"):
                continue
            self.reset_setting(setting)

    # region Strings (Instance Labels)
    creatureLabel: SettingsProperty[str] = Settings.addSetting(
        "creatureLabel",
        "",
    )
    doorLabel: SettingsProperty[str] = Settings.addSetting(
        "doorLabel",
        "",
    )
    placeableLabel = Settings.addSetting(
        "placeableLabel",
        "",
    )
    storeLabel = Settings.addSetting(
        "storeLabel",
        "",
    )
    soundLabel = Settings.addSetting(
        "soundLabel",
        "",
    )
    waypointLabel = Settings.addSetting(
        "waypointLabel",
        "",
    )
    cameraLabel = Settings.addSetting(
        "cameraLabel",
        "",
    )
    encounterLabel = Settings.addSetting(
        "encounterLabel",
        "",
    )
    triggerLabel = Settings.addSetting(
        "triggerLabel",
        "",
    )
    # endregion

    # region Ints (Material Colours)
    undefinedMaterialColour = Settings.addSetting(
        "undefinedMaterialColour",
        Color(0.400, 0.400, 0.400, 0.5).rgba_integer(),
    )
    dirtMaterialColour = Settings.addSetting(
        "dirtMaterialColour",
        Color(0.610, 0.235, 0.050, 0.5).rgba_integer(),
    )
    obscuringMaterialColour = Settings.addSetting(
        "obscuringMaterialColour",
        Color(0.100, 0.100, 0.100, 0.5).rgba_integer(),
    )
    grassMaterialColour = Settings.addSetting(
        "grassMaterialColour",
        Color(0.000, 0.600, 0.000, 0.5).rgba_integer(),
    )
    stoneMaterialColour = Settings.addSetting(
        "stoneMaterialColour",
        Color(0.162, 0.216, 0.279, 0.5).rgba_integer(),
    )
    woodMaterialColour = Settings.addSetting(
        "woodMaterialColour",
        Color(0.258, 0.059, 0.007, 0.5).rgba_integer(),
    )
    waterMaterialColour = Settings.addSetting(
        "waterMaterialColour",
        Color(0.000, 0.000, 1.000, 0.5).rgba_integer(),
    )
    nonWalkMaterialColour = Settings.addSetting(
        "nonWalkMaterialColour",
        Color(1.000, 0.000, 0.000, 0.5).rgba_integer(),
    )
    transparentMaterialColour = Settings.addSetting(
        "transparentMaterialColour",
        Color(1.000, 1.000, 1.000, 0.5).rgba_integer(),
    )
    carpetMaterialColour = Settings.addSetting(
        "carpetMaterialColour",
        Color(1.000, 0.000, 1.000, 0.5).rgba_integer(),
    )
    metalMaterialColour = Settings.addSetting(
        "metalMaterialColour",
        Color(0.434, 0.552, 0.730, 0.5).rgba_integer(),
    )
    puddlesMaterialColour = Settings.addSetting(
        "puddlesMaterialColour",
        Color(0.509, 0.474, 0.147, 0.5).rgba_integer(),
    )
    swampMaterialColour = Settings.addSetting(
        "swampMaterialColour",
        Color(0.216, 0.216, 0.000, 0.5).rgba_integer(),
    )
    mudMaterialColour = Settings.addSetting(
        "mudMaterialColour",
        Color(0.091, 0.147, 0.028, 0.5).rgba_integer(),
    )
    leavesMaterialColour = Settings.addSetting(
        "leavesMaterialColour",
        Color(0.000, 0.000, 0.216, 0.5).rgba_integer(),
    )
    doorMaterialColour = Settings.addSetting(
        "doorMaterialColour",
        Color(0.000, 0.000, 0.000, 0.5).rgba_integer(),
    )
    lavaMaterialColour = Settings.addSetting(
        "lavaMaterialColour",
        Color(0.300, 0.000, 0.000, 0.5).rgba_integer(),
    )
    bottomlessPitMaterialColour = Settings.addSetting(
        "bottomlessPitMaterialColour",
        Color(0.000, 0.000, 0.000, 0.5).rgba_integer(),
    )
    deepWaterMaterialColour = Settings.addSetting(
        "deepWaterMaterialColour",
        Color(0.000, 0.000, 0.216, 0.5).rgba_integer(),
    )
    nonWalkGrassMaterialColour = Settings.addSetting(
        "nonWalkGrassMaterialColour",
        Color(0.000, 0.600, 0.000, 0.5).rgba_integer(),
    )
    # endregion

    # region Binds (Controls)
    moveCameraBind = Settings.addSetting(
        "moveCameraBind",
        ({Qt.Key.Key_Control}, {Qt.MouseButton.LeftButton}),
    )
    rotateCameraBind = Settings.addSetting(
        "rotateCameraBind",
        ({Qt.Key.Key_Control}, {Qt.MouseButton.MiddleButton}),
    )
    zoomCameraBind = Settings.addSetting(
        "zoomCameraBind",
        ({Qt.Key.Key_Control}, set()),
    )
    rotateSelectedToPointBind = Settings.addSetting(
        "rotateSelectedToPointBind",
        (set(), {Qt.MouseButton.MiddleButton}),
    )
    moveSelectedBind = Settings.addSetting(
        "moveSelectedBind",
        (set(), {Qt.MouseButton.LeftButton}),
    )
    selectUnderneathBind = Settings.addSetting(
        "selectUnderneathBind",
        (set(), {Qt.MouseButton.LeftButton}),
    )
    deleteSelectedBind = Settings.addSetting(
        "deleteSelectedBind",
        ({Qt.Key.Key_Delete}, None),
    )
    duplicateSelectedBind = Settings.addSetting(
        "duplicateSelectedBind",
        ({Qt.Key.Key_Alt}, {Qt.MouseButton.LeftButton}),
    )
    toggleLockInstancesBind = Settings.addSetting(
        "toggleLockInstancesBind",
        ({Qt.Key.Key_L}, set()),
    )
    # endregion
