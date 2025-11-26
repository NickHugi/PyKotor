from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QMessageBox, QPushButton

from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.common.localization import translate as tr
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from qtpy.QtCore import QSize
    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QTreeWidgetItem, QWidget


class SettingsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget
    ):
        """Initialize Holocron Toolset settings dialog editor.

        Args:
        ----
            parent: QWidget: The parent widget of this dialog
        """
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._is_resetting: bool = False
        self.installation_edited: bool = False

        from toolset.uic.qtpy.dialogs import settings

        self.ui = settings.Ui_Dialog()
        self.ui.setupUi(self)
        self._setup_signals()
        self.no_scroll_filter: NoScrollEventFilter = NoScrollEventFilter()
        self.installEventFilter(self.no_scroll_filter)

        # Variable to store the original size
        self.original_size: QSize | None = None
        self.previous_page: str | None = None

        self.page_dict: dict[str, QWidget] = {  # pyright: ignore[reportAttributeAccessIssue]
            "Installations": self.ui.installationsPage,
            "GIT Editor": self.ui.gitEditorPage,
            "Misc": self.ui.miscPage,
            "Module Designer": self.ui.moduleDesignerPage,
            "Application": self.ui.applicationSettingsPage,
        }

    def _setup_signals(self):
        self.ui.installationsWidget.sig_settings_edited.connect(self.on_installation_edited)
        self.ui.settingsTree.itemClicked.connect(self.on_page_change)
        self.reset_button = QPushButton(tr("Reset All Settings"), self)
        self.reset_button.setObjectName("resetButton")
        self.reset_button.clicked.connect(self.on_reset_all_settings)
        self.ui.verticalLayout.addWidget(self.reset_button)  # pyright: ignore[reportCallIssue, reportArgumentType]

    def closeEvent(
        self,
        a0: QCloseEvent | None
    ) -> None:
        self.accept()
        return super().closeEvent(a0)  # pyright: ignore[reportArgumentType]

    def on_page_change(
        self,
        page_tree_item: QTreeWidgetItem
    ):
        page_item_text: str = page_tree_item.text(0)
        new_page: QWidget = self.page_dict[page_item_text]
        self.ui.settingsStack.setCurrentWidget(new_page)  # type: ignore[arg-type]
        if self.isMaximized():
            return

        if self.previous_page not in ("GIT Editor", "Module Designer") and page_item_text in ("GIT Editor", "Module Designer"):
            self.original_size = self.size()
            self.resize(800, 800)  # Adjust the size based on the image dimensions
        elif self.previous_page in ("GIT Editor", "Module Designer") and page_item_text not in ("GIT Editor", "Module Designer"):
            if self.original_size is not None:
                self.resize(self.original_size)

        self.previous_page = page_item_text

    def on_reset_all_settings(self):
        reply: QMessageBox.StandardButton = QMessageBox.question(
            self,
            tr("Reset All Settings"),
            tr("Are you sure you want to reset all settings to their default values? This action cannot be undone."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            GlobalSettings().settings.clear()
            QMessageBox.information(
                self,
                tr("Settings Reset"),
                tr("All settings have been cleared and reset to their default values.")
            )
            self._is_resetting = True
            self.close()

    def on_installation_edited(self):
        self.installation_edited = True

    def accept(self):
        super().accept()
        if self._is_resetting:
            return

        self.ui.miscWidget.save()
        self.ui.gitEditorWidget.save()
        self.ui.moduleDesignerWidget.save()
        self.ui.installationsWidget.save()
        self.ui.applicationSettingsWidget.save()
