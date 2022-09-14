from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget

from data.misc import Bind
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


class GITSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'GITEditor')

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
    @property
    def creatureLabel(self) -> str:
        return self.settings.value("creatureLabel", "", str)

    @creatureLabel.setter
    def creatureLabel(self, value: str) -> None:
        self.settings.setValue('creatureLabel', value)

    @property
    def doorLabel(self) -> str:
        return self.settings.value("doorLabel", "", str)

    @doorLabel.setter
    def doorLabel(self, value: str) -> None:
        self.settings.setValue('doorLabel', value)

    @property
    def placeableLabel(self) -> str:
        return self.settings.value("placeableLabel", "", str)

    @placeableLabel.setter
    def placeableLabel(self, value: str) -> None:
        self.settings.setValue('placeableLabel', value)

    @property
    def storeLabel(self) -> str:
        return self.settings.value("storeLabel", "", str)

    @storeLabel.setter
    def storeLabel(self, value: str) -> None:
        self.settings.setValue('storeLabel', value)

    @property
    def soundLabel(self) -> str:
        return self.settings.value("soundLabel", "", str)

    @soundLabel.setter
    def soundLabel(self, value: str) -> None:
        self.settings.setValue('soundLabel', value)

    @property
    def waypointLabel(self) -> str:
        return self.settings.value("waypointLabel", "", str)

    @waypointLabel.setter
    def waypointLabel(self, value: str) -> None:
        self.settings.setValue('waypointLabel', value)

    @property
    def cameraLabel(self) -> str:
        return self.settings.value("cameraLabel", "", str)

    @cameraLabel.setter
    def cameraLabel(self, value: str) -> None:
        self.settings.setValue('cameraLabel', value)

    @property
    def encounterLabel(self) -> str:
        return self.settings.value("encounterLabel", "", str)

    @encounterLabel.setter
    def encounterLabel(self, value: str) -> None:
        self.settings.setValue('encounterLabel', value)

    @property
    def triggerLabel(self) -> str:
        return self.settings.value("triggerLabel", "", str)

    @triggerLabel.setter
    def triggerLabel(self, value: str) -> None:
        self.settings.setValue('triggerLabel', value)
    # endregion

    # region Ints (Material Colours)
    @property
    def undefinedMaterialColour(self) -> int:
        return self.settings.value("undefinedMaterialColour", 671088895, int)

    @undefinedMaterialColour.setter
    def undefinedMaterialColour(self, value: int) -> None:
        self.settings.setValue('undefinedMaterialColour', value)

    @property
    def dirtMaterialColour(self) -> int:
        return self.settings.value("dirtMaterialColour", 4281084972, int)

    @dirtMaterialColour.setter
    def dirtMaterialColour(self, value: int) -> None:
        self.settings.setValue('dirtMaterialColour', value)

    @property
    def obscuringMaterialColour(self) -> int:
        return self.settings.value("obscuringMaterialColour", 671088895, int)

    @obscuringMaterialColour.setter
    def obscuringMaterialColour(self, value: int) -> None:
        self.settings.setValue('obscuringMaterialColour', value)

    @property
    def grassMaterialColour(self) -> int:
        return self.settings.value("grassMaterialColour", 4281084972, int)

    @grassMaterialColour.setter
    def grassMaterialColour(self, value: int) -> None:
        self.settings.setValue('grassMaterialColour', value)

    @property
    def stoneMaterialColour(self) -> int:
        return self.settings.value("stoneMaterialColour", 4281084972, int)

    @stoneMaterialColour.setter
    def stoneMaterialColour(self, value: int) -> None:
        self.settings.setValue('stoneMaterialColour', value)

    @property
    def woodMaterialColour(self) -> int:
        return self.settings.value("woodMaterialColour", 4281084972, int)

    @woodMaterialColour.setter
    def woodMaterialColour(self, value: int) -> None:
        self.settings.setValue('woodMaterialColour', value)

    @property
    def waterMaterialColour(self) -> int:
        return self.settings.value("waterMaterialColour", 4281084972, int)

    @waterMaterialColour.setter
    def waterMaterialColour(self, value: int) -> None:
        self.settings.setValue('waterMaterialColour', value)

    @property
    def nonWalkMaterialColour(self) -> int:
        return self.settings.value("nonWalkMaterialColour", 671088895, int)

    @nonWalkMaterialColour.setter
    def nonWalkMaterialColour(self, value: int) -> None:
        self.settings.setValue('nonWalkMaterialColour', value)

    @property
    def transparentMaterialColour(self) -> int:
        return self.settings.value("transparentMaterialColour", 671088895, int)

    @transparentMaterialColour.setter
    def transparentMaterialColour(self, value: int) -> None:
        self.settings.setValue('transparentMaterialColour', value)

    @property
    def carpetMaterialColour(self) -> int:
        return self.settings.value("carpetMaterialColour", 4281084972, int)

    @carpetMaterialColour.setter
    def carpetMaterialColour(self, value: int) -> None:
        self.settings.setValue('carpetMaterialColour', value)

    @property
    def metalMaterialColour(self) -> int:
        return self.settings.value("metalMaterialColour", 4281084972, int)

    @metalMaterialColour.setter
    def metalMaterialColour(self, value: int) -> None:
        self.settings.setValue('metalMaterialColour', value)

    @property
    def puddlesMaterialColour(self) -> int:
        return self.settings.value("puddlesMaterialColour", 4281084972, int)

    @puddlesMaterialColour.setter
    def puddlesMaterialColour(self, value: int) -> None:
        self.settings.setValue('puddlesMaterialColour', value)

    @property
    def swampMaterialColour(self) -> int:
        return self.settings.value("swampMaterialColour", 4281084972, int)

    @swampMaterialColour.setter
    def swampMaterialColour(self, value: int) -> None:
        self.settings.setValue('swampMaterialColour', value)

    @property
    def mudMaterialColour(self) -> int:
        return self.settings.value("mudMaterialColour", 4281084972, int)

    @mudMaterialColour.setter
    def mudMaterialColour(self, value: int) -> None:
        self.settings.setValue('mudMaterialColour', value)

    @property
    def leavesMaterialColour(self) -> int:
        return self.settings.value("leavesMaterialColour", 4281084972, int)

    @leavesMaterialColour.setter
    def leavesMaterialColour(self, value: int) -> None:
        self.settings.setValue('leavesMaterialColour', value)

    @property
    def doorMaterialColour(self) -> int:
        return self.settings.value("doorMaterialColour", 4281084972, int)

    @doorMaterialColour.setter
    def doorMaterialColour(self, value: int) -> None:
        self.settings.setValue('doorMaterialColour', value)

    @property
    def lavaMaterialColour(self) -> int:
        return self.settings.value("lavaMaterialColour", 671088895, int)

    @lavaMaterialColour.setter
    def lavaMaterialColour(self, value: int) -> None:
        self.settings.setValue('lavaMaterialColour', value)

    @property
    def bottomlessPitMaterialColour(self) -> int:
        return self.settings.value("bottomlessPitMaterialColour", 671088895, int)

    @bottomlessPitMaterialColour.setter
    def bottomlessPitMaterialColour(self, value: int) -> None:
        self.settings.setValue('bottomlessPitMaterialColour', value)

    @property
    def deepWaterMaterialColour(self) -> int:
        return self.settings.value("deepWaterMaterialColour", 671088895, int)

    @deepWaterMaterialColour.setter
    def deepWaterMaterialColour(self, value: int) -> None:
        self.settings.setValue('deepWaterMaterialColour', value)

    @property
    def nonWalkGrassMaterialColour(self) -> int:
        return self.settings.value("nonWalkGrassMaterialColour", 671088895, int)

    @nonWalkGrassMaterialColour.setter
    def nonWalkGrassMaterialColour(self, value: int) -> None:
        self.settings.setValue('nonWalkGrassMaterialColour', value)
    # endregion

    # region Binds (Controls)
    @property
    def panCameraBind(self) -> Bind:
        return self.settings.value("panCameraBind", ({QtKey.Key_Control}, {QtMouse.LeftButton}))

    @panCameraBind.setter
    def panCameraBind(self, value: Bind) -> None:
        self.settings.setValue('panCameraBind', value)

    @property
    def rotateCameraBind(self) -> Bind:
        return self.settings.value("rotateCameraBind", ({QtKey.Key_Control}, {QtMouse.MiddleButton}))

    @rotateCameraBind.setter
    def rotateCameraBind(self, value: Bind) -> None:
        self.settings.setValue('rotateCameraBind', value)

    @property
    def zoomCameraBind(self) -> Bind:
        return self.settings.value("zoomCameraBind", ({QtKey.Key_Control}, None))

    @zoomCameraBind.setter
    def zoomCameraBind(self, value: Bind) -> None:
        self.settings.setValue('zoomCameraBind', value)

    @property
    def rotateSelectedToPointBind(self) -> Bind:
        return self.settings.value("rotateSelectedToPoint", (set(), {QtMouse.MiddleButton}))

    @rotateSelectedToPointBind.setter
    def rotateSelectedToPointBind(self, value: Bind) -> None:
        self.settings.setValue('rotateSelectedToPoint', value)

    @property
    def moveSelectedBind(self) -> Bind:
        return self.settings.value("moveSelectedBind", (set(), {QtMouse.LeftButton}))

    @moveSelectedBind.setter
    def moveSelectedBind(self, value: Bind) -> None:
        self.settings.setValue('moveSelectedBind', value)

    @property
    def selectUnderneathBind(self) -> Bind:
        return self.settings.value("selectUnderneathBind", (set(), {QtMouse.LeftButton}))

    @selectUnderneathBind.setter
    def selectUnderneathBind(self, value: Bind) -> None:
        self.settings.setValue('selectUnderneathBind', value)

    @property
    def deleteSelectedBind(self) -> Bind:
        return self.settings.value("deleteSelectedBind", ({QtKey.Key_Delete}, None))

    @deleteSelectedBind.setter
    def deleteSelectedBind(self, value: Bind) -> None:
        self.settings.setValue('deleteSelectedBind', value)
    # endregion
