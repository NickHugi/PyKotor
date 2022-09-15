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
        self.ui.moveCamera3dBindEdit.setBind(self.settings.panCameraXY3dBind)
        self.ui.moveCameraZ3dBindEdit.setBind(self.settings.panCameraZ3dBind)
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

        self.settings.panCameraXY3dBind = self.ui.moveCamera3dBindEdit.bind()
        self.settings.panCameraZ3dBind = self.ui.moveCameraZ3dBindEdit.bind()
        self.settings.rotateCameraBind = self.ui.rotateCamera3dBindEdit.bind()
        self.settings.zoomCameraBind = self.ui.zoomCamera3dBindEdit.bind()
        self.settings.zoomCameraMMBind = self.ui.zoomCameraMM3dBindEdit.bind()
        self.settings.selectUnderneathBind = self.ui.selectObject3dBindEdit.bind()
        self.settings.moveSelectedXY3dBind = self.ui.moveObjectXY3dBindEdit.bind()
        self.settings.moveSelectedZ3dBind = self.ui.moveObjectZ3dBindEdit.bind()
        self.settings.rotateSelectedToPointBind = self.ui.rotateObject3dBindEdit.bind()
        self.settings.snapCameraToSelected3dBind = self.ui.moveCameraToSelection3dBindEdit.bind()
        self.settings.deleteSelectedBind = self.ui.deleteObject3dBindEdit.bind()

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
    def panCameraXY3dBind(self) -> Bind:
        return self.settings.value("panCameraXY3dBind", ({QtKey.Key_Control}, {QtMouse.LeftButton}))

    @panCameraXY3dBind.setter
    def panCameraXY3dBind(self, value: Bind) -> None:
        self.settings.setValue('panCameraXY3dBind', value)

    @property
    def panCameraZ3dBind(self) -> Bind:
        return self.settings.value("panCameraZ3dBind", ({QtKey.Key_Control}, set()))

    @panCameraZ3dBind.setter
    def panCameraZ3dBind(self, value: Bind) -> None:
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
    # endregion

    # region Ints
    @property
    def fieldOfView(self) -> int:
        return self.settings.value('fieldOfView', 90, int)

    @fieldOfView.setter
    def fieldOfView(self, value: int) -> None:
        self.settings.setValue('fieldOfView', value)
    # endregion
