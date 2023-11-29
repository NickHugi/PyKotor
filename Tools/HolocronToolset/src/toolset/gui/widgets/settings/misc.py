
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget

from toolset.gui.widgets.settings.installations import GlobalSettings


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
        self.ui.showPreviewUTCCheck.setChecked(self.settings.showPreviewUTC)
        self.ui.showPreviewUTPCheck.setChecked(self.settings.showPreviewUTP)
        self.ui.showPreviewUTDCheck.setChecked(self.settings.showPreviewUTD)
        self.ui.tempDirEdit.setText(self.settings.extractPath)
        self.ui.gffEditorCombo.setCurrentIndex(1 if self.settings.gff_specializedEditors else 0)
        self.ui.ncsToolEdit.setText(self.settings.ncsDecompilerPath)
        self.ui.nssCompEdit.setText(self.settings.nssCompilerPath)

    def save(self) -> None:
        self.settings.disableRIMSaving = not self.ui.saveRimCheck.isChecked()
        self.settings.joinRIMsTogether = self.ui.mergeRimCheck.isChecked()
        self.settings.greyRIMText = self.ui.greyRimCheck.isChecked()
        self.settings.showPreviewUTC = self.ui.showPreviewUTCCheck.isChecked()
        self.settings.showPreviewUTP = self.ui.showPreviewUTPCheck.isChecked()
        self.settings.showPreviewUTD = self.ui.showPreviewUTDCheck.isChecked()
        self.settings.extractPath = self.ui.tempDirEdit.text()
        self.settings.gff_specializedEditors = bool(self.ui.gffEditorCombo.currentIndex())
        self.settings.ncsDecompilerPath = self.ui.ncsToolEdit.text()
        self.settings.nssCompilerPath = self.ui.nssCompEdit.text()
