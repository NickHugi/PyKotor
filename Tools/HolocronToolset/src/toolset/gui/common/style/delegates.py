from __future__ import annotations

import re

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtCore import (
    QSize,
    Qt,
)
from qtpy.QtGui import (
    QPalette,
    QTextDocument,
)
from qtpy.QtWidgets import (
    QListView,
    QListWidget,
    QStyle,
    QStyledItemDelegate,
    QTreeView,
    QTreeWidget,
    QWidget,
)

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    pass
else:
    pass

if TYPE_CHECKING:


    from qtpy.QtCore import (
        QModelIndex,
    )
    from qtpy.QtGui import (
        QFont,
        QPainter,
    )
    from qtpy.QtWidgets import (
        QStyleOptionViewItem,
    )


FONT_SIZE_REPLACE_RE = re.compile(r"font-size:\d+pt;")


class HTMLDelegate(QStyledItemDelegate):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.text_size: int = 12
        self.customVerticalSpacing: int = 0  # Default vertical spacing between items
        self.nudgedModelIndexes: dict[QModelIndex, tuple[int, int]] = {}
        self.max_wraps: int = 3  # Maximum number of lines to wrap text

    def setVerticalSpacing(self, spacing: int):
        print(f"<SDM> [setVerticalSpacing scope] set vertical spacing from {self.customVerticalSpacing} to {spacing}")
        self.customVerticalSpacing = spacing

    def setTextSize(self, size: int):
        print(f"<SDM> [setTextSize scope] set text size from {self.text_size} to {size}")
        self.text_size = size

    def nudgeItem(
        self,
        index: QModelIndex,
        x: int,
        y: int,
    ):
        """Manually set the nudge offset for an item."""
        self.nudgedModelIndexes[index] = (x, y)
        print("<SDM> [nudgeItem scope] self.nudgedModelIndexes[index]: ", self.nudgedModelIndexes[index])

    def createTextDocument(self, html: str, font: QFont, width: int) -> QTextDocument:
        """Create and return a configured QTextDocument."""
        doc = QTextDocument()
        doc.setHtml(FONT_SIZE_REPLACE_RE.sub(f"font-size:{self.text_size}pt;", html))
        doc.setDefaultFont(font)
        doc.setTextWidth(width)
        return doc

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()

        # Apply nudge offsets
        nudge_offset = self.nudgedModelIndexes.get(index, (0, 0))
        painter.translate(*nudge_offset)

        display_data = index.data(Qt.DisplayRole)
        if not display_data:
            painter.restore()
            return

        doc = self.createTextDocument(display_data, option.font, option.rect.width())
        ctx = doc.documentLayout().PaintContext()
        ctx.palette = option.palette

        # Handle selection highlighting
        if bool(option.state & QStyle.StateFlag.State_Selected):
            highlight_color = option.palette.highlight().color()
            highlight_color.setAlpha(int(highlight_color.alpha() * 0.7))
            painter.fillRect(option.rect, highlight_color)
            ctx.palette.setColor(QPalette.Text, option.palette.highlightedText().color())
        else:
            ctx.palette.setColor(QPalette.Text, option.palette.text().color())

        painter.translate(option.rect.topLeft())
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def parent(self) -> QWidget:
        parent = super().parent()
        assert isinstance(parent, QWidget), f"HTMLDelegate.parent() returned non-QWidget: '{parent.__class__.__name__}'"
        return parent

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        html: str | None = index.data(Qt.ItemDataRole.DisplayRole)
        if html is None:
            return super().sizeHint(option, index)

        parentWidget = self.parent()
        if isinstance(parentWidget, (QListWidget, QListView, QTreeView, QTreeWidget)):
            available_width, available_height = parentWidget.viewport().width(), parentWidget.viewport().height()
            if isinstance(parentWidget, (QTreeView, QTreeWidget)):  # TreeView/Widget have indentation to account for.
                depth, parentIndex = 1, index.parent()
                while parentIndex.isValid():
                    depth += 1
                    parentIndex = parentIndex.parent()
                available_width = available_width - (depth * parentWidget.indentation())
        else:
            available_width, available_height = parentWidget.width(), parentWidget.height()

        # Create document to find natural size
        doc = self.createTextDocument(html, option.font, available_width)
        naturalWidth = int(doc.idealWidth())
        naturalHeight = int(doc.size().height())

        # Adjust for golden ratio, but prevent excessive white space
        golden_ratio = 1.618
        max_height = naturalWidth / golden_ratio
        adjusted_width = max(naturalWidth, available_width)
        adjusted_height = min(naturalHeight, max_height)

        return QSize(int(adjusted_width), int(adjusted_height + self.customVerticalSpacing))
