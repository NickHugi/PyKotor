"""Dialog for quick side-by-side resource comparison."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.extract.file import FileResource

# Constants for hex display
ASCII_MIN_PRINTABLE = 32
ASCII_MAX_PRINTABLE = 127


class ResourceComparisonDialog(QDialog):
    """Quick side-by-side comparison dialog for resources."""

    def __init__(
        self,
        parent: QWidget | None,
        resource1: FileResource,
        resource2: FileResource | None = None,
    ):
        super().__init__(parent)
        from toolset.gui.common.localization import translate as tr, trf
        self.setWindowTitle(trf("Compare: {name}.{ext}", name=resource1.resname(), ext=resource1.restype().extension))
        self.resize(1200, 700)

        self.resource1 = resource1
        self.resource2 = resource2

        self._setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        self._load_resources()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header with file paths
        header_layout = QHBoxLayout()

        # Left file info
        left_header = QVBoxLayout()
        self.left_path_label: QLabel = QLabel()
        self.left_path_label.setWordWrap(True)
        from toolset.gui.common.localization import translate as tr
        left_header.addWidget(QLabel(tr("<b>Left:</b>")))
        left_header.addWidget(self.left_path_label)
        header_layout.addLayout(left_header, 1)

        # Right file info
        right_header = QVBoxLayout()
        self.right_path_label: QLabel = QLabel()
        self.right_path_label.setWordWrap(True)
        right_header.addWidget(QLabel(tr("<b>Right:</b>")))
        right_header.addWidget(self.right_path_label)
        header_layout.addLayout(right_header, 1)

        layout.addLayout(header_layout)

        # Comparison view
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pane
        self.left_text: QPlainTextEdit = QPlainTextEdit()
        self.left_text.setReadOnly(True)
        self.left_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        splitter.addWidget(self.left_text)

        # Right pane
        self.right_text: QPlainTextEdit = QPlainTextEdit()
        self.right_text.setReadOnly(True)
        self.right_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        splitter.addWidget(self.right_text)

        # Sync scrollbars
        left_vscroll = self.left_text.verticalScrollBar()
        right_vscroll = self.right_text.verticalScrollBar()
        left_hscroll = self.left_text.horizontalScrollBar()
        right_hscroll = self.right_text.horizontalScrollBar()

        if left_vscroll and right_vscroll:
            left_vscroll.valueChanged.connect(right_vscroll.setValue)
            right_vscroll.valueChanged.connect(left_vscroll.setValue)

        if left_hscroll and right_hscroll:
            left_hscroll.valueChanged.connect(right_hscroll.setValue)
            right_hscroll.valueChanged.connect(left_hscroll.setValue)

        layout.addWidget(splitter)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _load_resources(self):
        """Load and display resource contents."""
        # Set paths
        self.left_path_label.setText(str(self.resource1.filepath()))
        if self.resource2:
            self.right_path_label.setText(str(self.resource2.filepath()))
        else:
            from toolset.gui.common.localization import translate as tr
            self.right_path_label.setText(tr("[Not selected]"))

        # Load left resource
        try:
            data = self.resource1.data()
            self.left_text.setPlainText(self._format_data(data))
        except Exception as e:  # noqa: BLE001
            self.left_text.setPlainText(f"Error loading resource:\n{e}")

        # Load right resource
        if self.resource2:
            try:
                data = self.resource2.data()
                self.right_text.setPlainText(self._format_data(data))
            except Exception as e:  # noqa: BLE001
                self.right_text.setPlainText(f"Error loading resource:\n{e}")
        else:
            self.right_text.setPlainText("[No resource selected for comparison]")

    def _format_data(self, data: bytes) -> str:
        """Format resource data for display."""
        # Try to decode as text
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:  # noqa: S110
            pass

        try:
            return data.decode("latin-1")
        except UnicodeDecodeError:  # noqa: S110
            pass

        # Fall back to hex view
        hex_lines = []
        for i in range(0, len(data), 16):
            chunk = data[i : i + 16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if ASCII_MIN_PRINTABLE <= b < ASCII_MAX_PRINTABLE else "." for b in chunk)
            hex_lines.append(f"{i:08x}  {hex_part:<48}  {ascii_part}")

        return "\n".join(hex_lines)
