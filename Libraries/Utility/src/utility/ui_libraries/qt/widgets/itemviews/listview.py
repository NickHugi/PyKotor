from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QListView

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu, QWidget


class RobustListView(RobustAbstractItemView, QListView):
    def __init__(self, parent: QWidget | None = None):
        QListView.__init__(self, parent)
        RobustAbstractItemView.__init__(self, parent)

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = super().build_context_menu(parent)

        list_menu = menu.addMenu("ListView")

        self._add_exclusive_menu_action(
            list_menu,
            "View Mode",
            self.viewMode,
            self.setViewMode,
            options={
                "List Mode": QListView.ViewMode.ListMode,
                "Icon Mode": QListView.ViewMode.IconMode
            },
            settings_key="viewMode"
        )
        self._add_menu_action(
            list_menu,
            "Uniform Item Sizes",
            self.uniformItemSizes,
            self.setUniformItemSizes,
            "uniformItemSizes"
        )
        self._add_menu_action(
            list_menu,
            "Word Wrap",
            self.wordWrap,
            self.setWordWrap,
            "wordWrap"
        )
        self._add_menu_action(
            list_menu,
            "Selection Rectangle Visible",
            self.isSelectionRectVisible,
            self.setSelectionRectVisible,
            "selectionRectVisible"
        )

        return menu
