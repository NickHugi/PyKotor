from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any, Callable

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QEvent, QPoint, QRect, QSize, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QIcon, QImage, QMouseEvent, QPainter, QPalette, QPen, QPixmap, QTextDocument, QTextOption
from qtpy.QtWidgets import QApplication, QListView, QListWidget, QStyle, QStyledItemDelegate, QToolTip, QTreeView, QTreeWidget, QWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject
    from qtpy.QtGui import QAbstractTextDocumentLayout
    from qtpy.QtWidgets import QStyleOptionViewItem


FONT_SIZE_REPLACE_RE: re.Pattern[str] = re.compile(r"font-size:\d+pt;")

ICONS_DATA_ROLE: int = Qt.ItemDataRole.UserRole + 10


class HTMLDelegate(QStyledItemDelegate):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        word_wrap: bool = True,
    ):
        super().__init__(parent)
        self.text_size: int = 12
        self.custom_vertical_spacing: int = 0
        self.nudged_model_indexes: dict[QModelIndex, tuple[int, int]] = {}
        self.word_wrap: bool = word_wrap

    def parent(self) -> QWidget:
        parent: QObject | None = super().parent()
        assert isinstance(parent, QWidget), f"HTMLDelegate.parent() returned non-QWidget: '{parent.__class__.__name__}'"
        return parent

    def set_vertical_spacing(
        self,
        spacing: int,
    ):
        self.custom_vertical_spacing = spacing

    def set_text_size(
        self,
        size: int,
    ):
        self.text_size = size

    def set_word_wrap(
        self,
        *,
        wrap: bool,
    ):
        self.word_wrap = wrap

    def nudge_item(
        self,
        index: QModelIndex,
        x: int,
        y: int,
    ):
        """Manually set the nudge offset for an item."""
        self.nudged_model_indexes[index] = (x, y)

    def create_text_document(
        self,
        html: str,
        font: QFont,
        width: int,
    ) -> QTextDocument:
        """Create and return a configured QTextDocument."""
        doc = QTextDocument()
        doc.setHtml(FONT_SIZE_REPLACE_RE.sub(f"font-size:{self.text_size}pt;", html))
        doc.setDefaultFont(font)
        if not self.word_wrap:
            text_option = QTextOption()
            text_option.setWrapMode(QTextOption.WrapMode.NoWrap)
            doc.setDefaultTextOption(text_option)
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
        painter.setFont(QFont("Arial", max(10, self.text_size - 1), QFont.Weight.Bold))
        text_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    def process_icons(  # noqa: C901, PLR0913, PLR0912, PLR0915
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
        event: QMouseEvent | None = None,
        *,
        show_tooltip: bool = False,
        execute_action: bool = False,
    ) -> tuple[int, bool]:
        icon_data: dict = index.data(ICONS_DATA_ROLE)
        icon_width_total = 0
        handled_click = False
        if icon_data:
            icon_size: int = int(self.text_size * 1.5)
            icon_spacing: int = icon_data["spacing"]
            columns: int = icon_data["columns"]
            icons: list[tuple[Any, Callable, str]] = icon_data["icons"]

            bottom_badge_info: dict[str, Any] | None = icon_data.get("bottom_badge")
            if (execute_action or show_tooltip) and bottom_badge_info:
                icons.append((None, bottom_badge_info["action"], bottom_badge_info["tooltip_callable"]()))
            y_offset: int | None = None
            icon_width_total: int = columns * (icon_size + icon_spacing) - icon_spacing

            for i, (iconSerialized, action, tooltip) in enumerate(icons):
                icon: QIcon | None = None

                if isinstance(iconSerialized, QIcon):
                    icon = iconSerialized
                elif isinstance(iconSerialized, QStyle.StandardPixmap):
                    q_app_style: QStyle | None = QApplication.style()
                    if q_app_style is None:
                        RobustLogger().error("QApplication.style() returned None")
                        continue
                    icon = q_app_style.standardIcon(iconSerialized)
                elif isinstance(iconSerialized, str):
                    scaled_pixmap: QPixmap = QPixmap(iconSerialized).scaled(
                        icon_size,
                        icon_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    icon = QIcon(scaled_pixmap)
                elif isinstance(iconSerialized, QPixmap):
                    icon = QIcon(iconSerialized)
                elif isinstance(iconSerialized, QImage):
                    icon = QIcon(QPixmap.fromImage(iconSerialized))
                else:
                    icon = None
                col: int = i % columns
                row: int = i // columns
                x_offset: int = option.rect.left() + (icon_size + icon_spacing) * col
                y_offset = option.rect.top() + icon_spacing + (icon_size + icon_spacing) * row

                icon_rect: QRect = QRect(x_offset, y_offset, icon_size, icon_size)

                if painter and icon is not None:
                    background_color: QColor = QColor(235, 245, 255)  # Light pastel blue
                    painter.fillRect(icon_rect, background_color)
                    icon.paint(painter, icon_rect)

                if event:
                    pos_for_mouse_event: QPoint = event.pos()
                    if icon_rect.contains(pos_for_mouse_event):
                        if show_tooltip:
                            QToolTip.showText(
                                event.globalPos()  # pyright: ignore[reportAttributeAccessIssue]
                                if qtpy.QT5
                                else event.globalPosition().toPoint(),
                                tooltip,
                                self.parent(),
                            )
                            return icon_width_total, True

                        if execute_action and action is not None:
                            action()
                            handled_click = True

            if bottom_badge_info:
                radius: int = icon_width_total // 2
                if y_offset is None:
                    center_y: int = option.rect.top() + icon_spacing + radius
                else:
                    center_y = y_offset + icon_width_total + icon_spacing + radius
                if painter:
                    self.draw_badge(painter, QPoint(option.rect.left() + radius, center_y), radius, bottom_badge_info["text_callable"]())

        if show_tooltip:
            QToolTip.hideText()

        return icon_width_total, handled_click

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ):
        painter.save()

        nudge_offset: tuple[int, int] = self.nudged_model_indexes.get(index, (0, 0))
        painter.translate(*nudge_offset)

        # Handle the Decoration Role (icon)
        decoration: Any = index.data(Qt.ItemDataRole.DecorationRole)
        if decoration:
            icon: QIcon = QIcon(decoration)
            icon_size: QSize = option.decorationSize
            icon_rect: QRect = QRect(option.rect.topLeft(), icon_size)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            option.rect.setLeft(icon_rect.right() + 5)  # Adjust text starting position

        display_data: Any = index.data(Qt.ItemDataRole.DisplayRole)
        if not display_data:
            painter.restore()
            return

        icon_width_total, _ = self.process_icons(painter, option, index)

        new_rect: QRect = option.rect.adjusted(icon_width_total, 0, 0, 0)
        painter.setClipRect(new_rect)
        display_data: Any = index.data(Qt.ItemDataRole.DisplayRole)
        if display_data:
            doc: QTextDocument = self.create_text_document(display_data, option.font, new_rect.width())
            doc_layout: QAbstractTextDocumentLayout | None = doc.documentLayout()
            if doc_layout is None:
                RobustLogger().error("QTextDocument.documentLayout() returned None")
                painter.restore()
                return
            ctx: QAbstractTextDocumentLayout.PaintContext = doc_layout.PaintContext()
            ctx.palette = option.palette
            if bool(option.state & QStyle.StateFlag.State_Selected):
                highlight_color: QColor = option.palette.highlight().color()
                if not option.widget.hasFocus():
                    highlight_color = QColor(100, 100, 100)  # Grey color
                highlight_color.setAlpha(int(highlight_color.alpha() * 0.4))
                painter.fillRect(new_rect, highlight_color)  # Fill only new_rect for highlighting
                ctx.palette.setColor(QPalette.ColorRole.Text, option.palette.highlightedText().color())
            else:
                ctx.palette.setColor(QPalette.ColorRole.Text, option.palette.text().color())
            painter.translate(new_rect.topLeft())
            doc_layout.draw(painter, ctx)

        painter.restore()

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QSize:
        html: str | None = index.data(Qt.ItemDataRole.DisplayRole)
        if html is None:
            return super().sizeHint(option, index)

        parent_widget: QWidget = self.parent()
        if isinstance(parent_widget, (QListWidget, QListView, QTreeView, QTreeWidget)):
            viewport: QWidget | None = parent_widget.viewport()
            if viewport is None:
                RobustLogger().error("QWidget.viewport() returned None")
                return super().sizeHint(option, index)
            available_width: int = viewport.width()
            available_height: int = viewport.height()
            if isinstance(parent_widget, (QTreeView, QTreeWidget)):  # TreeView/Widget have indentation to account for.
                depth: int = 1
                parent_index: QModelIndex = index.parent()
                while parent_index.isValid():
                    depth += 1
                    parent_index = parent_index.parent()
                available_width = available_width - (depth * parent_widget.indentation())
        else:
            available_width: int = parent_widget.width()
            available_height: int = parent_widget.height()

        doc: QTextDocument = self.create_text_document(html, option.font, available_height)
        natural_width: int = int(doc.idealWidth())
        natural_height: int = int(doc.size().height())
        ratio: float = 1.4
        min_width: float = natural_height * ratio
        max_height: float = min(natural_width / ratio, (natural_height * natural_width) / min_width)
        adjusted_width: float = max(natural_width, min_width)
        adjusted_height: float = min(natural_height, max_height)
        final_size: QSize = QSize(int(adjusted_width), int(adjusted_height + self.custom_vertical_spacing))

        icon_data: dict[str, Any] = index.data(ICONS_DATA_ROLE)
        if icon_data:
            icon_size = int(self.text_size * 1.5)
            icon_spacing: int = icon_data["spacing"]
            columns: int = icon_data["columns"]
            rows: int = (len(icon_data["icons"]) + columns - 1) // columns
            total_icon_width: int = columns * (icon_size + icon_spacing)
            final_size.setWidth(final_size.width() + total_icon_width)
            total_icon_height: int = rows * (icon_size + icon_spacing) + 2 * icon_spacing
            if icon_data.get("bottom_badge"):
                total_icon_height += (icon_size + icon_spacing) + 2 * icon_spacing
            final_size.setHeight(max(final_size.height(), total_icon_height))

        return final_size

    def editorEvent(
        self,
        event: QEvent,
        model: QAbstractItemModel,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease:
            assert isinstance(event, QMouseEvent)
            if event.button() == Qt.MouseButton.LeftButton:
                _, handled_click = self.process_icons(None, option, index, event=event, execute_action=True)
                if handled_click:
                    return True

        return super().editorEvent(event, model, option, index)

    def handle_icon_tooltips(
        self,
        event: QMouseEvent,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        """Must be called from the parent widget directly."""
        _, handled_tooltip = self.process_icons(None, option, index, event=event, show_tooltip=True)
        return handled_tooltip
