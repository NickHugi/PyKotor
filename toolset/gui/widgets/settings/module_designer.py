from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget

from data.misc import Bind
from utils.misc import QtKey, QtMouse


class ModuleDesignerWidget(QWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings = ModuleDesignerSettings()

        from toolset.uic.widgets.settings import module_designer
        self.ui = module_designer.Ui_Form()
        self.ui.setupUi(self)
        self.setupValues()

        self.ui.controls3dResetButton.clicked.connect(self.resetControls3d)
        self.ui.controls2dResetButton.clicked.connect(self.resetControls2d)

    def _setupBindValues(self) -> None:
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

        self.ui.moveCamera2dBindEdit.setBind(self.settings.moveCamera2dBind)
        self.ui.zoomCamera2dBindEdit.setBind(self.settings.zoomCamera2dBind)
        self.ui.rotateCamera2dBindEdit.setBind(self.settings.rotateCamera2dBind)
        self.ui.selectObject2dBindEdit.setBind(self.settings.selectObject2dBind)
        self.ui.rotateObject2dBindEdit.setBind(self.settings.rotateObject2dBind)
        self.ui.deleteObject2dBindEdit.setBind(self.settings.deleteObject2dBind)

    def setupValues(self) -> None:
        self.ui.fovSpin.setValue(self.settings.fieldOfView)
        self._setupBindValues()

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

    def resetControls3d(self) -> None:
        self.settings.resetControls3d()
        self._setupBindValues()

    def resetControls2d(self) -> None:
        self.settings.resetControls2d()
        self._setupBindValues()


class ModuleDesignerSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'ModuleDesigner')

    def resetControls3d(self) -> None:
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

    # region Binds (Controls - 3D)
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

    # region Binds (Controls - 2D)
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
