from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QHeaderView

from utility.ui_libraries.qt.widgets.itemviews.baseview import RobustAbstractItemView

if TYPE_CHECKING:
    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QMenu, QWidget


class RobustHeaderView(RobustAbstractItemView, QHeaderView):
    def __init__(
        self,
        orientation: Qt.Orientation,
        parent: QWidget | None = None,
    ):
        QHeaderView.__init__(self, orientation, parent)
        RobustAbstractItemView.__init__(self, parent)

    def build_context_menu(self) -> QMenu:
        menu = super().build_context_menu()
        header_menu = menu.addMenu("HeaderView")

        self._add_menu_action(
            header_menu,
            "Sections Movable",
            self.sectionsMovable,
            self.setSectionsMovable,
            "sectionsMovable"
        )
        self._add_menu_action(
            header_menu,
            "Sections Clickable",
            self.sectionsClickable,
            self.setSectionsClickable,
            "sectionsClickable"
        )
        self._add_menu_action(
            header_menu,
            "Sort Indicator Shown",
            self.isSortIndicatorShown,
            self.setSortIndicatorShown,
            "sortIndicatorShown"
        )
        self._add_menu_action(
            header_menu,
            "Stretch Last Section",
            self.stretchLastSection,
            self.setStretchLastSection,
            "stretchLastSection"
        )
        self._add_menu_action(
            header_menu,
            "Cascading Section Resizes",
            self.cascadingSectionResizes,
            self.setCascadingSectionResizes,
            "cascadingSectionResizes"
        )

        return menu
