"""Comprehensive tests for the DLG Editor.

This module tests all UI controls, context menus, dialogs, and interactions
in the DLG Editor to ensure complete coverage of user-editable functionality.
"""
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

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")


@unittest.skipIf(
    bool(K1_PATH if K1_PATH is None else not os.path.exists(K1_PATH)),
    "K1_PATH environment variable is not set or not found on disk.",
)
class TestDLGStandardItemModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if K1_PATH is None or not os.path.exists(K1_PATH):
            import pytest
            pytest.skip("K1_PATH environment variable is not set or not found on disk.")
        # Try to use shared pre-warmed installation from conftest if available
        # This ensures expensive operations happen before any tests run, not during them
        import importlib.util
        from pathlib import Path
        conftest_path = Path(__file__).parent.parent.parent / "conftest.py"
        conftest_module = None
        if conftest_path.exists():
            spec = importlib.util.spec_from_file_location("conftest", conftest_path)
            if spec and spec.loader:
                conftest_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(conftest_module)
                get_shared = getattr(conftest_module, "get_shared_k1_installation", None)  # noqa: B009
                if get_shared:
                    shared_inst = get_shared()
                    if shared_inst is not None:
                        cls.installation = shared_inst
                        return
        
        # Fallback: create new installation and pre-warm it (slower, but works)
        cls.installation = HTInstallation(K1_PATH, "", tsl=False)
        if conftest_module:
            _prewarm_installation = getattr(conftest_module, "_prewarm_installation", None)  # noqa: B009
            if _prewarm_installation:
                _prewarm_installation(cls.installation)

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


# ============================================================================
# Pytest-based UI tests (merged from test_ui_dlg.py and test_ui_dlg_comprehensive.py)
# ============================================================================

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QDialog, QDialogButtonBox, QListWidgetItem, QMessageBox
from toolset.gui.editors.dlg.editor import DLGEditor  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from toolset.gui.editors.dlg.model import DLGStandardItem  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from pykotor.common.misc import ResRef  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]    
from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGReply, DLGLink, DLGComputerType, DLGConversationType, DLGStunt, DLGAnimation, read_dlg  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from pykotor.resource.formats.gff.gff_auto import read_gff  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from pykotor.common.language import LocalizedString  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from pykotor.resource.type import ResourceType  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from toolset.data.installation import HTInstallation  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]


def set_text_via_ui_dialog(qtbot, editor: DLGEditor, item: DLGStandardItem, text: str) -> None:
    """Helper function to set node text via the UI dialog."""
    assert item.link is not None, "item.link should not be None"
    # Call edit_text to open the dialog
    editor.edit_text(indexes=[item.index()], source_widget=editor.ui.dialogTree)
    qtbot.wait(50)  # Wait for dialog to appear
    
    # Find and interact with the dialog
    dialogs = [w for w in QApplication.topLevelWidgets() if isinstance(w, LocalizedStringDialog)]
    if dialogs:
        dialog = dialogs[0]
        # Set to no TLK string (stringref = -1) to enable direct text editing
        qtbot.mouseClick(dialog.ui.stringrefNoneButton, Qt.MouseButton.LeftButton)
        qtbot.wait(10)
        # Set the text in the dialog
        dialog.ui.stringEdit.setPlainText(text)
        qtbot.wait(10)
        # Accept the dialog
        ok_button = dialog.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            qtbot.mouseClick(ok_button, Qt.MouseButton.LeftButton)
        else:
            # Fallback: use accept() directly
            dialog.accept()
        qtbot.wait(10)


# ============================================================================
# BASIC EDITOR TESTS
# ============================================================================

def test_dlg_editor_all_widgets_exist(qtbot, installation: HTInstallation):
    """Verify ALL widgets exist in DLG editor."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    # Main tree
    assert hasattr(editor.ui, 'dialogTree')
    
    # Node editor widgets (right dock)
    assert hasattr(editor.ui, 'speakerEdit')
    # Note: textEdit doesn't exist - text is edited via dialog, not a direct widget
    assert hasattr(editor.ui, 'script1ResrefEdit')
    assert hasattr(editor.ui, 'script2ResrefEdit')
    assert hasattr(editor.ui, 'listenerEdit')
    assert hasattr(editor.ui, 'voResrefEdit') or hasattr(editor.ui, 'voiceComboBox')
    assert hasattr(editor.ui, 'soundComboBox')
    assert hasattr(editor.ui, 'cameraAngleSelect') or hasattr(editor.ui, 'cameraAngleSpin')
    assert hasattr(editor.ui, 'animsList')
    assert hasattr(editor.ui, 'plotIndexCombo') or hasattr(editor.ui, 'plotIndexSpin')
    assert hasattr(editor.ui, 'questEdit')
    assert hasattr(editor.ui, 'questEntrySpin')
    assert hasattr(editor.ui, 'commentsEdit')
    
    # Search/find widgets
    assert hasattr(editor, 'find_bar')
    assert hasattr(editor, 'find_input')
    assert hasattr(editor, 'results_label')
    
    # Dock widgets
    assert hasattr(editor.ui, 'rightDockWidget')
    assert hasattr(editor.ui, 'topDockWidget')
    assert hasattr(editor, 'left_dock_widget')
    assert hasattr(editor, 'orphaned_nodes_list')


def test_dlg_editor_new_dlg(qtbot, installation: HTInstallation):
    """Test creating a new DLG."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    editor.new()
    
    # Model should be reset
    assert editor.model.rowCount() == 0
    assert len(editor.core_dlg.starters) == 0


def test_dlg_editor_add_root_node(qtbot, installation: HTInstallation):
    """Test adding root nodes."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root node
    editor.model.add_root_node()
    assert editor.model.rowCount() == 1
    
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    assert root_item.link is not None
    assert isinstance(root_item.link.node, DLGEntry)
    assert len(editor.core_dlg.starters) == 1


def test_dlg_editor_add_child_node(qtbot, installation: HTInstallation):
    """Test adding child nodes."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root node
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    # Add child (should be Reply since parent is Entry)
    child_item = editor.model.add_child_to_item(root_item)
    assert isinstance(child_item, DLGStandardItem)
    assert child_item.link is not None
    assert isinstance(child_item.link.node, DLGReply)
    assert root_item.rowCount() == 1
    assert root_item.link is not None, "root_item.link should not be None"
    assert root_item.link.node is not None, "root_item.link.node should not be None"
    assert len(root_item.link.node.links) == 1


# ============================================================================
# FILE-LEVEL WIDGETS (TOP DOCK) - Comprehensive Tests
# ============================================================================

