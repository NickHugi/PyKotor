from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QColumnView

from utility.ui_libraries.qt.widgets.itemviews.baseview import RobustAbstractItemView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu, QWidget


class RobustColumnView(RobustAbstractItemView, QColumnView):
    def __init__(self, parent: QWidget | None = None):
        QColumnView.__init__(self, parent)
        RobustAbstractItemView.__init__(self, parent)

    def build_context_menu(self) -> QMenu:
        menu = super().build_context_menu()

        column_menu = menu.addMenu("ColumnView")

        self._add_menu_action(
            column_menu,
            "Resize Grips Visible",
            self.resizeGripsVisible,
            self.setResizeGripsVisible,
            "resizeGripsVisible"
        )
        self._add_menu_action(
            column_menu,
            "Column Widths",
            self.columnWidths,
            self.setColumnWidths,
            "columnWidths",
            param_type=list
        )

        return menu
