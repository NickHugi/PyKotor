"""Breadcrumbs Widget - Shows navigation path in VS Code style."""

from __future__ import annotations

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class BreadcrumbsWidget(QWidget):
    """Breadcrumbs navigation widget showing current context path."""
    
    item_clicked = Signal(str)  # path segment clicked
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._path: list[str] = []
        self._separator = " > "
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        
        # Use palette for theme-safe styling
        self.setStyleSheet("""
            QWidget {
                background-color: palette(window);
            }
            QPushButton {
                background-color: transparent;
                color: palette(windowText);
                border: none;
                padding: 2px 4px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: palette(button);
            }
            QLabel {
                color: palette(mid);
            }
        """)
        
        self._buttons: list[QPushButton] = []
    
    def set_path(self, path: list[str]):
        """Set the breadcrumb path.
        
        Args:
        ----
            path: list[str]: List of path segments (e.g., ["File", "Function", "Variable"])
        """
        self._path = path
        self._update_display()
    
    def _update_display(self):
        """Update the breadcrumb display."""
        # Clear existing buttons
        layout = self.layout()
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._buttons.clear()
        
        # Add buttons for each path segment
        for i, segment in enumerate(self._path):
            if i > 0:
                # Add separator
                separator = QLabel(self._separator, self)
                layout.addWidget(separator)
            
            button = QPushButton(segment, self)
            button.setFlat(True)
            button.clicked.connect(lambda checked=False, idx=i: self._on_segment_clicked(idx))
            layout.addWidget(button)
            self._buttons.append(button)
        
        layout.addStretch()
    
    def _on_segment_clicked(self, index: int):
        """Handle breadcrumb segment click."""
        if 0 <= index < len(self._path):
            self.item_clicked.emit(self._path[index])
    
    def clear(self):
        """Clear the breadcrumb path."""
        self.set_path([])

