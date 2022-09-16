from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget

from data.misc import Bind
from pykotor.common.misc import Color
from utils.misc import QtKey, QtMouse


class ModuleDesignerWidget(QWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings = ModuleDesignerSettings()

        from toolset.uic.widgets.settings import module_designer
        self.ui = module_designer.Ui_Form()
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

        self.ui.controls3dResetButton.clicked.connect(self.resetControls3d)
        self.ui.controls2dResetButton.clicked.connect(self.resetControls2d)
        self.ui.coloursResetButton.clicked.connect(self.resetColours)

        self.setupValues()

    def _setupControlValues(self) -> None:
        self.ui.moveCameraSensitivity3dEdit.setValue(self.settings.moveCameraSensitivity3d)
        self.ui.rotateCameraSensitivity3dEdit.setValue(self.settings.rotateCameraSensitivity3d)
        self.ui.zoomCameraSensitivity3dEdit.setValue(self.settings.zoomCameraSensitivity3d)

        self.ui.moveCamera3dBindEdit.setBind(self.settings.moveCameraXY3dBind)
        self.ui.moveCameraZ3dBindEdit.setBind(self.settings.moveCameraZ3dBind)
        self.ui.rotateCamera3dBindEdit.setBind(self.settings.rotateCamera3dBind)
        self.ui.zoomCamera3dBindEdit.setBind(self.settings.zoomCamera3dBind)
        self.ui.zoomCameraMM3dBindEdit.setBind(self.settings.zoomCamera3dMMBind)
        self.ui.moveCameraToSelection3dBindEdit.setBind(self.settings.snapCameraToSelected3dBind)
        self.ui.selectObject3dBindEdit.setBind(self.settings.selectUnderneath3dBind)
        self.ui.moveObjectXY3dBindEdit.setBind(self.settings.moveSelectedXY3dBind)
        self.ui.moveObjectZ3dBindEdit.setBind(self.settings.moveSelectedZ3dBind)
        self.ui.rotateObject3dBindEdit.setBind(self.settings.rotateSelected3dBind)
        self.ui.deleteObject3dBindEdit.setBind(self.settings.deleteSelected3dBind)

        self.ui.moveCameraSensitivity2dEdit.setValue(self.settings.moveCameraSensitivity2d)
        self.ui.rotateCameraSensitivity2dEdit.setValue(self.settings.rotateCameraSensitivity2d)
        self.ui.zoomCameraSensitivity2dEdit.setValue(self.settings.zoomCameraSensitivity2d)

        self.ui.moveCamera2dBindEdit.setBind(self.settings.moveCamera2dBind)
        self.ui.zoomCamera2dBindEdit.setBind(self.settings.zoomCamera2dBind)
        self.ui.rotateCamera2dBindEdit.setBind(self.settings.rotateCamera2dBind)
        self.ui.selectObject2dBindEdit.setBind(self.settings.selectObject2dBind)
        self.ui.rotateObject2dBindEdit.setBind(self.settings.rotateObject2dBind)
        self.ui.deleteObject2dBindEdit.setBind(self.settings.deleteObject2dBind)

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

    def setupValues(self) -> None:
        self.ui.fovSpin.setValue(self.settings.fieldOfView)
        self._setupControlValues()
        self._setupColourValues()

    def save(self) -> None:
        self.settings.fieldOfView = self.ui.fovSpin.value()

        self.settings.moveCameraXY3dBind = self.ui.moveCamera3dBindEdit.bind()
        self.settings.moveCameraZ3dBind = self.ui.moveCameraZ3dBindEdit.bind()
        self.settings.rotateCamera3dBind = self.ui.rotateCamera3dBindEdit.bind()
        self.settings.zoomCamera3dBind = self.ui.zoomCamera3dBindEdit.bind()
        self.settings.zoomCamera3dMMBind = self.ui.zoomCameraMM3dBindEdit.bind()
        self.settings.selectUnderneath3dBind = self.ui.selectObject3dBindEdit.bind()
        self.settings.moveSelectedXY3dBind = self.ui.moveObjectXY3dBindEdit.bind()
        self.settings.moveSelectedZ3dBind = self.ui.moveObjectZ3dBindEdit.bind()
        self.settings.rotateSelected3dBind = self.ui.rotateObject3dBindEdit.bind()
        self.settings.snapCameraToSelected3dBind = self.ui.moveCameraToSelection3dBindEdit.bind()
        self.settings.deleteSelected3dBind = self.ui.deleteObject3dBindEdit.bind()

        self.settings.moveCamera2dBind = self.ui.moveCamera2dBindEdit.bind()
        self.settings.zoomCamera2dBind = self.ui.zoomCamera2dBindEdit.bind()
        self.settings.rotateCamera2dBind = self.ui.rotateCamera2dBindEdit.bind()
        self.settings.selectObject2dBind = self.ui.selectObject2dBindEdit.bind()
        self.settings.rotateObject2dBind = self.ui.rotateObject2dBindEdit.bind()
        self.settings.deleteObject2dBind = self.ui.deleteObject2dBindEdit.bind()

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

    def resetControls3d(self) -> None:
        self.settings.resetControls3d()
        self._setupControlValues()

    def resetControls2d(self) -> None:
        self.settings.resetControls2d()
        self._setupControlValues()

    def resetColours(self) -> None:
        self.settings.resetMaterialColors()
        self._setupColourValues()


class ModuleDesignerSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'ModuleDesigner')

    def resetControls3d(self) -> None:
        self.settings.remove("moveCameraSensitivity3d")
        self.settings.remove("rotateCameraSensitivity3d")
        self.settings.remove("zoomCameraSensitivity3d")
        self.settings.remove("panCameraXY3dBind")
        self.settings.remove("panCameraZ3dBind")
        self.settings.remove("rotateCamera3dBind")
        self.settings.remove("zoomCamera3dBind")
        self.settings.remove("zoomCamera3dMMBind")
        self.settings.remove("rotateSelected3dBind")
        self.settings.remove("moveSelectedXY3dBind")
        self.settings.remove("moveSelectedZ3dBind")
        self.settings.remove("selectUnderneath3dBind")
        self.settings.remove("snapCameraToSelected3dBind")
        self.settings.remove("deleteSelected3dBind")

    def resetControls2d(self) -> None:
        self.settings.remove("moveCamera2dBind")
        self.settings.remove("zoomCamera2dBind")
        self.settings.remove("rotateCamera2dBind")
        self.settings.remove("selectObject2dBind")
        self.settings.remove("moveObject2dBind")
        self.settings.remove("rotateObject2dBind")
        self.settings.remove("deleteObject2dBind")

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

    # region Int/Binds (Controls - 3D)
    @property
    def moveCameraSensitivity3d(self) -> int:
        return self.settings.value("moveCameraSensitivity3d", 100)

    @moveCameraSensitivity3d.setter
    def moveCameraSensitivity3d(self, value: int) -> None:
        self.settings.setValue('moveCameraSensitivity3d', value)

    @property
    def rotateCameraSensitivity3d(self) -> int:
        return self.settings.value("rotateCameraSensitivity3d", 100)

    @rotateCameraSensitivity3d.setter
    def rotateCameraSensitivity3d(self, value: int) -> None:
        self.settings.setValue('rotateCameraSensitivity3d', value)

    @property
    def zoomCameraSensitivity3d(self) -> int:
        return self.settings.value("zoomCameraSensitivity3d", 100)

    @zoomCameraSensitivity3d.setter
    def zoomCameraSensitivity3d(self, value: int) -> None:
        self.settings.setValue('zoomCameraSensitivity3d', value)

    ##############################

    @property
    def moveCameraXY3dBind(self) -> Bind:
        return self.settings.value("panCameraXY3dBind", ({QtKey.Key_Control}, {QtMouse.LeftButton}))

    @moveCameraXY3dBind.setter
    def moveCameraXY3dBind(self, value: Bind) -> None:
        self.settings.setValue('panCameraXY3dBind', value)

    @property
    def moveCameraZ3dBind(self) -> Bind:
        return self.settings.value("panCameraZ3dBind", ({QtKey.Key_Control}, set()))

    @moveCameraZ3dBind.setter
    def moveCameraZ3dBind(self, value: Bind) -> None:
        self.settings.setValue('panCameraZ3dBind', value)

    @property
    def rotateCamera3dBind(self) -> Bind:
        return self.settings.value("rotateCamera3dBind", ({QtKey.Key_Control}, {QtMouse.MiddleButton}))

    @rotateCamera3dBind.setter
    def rotateCamera3dBind(self, value: Bind) -> None:
        self.settings.setValue('rotateCamera3dBind', value)

    @property
    def zoomCamera3dBind(self) -> Bind:
        return self.settings.value("zoomCamera3dBind", (set(), None))

    @zoomCamera3dBind.setter
    def zoomCamera3dBind(self, value: Bind) -> None:
        self.settings.setValue('zoomCamera3dBind', value)

    @property
    def zoomCamera3dMMBind(self) -> Bind:
        return self.settings.value("zoomCamera3dMMBind", ({QtKey.Key_Control}, {QtMouse.RightButton}))

    @zoomCamera3dMMBind.setter
    def zoomCamera3dMMBind(self, value: Bind) -> None:
        self.settings.setValue('zoomCamera3dMMBind', value)

    @property
    def rotateSelected3dBind(self) -> Bind:
        return self.settings.value("rotateSelected3dBind", (set(), {QtMouse.MiddleButton}))

    @rotateSelected3dBind.setter
    def rotateSelected3dBind(self, value: Bind) -> None:
        self.settings.setValue('rotateSelected3dBind', value)

    @property
    def moveSelectedXY3dBind(self) -> Bind:
        return self.settings.value("moveSelectedXY3dBind", (set(), {QtMouse.LeftButton}))

    @moveSelectedXY3dBind.setter
    def moveSelectedXY3dBind(self, value: Bind) -> None:
        self.settings.setValue('moveSelectedXY3dBind', value)

    @property
    def moveSelectedZ3dBind(self) -> Bind:
        return self.settings.value("moveSelectedZ3dBind", ({QtKey.Key_Shift}, {QtMouse.LeftButton}))

    @moveSelectedZ3dBind.setter
    def moveSelectedZ3dBind(self, value: Bind) -> None:
        self.settings.setValue('moveSelectedZ3dBind', value)

    @property
    def selectUnderneath3dBind(self) -> Bind:
        return self.settings.value("selectUnderneath3dBind", (set(), {QtMouse.LeftButton}))

    @selectUnderneath3dBind.setter
    def selectUnderneath3dBind(self, value: Bind) -> None:
        self.settings.setValue('selectUnderneath3dBind', value)

    @property
    def snapCameraToSelected3dBind(self) -> Bind:
        return self.settings.value("snapCameraToSelected3dBind", ({QtKey.Key_Z}, None))

    @snapCameraToSelected3dBind.setter
    def snapCameraToSelected3dBind(self, value: Bind) -> None:
        self.settings.setValue('snapCameraToSelected3dBind', value)

    @property
    def deleteSelected3dBind(self) -> Bind:
        return self.settings.value("deleteSelected3dBind", ({QtKey.Key_Delete}, None))

    @deleteSelected3dBind.setter
    def deleteSelected3dBind(self, value: Bind) -> None:
        self.settings.setValue('deleteSelected3dBind', value)
    # endregion

    # region Int/Binds (Controls - 2D)
    @property
    def moveCameraSensitivity2d(self) -> int:
        return self.settings.value("moveCameraSensitivity2d", 100)

    @moveCameraSensitivity2d.setter
    def moveCameraSensitivity2d(self, value: int) -> None:
        self.settings.setValue('moveCameraSensitivity2d', value)

    @property
    def rotateCameraSensitivity2d(self) -> int:
        return self.settings.value("rotateCameraSensitivity2d", 100)

    @rotateCameraSensitivity2d.setter
    def rotateCameraSensitivity2d(self, value: int) -> None:
        self.settings.setValue('rotateCameraSensitivity2d', value)

    @property
    def zoomCameraSensitivity2d(self) -> int:
        return self.settings.value("zoomCameraSensitivity2d", 100)

    @zoomCameraSensitivity2d.setter
    def zoomCameraSensitivity2d(self, value: int) -> None:
        self.settings.setValue('zoomCameraSensitivity2d', value)

    ##############################

    @property
    def moveCamera2dBind(self) -> Bind:
        return self.settings.value("moveCamera2dBind", ({QtKey.Key_Control}, {QtMouse.LeftButton}))

    @moveCamera2dBind.setter
    def moveCamera2dBind(self, value: Bind) -> None:
        self.settings.setValue('moveCamera2dBind', value)

    @property
    def zoomCamera2dBind(self) -> Bind:
        return self.settings.value("zoomCamera2dBind", ({QtKey.Key_Control}, set()))

    @zoomCamera2dBind.setter
    def zoomCamera2dBind(self, value: Bind) -> None:
        self.settings.setValue('zoomCamera2dBind', value)

    @property
    def rotateCamera2dBind(self) -> Bind:
        return self.settings.value("rotateCamera2dBind", ({QtKey.Key_Control}, {QtMouse.MiddleButton}))

    @rotateCamera2dBind.setter
    def rotateCamera2dBind(self, value: Bind) -> None:
        self.settings.setValue('rotateCamera2dBind', value)

    @property
    def selectObject2dBind(self) -> Bind:
        return self.settings.value("selectObject2dBind", (set(), {QtMouse.LeftButton}))

    @selectObject2dBind.setter
    def selectObject2dBind(self, value: Bind) -> None:
        self.settings.setValue('selectObject2dBind', value)

    @property
    def moveObject2dBind(self) -> Bind:
        return self.settings.value("moveObject2dBind", (set(), {QtMouse.LeftButton}))

    @moveObject2dBind.setter
    def moveObject2dBind(self, value: Bind) -> None:
        self.settings.setValue('moveObject2dBind', value)

    @property
    def rotateObject2dBind(self) -> Bind:
        return self.settings.value("rotateObject2dBind", (set(), {QtMouse.MiddleButton}))

    @rotateObject2dBind.setter
    def rotateObject2dBind(self, value: Bind) -> None:
        self.settings.setValue('rotateObject2dBind', value)

    @property
    def deleteObject2dBind(self) -> Bind:
        return self.settings.value("deleteObject2dBind", ({QtKey.Key_Delete}, set()))

    @deleteObject2dBind.setter
    def deleteObject2dBind(self, value: Bind) -> None:
        self.settings.setValue('deleteObject2dBind', value)

    @property
    def snapCameraToSelected2dBind(self) -> Bind:
        return self.settings.value("snapCameraToSelected2dBind", ({QtKey.Key_Z}, set()))

    @snapCameraToSelected2dBind.setter
    def snapCameraToSelected2dBind(self, value: Bind) -> None:
        self.settings.setValue('snapCameraToSelected2dBind', value)
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

    # region Ints
    @property
    def fieldOfView(self) -> int:
        return self.settings.value('fieldOfView', 90, int)

    @fieldOfView.setter
    def fieldOfView(self, value: int) -> None:
        self.settings.setValue('fieldOfView', value)
    # endregion
