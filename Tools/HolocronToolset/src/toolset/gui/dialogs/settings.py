from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QDialog

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTreeWidgetItem, QWidget


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

        self.installationEdited: bool = False

        from toolset.uic.dialogs import settings  # pylint: disable=C0415  # noqa: PLC0415

        self.ui = settings.Ui_Dialog()
        self.ui.setupUi(self)
        self._setupSignals()

        self.pageDict = {
            "Installations": self.ui.installationsPage,
            "GIT Editor": self.ui.gitEditorPage,
            "Misc": self.ui.miscPage,
            "Module Designer": self.ui.moduleDesignerPage,
        }

    def _setupSignals(self):
        self.ui.installationsWidget.edited.connect(self.onInstallationEdited)
        self.ui.settingsTree.itemClicked.connect(self.pageChanged)

    def pageChanged(self, pageTreeItem: QTreeWidgetItem):
        newPage = self.pageDict[pageTreeItem.text(0)]
        self.ui.settingsStack.setCurrentWidget(newPage)

    def onInstallationEdited(self):
        self.installationEdited = True

    def accept(self):
        super().accept()

        self.ui.miscWidget.save()
        self.ui.gitEditorWidget.save()
        self.ui.moduleDesignerWidget.save()
        self.ui.installationsWidget.save()
