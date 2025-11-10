from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QTransform
from qtpy.QtWidgets import QGraphicsView

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu, QWidget


class RobustGraphicsView(RobustAbstractItemView, QGraphicsView):
    def __new__(cls, *args, **kwargs):
        # For PySide6 compatibility with multiple inheritance
        return QGraphicsView.__new__(cls)

    def __init__(
        self,
        parent: QWidget | None = None,
        *args,
        should_call_qt_init: bool = True,
        **kwargs,
    ):
        if should_call_qt_init:
            QGraphicsView.__init__(self, parent)
        RobustAbstractItemView.__init__(self, parent, *args, **kwargs)

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = super().build_context_menu(parent)

        graphics_menu = menu.addMenu("GraphicsView")

        self._add_exclusive_menu_action(
            graphics_menu,
            "Drag Mode",
            self.dragMode,
            self.setDragMode,
            options={
                "No Drag": QGraphicsView.NoDrag,
                "Scroll Hand Drag": QGraphicsView.ScrollHandDrag,
                "Rubber Band Drag": QGraphicsView.RubberBandDrag
            },
            settings_key="dragMode"
        )
        self._add_menu_action(
            graphics_menu,
            "Cache Mode",
            self.cacheMode,
            self.setCacheMode,
            "cacheMode",
            param_type=QGraphicsView.CacheMode
        )
        self._add_menu_action(
            graphics_menu,
            "Render Hints",
            self.renderHints,
            self.setRenderHints,
            "renderHints",
            param_type=int
        )
        self._add_menu_action(
            graphics_menu,
            "Transform",
            self.transform,
            self.setTransform,
            "transform",
            param_type=QTransform
        )

        return menu
