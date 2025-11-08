from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListWidget, QMenu

from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QListWidgetItem, QMenu, QWidget


class RobustListWidget(QListWidget, RobustListView):
    """A list widget that supports common features and settings."""
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        QListWidget.__init__(self, parent)
        RobustListView.__init__(self, parent)

    def invert_selection(self):
        for i in range(self.count()):
            item: QListWidgetItem | None = self.item(i)
            if item is None:
                continue
            item.setSelected(not item.isSelected())

    def build_context_menu(self) -> QMenu:
        menu: QMenu = super().build_context_menu()

        # List-specific actions
        list_widget_menu: QMenu | None = menu.addMenu("ListWidget")
        assert list_widget_menu is not None

        # Sorting
        self._add_menu_action(list_widget_menu, "Enable Sorting", self.isSortingEnabled, self.setSortingEnabled, "sortingEnabled")
        self._add_simple_action(list_widget_menu, "Sort Items (Ascending)", lambda: self.sortItems(Qt.SortOrder.AscendingOrder))
        self._add_simple_action(list_widget_menu, "Sort Items (Descending)", lambda: self.sortItems(Qt.SortOrder.DescendingOrder))

        # Selection
        selection_menu: QMenu | None = list_widget_menu.addMenu("Selection")
        assert selection_menu is not None

        self._add_simple_action(selection_menu, "Select All", self.selectAll)
        self._add_simple_action(selection_menu, "Clear Selection", self.clearSelection)
        self._add_simple_action(selection_menu, "Invert Selection", self.invert_selection)

        # Item manipulation
        item_menu: QMenu | None = list_widget_menu.addMenu("Item Actions")
        assert item_menu is not None

        self._add_simple_action(item_menu, "Add Item", lambda: self.addItem("New Item"))
        self._add_simple_action(item_menu, "Insert Item", lambda: self.insertItem(self.currentRow(), "Inserted Item"))
        self._add_simple_action(item_menu, "Remove Current Item", lambda: self.takeItem(self.currentRow()))
        self._add_simple_action(item_menu, "Clear All Items", self.clear)
        self._add_simple_action(item_menu, "Edit Current Item", lambda: self.editItem(self.currentItem()))

        # View options
        view_menu: QMenu | None = list_widget_menu.addMenu("View Options")
        assert view_menu is not None

        self._add_menu_action(view_menu, "Wrap Items", self.isWrapping, self.setWrapping, "wrapping")
        self._add_menu_action(view_menu, "Uniform Item Sizes", self.uniformItemSizes, self.setUniformItemSizes, "uniformItemSizes")
        self._add_menu_action(view_menu, "Word Wrap", self.wordWrap, self.setWordWrap, "wordWrap")

        # Advanced options
        advanced_menu: QMenu | None = list_widget_menu.addMenu("Advanced")
        assert advanced_menu is not None

        self._add_menu_action(advanced_menu, "Drag Enabled", self.dragEnabled, self.setDragEnabled, "dragEnabled")
        self._add_menu_action(advanced_menu, "Drop Enabled", self.acceptDrops, self.setAcceptDrops, "dropEnabled")

        return menu
