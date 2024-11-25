from __future__ import annotations

import json
import os
import sys
import unittest

from typing import Any, Union, cast

from loggerplus import RobustLogger
from pykotor.common.language import LocalizedString
from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGLink, DLGNode, DLGReply
from qtpy.QtCore import QByteArray, QDataStream, QIODevice, QMimeData, QModelIndex, Qt
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import QApplication
from toolset.data.installation import HTInstallation
from toolset.gui.editors.dlg import DLGEditor, DLGStandardItem, DLGStandardItemModel, DLGTreeView, _DLG_MIME_DATA_ROLE, _MODEL_INSTANCE_ID_ROLE, QT_STANDARD_ITEM_FORMAT

app = QApplication(sys.argv)

K1_PATH: str | None = os.environ.get("K1_PATH")


@unittest.skipIf(
    bool(K1_PATH if K1_PATH is None else not os.path.exists(K1_PATH)),
    "K1_PATH environment variable is not set or not found on disk.",
)
class TestDLGStandardItemModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert K1_PATH is not None
        cls.installation: HTInstallation = HTInstallation(K1_PATH, "", tsl=False)

    def setUp(self):
        self.editor: DLGEditor = DLGEditor(None, self.installation)
        self.tree_view: DLGTreeView = self.editor.ui.dialogTree
        model: DLGStandardItemModel | None = self.editor.ui.dialogTree.model()
        assert isinstance(model, DLGStandardItemModel)
        self.model: DLGStandardItemModel = model
        self.editor.core_dlg = DLG()

    def tearDown(self):
        self.model.clear()

    def create_item(
        self,
        node: DLGNode,
    ) -> DLGStandardItem:
        link: DLGLink = DLGLink(node=node)
        item: DLGStandardItem = DLGStandardItem(link=link)
        self.model.load_dlg_item_rec(item)
        return item

    def create_complex_tree(self) -> DLG:
        # Create the DLG structure with entries and replies
        dlg = DLG()
        entries: list[DLGEntry] = [DLGEntry(comment=f"E{i}") for i in range(5)]
        replies: list[DLGReply] = [DLGReply(text=LocalizedString.from_english(f"R{i}")) for i in range(5, 10)]

        # Create a nested structure
        def add_links(
            parent_node: DLGNode,
            children: list[DLGNode],
        ):
            for i, child in enumerate(children):
                if isinstance(parent_node, DLGEntry):
                    assert isinstance(child, DLGReply)
                elif isinstance(parent_node, DLGReply):
                    assert isinstance(child, DLGEntry)
                else:
                    assert False, f"{parent_node.__class__.__name__}: {parent_node}"
                link: DLGLink = DLGLink(node=child, list_index=i)
                parent_node.links.append(link)

        # Create primary path
        add_links(entries[0], [replies[0]])  # E0 -> R5
        add_links(replies[0], [entries[1]])  # R5 -> E1
        add_links(entries[1], [replies[1]])  # E1 -> R6
        add_links(replies[1], [entries[2]])  # R6 -> E2
        add_links(entries[2], [replies[2]])  # E2 -> R7
        add_links(replies[2], [entries[3]])  # R7 -> E3
        add_links(entries[3], [replies[3]])  # E3 -> R8
        add_links(replies[3], [entries[4]])  # R8 -> E4

        # Add cross-links that create cycles but avoid infinite recursion
        # Since DLGLink instances are unique (they have unique hashes),
        # this creates new edges to existing nodes
        entries[2].links.append(DLGLink(node=replies[1], list_index=1))  # E2 -> R6 (creates cycle)
        replies[0].links.append(DLGLink(node=entries[4], list_index=1))  # R5 -> E4 (shortcut)

        # Set starters
        dlg.starters.append(DLGLink(node=entries[0], list_index=0))  # Start with E0
        dlg.starters.append(DLGLink(node=entries[1], list_index=1))  # Alternative start with E1

        # Manually update list_index
        def update_list_index(
            links: list[DLGLink],
            seen_nodes: set[DLGNode] | None = None,
        ):
            if seen_nodes is None:
                seen_nodes = set()

            for i, link in enumerate(links):
                link.list_index = i
                if link.node is None or link.node in seen_nodes:
                    continue
                seen_nodes.add(link.node)
                update_list_index(link.node.links, seen_nodes)

        update_list_index(dlg.starters)
        return dlg

    def test_dictionaries_filled_correctly(self):
        dlg: DLG = self.create_complex_tree()
        self.editor._load_dlg(dlg)
        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.link_to_items.get(link, []))

        for item in items:
            assert item.link is not None
            assert item in self.model.link_to_items[item.link]
            assert item in self.model.node_to_items[item.link.node]
            assert item.link in self.model.link_to_items
            assert item.link.node is not None
            assert item.link.node in self.model.node_to_items

    def test_hashing(self):
        dlg: DLG = self.create_complex_tree()
        self.editor._load_dlg(dlg)
        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.link_to_items.get(link, []))

        for item in items:
            assert hash(item) == id(item)

    def test_link_list_index_sync(self):
        dlg: DLG = self.create_complex_tree()

        def verify_list_index(
            node: DLGNode,
            seen_nodes: set[DLGNode] | None = None,
        ):
            if seen_nodes is None:
                seen_nodes = set()
            
            for i, link in enumerate(node.links):
                assert link.list_index == i, f"Link list_index {link.list_index} == {i} before loading to the model"
                if link.node is None or link.node in seen_nodes:
                    continue
                seen_nodes.add(link.node)
                verify_list_index(link.node, seen_nodes)

        for i, link in enumerate(dlg.starters):
            assert link.list_index == i, f"Starter link list_index {link.list_index} == {i} before loading to the model"
            verify_list_index(link.node)

        self.editor._load_dlg(dlg)

        for i, link in enumerate(dlg.starters):
            assert link.list_index == i, f"Starter link list_index {link.list_index} == {i} after loading to the model"
            verify_list_index(link.node)

        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.link_to_items.get(link, []))

        for index, item in enumerate(items):
            assert item.link is not None
            assert item.link.list_index == index, f"{item.link.list_index} == {index}"

    def test_shift_item(self):
        dlg: DLG = self.create_complex_tree()
        self.editor._load_dlg(dlg)
        items_before: list[DLGStandardItem] = []
        for link in dlg.starters:
            items_before.extend(self.model.link_to_items.get(link, []))

        self.model.shift_item(items_before[0], 1)

        # Re-fetch items from model
        items_after: list[DLGStandardItem] = []
        for i in range(self.model.rowCount()):
            item: DLGStandardItem | QStandardItem = self.model.item(i, 0)
            if isinstance(item, DLGStandardItem):
                items_after.append(item)

        # Now check that the items are in the expected order
        self.assertEqual(items_after[0], items_before[1])
        self.assertEqual(items_after[1], items_before[0])

    def test_paste_item(self):
        dlg: DLG = self.create_complex_tree()
        self.editor._load_dlg(dlg)
        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.link_to_items.get(link, []))

        self.model.paste_item(
            items[0],
            DLGLink(
                node=DLGReply(
                    text=LocalizedString.from_english("Pasted Entry"),
                    list_index=69,
                ),
            ),
        )

        pasted_item: QStandardItem | None = items[0].child(0)
        assert isinstance(pasted_item, DLGStandardItem), f"{pasted_item!r} is not a DLGStandardItem, instead was {pasted_item.__class__.__name__}"
        assert pasted_item.link is not None, f"{pasted_item.link!r} is None"
        assert pasted_item.link.node is not None, f"{pasted_item.link.node!r} is None"
        assert items[0].link is not None, f"{items[0].link!r} is None (items[0] is {items[0]!r})"
        assert pasted_item.link == items[0].link.node.links[0], f"{pasted_item.link!r} != {items[0].link.node.links[0]!r}"

    def test_serialize_mime_data(self):
        dlg: DLG = self.create_complex_tree()
        self.editor._load_dlg(dlg)

        # Step 1: Generate a flat list of all QModelIndex objects
        all_indices: list[QModelIndex] = []

        def collect_indices(
            parent_index: QModelIndex = QModelIndex(),
        ):
            for row in range(self.model.rowCount(parent_index)):
                index: QModelIndex = self.model.index(row, 0, parent_index)
                if not index.isValid():
                    continue
                all_indices.append(index)
                collect_indices(index)

        collect_indices()

        # Step 2: Generate a flat list of all DLGStandardItem objects
        all_items: list[DLGStandardItem] = []
        invalid_indices: list[QModelIndex] = []

        for index in all_indices:
            item: QStandardItem | None = self.model.itemFromIndex(index)  # pyright: ignore[reportArgumentType]
            if item is None:
                invalid_indices.append(index)
                continue
            assert isinstance(item, DLGStandardItem), f"item is {item.__class__.__name__}, {item} for index {index} ({index.row()}, {index.column()}) expected DLGStandardItem"
            all_items.append(item)

        mime_data: QMimeData = self.model.mimeData([item.index() for item in all_items])

        assert mime_data.hasFormat(QT_STANDARD_ITEM_FORMAT)

        data: QByteArray = mime_data.data(QT_STANDARD_ITEM_FORMAT)
        stream: QDataStream = QDataStream(data, QIODevice.OpenModeFlag.ReadOnly)

        while not stream.atEnd():
            row: int = stream.readInt32()
            column: int = stream.readInt32()
            num_roles: int = stream.readInt32()
            for _ in range(num_roles):
                role: int = stream.readInt32()
                if role == int(Qt.ItemDataRole.DisplayRole):
                    display_data: str = stream.readQString()
                elif role == _DLG_MIME_DATA_ROLE:
                    dlg_data_encoded: bytes | str | None = cast(Union[bytes, str, None], stream.readQString())
                    assert dlg_data_encoded is not None, "dlg_data_encoded is None, expected byte-encoded string of DLG data."
                    dlg_data_dict: dict[str | int, Any] = json.loads(dlg_data_encoded)
                elif role == _MODEL_INSTANCE_ID_ROLE:
                    model_id: int = stream.readInt64()

        # Deserialize and compare
        deserialized_link: DLGLink = DLGLink.from_dict(dlg_data_dict)
        assert deserialized_link == all_items[4].link, f"{deserialized_link!r} != {all_items[4].link!r}"


if __name__ == "__main__":
    try:
        import pytest  # pyright: ignore[reportMissingImports]
    except ImportError:
        unittest.main()
    else:
        pytest.main(["-v", "-s", __file__])
