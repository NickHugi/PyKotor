from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog

from data.configuration import Configuration, InstallationConfig
from misc import settings_ui


class Settings(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = settings_ui.Ui_Dialog()
        self.ui.setupUi(self)

        self.applied: bool = False
        self.config: Configuration = Configuration()

        self.pathsModel: QStandardItemModel = QStandardItemModel()
        self.ui.pathList.setModel(self.pathsModel)
        self.ui.pathList.selectionModel().selectionChanged.connect(self.pathSelected)
        self.ui.pathNameEdit.editingFinished.connect(self.pathUpdated)
        self.ui.pathDirEdit.editingFinished.connect(self.pathUpdated)
        self.ui.pathTslCheckbox.clicked.connect(self.pathUpdated)
        self.ui.addPathButton.clicked.connect(self.addPath)
        self.ui.removePathButton.clicked.connect(self.removePath)

        self.ui.gffToolCombo.currentIndexChanged.connect(self.toolComboChanged)
        self.ui.twodaToolCombo.currentIndexChanged.connect(self.toolComboChanged)
        self.ui.dlgToolCombo.currentIndexChanged.connect(self.toolComboChanged)
        self.ui.tlkToolCombo.currentIndexChanged.connect(self.toolComboChanged)
        self.ui.nssToolCombo.currentIndexChanged.connect(self.toolComboChanged)
        self.ui.txtToolCombo.currentIndexChanged.connect(self.toolComboChanged)

        self.loadPaths()
        self.loadTools()
        self.loadMisc()

        self.ui.okButton.clicked.connect(self.ok)
        self.ui.applyButton.clicked.connect(self.apply)
        self.ui.cancelButton.clicked.connect(self.cancel)

    def ok(self) -> None:
        self.apply()
        self.accept()

    def apply(self) -> None:
        """
        Updates the user settings from values in the dialog.
        """
        self.applied = True

        self.config.installations = []
        for i in range(self.pathsModel.rowCount()):
            item = self.pathsModel.item(i, 0)
            installation = InstallationConfig(item.text(), item.data()['path'], item.data()['tsl'])
            self.config.installations.append(installation)

        self.config.gffEditorPath = self.ui.gffToolEdit.text()
        self.config.twodaEditorPath = self.ui.twodaToolEdit.text()
        self.config.dlgEditorPath = self.ui.dlgToolEdit.text()
        self.config.tlkEditorPath = self.ui.tlkToolEdit.text()
        self.config.txtEditorPath = self.ui.txtToolEdit.text()
        self.config.nssEditorPath = self.ui.nssToolEdit.text()
        self.config.gffSpecializedEditors = self.ui.utxToolCombo.currentIndex() == 1

        self.config.nssCompilerPath = self.ui.nssCompToolEdit.text()
        self.config.ncsDecompilerPath = self.ui.ncsToolEdit.text()

        self.config.extractPath = self.ui.tempMiscEdit.text()
        self.config.mdlAllowDecompile = self.ui.experimentalMdlCheckbox.isChecked()
        self.config.erfExternalEditors = self.ui.experimentalExternalCheckbox.isChecked()
        self.config.showModuleNames = self.ui.showModuleNameCheckbox.isChecked()

        self.config.save()

    def cancel(self) -> None:
        """
        Any changes that are not applied are forgotten. Closes the dialog.
        """
        if self.applied:
            self.accept()
        else:
            self.reject()

    def pathSelected(self) -> None:
        if len(self.ui.pathList.selectedIndexes()) > 0:
            self.ui.pathFrame.setEnabled(True)

            index = self.ui.pathList.selectedIndexes()[0]
            item = self.pathsModel.itemFromIndex(index)

            self.ui.pathNameEdit.setText(item.text())
            self.ui.pathDirEdit.setText(item.data()['path'])
            self.ui.pathTslCheckbox.setChecked(bool(item.data()['tsl']))

    def pathUpdated(self) -> None:
        index = self.ui.pathList.selectedIndexes()[0]
        item = self.pathsModel.itemFromIndex(index)

        data = item.data()
        data['path'] = self.ui.pathDirEdit.text()
        data['tsl'] = self.ui.pathTslCheckbox.isChecked()
        item.setData(data)

        item.setText(self.ui.pathNameEdit.text())

    def addPath(self) -> None:
        item = QStandardItem("New")
        item.setData({'path': '', 'tsl': False})
        self.pathsModel.appendRow(item)

    def removePath(self) -> None:
        if len(self.ui.pathList.selectedIndexes()) > 0:
            index = self.ui.pathList.selectedIndexes()[0]
            item = self.pathsModel.itemFromIndex(index)
            self.pathsModel.removeRow(item.row())

        if len(self.ui.pathList.selectedIndexes()) == 0:
            self.ui.pathFrame.setEnabled(False)

    def toolComboChanged(self) -> None:
        if self.ui.gffToolCombo.currentText() == "External":
            self.ui.gffToolEdit.setEnabled(True)
        else:
            self.ui.gffToolEdit.setEnabled(False)
            self.ui.gffToolEdit.setText("")

        if self.ui.tlkToolCombo.currentText() == "External":
            self.ui.tlkToolEdit.setEnabled(True)
        else:
            self.ui.tlkToolEdit.setText("")
            self.ui.tlkToolEdit.setEnabled(False)

        if self.ui.dlgToolCombo.currentText() == "External":
            self.ui.dlgToolEdit.setEnabled(True)
        else:
            self.ui.dlgToolEdit.setText("")
            self.ui.dlgToolEdit.setEnabled(False)

        if self.ui.twodaToolCombo.currentText() == "External":
            self.ui.twodaToolEdit.setEnabled(True)
        else:
            self.ui.twodaToolEdit.setEnabled(False)
            self.ui.twodaToolEdit.setText("")

        if self.ui.txtToolCombo.currentText() == "External":
            self.ui.txtToolEdit.setEnabled(True)
        else:
            self.ui.txtToolEdit.setEnabled(False)
            self.ui.txtToolEdit.setText("")

        if self.ui.nssToolCombo.currentText() == "External":
            self.ui.nssToolEdit.setEnabled(True)
        else:
            self.ui.nssToolEdit.setEnabled(False)
            self.ui.nssToolEdit.setText("")

    def loadPaths(self) -> None:
        for installation in self.config.installations:
            item = QStandardItem(installation.name)
            item.setData({'path': installation.path, 'tsl': installation.tsl})
            self.pathsModel.appendRow(item)

    def loadTools(self) -> None:
        if self.config.gffEditorPath:
            self.ui.gffToolCombo.setCurrentText("External")
            self.ui.gffToolEdit.setText(self.config.gffEditorPath)

        if self.config.twodaEditorPath:
            self.ui.twodaToolCombo.setCurrentText("External")
            self.ui.twodaToolEdit.setText(self.config.twodaEditorPath)

        if self.config.dlgEditorPath:
            self.ui.dlgToolCombo.setCurrentText("External")
            self.ui.dlgToolEdit.setText(self.config.dlgEditorPath)

        if self.config.tlkEditorPath:
            self.ui.tlkToolCombo.setCurrentText("External")
            self.ui.tlkToolEdit.setText(self.config.tlkEditorPath)

        if self.config.txtEditorPath:
            self.ui.txtToolCombo.setCurrentText("External")
            self.ui.txtToolEdit.setText(self.config.txtEditorPath)

        if self.config.nssEditorPath:
            self.ui.nssToolCombo.setCurrentText("External")
            self.ui.nssToolEdit.setText(self.config.nssEditorPath)

        if self.config.gffSpecializedEditors:
            self.ui.utxToolCombo.setCurrentIndex(1)
        else:
            self.ui.utxToolCombo.setCurrentIndex(0)

        self.ui.nssCompToolEdit.setText(self.config.nssCompilerPath)
        self.ui.ncsToolEdit.setText(self.config.ncsDecompilerPath)

    def loadMisc(self) -> None:
        self.ui.tempMiscEdit.setText(self.config.extractPath)
        self.ui.experimentalMdlCheckbox.setChecked(self.config.mdlAllowDecompile)
        self.ui.experimentalExternalCheckbox.setChecked(self.config.erfExternalEditors)
        self.ui.showModuleNameCheckbox.setChecked(self.config.showModuleNames)
