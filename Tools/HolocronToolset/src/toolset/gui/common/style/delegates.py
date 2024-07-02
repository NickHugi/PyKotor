from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any, Callable

from qtpy.QtCore import (
    QEvent,
    QPoint,
    QRect,
    QSize,
    Qt,
)
from qtpy.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QMouseEvent,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
    QTextDocument,
)
from qtpy.QtWidgets import (
    QApplication,
    QListView,
    QListWidget,
    QStyle,
    QStyledItemDelegate,
    QToolTip,
    QTreeView,
    QTreeWidget,
    QWidget,
)

if TYPE_CHECKING:


    from qtpy.QtCore import (
        QAbstractItemModel,
        QModelIndex,
    )
    from qtpy.QtWidgets import (
        QStyleOptionViewItem,
    )


FONT_SIZE_REPLACE_RE = re.compile(r"font-size:\d+pt;")

_ICONS_DATA_ROLE = Qt.ItemDataRole.UserRole + 10


class HTMLDelegate(QStyledItemDelegate):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.text_size: int = 12
        self.customVerticalSpacing: int = 0
        self.nudgedModelIndexes: dict[QModelIndex, tuple[int, int]] = {}

    def parent(self) -> QWidget:
        parent = super().parent()
        assert isinstance(parent, QWidget), f"HTMLDelegate.parent() returned non-QWidget: '{parent.__class__.__name__}'"
        return parent

    def setVerticalSpacing(self, spacing: int):
        self.customVerticalSpacing = spacing

    def setTextSize(self, size: int):
        self.text_size = size

    def nudgeItem(
        self,
        index: QModelIndex,
        x: int,
        y: int,
    ):
        """Manually set the nudge offset for an item."""
        self.nudgedModelIndexes[index] = (x, y)

    def createTextDocument(self, html: str, font: QFont, width: int) -> QTextDocument:
        """Create and return a configured QTextDocument."""
        doc = QTextDocument()
        doc.setHtml(FONT_SIZE_REPLACE_RE.sub(f"font-size:{self.text_size}pt;", html))
        doc.setDefaultFont(font)
        doc.setTextWidth(width)
        return doc

    def draw_badge(
        self,
        painter: QPainter,
        center: QPoint,
        radius: int,
        text: str,
    ):
        painter.save()
        background_color = QColor(255, 255, 255)
        border_color = QColor(200, 200, 200)

        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(border_color, 2))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawEllipse(center, radius, radius)
        text_color = QColor(0, 0, 0)
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Arial", max(10, self.text_size - 1), QFont.Bold))
        text_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
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
            start_x = option.rect.left()
            start_y = option.rect.top() + icon_spacing
            y_offset = None
            icon_width_total = columns * (icon_size + icon_spacing) - icon_spacing

            for i, (iconSerialized, action, tooltip) in enumerate(icons):
                if isinstance(iconSerialized, QStyle.StandardPixmap):
                    icon = QApplication.style().standardIcon(iconSerialized)
                elif isinstance(iconSerialized, str):
                    pixmap = QPixmap(iconSerialized)
                    scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon = QIcon(scaled_pixmap)
                else:
                    icon = None
                col = i % columns
                row = i // columns
                x_offset = start_x + (icon_size + icon_spacing) * col
                y_offset = start_y + (icon_size + icon_spacing) * row

                icon_rect = QRect(x_offset, y_offset, icon_size, icon_size)

                if painter and icon is not None:
                    background_color = QColor(235, 245, 255)  # Light pastel blue
                    painter.fillRect(icon_rect, background_color)
                    icon.paint(painter, icon_rect)

                if event:
                    posForMouseEvent = event.pos()
                    if icon_rect.contains(posForMouseEvent):
                        if show_tooltip:
                            QToolTip.showText(event.globalPos(), tooltip, self.parent())
                            return icon_width_total, True

                        if execute_action and action:
                            action()
                            handled_click = True

            if bottom_badge_info:
                left_text = bottom_badge_info["text_callable"]()
                radius = icon_width_total // 2
                center_x = start_x + radius
                if y_offset is None:
                    center_y = option.rect.top() + icon_spacing + radius
                else:
                    center_y = y_offset + icon_width_total + icon_spacing + radius

                center = QPoint(center_x, center_y)
                if painter:
                    self.draw_badge(painter, center, radius, left_text)

        if show_tooltip:
            QToolTip.hideText()

        return icon_width_total, handled_click

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()

        nudge_offset = self.nudgedModelIndexes.get(index, (0, 0))
        painter.translate(*nudge_offset)

        display_data = index.data(Qt.DisplayRole)
        if not display_data:
            painter.restore()
            return

        icon_width_total, _ = self.process_icons(painter, option, index)

        new_rect = option.rect.adjusted(icon_width_total, 0, 0, 0)
        display_data = index.data(Qt.DisplayRole)
        if display_data:
            doc = self.createTextDocument(display_data, option.font, new_rect.width())
            ctx = doc.documentLayout().PaintContext()
            ctx.palette = option.palette
            if bool(option.state & QStyle.StateFlag.State_Selected):
                highlight_color = option.palette.highlight().color()
                if not option.widget.hasFocus():
                    highlight_color = QColor(100, 100, 100)  # Grey color
                highlight_color.setAlpha(int(highlight_color.alpha() * 0.4))
                painter.fillRect(new_rect, highlight_color)  # Fill only new_rect for highlighting
                ctx.palette.setColor(QPalette.Text, option.palette.highlightedText().color())
            else:
                ctx.palette.setColor(QPalette.Text, option.palette.text().color())
            painter.translate(new_rect.topLeft())
            doc.documentLayout().draw(painter, ctx)

        painter.restore()

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

        doc = self.createTextDocument(html, option.font, available_height)
        naturalWidth = int(doc.idealWidth())
        naturalHeight = int(doc.size().height())
        ratio = 1.4
        min_width = naturalHeight * ratio
        max_height = min(naturalWidth / ratio, (naturalHeight * naturalWidth) / min_width)
        adjusted_width = max(naturalWidth, min_width)
        adjusted_height = min(naturalHeight, max_height)
        finalSize = QSize(int(adjusted_width), int(adjusted_height + self.customVerticalSpacing))

        icon_data: dict[str, Any] = index.data(_ICONS_DATA_ROLE)
        if icon_data:
            icon_size = int(self.text_size * 1.5)
            icon_spacing = icon_data["spacing"]
            columns = icon_data["columns"]
            rows = (len(icon_data["icons"]) + columns - 1) // columns
            total_icon_width = columns * (icon_size + icon_spacing)
            finalSize.setWidth(finalSize.width() + total_icon_width)
            total_icon_height = rows * (icon_size + icon_spacing) + 2 * icon_spacing
            if icon_data.get("bottom_badge"):
                total_icon_height += (icon_size + icon_spacing) + 2 * icon_spacing
            finalSize.setHeight(max(finalSize.height(), total_icon_height))

        return finalSize

    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            assert isinstance(event, QMouseEvent)
            if event.button() == Qt.LeftButton:
                _, handled_click = self.process_icons(None, option, index, event=event, execute_action=True)
                if handled_click:
                    return True

        return super().editorEvent(event, model, option, index)

    def handleIconTooltips(self, event: QMouseEvent, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """Must be called from the parent widget directly."""
        _, handled_tooltip = self.process_icons(None, option, index, event=event, show_tooltip=True)
        return handled_tooltip
