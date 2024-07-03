from __future__ import annotations

import unittest
from unittest.mock import Mock
from qtpy.QtCore import Qt, QModelIndex, QMimeData, QByteArray, QDataStream, QIODevice
from qtpy.QtWidgets import QApplication, QWidget
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.common.stream import BinaryReader
from pykotor.resource.generics.dlg import DLG, DLGNode, DLGLink, DLGEntry, DLGReply
from pykotor.resource.type import ResourceType
from toolset.gui.editors.dlg import DLGEditor, DLGStandardItemModel, DLGStandardItem, DLGTreeView
from toolset.gui.editor import Editor
from pykotor.common.language import LocalizedString
import json

from utility.logger_util import RobustRootLogger

app = QApplication([])

class TestDLGStandardItemModel(unittest.TestCase):
    def setUp(self):
        self.editor = DLGEditor(None, None)
        self.treeView: DLGTreeView = self.editor.ui.dialogTree
        self.model: DLGStandardItemModel = self.editor.ui.dialogTree.model()
        self.editor.core_dlg = DLG()

    def tearDown(self):
        self.model = None

    def create_item(self, node) -> DLGStandardItem:
        link = DLGLink(node=node)
        item = DLGStandardItem(link=link)
        self.model.loadDLGItemRec(item)
        return item

    def create_complex_tree(self) -> DLG:
        # Create the DLG structure with entries and replies
        dlg = DLG()
        entries = [DLGEntry(comment=f"E{i}") for i in range(5)]
        replies = [DLGReply(text=LocalizedString.from_english(f"R{i}")) for i in range(5, 10)]

        # Create a nested structure
        def add_links(parent_node: DLGNode, children: list[DLGNode]):
            for i, child in enumerate(children):
                link = DLGLink(node=child, list_index=i)
                parent_node.links.append(link)

        add_links(entries[0], [replies[0]])
        add_links(replies[0], [entries[1]])
        add_links(entries[1], [replies[1]])
        add_links(replies[1], [entries[2]])
        add_links(entries[2], [replies[2]])
        add_links(replies[2], [entries[3]])
        add_links(entries[3], [replies[3]])
        add_links(replies[3], [entries[4]])

        # Reuse nodes/links
        entries[2].links.append(DLGLink(node=entries[4], list_index=1))  # reuse E4
        replies[0].links.append(DLGLink(node=replies[1], list_index=1))  # reuse R7

        # Set starters
        dlg.starters.append(DLGLink(node=entries[0], list_index=0))  # Start with the first entry

        # Manually update list_index
        def update_list_index(links: list[DLGLink]):
            for i, link in enumerate(links):
                link.list_index = i
                if link.node:
                    update_list_index(link.node.links)

        update_list_index(dlg.starters)

        return dlg

    def test_dictionaries_filled_correctly(self):
        dlg = self.create_complex_tree()
        self.editor._loadDLG(dlg)
        items = []
        for link in dlg.starters:
            items.extend(self.model.linkToItems.get(link, []))

        for item in items:
            self.assertIn(item, self.model.linkToItems[item.link])
            self.assertIn(item, self.model.nodeToItems[item.link.node])
            self.assertIn(item.link, self.model.linkToItems)
            self.assertIn(item.link.node, self.model.nodeToItems)

    def test_hashing(self):
        dlg = self.create_complex_tree()
        self.editor._loadDLG(dlg)
        items = []
        for link in dlg.starters:
            items.extend(self.model.linkToItems.get(link, []))

        for item in items:
            self.assertEqual(hash(item), id(item))

    def test_link_list_index_sync(self):
        dlg: DLG = self.create_complex_tree()

        def verify_list_index(node: DLGNode):
            for i, link in enumerate(node.links):
                self.assertEqual(link.list_index, i, f"Link list_index {link.list_index} != {i} before loading to the model")
                verify_list_index(link.node)

        for i, link in enumerate(dlg.starters):
            self.assertEqual(link.list_index, i, f"Starter link list_index {link.list_index} != {i} before loading to the model")
            verify_list_index(link.node)

        self.editor._loadDLG(dlg)

        for i, link in enumerate(dlg.starters):
            self.assertEqual(link.list_index, i, f"Starter link list_index {link.list_index} != {i} after loading to the model")
            verify_list_index(link.node)

        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.linkToItems.get(link, []))

        for index, item in enumerate(items):
            self.assertEqual(item.link.list_index, index, f"{item.link.list_index} != {index}")


    def test_shift_item(self):  # sourcery skip: class-extract-method
        dlg = self.create_complex_tree()
        self.editor._loadDLG(dlg)
        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.linkToItems.get(link, []))

        self.model.shiftItem(items[0], 1)
        self.assertEqual(items[0].row(), 1)
        self.assertEqual(items[1].row(), 0)

    def test_move_item_to_index(self):
        dlg = self.create_complex_tree()
        self.editor._loadDLG(dlg)
        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.linkToItems.get(link, []))

        self.model.moveItemToIndex(items[0], 1, None)
        self.assertEqual(items[0].row(), 1)
        self.assertEqual(items[1].row(), 0)

    def test_paste_item(self):
        dlg = self.create_complex_tree()
        self.editor._loadDLG(dlg)
        items: list[DLGStandardItem] = []
        for link in dlg.starters:
            items.extend(self.model.linkToItems.get(link, []))

        node = DLGNode()
        self.model.pasteItem(items[0], node)

        pastedItem = items[0].child(0)
        self.assertEqual(pastedItem.link.node, node)

    def test_serialize_mime_data(self):
        dlg = self.create_complex_tree()
        self.editor._loadDLG(dlg)

        # Step 1: Generate a flat list of all QModelIndex objects
        all_indices = []

        def collect_indices(parent_index=QModelIndex()):
            for row in range(self.model.rowCount(parent_index)):
                index = self.model.index(row, 0, parent_index)
                if index.isValid():
                    all_indices.append(index)
                    collect_indices(index)

        collect_indices()

        # Step 2: Generate a flat list of all DLGStandardItem objects
        all_items = []
        invalid_indices = []

        for index in all_indices:
            item = self.model.itemFromIndex(index)
            if item is None:
                invalid_indices.append(index)
            else:
                all_items.append(item)

        mime_data = self.model.mimeData([item.index() for item in all_items])

        self.assertTrue(mime_data.hasFormat("application/x-qabstractitemmodeldatalist"))
        self.assertTrue(mime_data.hasFormat("application/x-pykotor-dlgbranch"))

        data = mime_data.data("application/x-pykotor-dlgbranch")
        stream = QDataStream(data, QIODevice.ReadOnly)
        model_memory_id = stream.readInt64()
        dlg_nodes_encoded = stream.readString()
        dlg_nodes_json = dlg_nodes_encoded.decode()
        dlg_nodes_dict = json.loads(dlg_nodes_json)

        # Deserialize and compare
        try:
            deserialized_node = DLGNode.from_dict(dlg_nodes_dict)
        except Exception:
            RobustRootLogger.exception("Unhandled exception by DLGNode.from_dict.")
            raise
        test1 = deserialized_node.links[0].node.links[0].node.links[0].node
        try:
            test2 = all_items[4].link.node
        except IndexError:
            RobustRootLogger.exception("IndexError: items[4].link.node")
            raise
        self.assertEqual(test1, test2)


if __name__ == "__main__":
    unittest.main()
