from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.font.font_widget import FontWidget

if TYPE_CHECKING:
    from qtpy.QtWidgets import QLayout


class FontDialog(QDialog):
    def __init__(
        self,
        font: QFont = QFont("Arial", 10),
        title: str = "Font",
    ):
        super().__init__()
        self._current_font: QFont = font
        self._init_ui(font=font, title=title)

    def _init_ui(
        self,
        font: QFont,
        title: str,
    ):
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

        self._font_widget = FontWidget(font=font)
        font_widget_layout: QLayout | None = self._font_widget.layout()
        assert font_widget_layout is not None
        font_widget_layout.setContentsMargins(0, 0, 0, 0)

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.close)

        lay = QHBoxLayout()
        lay.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(ok_button)
        lay.addWidget(cancel_button)
        lay.setContentsMargins(0, 2, 0, 0)

        ok_cancel_widget = QWidget()
        ok_cancel_widget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(self._font_widget)
        lay.addWidget(ok_cancel_widget)
        self.setLayout(lay)

    def get_font(self) -> QFont:
        return self._font_widget.get_font()

    def get_font_widget(self) -> FontWidget:
        return self._font_widget