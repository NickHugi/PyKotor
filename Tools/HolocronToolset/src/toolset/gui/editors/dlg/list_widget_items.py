from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qtpy.QtCore import Qt

from toolset.gui.editors.dlg.list_widget_base import DLGListWidget
from toolset.gui.editors.dlg.list_widget_item import DLGListWidgetItem

if TYPE_CHECKING:
    import weakref

    from pykotor.resource.generics.dlg import DLGLink
    from toolset.gui.editors.dlg.editor import DLGEditor


class DLGListWidgetItems(DLGListWidget):
    def __init__(self, parent: DLGEditor | None = None):
        super().__init__(parent)

    def add_item(
        self,
        text: str,
        link: DLGLink,
        ref: weakref.ref[DLGLink] | None = None,
        data: Any | None = None,
    ) -> DLGListWidgetItem:
        """Add a new item to the list widget."""
        item = DLGListWidgetItem(text, link=link, ref=ref)
        if data is not None:
            item.setData(Qt.ItemDataRole.UserRole, data)
        self.addItem(item)
        return item

    def insert_item(
        self,
        index: int,
        text: str,
        link: DLGLink,
        ref: weakref.ref[DLGLink] | None = None,
        data: Any | None = None,
    ) -> DLGListWidgetItem:
        """Insert a new item at the specified index."""
        item = DLGListWidgetItem(text, link=link, ref=ref)
        if data is not None:
            item.setData(Qt.ItemDataRole.UserRole, data)
        self.insertItem(index, item)
        return item

    def remove_item(self, index: int):
        """Remove an item at the specified index."""
        if 0 <= index < self.count():
            self.takeItem(index)

    def clear_items(self):
        """Clear all items from the list widget."""
        self.clear()

    def move_item(self, from_index: int, to_index: int):
        """Move an item from one index to another."""
        if not (0 <= from_index < self.count() and 0 <= to_index < self.count()):
            return

        item = self.takeItem(from_index)
        if not item:
            return

        self.insertItem(to_index, item)
        if self._on_item_moved_callback:
            self._on_item_moved_callback(from_index, to_index)

    def swap_items(self, index1: int, index2: int):
        """Swap two items in the list widget."""
        if not (0 <= index1 < self.count() and 0 <= index2 < self.count()):
            return

        item1 = self.item(index1)
        item2 = self.item(index2)
        if not (item1 and item2):
            return

        # Store data
        data1 = {role: item1.data(role) for role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.UserRole)}
        data2 = {role: item2.data(role) for role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.UserRole)}

        # Swap data
        for role, value in data1.items():
            item2.setData(role, value)
        for role, value in data2.items():
            item1.setData(role, value)

        if self._on_item_moved_callback:
            self._on_item_moved_callback(index1, index2)

    def get_all_items(self) -> list[DLGListWidgetItem]:
        """Get all items in the list widget."""
        return [self.item(i) for i in range(self.count())]  # type: ignore

    def get_all_links(self) -> list[DLGLink]:
        """Get all DLGLinks from the items."""
        return [item.link for item in self.get_all_items()]

    def get_all_link_refs(self) -> list[weakref.ref[DLGLink]]:
        """Get all DLGLink references from the items."""
        return [item._link_ref for item in self.get_all_items() if item._link_ref is not None]
