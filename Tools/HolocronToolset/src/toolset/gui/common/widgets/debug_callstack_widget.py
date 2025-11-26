"""Debug Call Stack Widget - Shows function call stack during debugging."""

from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DebugCallStackWidget(QWidget):
    """Widget that displays the call stack during debugging."""
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create table for call stack
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Frame", "Function", "Instruction"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
    
    def update_call_stack(self, call_stack: list[tuple[str, int, int]]):
        """Update the call stack display.
        
        Args:
        ----
            call_stack: list of (function_name, instruction_index, return_address) tuples
        """
        self.table.setRowCount(0)
        
        # Display call stack in reverse order (top of stack first)
        for i, (func_name, inst_idx, return_addr) in enumerate(reversed(call_stack)):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Frame number (0 = current frame)
            frame_item = QTableWidgetItem(str(len(call_stack) - 1 - i))
            frame_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, frame_item)
            
            # Function name
            func_item = QTableWidgetItem(func_name if func_name else "<unknown>")
            self.table.setItem(row, 1, func_item)
            
            # Instruction index
            inst_item = QTableWidgetItem(str(inst_idx))
            inst_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, inst_item)
        
        # Resize columns to fit content
        self.table.resizeColumnsToContents()
    
    def clear(self):
        """Clear the call stack."""
        self.table.setRowCount(0)

