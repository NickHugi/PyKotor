from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget

from data.misc import Bind
from data.settings import Settings
from gui.widgets.settings.base import SettingsWidget
from pykotor.common.misc import Color
from utils.misc import QtKey, QtMouse


class GITWidget(SettingsWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
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

    def _setupColourValues(self) -> None:
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            self._registerColour(getattr(self.ui, colorEdit), colorEdit[:-4])

    def _setupBindValues(self) -> None:
        self.ui.moveCameraBindEdit.setBind(self.settings.panCameraBind)
        self.ui.rotateCameraBindEdit.setBind(self.settings.rotateCameraBind)
        self.ui.zoomCameraBindEdit.setBind(self.settings.zoomCameraBind)
        self.ui.selectObjectBindEdit.setBind(self.settings.selectUnderneathBind)
        self.ui.rotateObjectBindEdit.setBind(self.settings.rotateSelectedToPointBind)
        self.ui.deleteObjectBindEdit.setBind(self.settings.deleteSelectedBind)

    def setupValues(self) -> None:
        self._setupColourValues()
        self._setupBindValues()

    def save(self) -> None:
        self.settings.panCameraBind = self.ui.moveCameraBindEdit.bind()
        self.settings.rotateCameraBind = self.ui.rotateCameraBindEdit.bind()
        self.settings.zoomCameraBind = self.ui.zoomCameraBindEdit.bind()
        self.settings.selectUnderneathBind = self.ui.selectObjectBindEdit.bind()
        self.settings.rotateSelectedToPointBind = self.ui.rotateObjectBindEdit.bind()
        self.settings.deleteSelectedBind = self.ui.deleteObjectBindEdit.bind()

        self.settings.undefinedMaterialColour = self.ui.undefinedMaterialColourEdit.color().rgba_integer()
        self.settings.dirtMaterialColour = self.ui.dirtMaterialColourEdit.color().rgba_integer()
        self.settings.obscuringMaterialColour = self.ui.obscuringMaterialColourEdit.color().rgba_integer()
        self.settings.grassMaterialColour = self.ui.grassMaterialColourEdit.color().rgba_integer()
        self.settings.stoneMaterialColour = self.ui.stoneMaterialColourEdit.color().rgba_integer()
        self.settings.woodMaterialColour = self.ui.woodMaterialColourEdit.color().rgba_integer()
        self.settings.waterMaterialColour = self.ui.waterMaterialColourEdit.color().rgba_integer()
        self.settings.nonWalkMaterialColour = self.ui.nonWalkMaterialColourEdit.color().rgba_integer()
        self.settings.transparentMaterialColour = self.ui.transparentMaterialColourEdit.color().rgba_integer()
        self.settings.carpetMaterialColour = self.ui.carpetMaterialColourEdit.color().rgba_integer()
        self.settings.metalMaterialColour = self.ui.metalMaterialColourEdit.color().rgba_integer()
        self.settings.puddlesMaterialColour = self.ui.puddlesMaterialColourEdit.color().rgba_integer()
        self.settings.swampMaterialColour = self.ui.swampMaterialColourEdit.color().rgba_integer()
        self.settings.mudMaterialColour = self.ui.mudMaterialColourEdit.color().rgba_integer()
        self.settings.leavesMaterialColour = self.ui.leavesMaterialColourEdit.color().rgba_integer()
        self.settings.lavaMaterialColour = self.ui.lavaMaterialColourEdit.color().rgba_integer()
        self.settings.bottomlessPitMaterialColour = self.ui.bottomlessPitMaterialColourEdit.color().rgba_integer()
        self.settings.deepWaterMaterialColour = self.ui.deepWaterMaterialColourEdit.color().rgba_integer()
        self.settings.doorMaterialColour = self.ui.doorMaterialColourEdit.color().rgba_integer()
        self.settings.nonWalkGrassMaterialColour = self.ui.nonWalkGrassMaterialColourEdit.color().rgba_integer()

    def resetColours(self) -> None:
        self.settings.resetMaterialColors()
        self._setupColourValues()

    def resetControls(self) -> None:
        self.settings.resetControls()
        self._setupBindValues()


class GITSettings(Settings):
    def __init__(self):
        super().__init__("GITEditor")

    def resetMaterialColors(self) -> None:
        for setting in dir(self):
            if setting.endswith("Colour"):
                self.settings.remove(setting)

    def resetControls(self) -> None:
        for setting in dir(self):
            if setting.endswith("Bind"):
                self.settings.remove(setting)

    # region Strings (Instance Labels)
    creatureLabel = Settings._addSetting(
        "creatureLabel",
        ""
    )
    doorLabel = Settings._addSetting(
        "doorLabel",
        ""
    )
    placeableLabel = Settings._addSetting(
        "placeableLabel",
        ""
    )
    storeLabel = Settings._addSetting(
        "storeLabel",
        ""
    )
    soundLabel = Settings._addSetting(
        "soundLabel",
        ""
    )
    waypointLabel = Settings._addSetting(
        "waypointLabel",
        ""
    )
    cameraLabel = Settings._addSetting(
        "cameraLabel",
        ""
    )
    encounterLabel = Settings._addSetting(
        "encounterLabel",
        ""
    )
    triggerLabel = Settings._addSetting(
        "triggerLabel",
        ""
    )
    # endregion

    # region Ints (Material Colours)
    undefinedMaterialColour = Settings._addSetting(
        "undefinedMaterialColour",
        671088895
    )
    dirtMaterialColour = Settings._addSetting(
        "undefinedMaterialColour",
        4281084972
    )
    obscuringMaterialColour = Settings._addSetting(
        "obscuringMaterialColour",
        671088895
    )
    grassMaterialColour = Settings._addSetting(
        "grassMaterialColour",
        4281084972
    )
    stoneMaterialColour = Settings._addSetting(
        "stoneMaterialColour",
        4281084972
    )
    woodMaterialColour = Settings._addSetting(
        "woodMaterialColour",
        4281084972
    )
    waterMaterialColour = Settings._addSetting(
        "waterMaterialColour",
        4281084972
    )
    nonWalkMaterialColour = Settings._addSetting(
        "nonWalkMaterialColour",
        671088895
    )
    transparentMaterialColour = Settings._addSetting(
        "transparentMaterialColour",
        671088895
    )
    carpetMaterialColour = Settings._addSetting(
        "carpetMaterialColour",
        4281084972
    )
    metalMaterialColour = Settings._addSetting(
        "metalMaterialColour",
        4281084972
    )
    puddlesMaterialColour = Settings._addSetting(
        "puddlesMaterialColour",
        4281084972
    )
    swampMaterialColour = Settings._addSetting(
        "swampMaterialColour",
        4281084972
    )
    mudMaterialColour = Settings._addSetting(
        "mudMaterialColour",
        4281084972
    )
    leavesMaterialColour = Settings._addSetting(
        "leavesMaterialColour",
        4281084972
    )
    doorMaterialColour = Settings._addSetting(
        "doorMaterialColour",
        4281084972
    )
    lavaMaterialColour = Settings._addSetting(
        "lavaMaterialColour",
        671088895
    )
    bottomlessPitMaterialColour = Settings._addSetting(
        "bottomlessPitMaterialColour",
        671088895
    )
    deepWaterMaterialColour = Settings._addSetting(
        "deepWaterMaterialColour",
        671088895
    )
    nonWalkGrassMaterialColour = Settings._addSetting(
        "nonWalkGrassMaterialColour",
        671088895
    )
    # endregion

    # region Binds (Controls)
    panCameraBind = Settings._addSetting(
        "panCameraBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton})
    )
    rotateCameraBind = Settings._addSetting(
        "rotateCameraBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton})
    )
    zoomCameraBind = Settings._addSetting(
        "zoomCameraBind",
        ({QtKey.Key_Control}, None)
    )
    rotateSelectedToPointBind = Settings._addSetting(
        "rotateSelectedToPointBind",
        (set(), {QtMouse.MiddleButton})
    )
    moveSelectedBind = Settings._addSetting(
        "moveSelectedBind",
        (set(), {QtMouse.LeftButton})
    )
    selectUnderneathBind = Settings._addSetting(
        "selectUnderneathBind",
        (set(), {QtMouse.LeftButton})
    )
    deleteSelectedBind = Settings._addSetting(
        "deleteSelectedBind",
        ({QtKey.Key_Delete}, None)
    )
    # endregion
