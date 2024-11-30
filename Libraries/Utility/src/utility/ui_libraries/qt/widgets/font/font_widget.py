from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QTextEdit, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.font.font_item_widget import FontItemWidget
from utility.ui_libraries.qt.widgets.font.size_widget import SizeWidget
from utility.ui_libraries.qt.widgets.font.style_widget import StyleWidget

if TYPE_CHECKING:
    from qtpy.QtGui import QFontDatabase


class FontWidget(QWidget):
    sig_font_changed: Signal = Signal(QFont)

    def __init__(
        self,
        font: QFont = QFont("Arial", 10),
    ):
        super().__init__()
        self._current_font: QFont = font
        self._init_ui(font=font)

    def _init_ui(
        self,
        font: QFont,
    ):
        self._preview_text_edit: QTextEdit = QTextEdit()
        self._preview_text_edit.textChanged.connect(self._text_changed)

        self._font_item_widget = FontItemWidget(font)
        self._font_item_widget.sig_item_font_changed.connect(self._font_item_changed_exec)

        self._size_widget = SizeWidget(font)
        self._size_widget.sig_item_size_changed.connect(self._size_item_changed_exec)

        self._style_widget = StyleWidget(font)
        self._style_widget.sig_bold_checked.connect(self._set_bold)
        self._style_widget.sig_italic_checked.connect(self._set_italic)

        self._init_preview_text_edit()

        lay = QHBoxLayout()
        lay.addWidget(self._font_item_widget)
        lay.addWidget(self._size_widget)
        lay.addWidget(self._style_widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        top_widget = QWidget()
        top_widget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("Preview"))
        lay.addWidget(self._preview_text_edit)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        bottom_widget = QWidget()
        bottom_widget.setLayout(lay)
        bottom_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)

        lay = QVBoxLayout()
        lay.addWidget(top_widget)
        lay.addWidget(bottom_widget)
        self.setLayout(lay)

    def _init_preview_text_edit(self):
        font_family: str = self._font_item_widget.get_font_family()
        font_size: str = self._size_widget.get_size()
        bold_f: bool = self._style_widget.is_bold()
        italic_f: bool = self._style_widget.is_italic()
        font: QFont = self._preview_text_edit.currentFont()
        font.setFamily(font_family)
        font.setPointSize(int(font_size))
        font.setBold(bold_f)
        font.setItalic(italic_f)
        self._preview_text_edit.setCurrentFont(font)
        self._preview_text_edit.setText("Sample")

    def _set_bold(
        self,
        f: bool,
    ):
        self._preview_text_edit.selectAll()
        font: QFont = self._preview_text_edit.currentFont()
        font.setBold(f)
        self._preview_text_edit.setCurrentFont(font)

        self._current_font = font
        self.sig_font_changed.emit(self._current_font)

    def _set_italic(
        self,
        f: bool,
    ):
        self._preview_text_edit.selectAll()
        font: QFont = self._preview_text_edit.currentFont()
        font.setItalic(f)
        self._preview_text_edit.setCurrentFont(font)

        self._current_font = font
        self.sig_font_changed.emit(self._current_font)

    def _size_item_changed_exec(
        self,
        size: int,
    ):
        self._preview_text_edit.selectAll()
        font: QFont = self._preview_text_edit.currentFont()
        font.setPointSize(size)
        self._preview_text_edit.setCurrentFont(font)

        self._current_font = font
        self.sig_font_changed.emit(self._current_font)

    def _font_item_changed_exec(
        self,
        font_text: str,
        fd: QFontDatabase,
    ):
        self._preview_text_edit.selectAll()
        font: QFont = self._preview_text_edit.currentFont()
        prev_size: int = font.pointSize()
        styles: list[str] = fd.styles(font_text)

        font.setFamily(font_text)

        sizes: list[int] = fd.pointSizes(font_text, styles[0])
        if prev_size in sizes:
            self._size_widget.set_sizes(sizes, prev_size)
            font.setPointSize(prev_size)
        else:
            self._size_widget.set_sizes(sizes, prev_size)
            # font.setPointSize(sizes[0])

        self._preview_text_edit.setCurrentFont(font)
        self._current_font = font
        self.sig_font_changed.emit(self._current_font)

    def get_font(self) -> QFont:
        return self._preview_text_edit.currentFont()

    def set_current_font(
        self,
        font: QFont,
    ):
        self._font_item_widget.set_current_font(font=font)
        self._size_widget.set_current_size(font=font)
        self._style_widget.set_current_style(font=font)

        self._preview_text_edit.setCurrentFont(font)
        self._current_font = font
        self.sig_font_changed.emit(self._current_font)

    def _text_changed(self):
        text: str = self._preview_text_edit.toPlainText()
        if text.strip() != "":
            pass
        else:
            self._preview_text_edit.setCurrentFont(self._current_font)