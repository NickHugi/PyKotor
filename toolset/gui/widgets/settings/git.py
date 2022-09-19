from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget

from data.misc import Bind
from data.settings import Settings
from pykotor.common.misc import Color
from utils.misc import QtKey, QtMouse


class GITWidget(QWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings = GITSettings()

        from toolset.uic.widgets.settings.git import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.undefinedColorEdit.allowAlpha = True
        self.ui.dirtColorEdit.allowAlpha = True
        self.ui.obscuringColorEdit.allowAlpha = True
        self.ui.grassColorEdit.allowAlpha = True
        self.ui.stoneColorEdit.allowAlpha = True
        self.ui.woodColorEdit.allowAlpha = True
        self.ui.waterColorEdit.allowAlpha = True
        self.ui.nonWalkColorEdit.allowAlpha = True
        self.ui.transparentColorEdit.allowAlpha = True
        self.ui.carpetColorEdit.allowAlpha = True
        self.ui.metalColorEdit.allowAlpha = True
        self.ui.puddlesColorEdit.allowAlpha = True
        self.ui.swampColorEdit.allowAlpha = True
        self.ui.mudColorEdit.allowAlpha = True
        self.ui.leavesColorEdit.allowAlpha = True
        self.ui.lavaColorEdit.allowAlpha = True
        self.ui.bottomlessPitColorEdit.allowAlpha = True
        self.ui.deepWaterColorEdit.allowAlpha = True
        self.ui.doorColorEdit.allowAlpha = True
        self.ui.nonWalkGrassColorEdit.allowAlpha = True

        self.ui.coloursResetButton.clicked.connect(self.resetColours)
        self.ui.controlsResetButton.clicked.connect(self.resetControls)

        self.setupValues()

    def _setupColourValues(self) -> None:
        self.ui.undefinedColorEdit.setColor(Color.from_rgba_integer(self.settings.undefinedMaterialColour))
        self.ui.dirtColorEdit.setColor(Color.from_rgba_integer(self.settings.dirtMaterialColour))
        self.ui.obscuringColorEdit.setColor(Color.from_rgba_integer(self.settings.obscuringMaterialColour))
        self.ui.grassColorEdit.setColor(Color.from_rgba_integer(self.settings.grassMaterialColour))
        self.ui.stoneColorEdit.setColor(Color.from_rgba_integer(self.settings.stoneMaterialColour))
        self.ui.woodColorEdit.setColor(Color.from_rgba_integer(self.settings.woodMaterialColour))
        self.ui.waterColorEdit.setColor(Color.from_rgba_integer(self.settings.waterMaterialColour))
        self.ui.nonWalkColorEdit.setColor(Color.from_rgba_integer(self.settings.nonWalkMaterialColour))
        self.ui.transparentColorEdit.setColor(Color.from_rgba_integer(self.settings.transparentMaterialColour))
        self.ui.carpetColorEdit.setColor(Color.from_rgba_integer(self.settings.carpetMaterialColour))
        self.ui.metalColorEdit.setColor(Color.from_rgba_integer(self.settings.metalMaterialColour))
        self.ui.puddlesColorEdit.setColor(Color.from_rgba_integer(self.settings.puddlesMaterialColour))
        self.ui.swampColorEdit.setColor(Color.from_rgba_integer(self.settings.swampMaterialColour))
        self.ui.mudColorEdit.setColor(Color.from_rgba_integer(self.settings.mudMaterialColour))
        self.ui.leavesColorEdit.setColor(Color.from_rgba_integer(self.settings.leavesMaterialColour))
        self.ui.lavaColorEdit.setColor(Color.from_rgba_integer(self.settings.lavaMaterialColour))
        self.ui.bottomlessPitColorEdit.setColor(Color.from_rgba_integer(self.settings.bottomlessPitMaterialColour))
        self.ui.deepWaterColorEdit.setColor(Color.from_rgba_integer(self.settings.deepWaterMaterialColour))
        self.ui.doorColorEdit.setColor(Color.from_rgba_integer(self.settings.doorMaterialColour))
        self.ui.nonWalkGrassColorEdit.setColor(Color.from_rgba_integer(self.settings.nonWalkGrassMaterialColour))

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

        self.settings.undefinedMaterialColour = self.ui.undefinedColorEdit.color().rgba_integer()
        self.settings.dirtMaterialColour = self.ui.dirtColorEdit.color().rgba_integer()
        self.settings.obscuringMaterialColour = self.ui.obscuringColorEdit.color().rgba_integer()
        self.settings.grassMaterialColour = self.ui.grassColorEdit.color().rgba_integer()
        self.settings.stoneMaterialColour = self.ui.stoneColorEdit.color().rgba_integer()
        self.settings.woodMaterialColour = self.ui.woodColorEdit.color().rgba_integer()
        self.settings.waterMaterialColour = self.ui.waterColorEdit.color().rgba_integer()
        self.settings.nonWalkMaterialColour = self.ui.nonWalkColorEdit.color().rgba_integer()
        self.settings.transparentMaterialColour = self.ui.transparentColorEdit.color().rgba_integer()
        self.settings.carpetMaterialColour = self.ui.carpetColorEdit.color().rgba_integer()
        self.settings.metalMaterialColour = self.ui.metalColorEdit.color().rgba_integer()
        self.settings.puddlesMaterialColour = self.ui.puddlesColorEdit.color().rgba_integer()
        self.settings.swampMaterialColour = self.ui.swampColorEdit.color().rgba_integer()
        self.settings.mudMaterialColour = self.ui.mudColorEdit.color().rgba_integer()
        self.settings.leavesMaterialColour = self.ui.leavesColorEdit.color().rgba_integer()
        self.settings.lavaMaterialColour = self.ui.lavaColorEdit.color().rgba_integer()
        self.settings.bottomlessPitMaterialColour = self.ui.bottomlessPitColorEdit.color().rgba_integer()
        self.settings.deepWaterMaterialColour = self.ui.deepWaterColorEdit.color().rgba_integer()
        self.settings.doorMaterialColour = self.ui.doorColorEdit.color().rgba_integer()
        self.settings.nonWalkGrassMaterialColour = self.ui.nonWalkGrassColorEdit.color().rgba_integer()

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
        self.settings.remove("undefinedMaterialColour")
        self.settings.remove("dirtMaterialColour")
        self.settings.remove("obscuringMaterialColour")
        self.settings.remove("grassMaterialColour")
        self.settings.remove("stoneMaterialColour")
        self.settings.remove("woodMaterialColour")
        self.settings.remove("waterMaterialColour")
        self.settings.remove("nonWalkMaterialColour")
        self.settings.remove("transparentMaterialColour")
        self.settings.remove("carpetMaterialColour")
        self.settings.remove("metalMaterialColour")
        self.settings.remove("puddlesMaterialColour")
        self.settings.remove("swampMaterialColour")
        self.settings.remove("mudMaterialColour")
        self.settings.remove("leavesMaterialColour")
        self.settings.remove("doorMaterialColour")
        self.settings.remove("lavaMaterialColour")
        self.settings.remove("bottomlessPitMaterialColour")
        self.settings.remove("deepWaterMaterialColour")
        self.settings.remove("nonWalkGrassMaterialColour")

    def resetControls(self) -> None:
        self.settings.remove("panCameraBind")
        self.settings.remove("rotateCameraBind")
        self.settings.remove("zoomCameraBind")
        self.settings.remove("rotateSelectedToPointBind")
        self.settings.remove("moveSelectedBind")
        self.settings.remove("selectUnderneathBind")
        self.settings.remove("deleteSelectedBind")

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
