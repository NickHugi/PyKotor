from __future__ import annotations

from typing import TYPE_CHECKING, cast

from qtpy.QtCore import QRect, QSize, Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QListView, QStyle, QStyledItemDelegate

from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex
    from qtpy.QtGui import QPainter
    from qtpy.QtWidgets import QStyleOptionViewItem, QWidget


class RobustTileView(RobustListView):
    """A view that displays items in a 2D grid."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setWrapping(True)
        self.setUniformItemSizes(False)
        self.setItemDelegate(TileItemDelegate(self))

    def setIconSize(self, size: QSize):
        super().setIconSize(size)
        self.setGridSize(QSize(size.width(), size.height()))


class TileItemDelegate(QStyledItemDelegate):
    """A delegate that paints items in a 2D grid."""

    # @print_func_call
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()

        # Draw background
        if bool(option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())

        # Draw icon
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        icon_size = min(option.rect.width(), option.rect.height() - 40)  # Increased space for text
        icon_rect = QRect(option.rect.left() + (option.rect.width() - icon_size) // 2, option.rect.top() + 5, icon_size, icon_size)

        if isinstance(icon, QIcon):
            pixmap = icon.pixmap(icon_size, icon_size)
        scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(icon_rect, scaled_pixmap)

        # Draw text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            text_rect = QRect(
                option.rect.left() + 5,  # Add some padding
                icon_rect.bottom() + 5,
                option.rect.width() - 10,  # Subtract padding from both sides
                option.rect.height() - icon_rect.height() - 10,
            )
            painter.drawText(text_rect, cast(Qt.AlignmentFlag, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap), text)

        painter.restore()

    # @print_func_call
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        # Get the icon size
        icon_size = cast(QListView, self.parent()).iconSize()

        # Calculate the width based on icon size
        width = max(120, icon_size.width() + 20)  # Minimum width of 120, or icon width + padding

        # Get the text and calculate its height
        text = index.data(Qt.ItemDataRole.DisplayRole)
        fm = option.fontMetrics
        text_width = width - 10  # Accounting for left and right padding
        text_height = fm.boundingRect(QRect(0, 0, text_width, 1000), Qt.TextFlag.TextWordWrap, text).height()

        # Calculate the total height
        height = icon_size.height() + 10 + text_height + 10  # icon height + padding + text height + bottom padding

        return QSize(width, height)
