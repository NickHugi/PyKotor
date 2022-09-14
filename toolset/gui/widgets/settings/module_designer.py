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

    def _setupBindValues(self) -> None:
        self.ui.moveCameraBindEdit.setBind(self.settings.panCamera3dBind)
        self.ui.rotateCameraBindEdit.setBind(self.settings.rotateCamera3dBind)
        self.ui.zoomCameraBindEdit.setBind(self.settings.zoomCamera3dBind)
        self.ui.moveCameraToSelectionBindEdit.setBind(self.settings.snapCameraToSelected3dBind)
        self.ui.selectObjectBindEdit.setBind(self.settings.selectUnderneath3dBind)
        self.ui.rotateObjectBindEdit.setBind(self.settings.rotateSelected3dBind)
        self.ui.deleteObjectBindEdit.setBind(self.settings.deleteSelected3dBind)

    def setupValues(self) -> None:
        self.ui.fovSpin.setValue(self.settings.fieldOfView)
        self._setupBindValues()

    def save(self) -> None:
        self.settings.fieldOfView = self.ui.fovSpin.value()

        self.settings.panCameraBind = self.ui.moveCameraBindEdit.bind()
        self.settings.rotateCameraBind = self.ui.rotateCameraBindEdit.bind()
        self.settings.zoomCameraBind = self.ui.zoomCameraBindEdit.bind()
        self.settings.selectUnderneathBind = self.ui.selectObjectBindEdit.bind()
        self.settings.rotateSelectedToPointBind = self.ui.rotateObjectBindEdit.bind()
        self.settings.snapCameraToSelected3dBind = self.ui.moveCameraToSelectionBindEdit.bind()
        self.settings.deleteSelectedBind = self.ui.deleteObjectBindEdit.bind()

    def resetControls(self) -> None:
        self.settings.resetControls()
        self._setupBindValues()


class ModuleDesignerSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'ModuleDesigner')

    def resetControls(self) -> None:
        self.settings.remove("panCamera3dBind")
        self.settings.remove("rotateCamera3dBind")
        self.settings.remove("zoomCamera3dBind")
        self.settings.remove("rotateSelected3dBind")
        self.settings.remove("moveSelected3dBind")
        self.settings.remove("selectUnderneath3dBind")
        self.settings.remove("deleteSelected3dBind")

    # region Binds (Controls)
    @property
    def panCamera3dBind(self) -> Bind:
        return self.settings.value("panCamera3dBind", ({QtKey.Key_Control}, {QtMouse.LeftButton}))

    @panCamera3dBind.setter
    def panCamera3dBind(self, value: Bind) -> None:
        self.settings.setValue('panCamera3dBind', value)

    @property
    def rotateCamera3dBind(self) -> Bind:
        return self.settings.value("rotateCamera3dBind", ({QtKey.Key_Control}, {QtMouse.MiddleButton}))

    @rotateCamera3dBind.setter
    def rotateCamera3dBind(self, value: Bind) -> None:
        self.settings.setValue('rotateCamera3dBind', value)

    @property
    def zoomCamera3dBind(self) -> Bind:
        return self.settings.value("zoomCamera3dBind", ({QtKey.Key_Control}, None))

    @zoomCamera3dBind.setter
    def zoomCamera3dBind(self, value: Bind) -> None:
        self.settings.setValue('zoomCamera3dBind', value)

    @property
    def rotateSelected3dBind(self) -> Bind:
        return self.settings.value("rotateSelected3dBind", (set(), {QtMouse.MiddleButton}))

    @rotateSelected3dBind.setter
    def rotateSelected3dBind(self, value: Bind) -> None:
        self.settings.setValue('rotateSelected3dBind', value)

    @property
    def moveSelected3dBind(self) -> Bind:
        return self.settings.value("moveSelected3dBind", (set(), {QtMouse.LeftButton}))

    @moveSelected3dBind.setter
    def moveSelected3dBind(self, value: Bind) -> None:
        self.settings.setValue('moveSelected3dBind', value)

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

    # region Ints
    @property
    def fieldOfView(self) -> int:
        return self.settings.value('fieldOfView', 90, int)

    @fieldOfView.setter
    def fieldOfView(self, value: int) -> None:
        self.settings.setValue('fieldOfView', value)
    # endregion
