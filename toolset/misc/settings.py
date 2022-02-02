from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog

from misc import settings_ui


class Settings(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = settings_ui.Ui_Dialog()
        self.ui.setupUi(self)

        self.applied: bool = False
        self.settings = QSettings('cortisol', 'holocrontoolset')

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

        games = {}
        for i in range(self.pathsModel.rowCount()):
            item = self.pathsModel.item(i, 0)
            name, path, tsl = item.text(), item.data()['path'], item.data()['tsl']
            games[name] = {'path': path, 'tsl': tsl}
        self.settings.setValue('games', games)

        self.settings.setValue('gffEditor', self.ui.gffToolEdit.text())
        self.settings.setValue('2daEditor', self.ui.twodaToolEdit.text())
        self.settings.setValue('dlgEditor', self.ui.dlgToolEdit.text())
        self.settings.setValue('tlkEditor', self.ui.tlkToolEdit.text())
        self.settings.setValue('txtEditor', self.ui.txtToolEdit.text())
        self.settings.setValue('nssEditor', self.ui.nssToolEdit.text())

        self.settings.setValue('tempDir', self.ui.tempMiscEdit.text().replace('\\', '/'))
        self.settings.setValue('mdlDecompile', self.ui.experimentalMdlCheckbox.isChecked())
        self.settings.setValue('encapsulatedExternalEditor', self.ui.experimentalExternalCheckbox.isChecked())
        self.settings.setValue('showModuleNames', self.ui.showModuleNameCheckbox.isChecked())

    def cancel(self) -> None:
        """
        Any changes that are not applied are forgotten. Closes the dialog.
        """
        if self.applied:
            self.accept()
        else:
            self.reject()

    def loadPaths(self) -> None:
        for name, data in self.settings.value('games').items():
            item = QStandardItem(name)
            item.setData(data)
            self.pathsModel.appendRow(item)

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

    def loadTools(self) -> None:
        if self.settings.value('gffEditor'):
            self.ui.gffToolCombo.setCurrentText("External")
            self.ui.gffToolEdit.setText(self.settings.value('gffEditor'))

        if self.settings.value('2daEditor'):
            self.ui.twodaToolCombo.setCurrentText("External")
            self.ui.twodaToolEdit.setText(self.settings.value('2daEditor'))

        if self.settings.value('dlgEditor'):
            self.ui.dlgToolCombo.setCurrentText("External")
            self.ui.dlgToolEdit.setText(self.settings.value('dlgEditor'))

        if self.settings.value('tlkEditor'):
            self.ui.tlkToolCombo.setCurrentText("External")
            self.ui.tlkToolEdit.setText(self.settings.value('tlkEditor'))

        if self.settings.value('txtEditor'):
            self.ui.txtToolCombo.setCurrentText("External")
            self.ui.txtToolEdit.setText(self.settings.value('txtEditor'))

        if self.settings.value('nssEditor'):
            self.ui.nssToolCombo.setCurrentText("External")
            self.ui.nssToolEdit.setText(self.settings.value('nssEditor'))

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

    def loadMisc(self) -> None:
        self.ui.tempMiscEdit.setText(self.settings.value('tempDir'))
        self.ui.experimentalMdlCheckbox.setChecked(self.settings.value('mdlDecompile', False, bool))
        self.ui.experimentalExternalCheckbox.setChecked(self.settings.value('encapsulatedExternalEditor', False, bool))
        self.ui.showModuleNameCheckbox.setChecked(self.settings.value('showModuleNames', True, bool))