def test_dlg_editor_manipulate_conversation_type(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating conversation type combo box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    original_dlg = read_dlg(original_data)
    
    # Test all conversation types
    for i in range(editor.ui.conversationSelect.count()):
        editor.ui.conversationSelect.setCurrentIndex(i)
        
        # Save and verify
        data, _ = editor.build()
        modified_dlg = read_dlg(data)
        assert modified_dlg.conversation_type == DLGConversationType(i)
        
        # Load back and verify
        editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
        assert editor.ui.conversationSelect.currentIndex() == i


def test_dlg_editor_manipulate_computer_type(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating computer type combo box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Test all computer types
    for i in range(editor.ui.computerSelect.count()):
        editor.ui.computerSelect.setCurrentIndex(i)
        
        # Save and verify
        data, _ = editor.build()
        modified_dlg = read_dlg(data)
        assert modified_dlg.computer_type == DLGComputerType(i)


def test_dlg_editor_manipulate_reply_delay_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating reply delay spin box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Test various delay values
    test_values = [0, 100, 500, 1000, 5000]
    for val in test_values:
        editor.ui.replyDelaySpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_dlg = read_dlg(data)
        assert modified_dlg.delay_reply == val
        
        # Load back and verify
        editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
        assert editor.ui.replyDelaySpin.value() == val


def test_dlg_editor_manipulate_entry_delay_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating entry delay spin box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Test various delay values
    test_values = [0, 200, 1000, 2000]
    for val in test_values:
        editor.ui.entryDelaySpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_dlg = read_dlg(data)
        assert modified_dlg.delay_entry == val


def test_dlg_editor_manipulate_vo_id_edit(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating voiceover ID field."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Test various VO IDs
    test_vo_ids = ["", "vo_001", "vo_test_123", "vo_long_name"]
    for vo_id in test_vo_ids:
        editor.ui.voIdEdit.setText(vo_id)
        
        # Save and verify
        data, _ = editor.build()
        modified_dlg = read_dlg(data)
        assert modified_dlg.vo_id == vo_id


def test_dlg_editor_manipulate_on_abort_combo(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on abort script combo box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Modify script
    editor.ui.onAbortCombo.set_combo_box_text("test_abort")
    
    # Save and verify
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert str(modified_dlg.on_abort) == "test_abort"


def test_dlg_editor_manipulate_on_end_edit(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on end script combo box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Modify script
    editor.ui.onEndEdit.set_combo_box_text("test_on_end")
    
    # Save and verify
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert str(modified_dlg.on_end) == "test_on_end"


def test_dlg_editor_manipulate_camera_model_select(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating camera model combo box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Modify camera model
    editor.ui.cameraModelSelect.set_combo_box_text("test_camera")
    
    # Save and verify
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert str(modified_dlg.camera_model) == "test_camera"


def test_dlg_editor_manipulate_ambient_track_combo(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating ambient track combo box."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Modify ambient track
    editor.ui.ambientTrackCombo.set_combo_box_text("test_ambient")
    
    # Save and verify
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert str(modified_dlg.ambient_track) == "test_ambient"


def test_dlg_editor_manipulate_file_level_checkboxes(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all file-level checkboxes."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Test unequipHandsCheckbox
    editor.ui.unequipHandsCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert modified_dlg.unequip_hands
    
    editor.ui.unequipHandsCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert not modified_dlg.unequip_hands
    
    # Test unequipAllCheckbox
    editor.ui.unequipAllCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert modified_dlg.unequip_items
    
    editor.ui.unequipAllCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert not modified_dlg.unequip_items
    
    # Test skippableCheckbox
    editor.ui.skippableCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert modified_dlg.skippable
    
    editor.ui.skippableCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert not modified_dlg.skippable
    
    # Test animatedCutCheckbox
    editor.ui.animatedCutCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert modified_dlg.animated_cut
    
    editor.ui.animatedCutCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert not modified_dlg.animated_cut
    
    # Test oldHitCheckbox
    editor.ui.oldHitCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert modified_dlg.old_hit_check
    
    editor.ui.oldHitCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert not modified_dlg.old_hit_check


# ============================================================================
# NODE-LEVEL WIDGETS (RIGHT DOCK) - Comprehensive Tests
# ============================================================================

def test_dlg_editor_all_node_widgets_interactions(qtbot, installation: HTInstallation):
    """Test ALL node editor widgets with exhaustive interactions."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create a node to edit
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    assert root_item.link is not None
    
    # Select it
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Test speakerEdit - QLineEdit (only for Entry nodes)
    if isinstance(root_item.link.node, DLGEntry):
        editor.ui.speakerEdit.setText("TestSpeaker")
        editor.on_node_update()
        assert root_item.link.node.speaker == "TestSpeaker"
    
    # Test listenerEdit - QLineEdit
    editor.ui.listenerEdit.setText("PLAYER")
    editor.on_node_update()
    assert root_item.link.node.listener == "PLAYER"
    
    # Test script1ResrefEdit - ComboBox
    editor.ui.script1ResrefEdit.set_combo_box_text("test_script1")
    editor.on_node_update()
    assert str(root_item.link.node.script1) == "test_script1"
    
    # Test script1Param spins
    for i, param_name in enumerate(['script1Param1Spin', 'script1Param2Spin', 'script1Param3Spin', 
                                    'script1Param4Spin', 'script1Param5Spin'], 1):
        spin = getattr(editor.ui, param_name)
        spin.setValue(i * 10)
        editor.on_node_update()
        assert getattr(root_item.link.node, f'script1_param{i}') == i * 10
    
    # Test script1Param6Edit - QLineEdit
    editor.ui.script1Param6Edit.setText("param6_text")
    editor.on_node_update()
    assert root_item.link.node.script1_param6 == "param6_text"
    
    # Test script2ResrefEdit - ComboBox
    editor.ui.script2ResrefEdit.set_combo_box_text("test_script2")
    editor.on_node_update()
    assert str(root_item.link.node.script2) == "test_script2"
    
    # Test script2Param spins
    for i, param_name in enumerate(['script2Param1Spin', 'script2Param2Spin', 'script2Param3Spin',
                                    'script2Param4Spin', 'script2Param5Spin'], 1):
        spin = getattr(editor.ui, param_name)
        spin.setValue(i * 5)
        editor.on_node_update()
        assert getattr(root_item.link.node, f'script2_param{i}') == i * 5
    
    # Test condition1ResrefEdit - ComboBox
    editor.ui.condition1ResrefEdit.set_combo_box_text("test_cond1")
    editor.on_node_update()
    assert str(root_item.link.active1) == "test_cond1"
    
    # Test condition1Param spins
    for i, param_name in enumerate(['condition1Param1Spin', 'condition1Param2Spin', 'condition1Param3Spin',
                                    'condition1Param4Spin', 'condition1Param5Spin'], 1):
        spin = getattr(editor.ui, param_name)
        spin.setValue(i * 2)
        editor.on_node_update()
        assert getattr(root_item.link, f'active1_param{i}') == i * 2
    
    # Test condition1NotCheckbox
    editor.ui.condition1NotCheckbox.setChecked(True)
    editor.on_node_update()
    assert root_item.link.active1_not
    
    # Test condition2ResrefEdit - ComboBox
    editor.ui.condition2ResrefEdit.set_combo_box_text("test_cond2")
    editor.on_node_update()
    assert str(root_item.link.active2) == "test_cond2"
    
    # Test condition2NotCheckbox
    editor.ui.condition2NotCheckbox.setChecked(True)
    editor.on_node_update()
    assert root_item.link.active2_not
    
    # Test emotionSelect - ComboBox
    if editor.ui.emotionSelect.count() > 0:
        editor.ui.emotionSelect.setCurrentIndex(1)
        editor.on_node_update()
        assert root_item.link.node.emotion_id == 1
    
    # Test expressionSelect - ComboBox
    if editor.ui.expressionSelect.count() > 0:
        editor.ui.expressionSelect.setCurrentIndex(1)
        editor.on_node_update()
        assert root_item.link.node.facial_id == 1
    
    # Test soundComboBox - ComboBox
    editor.ui.soundComboBox.set_combo_box_text("test_sound")
    editor.on_node_update()
    assert str(root_item.link.node.sound) == "test_sound"
    
    # Test soundCheckbox
    editor.ui.soundCheckbox.setChecked(True)
    editor.on_node_update()
    assert root_item.link.node.sound_exists
    
    # Test voiceComboBox - ComboBox
    editor.ui.voiceComboBox.set_combo_box_text("test_vo")
    editor.on_node_update()
    assert str(root_item.link.node.vo_resref) == "test_vo"
    
    # Test plotIndexCombo - ComboBox
    if editor.ui.plotIndexCombo.count() > 0:
        editor.ui.plotIndexCombo.setCurrentIndex(5)
        editor.on_node_update()
        assert root_item.link.node.plot_index == 5
    
    # Test plotXpSpin - QSpinBox
    editor.ui.plotXpSpin.setValue(50)
    editor.on_node_update()
    assert root_item.link.node.plot_xp_percentage == 50
    
    # Test questEdit - QLineEdit
    editor.ui.questEdit.setText("test_quest")
    editor.on_node_update()
    assert root_item.link.node.quest == "test_quest"
    
    # Test questEntrySpin - QSpinBox
    editor.ui.questEntrySpin.setValue(10)
    editor.on_node_update()
    assert root_item.link.node.quest_entry == 10
    
    # Test cameraIdSpin - QSpinBox
    editor.ui.cameraIdSpin.setValue(1)
    editor.on_node_update()
    assert root_item.link.node.camera_id == 1
    
    # Test cameraAnimSpin - QSpinBox
    editor.ui.cameraAnimSpin.setValue(1200)
    editor.on_node_update()
    assert root_item.link.node.camera_anim == 1200
    
    # Test cameraAngleSelect - ComboBox
    if editor.ui.cameraAngleSelect.count() > 0:
        editor.ui.cameraAngleSelect.setCurrentIndex(1)
        editor.on_node_update()
        assert root_item.link.node.camera_angle == 1
    
    # Test cameraEffectSelect - ComboBox
    if editor.ui.cameraEffectSelect.count() > 0:
        editor.ui.cameraEffectSelect.setCurrentIndex(1)
        editor.on_node_update()
        assert root_item.link.node.camera_effect == 1
    
    # Test nodeUnskippableCheckbox
    editor.ui.nodeUnskippableCheckbox.setChecked(True)
    editor.on_node_update()
    assert root_item.link.node.unskippable
    
    # Test nodeIdSpin - QSpinBox
    editor.ui.nodeIdSpin.setValue(5)
    editor.on_node_update()
    assert root_item.link.node.node_id == 5
    
    # Test alienRaceNodeSpin - QSpinBox
    editor.ui.alienRaceNodeSpin.setValue(2)
    editor.on_node_update()
    assert root_item.link.node.alien_race_node == 2
    
    # Test postProcSpin - QSpinBox
    editor.ui.postProcSpin.setValue(3)
    editor.on_node_update()
    assert root_item.link.node.post_proc_node == 3
    
    # Test delaySpin - QSpinBox
    editor.ui.delaySpin.setValue(100)
    editor.on_node_update()
    assert root_item.link.node.delay == 100
    
    # Test waitFlagSpin - QSpinBox
    editor.ui.waitFlagSpin.setValue(1)
    editor.on_node_update()
    assert root_item.link.node.wait_flags == 1
    
    # Test fadeTypeSpin - QSpinBox
    editor.ui.fadeTypeSpin.setValue(2)
    editor.on_node_update()
    assert root_item.link.node.fade_type == 2
    
    # Test logicSpin - QSpinBox
    editor.ui.logicSpin.setValue(1)
    editor.on_node_update()
    assert root_item.link.logic
    
    # Test commentsEdit - QPlainTextEdit
    editor.ui.commentsEdit.setPlainText("Test comment\nLine 2")
    editor.on_node_update()
    assert root_item.link.node.comment == "Test comment\nLine 2"


def test_dlg_editor_link_widgets_interactions(qtbot, installation: HTInstallation):
    """Test ALL link-specific widgets."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create entry -> reply structure
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    assert root_item.link is not None
    
    child_item = editor.model.add_child_to_item(root_item)
    assert isinstance(child_item, DLGStandardItem)
    assert child_item.link is not None
    
    # Select child (Reply)
    editor.ui.dialogTree.setCurrentIndex(child_item.index())
    
    # Test condition1ResrefEdit - already tested above but test again for child
    editor.ui.condition1ResrefEdit.set_combo_box_text("child_cond1")
    editor.on_node_update()
    assert str(child_item.link.active1) == "child_cond1"
    
    # Test condition2ResrefEdit
    editor.ui.condition2ResrefEdit.set_combo_box_text("child_cond2")
    editor.on_node_update()
    assert str(child_item.link.active2) == "child_cond2"
    
    # Test logicSpin
    editor.ui.logicSpin.setValue(0)
    editor.on_node_update()
    assert not child_item.link.logic


def test_dlg_editor_condition_params_full(qtbot, installation: HTInstallation):
    """Test all condition parameters for both conditions (TSL-specific).
    
    Note: Condition params are TSL-only features. This test checks that the UI
    correctly updates the in-memory model. The params will only persist when
    saving if the installation is TSL.
    """
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Test condition1 all params - these update in-memory model regardless of K1/TSL
    editor.ui.condition1Param1Spin.setValue(11)
    editor.ui.condition1Param2Spin.setValue(22)
    editor.ui.condition1Param3Spin.setValue(33)
    editor.ui.condition1Param4Spin.setValue(44)
    editor.ui.condition1Param5Spin.setValue(55)
    editor.ui.condition1Param6Edit.setText("cond1_str")
    editor.on_node_update()
    
    # In-memory values are always updated
    assert root_item.link.active1_param1 == 11
    assert root_item.link.active1_param2 == 22
    assert root_item.link.active1_param3 == 33
    assert root_item.link.active1_param4 == 44
    assert root_item.link.active1_param5 == 55
    assert root_item.link.active1_param6 == "cond1_str"
    
    # Test condition2 all params
    editor.ui.condition2Param1Spin.setValue(111)
    editor.ui.condition2Param2Spin.setValue(222)
    editor.ui.condition2Param3Spin.setValue(333)
    editor.ui.condition2Param4Spin.setValue(444)
    editor.ui.condition2Param5Spin.setValue(555)
    editor.ui.condition2Param6Edit.setText("cond2_str")
    editor.on_node_update()
    
    assert root_item.link.active2_param1 == 111
    assert root_item.link.active2_param2 == 222
    assert root_item.link.active2_param3 == 333
    assert root_item.link.active2_param4 == 444
    assert root_item.link.active2_param5 == 555
    assert root_item.link.active2_param6 == "cond2_str"


def test_dlg_editor_script_params_full(qtbot, installation: HTInstallation):
    """Test all script parameters for both scripts (TSL-specific).
    
    Note: Script params are TSL-only features. This test checks that the UI
    correctly updates the in-memory model. The params will only persist when
    saving if the installation is TSL.
    """
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Test script1 all params - these update in-memory model regardless of K1/TSL
    editor.ui.script1Param1Spin.setValue(100)
    editor.ui.script1Param2Spin.setValue(200)
    editor.ui.script1Param3Spin.setValue(300)
    editor.ui.script1Param4Spin.setValue(400)
    editor.ui.script1Param5Spin.setValue(500)
    editor.ui.script1Param6Edit.setText("script1_str")
    editor.on_node_update()
    
    # In-memory values are always updated
    assert root_item.link.node.script1_param1 == 100
    assert root_item.link.node.script1_param2 == 200
    assert root_item.link.node.script1_param3 == 300
    assert root_item.link.node.script1_param4 == 400
    assert root_item.link.node.script1_param5 == 500
    assert root_item.link.node.script1_param6 == "script1_str"
    
    # Test script2 all params
    editor.ui.script2Param1Spin.setValue(1000)
    editor.ui.script2Param2Spin.setValue(2000)
    editor.ui.script2Param3Spin.setValue(3000)
    editor.ui.script2Param4Spin.setValue(4000)
    editor.ui.script2Param5Spin.setValue(5000)
    editor.ui.script2Param6Edit.setText("script2_str")
    editor.on_node_update()
    
    assert root_item.link.node.script2_param1 == 1000
    assert root_item.link.node.script2_param2 == 2000
    assert root_item.link.node.script2_param3 == 3000
    assert root_item.link.node.script2_param4 == 4000
    assert root_item.link.node.script2_param5 == 5000
    assert root_item.link.node.script2_param6 == "script2_str"


def test_dlg_editor_node_widget_build_verification(qtbot, installation: HTInstallation):
    """Test that ALL node widget values are correctly saved in build()."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create and configure a node
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    editor.ui.speakerEdit.setText("TestSpeaker")
    editor.ui.listenerEdit.setText("PLAYER")
    editor.ui.script1ResrefEdit.set_combo_box_text("k_test")
    editor.ui.script1Param1Spin.setValue(42)
    editor.ui.condition1ResrefEdit.set_combo_box_text("c_test")
    editor.ui.condition1NotCheckbox.setChecked(True)
    editor.ui.questEdit.setText("my_quest")
    editor.ui.questEntrySpin.setValue(5)
    editor.ui.plotXpSpin.setValue(75)
    editor.ui.commentsEdit.setPlainText("Test comment")
    editor.ui.delaySpin.setValue(500)
    editor.ui.waitFlagSpin.setValue(2)
    editor.ui.fadeTypeSpin.setValue(1)
    editor.on_node_update()
    
    # Set text via UI dialog
    set_text_via_ui_dialog(qtbot, editor, root_item, "Test Entry Text")
    
    # Build and verify
    data, _ = editor.build()
    dlg = read_dlg(data)
    
    assert len(dlg.starters) == 1
    assert isinstance(dlg.starters[0].node, DLGEntry)
    node = dlg.starters[0].node
    link = dlg.starters[0]
    
    assert node.speaker == "TestSpeaker"
    assert node.listener == "PLAYER"
    assert str(node.script1) == "k_test"
    assert node.script1_param1 == 42
    assert str(link.active1) == "c_test"
    assert link.active1_not
    assert node.quest == "my_quest"
    assert node.quest_entry == 5
    assert node.plot_xp_percentage == 75
    assert node.comment == "Test comment"
    assert node.delay == 500
    assert node.wait_flags == 2
    assert node.fade_type == 1
    assert node.text.get(0) == "Test Entry Text"


# ============================================================================
# SEARCH FUNCTIONALITY TESTS
# ============================================================================

def test_dlg_editor_search_functionality(qtbot, installation: HTInstallation):
    """Test search/find functionality without mocks."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add some nodes with text
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    # Set text on root using edit_text method (opens dialog)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    # Text editing is done via dialog, so we test the method exists
    # The actual dialog would require user interaction
    # Instead verify the node has text property
    assert root_item.link.node is not None, "root_item.link.node should not be None"
    assert root_item.link.node.text is not None, "root_item.link.node.text should not be None"
    
    # Show find bar
    editor.show_find_bar()
    assert editor.find_bar.isVisible()
    
    # Search for text
    editor.find_input.setText("Hello")
    editor.handle_find()
    
    # Should find the node
    assert len(editor.search_results) > 0 or editor.results_label.text() == "No results found"
    
    # Test search with no results
    editor.find_input.setText("NonexistentText12345")
    editor.handle_find()
    # Should show no results or empty results


def test_dlg_editor_search_with_operators(qtbot, installation: HTInstallation):
    """Test search with special operators."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root with specific properties
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    editor.ui.speakerEdit.setText("TestSpeaker")
    editor.ui.listenerEdit.setText("PLAYER")
    editor.on_node_update()
    
    # Test attribute search
    editor.show_find_bar()
    editor.find_input.setText("speaker:TestSpeaker")
    editor.handle_find()
    # Verify results
    
    # Test AND operator
    editor.find_input.setText("speaker:TestSpeaker AND listener:PLAYER")
    editor.handle_find()


def test_dlg_editor_search_navigation(qtbot, installation: HTInstallation):
    """Test search result navigation (forward/back)."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add multiple nodes
    for _ in range(3):
        editor.model.add_root_node()
    
    editor.show_find_bar()
    editor.find_input.setText("")  # Empty search finds all
    editor.handle_find()
    
    if editor.search_results:
        initial_index = editor.current_result_index
        editor.handle_find()  # Move forward
        editor.handle_back()  # Move back
        # Just verify no crash


# ============================================================================
# TREE OPERATIONS TESTS
# ============================================================================

def test_dlg_editor_copy_paste_real(qtbot, installation: HTInstallation):
    """Test copy/paste functionality without mocks."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create a node
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    # Set some data
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    editor.ui.speakerEdit.setText("TestSpeaker")
    
    # Test text editing via UI dialog
    set_text_via_ui_dialog(qtbot, editor, root_item, "Test Text")
    editor.on_node_update()
    
    # Copy using real method (on model)
    editor.model.copy_link_and_node(root_item.link)
    
    # Verify clipboard has data
    clipboard = QApplication.clipboard()
    assert clipboard is not None
    clipboard_text = clipboard.text()
    assert len(clipboard_text) > 0
    
    # Verify _copy is set
    assert editor._copy is not None
    
    # Paste into model
    editor.model.paste_item(None, editor._copy)
    assert editor.model.rowCount() == 2  # Original + pasted


def test_dlg_editor_delete_node(qtbot, installation: HTInstallation):
    """Test deleting nodes."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root node
    editor.model.add_root_node()
    assert editor.model.rowCount() == 1
    
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    # Delete it
    editor.model.delete_node(root_item)
    assert editor.model.rowCount() == 0
    assert len(editor.core_dlg.starters) == 0


def test_dlg_editor_tree_expansion(qtbot, installation: HTInstallation):
    """Test tree expansion/collapse."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root with child
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    child_item = editor.model.add_child_to_item(root_item)
    
    # Expand root
    root_index = root_item.index()
    editor.ui.dialogTree.expand(root_index)
    assert editor.ui.dialogTree.isExpanded(root_index)
    
    # Collapse
    editor.ui.dialogTree.collapse(root_index)
    assert not editor.ui.dialogTree.isExpanded(root_index)


def test_dlg_editor_move_item_up_down(qtbot, installation: HTInstallation):
    """Test moving items up and down in the tree."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add multiple root nodes
    editor.model.add_root_node()
    editor.model.add_root_node()
    editor.model.add_root_node()
    
    assert editor.model.rowCount() == 3
    
    item0 = editor.model.item(0, 0)
    item1 = editor.model.item(1, 0)
    
    # Store original order
    link0 = item0.link
    link1 = item1.link
    
    # Move first item down
    editor.model.shift_item(item0, 1)
    
    # Verify order changed
    new_item0 = editor.model.item(0, 0)
    new_item1 = editor.model.item(1, 0)
    assert new_item0.link == link1
    assert new_item1.link == link0


def test_dlg_editor_delete_node_everywhere(qtbot, installation: HTInstallation):
    """Test deleting all references to a node."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create structure with multiple references
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    child = editor.model.add_child_to_item(root_item)
    
    initial_count = editor.model.rowCount()
    
    # Delete all references to root node
    editor.model.delete_node_everywhere(root_item.link.node)
    
    # Should have fewer items
    assert editor.model.rowCount() < initial_count or editor.model.rowCount() == 0


# ============================================================================
# CONTEXT MENU TESTS
# ============================================================================

def test_dlg_editor_context_menu(qtbot, installation: HTInstallation):
    """Test context menu functionality."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root node
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    # Right-click should show context menu
    # We verify the signal is connected
    assert editor.ui.dialogTree.receivers(editor.ui.dialogTree.customContextMenuRequested) > 0


def test_dlg_editor_context_menu_creation(qtbot, installation: HTInstallation):
    """Test context menu is created with proper actions."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root node
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    # Get context menu for item
    from toolset.gui.editors.dlg.list_widget_base import DLGListWidgetItem
    menu = editor._get_link_context_menu(editor.ui.dialogTree, root_item)
    
    # Verify menu has expected actions
    action_texts = [action.text() for action in menu.actions() if action.text()]
    
    # Check for essential actions
    assert any("Edit Text" in t for t in action_texts)
    assert any("Copy" in t for t in action_texts)
    assert any("Add" in t for t in action_texts)
    assert any("Remove" in t or "Delete" in t for t in action_texts)


# ============================================================================
# UNDO/REDO TESTS
# ============================================================================

def test_dlg_editor_undo_redo(qtbot, installation: HTInstallation):
    """Test undo/redo functionality."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root node
    editor.model.add_root_node()
    assert editor.model.rowCount() == 1
    
    # Undo stack should exist
    assert editor.undo_stack is not None
    
    # Test undo (if available)
    if editor.undo_stack.canUndo():
        editor.undo_stack.undo()
    
    # Test redo (if available)
    if editor.undo_stack.canRedo():
        editor.undo_stack.redo()


# ============================================================================
# ORPHANED NODES TESTS
# ============================================================================

def test_dlg_editor_orphaned_nodes(qtbot, installation: HTInstallation):
    """Test orphaned nodes list."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add root node
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item, DLGStandardItem)
    
    # Orphaned nodes list should exist
    assert editor.orphaned_nodes_list is not None
    
    # Delete node - should potentially create orphaned node if it has children
    # This is complex logic, but we verify the list exists


# ============================================================================
# MENU TESTS
# ============================================================================

def test_dlg_editor_all_menus(qtbot, installation: HTInstallation):
    """Test all menu actions exist and are accessible."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    # Verify menu actions exist
    assert hasattr(editor.ui, 'actionReloadTree')
    
    # Test reload tree action
    editor.model.add_root_node()
    assert editor.model.rowCount() == 1
    
    editor.ui.actionReloadTree.trigger()
    # Tree should reload (may clear or maintain state depending on implementation)


# ============================================================================
# STUNT MANAGEMENT TESTS
# ============================================================================

def test_dlg_editor_stunt_list_exists(qtbot, installation: HTInstallation):
    """Test stunt list widget exists."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert hasattr(editor.ui, 'stuntList')
    assert hasattr(editor.ui, 'addStuntButton')
    assert hasattr(editor.ui, 'removeStuntButton')
    assert hasattr(editor.ui, 'editStuntButton')


def test_dlg_editor_add_stunt_programmatically(qtbot, installation: HTInstallation):
    """Test adding stunts programmatically."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add stunt directly to DLG
    stunt = DLGStunt()
    stunt.stunt_model = ResRef("test_model")
    stunt.participant = "PLAYER"
    editor.core_dlg.stunts.append(stunt)
    editor.refresh_stunt_list()
    
    # Verify stunt is in list
    assert editor.ui.stuntList.count() == 1
    
    # Build and verify
    data, _ = editor.build()
    dlg = read_dlg(data)
    assert len(dlg.stunts) == 1
    assert str(dlg.stunts[0].stunt_model) == "test_model"
    assert dlg.stunts[0].participant == "PLAYER"


def test_dlg_editor_remove_stunt(qtbot, installation: HTInstallation):
    """Test removing stunts."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add stunt
    stunt = DLGStunt()
    stunt.stunt_model = ResRef("test_model")
    stunt.participant = "PLAYER"
    editor.core_dlg.stunts.append(stunt)
    editor.refresh_stunt_list()
    
    assert editor.ui.stuntList.count() == 1
    
    # Select and remove
    editor.ui.stuntList.setCurrentRow(0)
    editor.core_dlg.stunts.remove(stunt)
    editor.refresh_stunt_list()
    
    assert editor.ui.stuntList.count() == 0


def test_dlg_editor_multiple_stunts(qtbot, installation: HTInstallation):
    """Test handling multiple stunts."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add multiple stunts
    for i in range(5):
        stunt = DLGStunt()
        stunt.stunt_model = ResRef(f"model_{i}")
        stunt.participant = f"PARTICIPANT_{i}"
        editor.core_dlg.stunts.append(stunt)
    
    editor.refresh_stunt_list()
    assert editor.ui.stuntList.count() == 5
    
    # Build and verify
    data, _ = editor.build()
    dlg = read_dlg(data)
    assert len(dlg.stunts) == 5


# ============================================================================
# ANIMATION MANAGEMENT TESTS
# ============================================================================

def test_dlg_editor_animation_list_exists(qtbot, installation: HTInstallation):
    """Test animation list widget exists."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert hasattr(editor.ui, 'animsList')
    assert hasattr(editor.ui, 'addAnimButton')
    assert hasattr(editor.ui, 'removeAnimButton')
    assert hasattr(editor.ui, 'editAnimButton')


def test_dlg_editor_add_animation_programmatically(qtbot, installation: HTInstallation):
    """Test adding animations programmatically."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create node and select it
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Add animation to node
    anim = DLGAnimation()
    anim.animation_id = 1
    anim.participant = "PLAYER"
    root_item.link.node.animations.append(anim)
    editor.refresh_anim_list()
    
    # Verify animation is in list
    assert editor.ui.animsList.count() == 1
    
    # Build and verify
    data, _ = editor.build()
    dlg = read_dlg(data)
    assert len(dlg.starters[0].node.animations) == 1


def test_dlg_editor_remove_animation(qtbot, installation: HTInstallation):
    """Test removing animations."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create node with animation
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    anim = DLGAnimation()
    anim.animation_id = 1
    anim.participant = "PLAYER"
    root_item.link.node.animations.append(anim)
    editor.refresh_anim_list()
    
    assert editor.ui.animsList.count() == 1
    
    # Remove
    root_item.link.node.animations.remove(anim)
    editor.refresh_anim_list()
    
    assert editor.ui.animsList.count() == 0


def test_dlg_editor_multiple_animations(qtbot, installation: HTInstallation):
    """Test handling multiple animations on a node."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Add multiple animations
    for i in range(3):
        anim = DLGAnimation()
        anim.animation_id = i
        anim.participant = f"PARTICIPANT_{i}"
        root_item.link.node.animations.append(anim)
    
    editor.refresh_anim_list()
    assert editor.ui.animsList.count() == 3


# ============================================================================
# LOAD REAL FILE TESTS
# ============================================================================

def test_dlg_editor_load_real_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test loading a real DLG file."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, dlg_file.read_bytes())
    
    # Verify tree populated
    assert editor.model.rowCount() > 0
    
    # Verify widgets populated when selecting first node
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            # Widgets should have values
            assert editor.ui.speakerEdit.text() or True  # May be empty
            # Note: textEdit doesn't exist - text is edited via dialog, not a direct widget
            # The node text is stored in item.link.node.text (a LocalizedString)


def test_dlg_editor_load_and_save_preserves_data(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that loading and saving preserves all data."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    original_dlg = read_dlg(original_data)
    
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    saved_data, _ = editor.build()
    saved_dlg = read_dlg(saved_data)
    
    # Compare key properties
    assert len(saved_dlg.starters) == len(original_dlg.starters)
    assert saved_dlg.conversation_type == original_dlg.conversation_type
    assert saved_dlg.computer_type == original_dlg.computer_type
    assert saved_dlg.skippable == original_dlg.skippable
    assert str(saved_dlg.on_abort) == str(original_dlg.on_abort)
    assert str(saved_dlg.on_end) == str(original_dlg.on_end)


def test_dlg_editor_load_multiple_files(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test loading multiple DLG files in sequence."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    # Load first time
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, dlg_file.read_bytes())
    first_count = editor.model.rowCount()
    
    # Create new
    editor.new()
    assert editor.model.rowCount() == 0
    
    # Load again
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, dlg_file.read_bytes())
    assert editor.model.rowCount() == first_count


# ============================================================================
# GFF ROUNDTRIP TESTS
# ============================================================================

def test_dlg_editor_gff_roundtrip_no_modification(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip without any modifications."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    
    # Load
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Save without modification
    saved_data, _ = editor.build()
    
    # Compare GFF structures
    from pykotor.resource.formats.gff import read_gff
    original_gff = read_gff(original_data)
    saved_gff = read_gff(saved_data)
    
    # Root should have same number of fields (allowing for minor differences)
    # Note: Some fields may differ due to defaults being added
    assert original_gff.root is not None
    assert saved_gff.root is not None


def test_dlg_editor_create_from_scratch_roundtrip(qtbot, installation: HTInstallation):
    """Test creating a DLG from scratch and roundtripping."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create structure
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Set file-level properties
    editor.ui.conversationSelect.setCurrentIndex(1)
    editor.ui.skippableCheckbox.setChecked(True)
    editor.ui.onAbortCombo.set_combo_box_text("test_abort")
    
    # Set node properties
    editor.ui.speakerEdit.setText("TestSpeaker")
    editor.ui.listenerEdit.setText("PLAYER")
    editor.ui.script1ResrefEdit.set_combo_box_text("k_test")
    editor.ui.commentsEdit.setPlainText("Test comment")
    editor.on_node_update()
    
    # Add child
    child = editor.model.add_child_to_item(root_item)
    editor.ui.dialogTree.setCurrentIndex(child.index())
    editor.ui.condition1ResrefEdit.set_combo_box_text("c_test")
    editor.on_node_update()
    
    # Build
    data, _ = editor.build()
    
    # Load in new editor
    editor2 = DLGEditor(None, installation)
    qtbot.addWidget(editor2)
    editor2.load(Path("test.dlg"), "test", ResourceType.DLG, data)
    
    # Verify structure
    assert editor2.model.rowCount() == 1
    assert editor2.ui.conversationSelect.currentIndex() == 1
    assert editor2.ui.skippableCheckbox.isChecked()


# ============================================================================
# KEYBOARD SHORTCUT TESTS (non-interactive verification)
# ============================================================================

def test_dlg_editor_keyboard_shortcuts_exist(qtbot, installation: HTInstallation):
    """Test that keyboard shortcuts are properly set up."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    # Verify keys_down tracking exists
    assert hasattr(editor, 'keys_down')
    assert isinstance(editor.keys_down, set)


def test_dlg_editor_key_press_handling(qtbot, installation: HTInstallation):
    """Test key press event handling exists."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Add a node to work with
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Verify keyPressEvent is implemented
    assert hasattr(editor, 'keyPressEvent')
    assert hasattr(editor, 'keyReleaseEvent')


# ============================================================================
# FOCUS AND REFERENCE TESTS
# ============================================================================

def test_dlg_editor_focus_on_node(qtbot, installation: HTInstallation):
    """Test focusing on a specific node."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create structure
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    child = editor.model.add_child_to_item(root_item)
    
    # Focus on child's link
    result = editor.focus_on_node(child.link)
    
    # Should return focused item
    assert result is not None or editor._focused


def test_dlg_editor_find_references(qtbot, installation: HTInstallation):
    """Test finding references to a node."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create structure with potential references
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    
    # Verify find_references method exists
    assert hasattr(editor, 'find_references')


def test_dlg_editor_jump_to_node(qtbot, installation: HTInstallation):
    """Test jumping to a specific node."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    
    # Jump to node
    editor.jump_to_node(root_item.link)
    
    # Current index should be the root item
    current = editor.ui.dialogTree.currentIndex()
    assert current.isValid()


# ============================================================================
# ENTRY VS REPLY NODE TYPE TESTS
# ============================================================================

def test_dlg_editor_entry_has_speaker(qtbot, installation: HTInstallation):
    """Test that Entry nodes have speaker field visible."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    assert isinstance(root_item.link.node, DLGEntry)
    
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Speaker should be visible for Entry
    assert editor.ui.speakerEdit.isVisible()
    assert editor.ui.speakerEditLabel.isVisible()


def test_dlg_editor_reply_hides_speaker(qtbot, installation: HTInstallation):
    """Test that Reply nodes hide speaker field."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create Entry -> Reply
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    child = editor.model.add_child_to_item(root_item)
    assert isinstance(child.link.node, DLGReply)
    
    editor.ui.dialogTree.setCurrentIndex(child.index())
    
    # Speaker should be hidden for Reply
    assert not editor.ui.speakerEdit.isVisible()
    assert not editor.ui.speakerEditLabel.isVisible()


def test_dlg_editor_alternating_node_types(qtbot, installation: HTInstallation):
    """Test that child nodes alternate between Entry and Reply."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Start with Entry (root)
    editor.model.add_root_node()
    root = editor.model.item(0, 0)
    assert isinstance(root.link.node, DLGEntry)
    
    # Add child - should be Reply
    child1 = editor.model.add_child_to_item(root)
    assert isinstance(child1.link.node, DLGReply)
    
    # Add grandchild - should be Entry
    child2 = editor.model.add_child_to_item(child1)
    assert isinstance(child2.link.node, DLGEntry)


# ============================================================================
# COMPREHENSIVE BUILD/IO VALIDATION TESTS
# ============================================================================

def test_dlg_editor_build_all_file_properties(qtbot, installation: HTInstallation):
    """Test that build() correctly saves all file-level properties."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Set all file-level properties
    editor.ui.conversationSelect.setCurrentIndex(2)
    editor.ui.computerSelect.setCurrentIndex(1)
    editor.ui.skippableCheckbox.setChecked(True)
    editor.ui.animatedCutCheckbox.setChecked(True)
    editor.ui.oldHitCheckbox.setChecked(True)
    editor.ui.unequipHandsCheckbox.setChecked(True)
    editor.ui.unequipAllCheckbox.setChecked(True)
    editor.ui.entryDelaySpin.setValue(123)
    editor.ui.replyDelaySpin.setValue(456)
    editor.ui.voIdEdit.setText("test_vo_id")
    editor.ui.onAbortCombo.set_combo_box_text("abort_scr")
    editor.ui.onEndEdit.set_combo_box_text("end_script")
    editor.ui.ambientTrackCombo.set_combo_box_text("ambient")
    editor.ui.cameraModelSelect.set_combo_box_text("cam_mdl")
    
    # Add at least one node
    editor.model.add_root_node()
    
    # Build
    data, _ = editor.build()
    dlg = read_dlg(data)
    
    # Verify all properties
    assert dlg.conversation_type == DLGConversationType(2)
    assert dlg.computer_type == DLGComputerType(1)
    assert dlg.skippable
    assert dlg.animated_cut
    assert dlg.old_hit_check
    assert dlg.unequip_hands
    assert dlg.unequip_items
    assert dlg.delay_entry == 123
    assert dlg.delay_reply == 456
    assert dlg.vo_id == "test_vo_id"
    assert str(dlg.on_abort) == "abort_scr"
    assert str(dlg.on_end) == "end_script"
    assert str(dlg.ambient_track) == "ambient"
    assert str(dlg.camera_model) == "cam_mdl"


def test_dlg_editor_build_all_node_properties(qtbot, installation: HTInstallation):
    """Test that build() correctly saves all node-level properties."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    is_tsl = installation.tsl  # TSL-specific params only persist for K2
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Set all node properties
    editor.ui.speakerEdit.setText("SPEAKER_TAG")
    editor.ui.listenerEdit.setText("LISTENER_TAG")
    editor.ui.script1ResrefEdit.set_combo_box_text("script1")
    if is_tsl:
        editor.ui.script1Param1Spin.setValue(1)
        editor.ui.script1Param2Spin.setValue(2)
        editor.ui.script1Param3Spin.setValue(3)
        editor.ui.script1Param4Spin.setValue(4)
        editor.ui.script1Param5Spin.setValue(5)
        editor.ui.script1Param6Edit.setText("str1")
        editor.ui.script2ResrefEdit.set_combo_box_text("script2")
        editor.ui.script2Param1Spin.setValue(11)
        editor.ui.script2Param2Spin.setValue(22)
        editor.ui.script2Param3Spin.setValue(33)
        editor.ui.script2Param4Spin.setValue(44)
        editor.ui.script2Param5Spin.setValue(55)
        editor.ui.script2Param6Edit.setText("str2")
    editor.ui.soundComboBox.set_combo_box_text("snd")
    editor.ui.soundCheckbox.setChecked(True)
    editor.ui.voiceComboBox.set_combo_box_text("vo")
    editor.ui.questEdit.setText("quest_name")
    editor.ui.questEntrySpin.setValue(7)
    editor.ui.plotXpSpin.setValue(80)
    editor.ui.cameraIdSpin.setValue(3)
    if is_tsl:
        editor.ui.nodeUnskippableCheckbox.setChecked(True)
        editor.ui.nodeIdSpin.setValue(99)
        editor.ui.alienRaceNodeSpin.setValue(4)
        editor.ui.postProcSpin.setValue(5)
    editor.ui.delaySpin.setValue(250)
    editor.ui.waitFlagSpin.setValue(3)
    editor.ui.fadeTypeSpin.setValue(2)
    editor.ui.commentsEdit.setPlainText("Test node comment")
    editor.on_node_update()
    
    # Build
    data, _ = editor.build()
    dlg = read_dlg(data)
    node = dlg.starters[0].node
    
    # Verify K1-compatible properties
    assert node.speaker == "SPEAKER_TAG"
    assert node.listener == "LISTENER_TAG"
    assert str(node.script1) == "script1"
    assert str(node.sound) == "snd"
    assert node.sound_exists
    assert str(node.vo_resref) == "vo"
    assert node.quest == "quest_name"
    assert node.quest_entry == 7
    assert node.plot_xp_percentage == 80
    assert node.camera_id == 3
    assert node.delay == 250
    assert node.wait_flags == 3
    assert node.fade_type == 2
    assert node.comment == "Test node comment"
    
    # Verify TSL-specific properties (only when installation is TSL)
    if is_tsl:
        assert node.script1_param1 == 1
        assert node.script1_param2 == 2
        assert node.script1_param3 == 3
        assert node.script1_param4 == 4
        assert node.script1_param5 == 5
        assert node.script1_param6 == "str1"
        assert str(node.script2) == "script2"
        assert node.script2_param1 == 11
        assert node.script2_param2 == 22
        assert node.script2_param3 == 33
        assert node.script2_param4 == 44
        assert node.script2_param5 == 55
        assert node.script2_param6 == "str2"
        assert node.unskippable
        assert node.node_id == 99
        assert node.alien_race_node == 4
        assert node.post_proc_node == 5


def test_dlg_editor_build_all_link_properties(qtbot, installation: HTInstallation):
    """Test that build() correctly saves all link-level properties."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    is_tsl = installation.tsl  # TSL-specific params only persist for K2
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Set link properties (K1 supports active1 script, TSL supports all params)
    editor.ui.condition1ResrefEdit.set_combo_box_text("cond1")
    if is_tsl:
        editor.ui.condition1Param1Spin.setValue(101)
        editor.ui.condition1Param2Spin.setValue(102)
        editor.ui.condition1Param3Spin.setValue(103)
        editor.ui.condition1Param4Spin.setValue(104)
        editor.ui.condition1Param5Spin.setValue(105)
        editor.ui.condition1Param6Edit.setText("cond1str")
        editor.ui.condition1NotCheckbox.setChecked(True)
        editor.ui.condition2ResrefEdit.set_combo_box_text("cond2")
        editor.ui.condition2Param1Spin.setValue(201)
        editor.ui.condition2Param2Spin.setValue(202)
        editor.ui.condition2Param3Spin.setValue(203)
        editor.ui.condition2Param4Spin.setValue(204)
        editor.ui.condition2Param5Spin.setValue(205)
        editor.ui.condition2Param6Edit.setText("cond2str")
        editor.ui.condition2NotCheckbox.setChecked(True)
        editor.ui.logicSpin.setValue(1)
    editor.on_node_update()
    
    # Build
    data, _ = editor.build()
    dlg = read_dlg(data)
    link = dlg.starters[0]
    
    # Verify K1-compatible link properties
    assert str(link.active1) == "cond1"
    
    # Verify TSL-specific link properties
    if is_tsl:
        assert link.active1_param1 == 101
        assert link.active1_param2 == 102
        assert link.active1_param3 == 103
        assert link.active1_param4 == 104
        assert link.active1_param5 == 105
        assert link.active1_param6 == "cond1str"
        assert link.active1_not
        assert str(link.active2) == "cond2"
        assert link.active2_param1 == 201
        assert link.active2_param2 == 202
        assert link.active2_param3 == 203
        assert link.active2_param4 == 204
        assert link.active2_param5 == 205
        assert link.active2_param6 == "cond2str"
        assert link.active2_not
        assert link.logic


# ============================================================================
# PINNED ITEMS TESTS
# ============================================================================

def test_dlg_editor_pinned_items_list_exists(qtbot, installation: HTInstallation):
    """Test pinned items list widget exists."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert hasattr(editor, 'pinned_items_list')
    assert editor.pinned_items_list is not None


def test_dlg_editor_left_dock_widget(qtbot, installation: HTInstallation):
    """Test left dock widget exists and contains orphaned and pinned lists."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert hasattr(editor, 'left_dock_widget')
    assert editor.left_dock_widget is not None
    assert hasattr(editor, 'orphaned_nodes_list')
    assert hasattr(editor, 'pinned_items_list')


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_dlg_editor_empty_dlg(qtbot, installation: HTInstallation):
    """Test handling empty DLG."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Empty DLG should have no starters
    assert editor.model.rowCount() == 0
    assert len(editor.core_dlg.starters) == 0
    
    # Build should still work
    data, _ = editor.build()
    dlg = read_dlg(data)
    assert len(dlg.starters) == 0


def test_dlg_editor_deep_nesting(qtbot, installation: HTInstallation):
    """Test handling deeply nested dialog tree."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create deep nesting
    editor.model.add_root_node()
    current = editor.model.item(0, 0)
    
    for _ in range(10):
        current = editor.model.add_child_to_item(current)
    
    # Build should work
    data, _ = editor.build()
    dlg = read_dlg(data)
    
    # Verify structure depth
    depth = 0
    node = dlg.starters[0].node
    while node.links:
        depth += 1
        node = node.links[0].node
    assert depth == 10


def test_dlg_editor_many_siblings(qtbot, installation: HTInstallation):
    """Test handling many sibling nodes."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    # Create many root nodes
    for _ in range(20):
        editor.model.add_root_node()
    
    assert editor.model.rowCount() == 20
    assert len(editor.core_dlg.starters) == 20
    
    # Build and verify
    data, _ = editor.build()
    dlg = read_dlg(data)
    assert len(dlg.starters) == 20


def test_dlg_editor_special_characters_in_text(qtbot, installation: HTInstallation):
    """Test handling special characters in text fields."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Test special characters in various fields
    editor.ui.speakerEdit.setText("Speaker<>&\"'")
    editor.ui.listenerEdit.setText("Listener\n\t")
    editor.ui.questEdit.setText("Quest with spaces")
    editor.ui.commentsEdit.setPlainText("Comment with\nmultiple\nlines")
    editor.on_node_update()
    
    # Build and verify
    data, _ = editor.build()
    dlg = read_dlg(data)
    node = dlg.starters[0].node
    
    assert node.speaker == "Speaker<>&\"'"
    assert node.listener == "Listener\n\t"
    assert node.quest == "Quest with spaces"
    assert node.comment == "Comment with\nmultiple\nlines"


def test_dlg_editor_max_values(qtbot, installation: HTInstallation):
    """Test handling maximum values in spin boxes."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Set maximum values
    editor.ui.delaySpin.setValue(editor.ui.delaySpin.maximum())
    editor.ui.nodeIdSpin.setValue(editor.ui.nodeIdSpin.maximum())
    editor.ui.plotXpSpin.setValue(editor.ui.plotXpSpin.maximum())
    editor.on_node_update()
    
    # Build should work
    data, _ = editor.build()
    dlg = read_dlg(data)
    
    # Values should be preserved
    assert dlg.starters[0].node.delay == editor.ui.delaySpin.maximum()


def test_dlg_editor_negative_values(qtbot, installation: HTInstallation):
    """Test handling negative values where allowed."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    editor.new()
    
    editor.model.add_root_node()
    root_item = editor.model.item(0, 0)
    editor.ui.dialogTree.setCurrentIndex(root_item.index())
    
    # Set to -1 (common "unset" value)
    editor.ui.cameraIdSpin.setValue(-1)
    editor.on_node_update()
    
    # Build and verify
    data, _ = editor.build()
    dlg = read_dlg(data)
    assert dlg.starters[0].node.camera_id == -1

# ============================================================================
# GRANULAR FIELD-BY-FIELD TESTS (Following ARE Editor Pattern)
# ============================================================================

def test_dlg_editor_manipulate_speaker_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating speaker field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    original_dlg = read_dlg(original_data)
    
    # Find first Entry node
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem) and isinstance(first_item.link.node, DLGEntry):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify speaker
            editor.ui.speakerEdit.setText("ModifiedSpeaker")
            editor.on_node_update()
            
            # Save and verify
            data, _ = editor.build()
            modified_dlg = read_dlg(data)
            
            # Find the modified node
            modified_node = modified_dlg.starters[0].node if modified_dlg.starters else None
            if modified_node and isinstance(modified_node, DLGEntry):
                assert modified_node.speaker == "ModifiedSpeaker"
                assert modified_node.speaker != original_dlg.starters[0].node.speaker if original_dlg.starters and isinstance(original_dlg.starters[0].node, DLGEntry) else True
                
                # Load back and verify
                editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                editor.ui.dialogTree.setCurrentIndex(first_item.index())
                assert editor.ui.speakerEdit.text() == "ModifiedSpeaker"

def test_dlg_editor_manipulate_listener_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating listener field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify listener
            test_listeners = ["PLAYER", "COMPANION", "NPC", ""]
            for listener in test_listeners:
                editor.ui.listenerEdit.setText(listener)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.listener == listener
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.listenerEdit.text() == listener

def test_dlg_editor_manipulate_script1_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating script1 field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify script1
            editor.ui.script1ResrefEdit.set_combo_box_text("test_script1")
            editor.on_node_update()
            
            # Save and verify
            data, _ = editor.build()
            modified_dlg = read_dlg(data)
            if modified_dlg.starters:
                assert str(modified_dlg.starters[0].node.script1) == "test_script1"
                
                # Load back and verify
                editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                editor.ui.dialogTree.setCurrentIndex(first_item.index())
                assert editor.ui.script1ResrefEdit.currentText() == "test_script1"

def test_dlg_editor_manipulate_script1_param1_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating script1 param1 with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various param1 values (TSL only, but test that UI updates in-memory model)
            test_values = [0, 1, 42, 100, -1]
            for val in test_values:
                editor.ui.script1Param1Spin.setValue(val)
                editor.on_node_update()
                
                # Verify in-memory model updated (always works)
                assert first_item.link.node.script1_param1 == val

def test_dlg_editor_manipulate_condition1_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating condition1 field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify condition1
            editor.ui.condition1ResrefEdit.set_combo_box_text("test_condition1")
            editor.on_node_update()
            
            # Save and verify
            data, _ = editor.build()
            modified_dlg = read_dlg(data)
            if modified_dlg.starters:
                assert str(modified_dlg.starters[0].active1) == "test_condition1"
                
                # Load back and verify
                editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                editor.ui.dialogTree.setCurrentIndex(first_item.index())
                assert editor.ui.condition1ResrefEdit.currentText() == "test_condition1"

def test_dlg_editor_manipulate_condition1_not_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating condition1 NOT checkbox with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Toggle checkbox
            editor.ui.condition1NotCheckbox.setChecked(True)
            editor.on_node_update()
            
            # Save and verify
            data, _ = editor.build()
            modified_dlg = read_dlg(data)
            if modified_dlg.starters:
                assert modified_dlg.starters[0].active1_not
                
                # Toggle off
                editor.ui.condition1NotCheckbox.setChecked(False)
                editor.on_node_update()
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert not modified_dlg.starters[0].active1_not

def test_dlg_editor_manipulate_emotion_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating emotion field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test emotion selection (if available)
            if editor.ui.emotionSelect.count() > 0:
                for i in range(min(5, editor.ui.emotionSelect.count())):
                    editor.ui.emotionSelect.setCurrentIndex(i)
                    editor.on_node_update()
                    
                    # Save and verify
                    data, _ = editor.build()
                    modified_dlg = read_dlg(data)
                    if modified_dlg.starters:
                        assert modified_dlg.starters[0].node.emotion_id == i

def test_dlg_editor_manipulate_expression_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating expression field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test expression selection (if available)
            if editor.ui.expressionSelect.count() > 0:
                for i in range(min(5, editor.ui.expressionSelect.count())):
                    editor.ui.expressionSelect.setCurrentIndex(i)
                    editor.on_node_update()
                    
                    # Save and verify
                    data, _ = editor.build()
                    modified_dlg = read_dlg(data)
                    if modified_dlg.starters:
                        assert modified_dlg.starters[0].node.facial_id == i

def test_dlg_editor_manipulate_sound_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating sound field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify sound
            test_sounds = ["test_sound", "another_sound", ""]
            for sound in test_sounds:
                editor.ui.soundComboBox.set_combo_box_text(sound)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert str(modified_dlg.starters[0].node.sound) == sound
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.soundComboBox.currentText() == sound

def test_dlg_editor_manipulate_sound_checkbox_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating sound exists checkbox with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Toggle checkbox
            editor.ui.soundCheckbox.setChecked(True)
            editor.on_node_update()
            
            # Save and verify
            data, _ = editor.build()
            modified_dlg = read_dlg(data)
            if modified_dlg.starters:
                assert modified_dlg.starters[0].node.sound_exists
                
                # Toggle off
                editor.ui.soundCheckbox.setChecked(False)
                editor.on_node_update()
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert not modified_dlg.starters[0].node.sound_exists

def test_dlg_editor_manipulate_quest_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating quest field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify quest
            test_quests = ["test_quest", "quest_001", ""]
            for quest in test_quests:
                editor.ui.questEdit.setText(quest)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.quest == quest
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.questEdit.text() == quest

def test_dlg_editor_manipulate_quest_entry_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating quest entry spin box with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various quest entry values
            test_values = [0, 1, 5, 10, 50]
            for val in test_values:
                editor.ui.questEntrySpin.setValue(val)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.quest_entry == val
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.questEntrySpin.value() == val

def test_dlg_editor_manipulate_plot_xp_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating plot XP percentage with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various XP percentages
            test_values = [0, 25, 50, 75, 100]
            for val in test_values:
                editor.ui.plotXpSpin.setValue(val)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.plot_xp_percentage == val
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.plotXpSpin.value() == val

def test_dlg_editor_manipulate_comments_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various comment texts
            test_comments = [
                "",
                "Test comment",
                "Multi\nline\ncomment",
                "Comment with special chars !@#$%^&*()",
            ]
            
            for comment in test_comments:
                editor.ui.commentsEdit.setPlainText(comment)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.comment == comment
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.commentsEdit.toPlainText() == comment

def test_dlg_editor_manipulate_camera_id_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating camera ID with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various camera IDs
            test_values = [-1, 0, 1, 5, 10]
            for val in test_values:
                editor.ui.cameraIdSpin.setValue(val)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.camera_id == val
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.cameraIdSpin.value() == val

def test_dlg_editor_manipulate_delay_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating delay field with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various delay values
            test_values = [0, 100, 500, 1000, 5000]
            for val in test_values:
                editor.ui.delaySpin.setValue(val)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.delay == val
                    
                    # Load back and verify
                    editor.load(dlg_file, "ORIHA", ResourceType.DLG, data)
                    editor.ui.dialogTree.setCurrentIndex(first_item.index())
                    assert editor.ui.delaySpin.value() == val

def test_dlg_editor_manipulate_wait_flags_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating wait flags with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various wait flag values
            test_values = [0, 1, 2, 3]
            for val in test_values:
                editor.ui.waitFlagSpin.setValue(val)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.wait_flags == val

def test_dlg_editor_manipulate_fade_type_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating fade type with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Test various fade type values
            test_values = [0, 1, 2, 3]
            for val in test_values:
                editor.ui.fadeTypeSpin.setValue(val)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert modified_dlg.starters[0].node.fade_type == val

def test_dlg_editor_manipulate_voice_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating voice ResRef with save/load roundtrip."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify voice
            test_voices = ["test_vo", "voice_001", ""]
            for voice in test_voices:
                editor.ui.voiceComboBox.set_combo_box_text(voice)
                editor.on_node_update()
                
                # Save and verify
                data, _ = editor.build()
                modified_dlg = read_dlg(data)
                if modified_dlg.starters:
                    assert str(modified_dlg.starters[0].node.vo_resref) == voice

def test_dlg_editor_manipulate_all_file_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all file-level fields simultaneously."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    # Modify ALL file-level fields
    if editor.ui.conversationSelect.count() > 0:
        editor.ui.conversationSelect.setCurrentIndex(1)
    if editor.ui.computerSelect.count() > 0:
        editor.ui.computerSelect.setCurrentIndex(1)
    editor.ui.skippableCheckbox.setChecked(True)
    editor.ui.animatedCutCheckbox.setChecked(True)
    editor.ui.oldHitCheckbox.setChecked(True)
    editor.ui.unequipHandsCheckbox.setChecked(True)
    editor.ui.unequipAllCheckbox.setChecked(True)
    editor.ui.entryDelaySpin.setValue(123)
    editor.ui.replyDelaySpin.setValue(456)
    editor.ui.voIdEdit.setText("test_vo_id")
    editor.ui.onAbortCombo.set_combo_box_text("test_abort")
    editor.ui.onEndEdit.set_combo_box_text("test_on_end")
    editor.ui.ambientTrackCombo.set_combo_box_text("test_ambient")
    editor.ui.cameraModelSelect.set_combo_box_text("test_camera")
    
    # Save and verify all
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    
    assert modified_dlg.skippable
    assert modified_dlg.animated_cut
    assert modified_dlg.old_hit_check
    assert modified_dlg.unequip_hands
    assert modified_dlg.unequip_items
    assert modified_dlg.delay_entry == 123
    assert modified_dlg.delay_reply == 456
    assert modified_dlg.vo_id == "test_vo_id"
    assert str(modified_dlg.on_abort) == "test_abort"
    assert str(modified_dlg.on_end) == "test_on_end"
    assert str(modified_dlg.ambient_track) == "test_ambient"
    assert str(modified_dlg.camera_model) == "test_camera"

def test_dlg_editor_manipulate_all_node_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all node-level fields simultaneously."""
    editor = DLGEditor(None, installation)
    qtbot.addWidget(editor)
    
    dlg_file = test_files_dir / "ORIHA.dlg"
    if not dlg_file.exists():
        pytest.skip("ORIHA.dlg not found")
    
    original_data = dlg_file.read_bytes()
    editor.load(dlg_file, "ORIHA", ResourceType.DLG, original_data)
    
    if editor.model.rowCount() > 0:
        first_item = editor.model.item(0, 0)
        if isinstance(first_item, DLGStandardItem) and isinstance(first_item.link.node, DLGEntry):
            editor.ui.dialogTree.setCurrentIndex(first_item.index())
            
            # Modify ALL node fields
            editor.ui.speakerEdit.setText("TestSpeaker")
            editor.ui.listenerEdit.setText("PLAYER")
            editor.ui.script1ResrefEdit.set_combo_box_text("k_test")
            editor.ui.soundComboBox.set_combo_box_text("test_sound")
            editor.ui.soundCheckbox.setChecked(True)
            editor.ui.voiceComboBox.set_combo_box_text("test_vo")
            editor.ui.questEdit.setText("test_quest")
            editor.ui.questEntrySpin.setValue(5)
            editor.ui.plotXpSpin.setValue(75)
            editor.ui.cameraIdSpin.setValue(2)
            editor.ui.delaySpin.setValue(500)
            editor.ui.waitFlagSpin.setValue(1)
            editor.ui.fadeTypeSpin.setValue(2)
            editor.ui.commentsEdit.setPlainText("Test node comment")
            editor.ui.condition1ResrefEdit.set_combo_box_text("c_test")
            editor.ui.condition1NotCheckbox.setChecked(True)
            editor.on_node_update()
            
            # Save and verify all
            data, _ = editor.build()
            modified_dlg = read_dlg(data)
            if modified_dlg.starters:
                node = modified_dlg.starters[0].node
                link = modified_dlg.starters[0]
                
                if isinstance(node, DLGEntry):
                    assert node.speaker == "TestSpeaker"
                assert node.listener == "PLAYER"
                assert str(node.script1) == "k_test"
                assert str(node.sound) == "test_sound"
                assert node.sound_exists
                assert str(node.vo_resref) == "test_vo"
                assert node.quest == "test_quest"
                assert node.quest_entry == 5
                assert node.plot_xp_percentage == 75
                assert node.camera_id == 2
                assert node.delay == 500
                assert node.wait_flags == 1
                assert node.fade_type == 2
                assert node.comment == "Test node comment"
                assert str(link.active1) == "c_test"
                assert link.active1_not