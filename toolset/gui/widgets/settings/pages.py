from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget
from pykotor.common.misc import Color

from globalsettings import GlobalSettings
from gui.editors.git import GITSettings
from gui.windows.module_designer import ModuleDesignerSettings


class MiscWidget(QWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings = GlobalSettings()

        from toolset.uic.widgets.settings import misc
        self.ui = misc.Ui_Form()
        self.ui.setupUi(self)
        self.setupValues()

    def setupValues(self) -> None:
        self.ui.saveRimCheck.setChecked(not self.settings.disableRIMSaving)
        self.ui.mergeRimCheck.setChecked(self.settings.joinRIMsTogether)
        self.ui.greyRimCheck.setChecked(self.settings.greyRIMText)
        self.ui.tempDirEdit.setText(self.settings.extractPath)
        self.ui.gffEditorCombo.setCurrentIndex(1 if self.settings.gffSpecializedEditors else 0)
        self.ui.ncsToolEdit.setText(self.settings.ncsDecompilerPath)
        self.ui.nssCompEdit.setText(self.settings.nssCompilerPath)

    def save(self) -> None:
        self.settings.disableRIMSaving = not self.ui.saveRimCheck.isChecked()
        self.settings.joinRIMsTogether = self.ui.mergeRimCheck.isChecked()
        self.settings.greyRIMText = self.ui.greyRimCheck.isChecked()
        self.settings.extractPath = self.ui.tempDirEdit.text()
        self.settings.gffSpecializedEditors = bool(self.ui.gffEditorCombo.currentIndex())
        self.settings.ncsDecompilerPath = self.ui.ncsToolEdit.text()
        self.settings.nssCompilerPath = self.ui.nssCompEdit.text()


class InstallationsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.installationsModel: QStandardItemModel = QStandardItemModel()
        self.settings = GlobalSettings()

        from toolset.uic.widgets.settings import installations
        self.ui = installations.Ui_Form()
        self.ui.setupUi(self)
        self.setupValues()
        self.setupSignals()

    def setupValues(self) -> None:
        self.installationsModel.clear()
        for installation in self.settings.installations().values():
            item = QStandardItem(installation.name)
            item.setData({'path': installation.path, 'tsl': installation.tsl})
            self.installationsModel.appendRow(item)

    def setupSignals(self) -> None:
        self.ui.pathList.setModel(self.installationsModel)

        self.ui.addPathButton.clicked.connect(self.addNewInstallation)
        self.ui.removePathButton.clicked.connect(self.removeSelectedInstallation)
        self.ui.pathNameEdit.textEdited.connect(self.updateInstallation)
        self.ui.pathDirEdit.textEdited.connect(self.updateInstallation)
        self.ui.pathTslCheckbox.stateChanged.connect(self.updateInstallation)
        self.ui.pathList.selectionModel().selectionChanged.connect(self.installationSelected)

    def save(self) -> None:
        installations = {}

        for row in range(self.installationsModel.rowCount()):
            item = self.installationsModel.item(row, 0)
            installations[item.text()] = item.data()
            installations[item.text()]["name"] = item.text()

        self.settings.settings.setValue("installations", installations)

    def addNewInstallation(self) -> None:
        item = QStandardItem("New")
        item.setData({'path': '', 'tsl': False})
        self.installationsModel.appendRow(item)

    def removeSelectedInstallation(self) -> None:
        if len(self.ui.pathList.selectedIndexes()) > 0:
            index = self.ui.pathList.selectedIndexes()[0]
            item = self.installationsModel.itemFromIndex(index)
            self.installationsModel.removeRow(item.row())

        if len(self.ui.pathList.selectedIndexes()) == 0:
            self.ui.pathFrame.setEnabled(False)

    def updateInstallation(self) -> None:
        index = self.ui.pathList.selectedIndexes()[0]
        item = self.installationsModel.itemFromIndex(index)

        data = item.data()
        data['path'] = self.ui.pathDirEdit.text()
        data['tsl'] = self.ui.pathTslCheckbox.isChecked()
        item.setData(data)

        item.setText(self.ui.pathNameEdit.text())

    def installationSelected(self) -> None:
        if len(self.ui.pathList.selectedIndexes()) > 0:
            self.ui.pathFrame.setEnabled(True)

            index = self.ui.pathList.selectedIndexes()[0]
            item = self.installationsModel.itemFromIndex(index)

            self.ui.pathNameEdit.setText(item.text())
            self.ui.pathDirEdit.setText(item.data()['path'])
            self.ui.pathTslCheckbox.setChecked(bool(item.data()['tsl']))


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
