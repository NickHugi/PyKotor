from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget

from globalsettings import GlobalSettings
from tools.module.me_settings import ModuleDesignerSettings


class MiscWidget(QWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings = GlobalSettings()

        from misc.settings import ui_misc_widget
        self.ui = ui_misc_widget.Ui_Form()
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

        from misc.settings import ui_installations_widget
        self.ui = ui_installations_widget.Ui_Form()
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

        from misc.settings import ui_module_editor_widget
        self.ui = ui_module_editor_widget.Ui_Form()
        self.ui.setupUi(self)
        self.setupValues()

    def setupValues(self) -> None:
        self.ui.fovSpin.setValue(self.settings.fieldOfView)

    def save(self) -> None:
        self.settings.fieldOfView = self.ui.fovSpin.value()
