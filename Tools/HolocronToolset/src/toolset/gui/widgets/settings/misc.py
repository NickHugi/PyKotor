from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QSlider,
    QSpinBox,
    QWidget,
)

from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from qtpy.QtCore import QObject


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

        # Install the event filter on all child widgets
        self.noScrollEventFilter: NoScrollEventFilter = NoScrollEventFilter(self)
        self.installEventFilters(self, self.noScrollEventFilter)

    def installEventFilters(
        self,
        parent_widget: QWidget,
        event_filter: QObject,
        include_types: list[type[QWidget]] | None = None
    ) -> None:
        """Recursively install event filters on all child widgets."""
        if include_types is None:
            include_types = [QComboBox, QSlider, QSpinBox, QGroupBox, QAbstractSpinBox, QDoubleSpinBox]

        for widget in parent_widget.findChildren(QWidget):
            if not widget.objectName():
                widget.setObjectName(widget.__class__.__name__)
            if isinstance(widget, tuple(include_types)):
                #RobustRootLogger.debug(f"Installing event filter on: {widget.objectName()} (type: {widget.__class__.__name__})")
                widget.installEventFilter(event_filter)
            #else:
            #    RobustRootLogger.debug(f"Skipping NoScrollEventFilter installation on '{widget.objectName()}' due to instance check {widget.__class__.__name__}.")
            self.installEventFilters(widget, event_filter, include_types)

    def setupValues(self):
        self.ui.useBetaChannel.setChecked(self.settings.useBetaChannel)
        self.ui.profileToolset.setChecked(self.settings.profileToolset)
        self.ui.attemptKeepOldGFFFields.setChecked(self.settings.attemptKeepOldGFFFields)
        self.ui.saveRimCheck.setChecked(not self.settings.disableRIMSaving)
        self.ui.mergeRimCheck.setChecked(self.settings.joinRIMsTogether)
        self.ui.moduleSortOptionComboBox.setCurrentIndex(self.settings.moduleSortOption)
        self.ui.greyRimCheck.setChecked(self.settings.greyRIMText)
        self.ui.showPreviewUTCCheck.setChecked(self.settings.showPreviewUTC)
        self.ui.showPreviewUTPCheck.setChecked(self.settings.showPreviewUTP)
        self.ui.showPreviewUTDCheck.setChecked(self.settings.showPreviewUTD)
        self.ui.tempDirEdit.setText(self.settings.extractPath)
        self.ui.gffEditorCombo.setCurrentIndex(1 if self.settings.gff_specializedEditors else 0)
        self.ui.ncsToolEdit.setText(self.settings.ncsDecompilerPath)
        self.ui.nssCompEdit.setText(self.settings.nssCompilerPath)

    def save(self):
        self.settings.useBetaChannel = self.ui.useBetaChannel.isChecked()
        self.settings.profileToolset = self.ui.profileToolset.isChecked()
        self.settings.attemptKeepOldGFFFields = self.ui.attemptKeepOldGFFFields.isChecked()
        self.settings.disableRIMSaving = not self.ui.saveRimCheck.isChecked()
        self.settings.joinRIMsTogether = self.ui.mergeRimCheck.isChecked()
        self.settings.moduleSortOption = self.ui.moduleSortOptionComboBox.currentIndex()
        self.settings.greyRIMText = self.ui.greyRimCheck.isChecked()
        self.settings.showPreviewUTC = self.ui.showPreviewUTCCheck.isChecked()
        self.settings.showPreviewUTP = self.ui.showPreviewUTPCheck.isChecked()
        self.settings.showPreviewUTD = self.ui.showPreviewUTDCheck.isChecked()
        self.settings.extractPath = self.ui.tempDirEdit.text()
        self.settings.gff_specializedEditors = bool(self.ui.gffEditorCombo.currentIndex())
        self.settings.ncsDecompilerPath = self.ui.ncsToolEdit.text()
        self.settings.nssCompilerPath = self.ui.nssCompEdit.text()
