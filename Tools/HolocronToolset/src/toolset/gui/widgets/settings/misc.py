from __future__ import annotations

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QWidget

from toolset.gui.widgets.settings.installations import GlobalSettings


class MiscWidget(QWidget):
    editedSignal = QtCore.Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings = GlobalSettings()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.settings import misc  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.settings import misc  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.settings import misc  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.settings import misc  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = misc.Ui_Form()
        self.ui.setupUi(self)
        self.setupValues()

    def setupValues(self):
        self.ui.alsoCheckReleaseVersion.setChecked(self.settings.alsoCheckReleaseVersion)
        self.ui.useBetaChannel.setChecked(self.settings.useBetaChannel)
        self.ui.saveRimCheck.setChecked(not self.settings.disableRIMSaving)
        self.ui.mergeRimCheck.setChecked(self.settings.joinRIMsTogether)
        self.ui.useModuleFilenamesCheck.setChecked(self.settings.useModuleFilenames)
        self.ui.greyRimCheck.setChecked(self.settings.greyRIMText)
        self.ui.showPreviewUTCCheck.setChecked(self.settings.showPreviewUTC)
        self.ui.showPreviewUTPCheck.setChecked(self.settings.showPreviewUTP)
        self.ui.showPreviewUTDCheck.setChecked(self.settings.showPreviewUTD)
        self.ui.tempDirEdit.setText(self.settings.extractPath)
        self.ui.gffEditorCombo.setCurrentIndex(1 if self.settings.gff_specializedEditors else 0)
        self.ui.ncsToolEdit.setText(self.settings.ncsDecompilerPath)
        self.ui.nssCompEdit.setText(self.settings.nssCompilerPath)

    def save(self):
        self.settings.alsoCheckReleaseVersion = self.ui.alsoCheckReleaseVersion.isChecked()
        self.settings.useBetaChannel = not self.ui.useBetaChannel.isChecked()
        self.settings.disableRIMSaving = not self.ui.saveRimCheck.isChecked()
        self.settings.joinRIMsTogether = self.ui.mergeRimCheck.isChecked()
        self.settings.useModuleFilenames = self.ui.useModuleFilenamesCheck.isChecked()
        self.settings.greyRIMText = self.ui.greyRimCheck.isChecked()
        self.settings.showPreviewUTC = self.ui.showPreviewUTCCheck.isChecked()
        self.settings.showPreviewUTP = self.ui.showPreviewUTPCheck.isChecked()
        self.settings.showPreviewUTD = self.ui.showPreviewUTDCheck.isChecked()
        self.settings.extractPath = self.ui.tempDirEdit.text()
        self.settings.gff_specializedEditors = bool(self.ui.gffEditorCombo.currentIndex())
        self.settings.ncsDecompilerPath = self.ui.ncsToolEdit.text()
        self.settings.nssCompilerPath = self.ui.nssCompEdit.text()
