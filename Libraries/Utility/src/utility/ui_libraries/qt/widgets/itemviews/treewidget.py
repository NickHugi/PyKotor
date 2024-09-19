from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QTreeWidget

from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu, QWidget


class RobustTreeWidget(QTreeWidget, RobustTreeView):
    """A tree widget that supports common features and settings."""
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        use_columns: bool = False,
    ):
        QTreeWidget.__init__(self, parent)
        RobustTreeView.__init__(self, parent, use_columns=use_columns)

    def build_context_menu(self) -> QMenu:
        menu = super().build_context_menu()

        tree_widget_menu = menu.addMenu("TreeWidget")
        advanced_menu = tree_widget_menu.addMenu("Advanced")

        # Tree-specific actions
        self._add_menu_action(
            tree_widget_menu,
            "Expand Current Item",
            lambda: self.isExpanded(self.currentIndex()),
            lambda x: self.expandItem(self.currentItem()) if x else self.collapseItem(self.currentItem()),
            "expandCurrentItem",
        )
        self._add_simple_action(tree_widget_menu, "Scroll to Current Item", lambda: self.scrollToItem(self.currentItem()))
        self._add_menu_action(
            tree_widget_menu,
            "Sort Items",
            self.isSortingEnabled,
            self.setSortingEnabled,
            "sortingEnabled",
        )
        self._add_menu_action(
            tree_widget_menu,
            "Column Count",
            self.columnCount,
            self.setColumnCount,
            "columnCount",
            param_type=int,
        )

        # Advanced actions
        self._add_menu_action(
            advanced_menu,
            "Header Hidden",
            self.isHeaderHidden,
            self.setHeaderHidden,
            "headerHidden",
        )
        self._add_menu_action(
            advanced_menu,
            "Root Is Decorated",
            self.rootIsDecorated,
            self.setRootIsDecorated,
            "rootIsDecorated",
        )
        self._add_menu_action(
            advanced_menu,
            "Items Expandable",
            self.itemsExpandable,
            self.setItemsExpandable,
            "itemsExpandable",
        )
        self._add_menu_action(
            advanced_menu,
            "Animated",
            self.isAnimated,
            self.setAnimated,
            "animated",
        )
        self._add_menu_action(
            advanced_menu,
            "Allow Expand on Single Click",
            self.allColumnsShowFocus,
            self.setAllColumnsShowFocus,
            "allColumnsShowFocus",
        )
        self._add_menu_action(
            advanced_menu,
            "Word Wrap",
            self.wordWrap,
            self.setWordWrap,
            "wordWrap",
        )

        # Item manipulation actions
        item_menu = tree_widget_menu.addMenu("Item Actions")
        self._add_simple_action(item_menu, "Add Top Level Item", lambda: self.addTopLevelItem(QTreeWidgetItem(["New Item"])))
        self._add_simple_action(item_menu, "Remove Current Item", lambda: self.takeTopLevelItem(self.indexOfTopLevelItem(self.currentItem())) if self.currentItem() else None)
        self._add_simple_action(item_menu, "Clear All Items", self.clear)
        self._add_simple_action(item_menu, "Edit Current Item", lambda: self.editItem(self.currentItem(), 0) if self.currentItem() else None)

        return menu
