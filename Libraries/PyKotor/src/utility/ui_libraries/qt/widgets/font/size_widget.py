from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qtpy.QtCore import Qt, pyqtSignal
from qtpy.QtGui import QFont, QFontDatabase
from qtpy.QtWidgets import QLabel, QLineEdit, QListWidget, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from qtpy.QtWidgets import QListWidgetItem


class SizeWidget(QWidget):
    sig_item_size_changed = pyqtSignal(int)

    def __init__(
        self,
        font: QFont | None = None,
    ):
        font = QFont("Arial", 10) if font is None else font
        super().__init__()
        self._init_ui(font=font)

    def _init_ui(
        self,
        font: QFont,
    ):
        self._size_line_edit: QLineEdit = QLineEdit()
        self._size_line_edit.textEdited.connect(self._text_edited)

        self._size_list_widget: QListWidget = QListWidget()
        self._init_sizes(font=font)
        self._size_list_widget.itemSelectionChanged.connect(self._size_item_changed)

        lay = QVBoxLayout()
        lay.addWidget(self._size_line_edit)
        lay.addWidget(self._size_list_widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        size_bottom_widget: QWidget = QWidget()
        size_bottom_widget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("Size"))
        lay.addWidget(size_bottom_widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        self.setLayout(lay)

    def _init_sizes(
        self,
        font: QFont,
    ):
        self._init_sizes_list(font=font)
        self.set_current_size(font=font)

    def _init_sizes_list(
        self,
        font: QFont,
    ):
        fd: QFontDatabase = QFontDatabase()  # pyright: ignore[reportCallIssue]
        font_name: str = font.family()
        style_names: list[str] = fd.styles(font_name)
        # In case of font is not in the font list
        if style_names:
            style_name: str = style_names[0]
        else:
            font_name = "Arial"
            style_name = fd.styles(font_name)[0]
        sizes: list[int] | list[str] = fd.pointSizes(font_name, style_name)
        sizes = list(map(str, sizes))
        self._size_list_widget.addItems(sizes)

    def set_current_size(
        self,
        font: QFont,
    ):
        items: list[QListWidgetItem] = self._size_list_widget.findItems(str(font.pointSize()), Qt.MatchFlag.MatchFixedString)
        item: QListWidgetItem | None = None
        if items:
            item = items[0]
        else:
            item = self._size_list_widget.item(0)
            if item is None:
                return
        self._size_list_widget.setCurrentItem(item)
        size_text: str = item.text()
        self._size_line_edit.setText(size_text)

    def _text_edited(self):
        size_text: str = self._size_line_edit.text()
        items: list[QListWidgetItem] = self._size_list_widget.findItems(size_text, Qt.MatchFlag.MatchFixedString)
        if items:
            self._size_list_widget.setCurrentItem(items[0])
        self.sig_item_size_changed.emit(int(size_text))

    def _size_item_changed(self):
        list_widget_item: QListWidgetItem | None = self._size_list_widget.currentItem()
        if list_widget_item is None:
            return
        size_text: str = list_widget_item.text()
        self.sig_item_size_changed.emit(int(size_text))
        self._size_line_edit.setText(size_text)

    def set_sizes(
        self,
        sizes: Sequence[int | str],
        prev_size: int = 10,
    ):
        sizes_list: list[str] = list(map(str, sizes))
        self._size_list_widget.clear()
        self._size_list_widget.addItems(sizes_list)
        items: list[QListWidgetItem] = self._size_list_widget.findItems(str(prev_size), Qt.MatchFlag.MatchFixedString)
        if len(items) > 0:
            item: QListWidgetItem = items[0]
            self._size_list_widget.setCurrentItem(item)
            self._size_line_edit.setText(item.text())
        else:
            self._size_line_edit.setText(str(prev_size))

    def get_size(self) -> str:
        item: QListWidgetItem | None = self._size_list_widget.currentItem()
        if item is None:
            return ""
        return item.text()
