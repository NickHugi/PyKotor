from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, pyqtSignal
from qtpy.QtGui import QFont, QFontDatabase
from qtpy.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from qtpy.QtWidgets import QListWidgetItem


class FontItemWidget(QWidget):
    sig_item_font_changed = pyqtSignal(str, QFontDatabase)

    def __init__(
        self,
        font: QFont = QFont("Arial", 10),
    ):
        super().__init__()
        self._font_families: list[str] = []
        self._init_ui(font=font)

    def _init_ui(
        self,
        font: QFont,
    ):
        self._font_line_edit: QLineEdit = QLineEdit()
        self._font_line_edit.textEdited.connect(self._text_edited)

        self._font_list_widget: QListWidget = QListWidget()
        self._font_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._font_list_widget.setViewMode(QListWidget.ViewMode.ListMode)

        self._init_fonts(font)
        self._font_list_widget.itemSelectionChanged.connect(self._font_item_changed)

        lay = QVBoxLayout()
        lay.addWidget(self._font_line_edit)
        lay.addWidget(self._font_list_widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        font_bottom_widget: QWidget = QWidget()
        font_bottom_widget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("Font"))
        lay.addWidget(font_bottom_widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        self.setLayout(lay)

    def _init_fonts(self, font: QFont):
        self._init_fonts_list()
        self.set_current_font(font=font)

    def _init_fonts_list(self):
        fd: QFontDatabase = QFontDatabase()  # pyright: ignore[reportCallIssue]
        font_families: list[str] = fd.families(QFontDatabase.WritingSystem.Any)
        self._font_families.extend(font_families)
        self._font_list_widget.addItems(font_families)

    def set_current_font(self, font: QFont):
        items: list[QListWidgetItem] = self._font_list_widget.findItems(font.family(), Qt.MatchFlag.MatchFixedString)
        item: QListWidgetItem | None = None
        if items:
            item = items[0]
        else:
            item = self._font_list_widget.item(0)
        if item is None:
            return
        self._font_list_widget.setCurrentItem(item)
        font_name = item.text()
        self._font_line_edit.setText(font_name)

    def _font_item_changed(self):
        item: QListWidgetItem | None = self._font_list_widget.currentItem()
        if item is None:
            return
        font_name = item.text()
        self._font_line_edit.setText(font_name)
        fd = QFontDatabase()  # pyright: ignore[reportCallIssue]
        self.sig_item_font_changed.emit(font_name, fd)

    def _text_edited(self):
        self._font_list_widget.clear()
        text = self._font_line_edit.text()
        if text.strip() != "":
            match_families: list[str] = []
            for family in self._font_families:
                if family.startswith(text):
                    match_families.append(family)
            if match_families:
                self._font_list_widget.addItems(match_families)
            else:
                pass
        else:
            self._font_list_widget.addItems(self._font_families)

    def get_font_family(self) -> str:
        item: QListWidgetItem | None = self._font_list_widget.currentItem()
        if item:
            return item.text()
        return "Arial"