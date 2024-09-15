from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any, Callable

from qtpy.QtCore import QEvent, QPoint, QRect, QSize, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QIcon, QImage, QMouseEvent, QPainter, QPalette, QPen, QPixmap, QTextDocument, QTextOption
from qtpy.QtWidgets import QApplication, QListView, QListWidget, QStyle, QStyledItemDelegate, QToolTip, QTreeView, QTreeWidget, QWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex
    from qtpy.QtWidgets import QStyleOptionViewItem


FONT_SIZE_REPLACE_RE = re.compile(r"font-size:\d+pt;")
_ICONS_DATA_ROLE = Qt.ItemDataRole.UserRole + 10


class HTMLDelegate(QStyledItemDelegate):
    """A delegate that paints items with HTML text.

    This delegate is used to paint items in a QListView, QListWidget, QTreeView, or QTreeWidget with HTML text.
    It allows for custom text size, vertical spacing, and word wrapping.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        word_wrap: bool = True,
        text_size: int = 12,
        custom_vertical_spacing: int = 0,
    ):
        super().__init__(parent)
        self.text_size: int = text_size
        self.customVerticalSpacing: int = custom_vertical_spacing
        self.nudgedModelIndexes: dict[QModelIndex, tuple[int, int]] = {}
        self.word_wrap: bool = word_wrap

    def parent(self) -> QWidget:
        parent = super().parent()
        assert isinstance(parent, QWidget), f"HTMLDelegate.parent() returned non-QWidget: '{parent.__class__.__name__}'"
        return parent

    def setVerticalSpacing(self, spacing: int):
        self.customVerticalSpacing = spacing

    def set_text_size(self, size: int):
        self.text_size = size

    def setWordWrap(self, *, wrap: bool):
        self.word_wrap = wrap

    def nudgeItem(self, index: QModelIndex, x: int, y: int):
        self.nudgedModelIndexes[index] = (x, y)

    def createTextDocument(self, html: str, font: QFont, width: int) -> QTextDocument:
        doc = QTextDocument()
        doc.setHtml(FONT_SIZE_REPLACE_RE.sub(f"font-size:{self.text_size}pt;", html))
        doc.setDefaultFont(font)
        if not self.word_wrap:
            text_option = QTextOption()
            text_option.setWrapMode(QTextOption.NoWrap)
            doc.setDefaultTextOption(text_option)
        doc.setTextWidth(width)
        return doc

    def draw_badge(self, painter: QPainter, center: QPoint, radius: int, text: str):
        painter.save()
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # noqa: FBT003
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", max(10, self.text_size - 1), QFont.Bold))
        painter.drawText(QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2), Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    def process_icons(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
        event: QMouseEvent | None = None,
        *,
        show_tooltip: bool = False,
        execute_action: bool = False,
    ) -> tuple[int, bool]:
        icon_data: dict = index.data(_ICONS_DATA_ROLE)
        icon_width_total = 0
        handled_click = False
        if icon_data:
            icon_size = int(self.text_size * 1.5)
            icon_spacing = icon_data["spacing"]
            columns = icon_data["columns"]
            icons: list[tuple[Any, Callable, str]] = icon_data["icons"]
            bottom_badge_info = icon_data.get("bottom_badge")

            if (execute_action or show_tooltip) and bottom_badge_info:
                icons.append((None, bottom_badge_info["action"], bottom_badge_info["tooltip_callable"]()))

            icon_width_total = columns * (icon_size + icon_spacing) - icon_spacing

            for i, (icon_serialized, action, tooltip) in enumerate(icons):
                icon = self._get_icon(icon_serialized, icon_size)
                col, row = i % columns, i // columns
                x_offset = option.rect.left() + (icon_size + icon_spacing) * col
                y_offset = option.rect.top() + icon_spacing + (icon_size + icon_spacing) * row
                icon_rect = QRect(x_offset, y_offset, icon_size, icon_size)

                if painter and icon:
                    painter.fillRect(icon_rect, QColor(235, 245, 255))
                    icon.paint(painter, icon_rect)

                if event and icon_rect.contains(event.pos()):
                    if show_tooltip:
                        QToolTip.showText(event.globalPos(), tooltip, self.parent())
                        return icon_width_total, True
                    if execute_action and action:
                        action()
                        handled_click = True

            if bottom_badge_info:
                radius = icon_width_total // 2
                center_y = y_offset + icon_width_total + icon_spacing + radius if y_offset else option.rect.top() + icon_spacing + radius
                if painter:
                    self.draw_badge(painter, QPoint(option.rect.left() + radius, center_y), radius, bottom_badge_info["text_callable"]())

        if show_tooltip:
            QToolTip.hideText()
        return icon_width_total, handled_click

    def _get_icon(self, iconSerialized: Any, icon_size: int) -> QIcon | None:  # noqa: N803
        if isinstance(iconSerialized, QIcon):
            return iconSerialized
        if isinstance(iconSerialized, QStyle.StandardPixmap):
            return QApplication.style().standardIcon(iconSerialized)
        if isinstance(iconSerialized, str):
            return QIcon(QPixmap(iconSerialized).scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        if isinstance(iconSerialized, QPixmap):
            return QIcon(iconSerialized)
        if isinstance(iconSerialized, QImage):
            return QIcon(QPixmap.fromImage(iconSerialized))
        return None

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.translate(*self.nudgedModelIndexes.get(index, (0, 0)))

        # Handle the Decoration Role (icon)
        decoration = index.data(Qt.ItemDataRole.DecorationRole)
        if decoration:
            icon = QIcon(decoration)
            icon_rect = QRect(option.rect.topLeft(), option.decorationSize)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            option.rect.setLeft(icon_rect.right() + 5)

        display_data = index.data(Qt.DisplayRole)
        if not display_data:
            painter.restore()
            return

        icon_width_total, _ = self.process_icons(painter, option, index)
        new_rect = option.rect.adjusted(icon_width_total, 0, 0, 0)
        painter.setClipRect(new_rect)

        doc = self.createTextDocument(display_data, option.font, new_rect.width())
        ctx = doc.documentLayout().PaintContext()
        ctx.palette = option.palette

        if bool(option.state & QStyle.StateFlag.State_Selected):
            highlight_color = option.palette.highlight().color() if option.widget.hasFocus() else QColor(100, 100, 100)
            highlight_color.setAlpha(int(highlight_color.alpha() * 0.4))
            painter.fillRect(new_rect, highlight_color)
            ctx.palette.setColor(QPalette.ColorRole.Text, option.palette.highlightedText().color())
        else:
            ctx.palette.setColor(QPalette.ColorRole.Text, option.palette.text().color())

        painter.translate(new_rect.topLeft())
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        html: str | None = index.data(Qt.ItemDataRole.DisplayRole)
        if html is None:
            return super().sizeHint(option, index)

        parentWidget = self.parent()
        available_width, available_height = self._get_available_size(parentWidget, index)

        doc = self.createTextDocument(html, option.font, available_height)
        naturalWidth, naturalHeight = int(doc.idealWidth()), int(doc.size().height())
        ratio = 1.4
        min_width = naturalHeight * ratio
        max_height = min(naturalWidth / ratio, (naturalHeight * naturalWidth) / min_width)
        finalSize = QSize(int(max(naturalWidth, min_width)), int(min(naturalHeight, max_height) + self.customVerticalSpacing))

        icon_data: dict[str, Any] = index.data(_ICONS_DATA_ROLE)
        if icon_data:
            finalSize = self._adjust_size_for_icons(finalSize, icon_data)

        return finalSize

    def _get_available_size(self, parentWidget: QWidget, index: QModelIndex) -> tuple[int, int]:  # noqa: N803
        if isinstance(parentWidget, (QListWidget, QListView, QTreeView, QTreeWidget)):
            available_width, available_height = parentWidget.viewport().width(), parentWidget.viewport().height()
            if isinstance(parentWidget, (QTreeView, QTreeWidget)):
                depth = 1
                parentIndex = index.parent()
                while parentIndex.isValid():
                    depth += 1
                    parentIndex = parentIndex.parent()
                available_width -= depth * parentWidget.indentation()
        else:
            available_width, available_height = parentWidget.width(), parentWidget.height()
        return available_width, available_height

    def _adjust_size_for_icons(self, size: QSize, icon_data: dict[str, Any]) -> QSize:
        icon_size = int(self.text_size * 1.5)
        icon_spacing = icon_data["spacing"]
        columns = icon_data["columns"]
        rows = (len(icon_data["icons"]) + columns - 1) // columns
        total_icon_width = columns * (icon_size + icon_spacing)
        size.setWidth(size.width() + total_icon_width)
        total_icon_height = rows * (icon_size + icon_spacing) + 2 * icon_spacing
        if icon_data.get("bottom_badge"):
            total_icon_height += (icon_size + icon_spacing) + 2 * icon_spacing
        size.setHeight(max(size.height(), total_icon_height))
        return size

    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
            _, handled_click = self.process_icons(None, option, index, event=event, execute_action=True)
            if handled_click:
                return True
        return super().editorEvent(event, model, option, index)

    def handleIconTooltips(self, event: QMouseEvent, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """Must be called from the parent widget directly."""
        return self.process_icons(None, option, index, event=event, show_tooltip=True)[1]
