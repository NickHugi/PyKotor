from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGraphicsWidget

from utility.ui_libraries.qt.widgets.itemviews.graphicsview import RobustGraphicsView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QGraphicsItem, QMenu, QWidget


class RobustGraphicsWidget(QGraphicsWidget, RobustGraphicsView):
    """A graphics widget that supports common features and settings."""
    def __init__(
        self,
        parent: QGraphicsItem | None = None,
        flags: Qt.WindowFlags | Qt.WindowType = Qt.WindowType.Widget,
        *args,
        should_call_qt_init: bool = True,
        **kwargs,
    ):
        if should_call_qt_init:
            QGraphicsWidget.__init__(self, parent, flags)
        RobustGraphicsView.__init__(self)

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = super().build_context_menu()


        # Graphics-specific actions
        graphics_widget_menu = menu.addMenu("GraphicsWidget")

        # Graphics-specific advanced actions
        advanced_menu = graphics_widget_menu.addMenu("Advanced")

        # Item manipulation actions
        item_menu = graphics_widget_menu.addMenu("Item Actions")

        return menu
