from __future__ import annotations

import re

from typing import TYPE_CHECKING

from qtpy.QtCore import QObject, Qt
from qtpy.QtWidgets import QMessageBox, QWidget

from utility.ui_libraries.qt.filesystem.qfiledialogextended.explorer import FileSystemExplorerWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex, QSortFilterProxyModel
    from qtpy.QtWidgets import QLineEdit


class SearchHandler(QObject):
    """Handles advanced search functionality with regex support."""

    def __init__(
        self,
        parent: FileSystemExplorerWidget | None = None,
    ) -> None:
        """Initialize the SearchHandler."""
        super().__init__(parent)
        self.last_valid_pattern: str = ""
        self.is_regex_mode: bool = False

    def setup_search_bar(
        self,
        search_bar: QLineEdit,
    ) -> None:
        """Configure the search bar with enhanced functionality."""
        search_bar.setPlaceholderText("Search (Ctrl+R for regex mode)...")
        search_bar.textChanged.connect(self.on_search_text_changed)

        # Add tooltip with search instructions
        search_bar.setToolTip(
            "Enter search terms to filter files and folders\n"
            "Ctrl+R: Toggle regex mode\n"
            "Regex Examples:\n"
            "  .*\\.txt$ - Find all .txt files\n"
            "  ^[A-Z] - Items starting with capital letter\n"
            "  \\d{4} - Items containing 4 digits"
        )

    def validate_regex(
        self,
        pattern: str,
    ) -> tuple[bool, str]:
        """Validate a regex pattern and return whether it's valid and any error message."""
        if not pattern:
            return True, ""
        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, f"Invalid regex pattern: {str(e)}"

    def apply_filter(
        self,
        proxy_model: QSortFilterProxyModel,
        text: str,
        source_index: QModelIndex,
    ) -> None:
        """Apply the search filter to the proxy model."""
        if not text:
            proxy_model.setFilterRegularExpression("")
            return

        if self.is_regex_mode:
            is_valid, error_msg = self.validate_regex(text)
            if is_valid:
                self.last_valid_pattern = text
                proxy_model.setFilterRegularExpression(text)
            else:
                # Keep the last valid pattern while showing error
                proxy_model.setFilterRegularExpression(self.last_valid_pattern)
                parent: QObject | None = self.parent()
                if isinstance(parent, QWidget):
                    QMessageBox.warning(
                        parent,
                        "Invalid Regex",
                        error_msg,
                        QMessageBox.StandardButton.Ok,
                    )
        else:
            # In normal mode, escape special regex characters
            escaped_text = re.escape(text)
            proxy_model.setFilterRegularExpression(escaped_text)

        proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def toggle_regex_mode(self) -> None:
        """Toggle between normal and regex search modes."""
        self.is_regex_mode = not self.is_regex_mode
        parent: QObject | None = self.parent()
        if isinstance(parent, QWidget):
            QMessageBox.information(
                parent,
                "Search Mode",
                f"Regex mode {'enabled' if self.is_regex_mode else 'disabled'}",
                QMessageBox.StandardButton.Ok,
            )

    def on_search_text_changed(
        self,
        text: str,
    ) -> None:
        """Handle search text changes."""
        parent: FileSystemExplorerWidget | QObject | None = self.parent()
        if isinstance(parent, FileSystemExplorerWidget):
            proxy_model: QSortFilterProxyModel = parent.proxy_model
            source_index = parent.fs_model.index(str(parent.current_path))
            self.apply_filter(proxy_model, text, source_index)
