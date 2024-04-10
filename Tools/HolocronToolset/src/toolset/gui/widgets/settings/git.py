from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore

from toolset.data.settings import Settings
from toolset.gui.widgets.settings.base import SettingsWidget
from toolset.utils.misc import QtKey, QtMouse

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class GITWidget(SettingsWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        """Initializes the GIT settings widget.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Calls the parent __init__ method
            - Initializes settings object
            - Loads UI from form
            - Sets alpha channel allowed for colour pickers
            - Connects reset buttons to methods
            - Calls setupValues method.
        """
        super().__init__(parent)

        self.settings = GITSettings()

        from toolset.uic.widgets.settings.git import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.undefinedMaterialColourEdit.allowAlpha = True
        self.ui.dirtMaterialColourEdit.allowAlpha = True
        self.ui.obscuringMaterialColourEdit.allowAlpha = True
        self.ui.grassMaterialColourEdit.allowAlpha = True
        self.ui.stoneMaterialColourEdit.allowAlpha = True
        self.ui.woodMaterialColourEdit.allowAlpha = True
        self.ui.waterMaterialColourEdit.allowAlpha = True
        self.ui.nonWalkMaterialColourEdit.allowAlpha = True
        self.ui.transparentMaterialColourEdit.allowAlpha = True
        self.ui.carpetMaterialColourEdit.allowAlpha = True
        self.ui.metalMaterialColourEdit.allowAlpha = True
        self.ui.puddlesMaterialColourEdit.allowAlpha = True
        self.ui.swampMaterialColourEdit.allowAlpha = True
        self.ui.mudMaterialColourEdit.allowAlpha = True
        self.ui.leavesMaterialColourEdit.allowAlpha = True
        self.ui.lavaMaterialColourEdit.allowAlpha = True
        self.ui.bottomlessPitMaterialColourEdit.allowAlpha = True
        self.ui.deepWaterMaterialColourEdit.allowAlpha = True
        self.ui.doorMaterialColourEdit.allowAlpha = True
        self.ui.nonWalkGrassMaterialColourEdit.allowAlpha = True

        self.ui.coloursResetButton.clicked.connect(self.resetColours)
        self.ui.controlsResetButton.clicked.connect(self.resetControls)

        self.setupValues()

    def _setupColourValues(self):
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            self._registerColour(getattr(self.ui, colorEdit), colorEdit[:-4])

    def _setupBindValues(self):
        for bindEdit in [widget for widget in dir(self.ui) if "BindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def setupValues(self):
        self._setupColourValues()
        self._setupBindValues()

    def save(self):
        for widget, bindName in self.binds:
            setattr(self.settings, bindName, widget.bind())
        for widget, colourName in self.colours:
            setattr(self.settings, colourName, widget.color().rgba_integer())

    def resetColours(self):
        self.settings.resetMaterialColors()
        self._setupColourValues()

    def resetControls(self):
        self.settings.resetControls()
        self._setupBindValues()


class GITSettings(Settings):
    def __init__(self):
        super().__init__("GITEditor")

    def resetMaterialColors(self):
        for setting in dir(self):
            if setting.endswith("Colour"):
                self.settings.remove(setting)

    def resetControls(self):
        for setting in dir(self):
            if setting.endswith("Bind"):
                self.settings.remove(setting)

    # region Strings (Instance Labels)
    creatureLabel = Settings.addSetting(
        "creatureLabel",
        "",
    )
    doorLabel = Settings.addSetting(
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
        671088895,
    )
    dirtMaterialColour = Settings.addSetting(
        "dirtMaterialColour",
        4281084972,
    )
    obscuringMaterialColour = Settings.addSetting(
        "obscuringMaterialColour",
        671088895,
    )
    grassMaterialColour = Settings.addSetting(
        "grassMaterialColour",
        4281084972,
    )
    stoneMaterialColour = Settings.addSetting(
        "stoneMaterialColour",
        4281084972,
    )
    woodMaterialColour = Settings.addSetting(
        "woodMaterialColour",
        4281084972,
    )
    waterMaterialColour = Settings.addSetting(
        "waterMaterialColour",
        4281084972,
    )
    nonWalkMaterialColour = Settings.addSetting(
        "nonWalkMaterialColour",
        671088895,
    )
    transparentMaterialColour = Settings.addSetting(
        "transparentMaterialColour",
        671088895,
    )
    carpetMaterialColour = Settings.addSetting(
        "carpetMaterialColour",
        4281084972,
    )
    metalMaterialColour = Settings.addSetting(
        "metalMaterialColour",
        4281084972,
    )
    puddlesMaterialColour = Settings.addSetting(
        "puddlesMaterialColour",
        4281084972,
    )
    swampMaterialColour = Settings.addSetting(
        "swampMaterialColour",
        4281084972,
    )
    mudMaterialColour = Settings.addSetting(
        "mudMaterialColour",
        4281084972,
    )
    leavesMaterialColour = Settings.addSetting(
        "leavesMaterialColour",
        4281084972,
    )
    doorMaterialColour = Settings.addSetting(
        "doorMaterialColour",
        4281084972,
    )
    lavaMaterialColour = Settings.addSetting(
        "lavaMaterialColour",
        671088895,
    )
    bottomlessPitMaterialColour = Settings.addSetting(
        "bottomlessPitMaterialColour",
        671088895,
    )
    deepWaterMaterialColour = Settings.addSetting(
        "deepWaterMaterialColour",
        671088895,
    )
    nonWalkGrassMaterialColour = Settings.addSetting(
        "nonWalkGrassMaterialColour",
        671088895,
    )
    # endregion

    # region Binds (Controls)
    moveCameraBind = Settings.addSetting(
        "moveCameraBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton}),
    )
    rotateCameraBind = Settings.addSetting(
        "rotateCameraBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton}),
    )
    zoomCameraBind = Settings.addSetting(
        "zoomCameraBind",
        ({QtKey.Key_Control}, None),
    )
    rotateSelectedToPointBind = Settings.addSetting(
        "rotateSelectedToPointBind",
        (set(), {QtMouse.MiddleButton}),
    )
    moveSelectedBind = Settings.addSetting(
        "moveSelectedBind",
        (set(), {QtMouse.LeftButton}),
    )
    selectUnderneathBind = Settings.addSetting(
        "selectUnderneathBind",
        (set(), {QtMouse.LeftButton}),
    )
    deleteSelectedBind = Settings.addSetting(
        "deleteSelectedBind",
        ({QtKey.Key_Delete}, None),
    )
    duplicateSelectedBind = Settings.addSetting(
        "duplicateSelectedBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    toggleLockInstancesBind = Settings.addSetting(
        "toggleLockInstancesBind",
        ({QtKey.Key_L}, set()),
    )
    # endregion
