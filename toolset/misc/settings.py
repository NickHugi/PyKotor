from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog

from data.configuration import Configuration, InstallationConfig
from misc import settings_ui


class Settings(QDialog):
    def __init__(self):
        super().__init__()

        self.pathsModel: QStandardItemModel = QStandardItemModel()

        self.ui = settings_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self._setupSignals()

        self.applied: bool = False
        self.config: Configuration = Configuration()

        self.loadPaths()
        self.loadTools()
        self.loadMisc()

        self.ui.okButton.clicked.connect(self.ok)
        self.ui.applyButton.clicked.connect(self.apply)
        self.ui.cancelButton.clicked.connect(self.cancel)

    def _setupSignals(self) -> None:
        self.ui.pathList.setModel(self.pathsModel)

        self.ui.pathList.selectionModel().selectionChanged.connect(self.pathSelected)
        self.ui.pathNameEdit.editingFinished.connect(self.pathUpdated)
        self.ui.pathDirEdit.editingFinished.connect(self.pathUpdated)
        self.ui.pathTslCheckbox.clicked.connect(self.pathUpdated)
        self.ui.addPathButton.clicked.connect(self.addPath)
        self.ui.removePathButton.clicked.connect(self.removePath)

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

        self.config.gffSpecializedEditors = self.ui.utxToolCombo.currentIndex() == 1

        self.config.nssCompilerPath = self.ui.nssCompToolEdit.text()
        self.config.ncsDecompilerPath = self.ui.ncsToolEdit.text()

        self.config.extractPath = self.ui.tempMiscEdit.text()

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

    def loadPaths(self) -> None:
        for installation in self.config.installations:
            item = QStandardItem(installation.name)
            item.setData({'path': installation.path, 'tsl': installation.tsl})
            self.pathsModel.appendRow(item)

    def loadTools(self) -> None:
        if self.config.gffSpecializedEditors:
            self.ui.utxToolCombo.setCurrentIndex(1)
        else:
            self.ui.utxToolCombo.setCurrentIndex(0)

        self.ui.nssCompToolEdit.setText(self.config.nssCompilerPath)
        self.ui.ncsToolEdit.setText(self.config.ncsDecompilerPath)

    def loadMisc(self) -> None:
        self.ui.tempMiscEdit.setText(self.config.extractPath)
