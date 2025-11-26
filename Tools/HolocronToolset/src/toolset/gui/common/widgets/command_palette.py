"""Command Palette Widget - VS Code-like command palette for executing editor commands."""

from __future__ import annotations

from typing import Any, Callable

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CommandPalette(QDialog):
    """VS Code-like command palette for executing commands."""
    
    command_selected = Signal(str)  # command_id
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(500)
        self.setMaximumWidth(700)
        
        # Command registry
        self._commands: dict[str, dict[str, Any]] = {}
        self._filtered_items: list[QListWidgetItem] = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Use palette for theme-safe styling
        self.setStyleSheet("""
            QDialog {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            QLineEdit {
                background-color: palette(base);
                color: palette(text);
                border: none;
                padding: 8px;
                font-size: 13px;
                border-bottom: 1px solid palette(mid);
            }
            QListWidget {
                background-color: palette(base);
                color: palette(text);
                border: none;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: palette(highlight);
                color: palette(highlightedText);
            }
            QListWidget::item:hover {
                background-color: palette(button);
            }
        """)
        
        # Search input
        self.search_edit = QLineEdit(self)
        from toolset.gui.common.localization import translate as tr
        self.search_edit.setPlaceholderText(tr("Type to search commands..."))
        self.search_edit.textChanged.connect(self._filter_commands)
        self.search_edit.returnPressed.connect(self._execute_selected)
        layout.addWidget(self.search_edit)
        
        # Command list
        self.command_list = QListWidget(self)
        self.command_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.command_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.command_list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.command_list)
        
        # Status label
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("padding: 4px 8px; color: palette(mid); font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def register_command(self, command_id: str, label: str, category: str = "", callback: Callable | None = None):
        """Register a command in the palette.
        
        Args:
        ----
            command_id: str: Unique identifier for the command
            label: str: Display label
            category: str: Category for grouping
            callback: Callable | None: Optional callback function
        """
        self._commands[command_id] = {
            "label": label,
            "category": category,
            "callback": callback,
            "keywords": f"{label} {category} {command_id}".lower()
        }
        self._refresh_list()
    
    def register_commands(self, commands: list[dict[str, Any]]):
        """Register multiple commands at once.
        
        Args:
        ----
            commands: list[dict]: List of command dicts with 'id', 'label', 'category', optionally 'callback'
        """
        for cmd in commands:
            self.register_command(
                cmd["id"],
                cmd["label"],
                cmd.get("category", ""),
                cmd.get("callback")
            )
    
    def _refresh_list(self):
        """Refresh the command list."""
        self.command_list.clear()
        self._filtered_items = []
        
        # Sort commands by category then label
        sorted_commands = sorted(
            self._commands.items(),
            key=lambda x: (x[1]["category"], x[1]["label"])
        )
        
        current_category = ""
        for command_id, command_data in sorted_commands:
            if command_data["category"] != current_category:
                current_category = command_data["category"]
                # Add category separator
                if current_category:
                    category_item = QListWidgetItem(f"▶ {current_category}")
                    category_item.setFlags(Qt.ItemFlag.NoItemFlags)
                    category_item.setForeground(self.palette().color(self.palette().ColorRole.Mid))
                    self.command_list.addItem(category_item)
            
            # Add command item
            label = command_data["label"]
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, command_id)
            self.command_list.addItem(item)
            self._filtered_items.append(item)
    
    def _filter_commands(self, text: str):
        """Filter commands based on search text."""
        if not text:
            # Show all commands
            for i in range(self.command_list.count()):
                item = self.command_list.item(i)
                if item is not None:
                    item.setHidden(False)
            if self.command_list.count() > 0:
                self.command_list.setCurrentRow(0)
            return
        
        text_lower = text.lower()
        visible_count = 0
        first_visible = -1
        
        for i in range(self.command_list.count()):
            item = self.command_list.item(i)
            if item is None:
                continue
            
            # Skip category separators
            if item.flags() == Qt.ItemFlag.NoItemFlags:
                item.setHidden(True)
                continue
            
            command_id = item.data(Qt.ItemDataRole.UserRole)
            if command_id is None:
                continue
            
            command_data = self._commands.get(str(command_id), {})
            keywords = command_data.get("keywords", "")
            
            # Show if matches keywords
            if text_lower in keywords:
                item.setHidden(False)
                if first_visible == -1:
                    first_visible = i
                visible_count += 1
            else:
                item.setHidden(True)
        
        # Update status
        if visible_count > 0:
            self.status_label.setText(f"{visible_count} command{'s' if visible_count != 1 else ''}")
            if first_visible >= 0:
                self.command_list.setCurrentRow(first_visible)
        else:
            from toolset.gui.common.localization import translate as tr
            self.status_label.setText(tr("No matching commands"))
    
    def _execute_selected(self):
        """Execute the currently selected command."""
        current_item = self.command_list.currentItem()
        if current_item is None:
            return
        
        command_id = current_item.data(Qt.ItemDataRole.UserRole)
        if command_id is None:
            return
        
        # Execute callback if available
        command_data = self._commands.get(str(command_id), {})
        callback = command_data.get("callback")
        if callback:
            callback()
        
        # Emit signal
        self.command_selected.emit(str(command_id))
        self.accept()
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double click on command item."""
        self._execute_selected()
    
    def _on_item_activated(self, item: QListWidgetItem):
        """Handle activation of command item."""
        self._execute_selected()
    
    def show_palette(self):
        """Show the command palette."""
        self.search_edit.clear()
        self._filter_commands("")
        self.search_edit.setFocus()
        self.exec_()
    
    def keyPressEvent(self, event: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Down:
            # Move selection down
            current_row = self.command_list.currentRow()
            for i in range(current_row + 1, self.command_list.count()):
                item = self.command_list.item(i)
                if item is not None and not item.isHidden() and item.flags() != Qt.ItemFlag.NoItemFlags:
                    self.command_list.setCurrentRow(i)
                    break
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Up:
            # Move selection up
            current_row = self.command_list.currentRow()
            for i in range(current_row - 1, -1, -1):
                item = self.command_list.item(i)
                if item is not None and not item.isHidden() and item.flags() != Qt.ItemFlag.NoItemFlags:
                    self.command_list.setCurrentRow(i)
                    break
            event.accept()
            return
        super().keyPressEvent(event)

