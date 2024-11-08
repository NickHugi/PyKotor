from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QPoint, QRect, QSize, Qt
from qtpy.QtWidgets import QLayout, QSizePolicy

if TYPE_CHECKING:
    from qtpy.QtCore import QMargins
    from qtpy.QtWidgets import QLayoutItem, QStyle, QWidget


class FlowLayout(QLayout):
    def __init__(
        self,
        parent: QWidget | None = None,
        margin: int = -1,
        h_spacing: int = -1,
        v_spacing: int = -1,
    ):
        super().__init__(parent)
        self.item_list: list[QLayoutItem] = []
        self.m_h_space: int = h_spacing
        self.m_v_space: int = v_spacing
        if margin < 0:
            return
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(
        self,
        item: QLayoutItem,
    ):
        self.item_list.append(item)

    def count(
        self,
    ) -> int:
        return len(self.item_list)

    def itemAt(
        self,
        index: int,
    ) -> QLayoutItem | None:
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(
        self,
        index: int,
    ) -> QLayoutItem | None:
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def setGeometry(
        self,
        rect: QRect,
    ):
        super().setGeometry(rect)
        self.rearrange_items(rect)

    def sizeHint(
        self,
    ) -> QSize:
        return self.calculate_size()

    def minimumSize(
        self,
    ) -> QSize:
        return self.calculate_size()

    def calculate_size(
        self,
    ) -> QSize:
        size: QSize = QSize()
        for item in self.item_list:
            size: QSize = size.expandedTo(item.minimumSize())
        margins: QMargins = self.contentsMargins()
        assert margins is not None
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def rearrange_items(
        self,
        rect: QRect,
    ):
        left, top, right, bottom = self.getContentsMargins()
        assert left is not None
        assert top is not None
        assert right is not None
        assert bottom is not None
        effective_rect: QRect = rect.adjusted(
            left,
            top,
            -right,
            -bottom,
        )
        assert effective_rect is not None
        x: float = effective_rect.x()
        y: float = effective_rect.y()
        line_height: int = 0
        max_width: int = effective_rect.width()
        max_height: int = effective_rect.height()

        current_line: list[QLayoutItem] = []

        def layout_current_line():
            nonlocal x, y, line_height
            if not current_line:
                return
            total_width: int = sum(
                item.sizeHint().width()
                for item in current_line
            )
            space_between: float = (  # pyright: ignore[reportAssignmentType]
                (max_width - total_width) / (len(current_line) - 1)
                if len(current_line) > 1
                else 0
            )
            x: float = effective_rect.x()
            for item in current_line:
                item.setGeometry(QRect(QPoint(int(x), int(y)), item.sizeHint()))
                x += item.sizeHint().width() + space_between
            y += line_height + space_y
            line_height = 0
            current_line.clear()

        for item in self.item_list:
            widget: QWidget | None = item.widget()
            assert widget is not None

            item_width: int = item.sizeHint().width()
            item_height: int = item.sizeHint().height()
            widget_style: QStyle | None = widget.style() if widget else None
            assert widget_style is not None
            space_x: int = (
                self.m_h_space
                if self.m_h_space >= 0
                else widget_style.layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal,
                )
            )
            space_y: int = (
                self.m_v_space
                if self.m_v_space >= 0
                else widget_style.layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical,
                )
            )

            if x + item_width > effective_rect.right():
                layout_current_line()

            if y + item_height + line_height + space_y > effective_rect.bottom():
                space_y = 0

            current_line.append(item)
            x += item_width + space_x
            line_height = max(line_height, item_height)

        layout_current_line()