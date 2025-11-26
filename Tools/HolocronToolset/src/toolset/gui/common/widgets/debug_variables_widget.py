"""Debug Variables Widget - Shows variable values during debugging."""

from __future__ import annotations

from typing import Any

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DebugVariablesWidget(QWidget):
    """Widget that displays variable values during debugging."""
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create table for variables
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
    
    def update_variables(self, variables: dict[str, dict[str, Any]]):
        """Update the variables display.
        
        Args:
        ----
            variables: dict mapping variable names to {type, value} dicts
        """
        self.table.setRowCount(0)
        
        for var_name, var_info in variables.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(var_name)
            self.table.setItem(row, 0, name_item)
            
            # Type
            var_type = var_info.get("type", "unknown")
            type_item = QTableWidgetItem(str(var_type))
            self.table.setItem(row, 1, type_item)
            
            # Value
            var_value = var_info.get("value", "")
            value_item = QTableWidgetItem(str(var_value))
            self.table.setItem(row, 2, value_item)
        
        # Resize columns to fit content
        self.table.resizeColumnsToContents()
    
    def clear(self):
        """Clear all variables."""
        self.table.setRowCount(0)

