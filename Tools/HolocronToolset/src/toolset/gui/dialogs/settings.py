from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QDialog, QMessageBox, QPushButton

from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from qtpy.QtWidgets import QTreeWidgetItem, QWidget


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget):
        """Initialize Holocron Toolset settings dialog editor.

        Args:
        ----
            parent: QWidget: The parent widget of this dialog

        Processing Logic:
        ----------------
            - Initialize parent class with parent widget
            - Set flag for edited installations
            - Import UI dialog class
            - Set up UI
            - Map pages to UI elements
            - Connect signal handlers.
        """
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.installationEdited: bool = False

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs import settings  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs import settings  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs import settings  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs import settings  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = settings.Ui_Dialog()
        self.ui.setupUi(self)
        self._setupSignals()

        # Variable to store the original size
        self.originalSize = None
        self.previousPage = None

        self.pageDict: dict[str, QWidget] = {
            "Installations": self.ui.installationsPage,
            "GIT Editor": self.ui.gitEditorPage,
            "Misc": self.ui.miscPage,
            "Module Designer": self.ui.moduleDesignerPage,
            "Application": self.ui.applicationSettingsPage,
        }

    def _setupSignals(self):
        self.ui.installationsWidget.edited.connect(self.onInstallationEdited)
        self.ui.settingsTree.itemClicked.connect(self.pageChanged)
        self.resetButton = QPushButton("Reset All Settings", self)
        self.resetButton.setObjectName("resetButton")
        self.resetButton.clicked.connect(self.resetAllSettings)
        self.ui.verticalLayout.addWidget(self.resetButton)

    def pageChanged(self, pageTreeItem: QTreeWidgetItem):
        pageItemText = pageTreeItem.text(0)
        newPage = self.pageDict[pageItemText]
        self.ui.settingsStack.setCurrentWidget(newPage)  # type: ignore[arg-type]
        if self.isMaximized():
            return

        if self.previousPage not in ("GIT Editor", "Module Designer") and pageItemText in ("GIT Editor", "Module Designer"):
            self.originalSize = self.size()
            self.resize(800, 800)  # Adjust the size based on the image dimensions
        elif self.previousPage in ("GIT Editor", "Module Designer") and pageItemText not in ("GIT Editor", "Module Designer"):
            if self.originalSize:
                self.resize(self.originalSize)

        self.previousPage = pageItemText

    def resetAllSettings(self):
        reply = QMessageBox.question(
            self,
            "Reset All Settings",
            "Are you sure you want to reset all settings to their default values? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            GlobalSettings().settings.clear()
            GlobalSettings().firstTime = True
            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been cleared and reset to their default values."
            )

    def onInstallationEdited(self):
        self.installationEdited = True

    def accept(self):
        super().accept()

        self.ui.miscWidget.save()
        self.ui.gitEditorWidget.save()
        self.ui.moduleDesignerWidget.save()
        self.ui.installationsWidget.save()
        self.ui.applicationSettingsWidget.save()
