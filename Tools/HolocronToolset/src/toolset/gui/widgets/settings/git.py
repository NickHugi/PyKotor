from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from toolset.data.settings import Settings
from toolset.gui.widgets.settings.base import SettingsWidget
from toolset.utils.misc import QtKey, QtMouse


class GITWidget(SettingsWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        """Initializes the GIT settings widget
        Args:
            parent (QWidget): The parent widget
        Returns:
            None
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

        from toolset.uic.widgets.settings.git import Ui_Form
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
    creatureLabel = Settings._addSetting(
        "creatureLabel",
        "",
    )
    doorLabel = Settings._addSetting(
        "doorLabel",
        "",
    )
    placeableLabel = Settings._addSetting(
        "placeableLabel",
        "",
    )
    storeLabel = Settings._addSetting(
        "storeLabel",
        "",
    )
    soundLabel = Settings._addSetting(
        "soundLabel",
        "",
    )
    waypointLabel = Settings._addSetting(
        "waypointLabel",
        "",
    )
    cameraLabel = Settings._addSetting(
        "cameraLabel",
        "",
    )
    encounterLabel = Settings._addSetting(
        "encounterLabel",
        "",
    )
    triggerLabel = Settings._addSetting(
        "triggerLabel",
        "",
    )
    # endregion

    # region Ints (Material Colours)
    undefinedMaterialColour = Settings._addSetting(
        "undefinedMaterialColour",
        671088895,
    )
    dirtMaterialColour = Settings._addSetting(
        "dirtMaterialColour",
        4281084972,
    )
    obscuringMaterialColour = Settings._addSetting(
        "obscuringMaterialColour",
        671088895,
    )
    grassMaterialColour = Settings._addSetting(
        "grassMaterialColour",
        4281084972,
    )
    stoneMaterialColour = Settings._addSetting(
        "stoneMaterialColour",
        4281084972,
    )
    woodMaterialColour = Settings._addSetting(
        "woodMaterialColour",
        4281084972,
    )
    waterMaterialColour = Settings._addSetting(
        "waterMaterialColour",
        4281084972,
    )
    nonWalkMaterialColour = Settings._addSetting(
        "nonWalkMaterialColour",
        671088895,
    )
    transparentMaterialColour = Settings._addSetting(
        "transparentMaterialColour",
        671088895,
    )
    carpetMaterialColour = Settings._addSetting(
        "carpetMaterialColour",
        4281084972,
    )
    metalMaterialColour = Settings._addSetting(
        "metalMaterialColour",
        4281084972,
    )
    puddlesMaterialColour = Settings._addSetting(
        "puddlesMaterialColour",
        4281084972,
    )
    swampMaterialColour = Settings._addSetting(
        "swampMaterialColour",
        4281084972,
    )
    mudMaterialColour = Settings._addSetting(
        "mudMaterialColour",
        4281084972,
    )
    leavesMaterialColour = Settings._addSetting(
        "leavesMaterialColour",
        4281084972,
    )
    doorMaterialColour = Settings._addSetting(
        "doorMaterialColour",
        4281084972,
    )
    lavaMaterialColour = Settings._addSetting(
        "lavaMaterialColour",
        671088895,
    )
    bottomlessPitMaterialColour = Settings._addSetting(
        "bottomlessPitMaterialColour",
        671088895,
    )
    deepWaterMaterialColour = Settings._addSetting(
        "deepWaterMaterialColour",
        671088895,
    )
    nonWalkGrassMaterialColour = Settings._addSetting(
        "nonWalkGrassMaterialColour",
        671088895,
    )
    # endregion

    # region Binds (Controls)
    moveCameraBind = Settings._addSetting(
        "moveCameraBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton}),
    )
    rotateCameraBind = Settings._addSetting(
        "rotateCameraBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton}),
    )
    zoomCameraBind = Settings._addSetting(
        "zoomCameraBind",
        ({QtKey.Key_Control}, None),
    )
    rotateSelectedToPointBind = Settings._addSetting(
        "rotateSelectedToPointBind",
        (set(), {QtMouse.MiddleButton}),
    )
    moveSelectedBind = Settings._addSetting(
        "moveSelectedBind",
        (set(), {QtMouse.LeftButton}),
    )
    selectUnderneathBind = Settings._addSetting(
        "selectUnderneathBind",
        (set(), {QtMouse.LeftButton}),
    )
    deleteSelectedBind = Settings._addSetting(
        "deleteSelectedBind",
        ({QtKey.Key_Delete}, None),
    )
    duplicateSelectedBind = Settings._addSetting(
        "duplicateSelectedBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    toggleLockInstancesBind = Settings._addSetting(
        "toggleLockInstancesBind",
        ({QtKey.Key_L}, set()),
    )
    # endregion
