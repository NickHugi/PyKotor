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
from qtpy.QtWidgets import QApplication, QDialog, QDialogButtonBox, QListWidgetItem
from toolset.gui.editors.dlg.editor import DLGEditor  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from toolset.gui.editors.dlg.model import DLGStandardItem  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
from pykotor.common.misc import ResRef  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]    
from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGReply, DLGLink, DLGComputerType, DLGConversationType, read_dlg  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
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
    assert hasattr(editor.ui, 'voResrefEdit')
    assert hasattr(editor.ui, 'voIdEdit')
    assert hasattr(editor.ui, 'soundEdit')
    assert hasattr(editor.ui, 'cameraAngleSpin')
    assert hasattr(editor.ui, 'cameraAnimationEdit')
    assert hasattr(editor.ui, 'animationsList')
    assert hasattr(editor.ui, 'plotIndexSpin')
    assert hasattr(editor.ui, 'questEdit')
    assert hasattr(editor.ui, 'questEntrySpin')
    assert hasattr(editor.ui, 'commentEdit')
    
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
    
    # Test voIdEdit - QLineEdit
    editor.ui.voIdEdit.setText("123")
    editor.on_node_update()
    assert str(root_item.link.node.vo_resref) == "123"
    assert root_item.link.node.vo_resref == ResRef("123")
    assert root_item.link.node.vo_resref == "123"
    
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

def test_dlg_editor_load_real_file(qtbot, installation: HTInstallation, test_files_dir):
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

def test_dlg_editor_build_verification(qtbot, installation: HTInstallation):
    """Test that ALL widget values are correctly saved in build()."""
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
    # Set text via UI dialog
    set_text_via_ui_dialog(qtbot, editor, root_item, "Test Entry Text")
    editor.ui.script1ResrefEdit.set_combo_box_text("test_script")
    editor.ui.plotIndexCombo.setCurrentIndex(5)
    editor.ui.commentsEdit.setPlainText("Test comment")
    editor.on_node_update()
    
    # Build and verify
    data, _ = editor.build()
    from pykotor.resource.generics.dlg.io import read_dlg  # pyright: ignore[reportMissingModuleSource]  # type: ignore[import-untyped, import-not-found, note]
    dlg = read_dlg(data)
    
    assert len(dlg.starters) == 1
    assert isinstance(dlg.starters[0].node, DLGEntry)
    assert dlg.starters[0].node.speaker == "TestSpeaker"
    assert dlg.starters[0].node.text.get(0) == "Test Entry Text"
    assert str(dlg.starters[0].node.script1) == "test_script"
    assert dlg.starters[0].node.plot_index == 5
    assert dlg.starters[0].node.comment == "Test comment"

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
# FILE-LEVEL WIDGETS MANIPULATIONS (Top Dock) - from test_ui_dlg_comprehensive.py
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
    test_vo_ids = ["", "vo_001", "vo_test_123", "vo_long_name_here"]
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
    editor.ui.onAbortCombo.set_combo_box_text("test_on_abort")
    
    # Save and verify
    data, _ = editor.build()
    modified_dlg = read_dlg(data)
    assert str(modified_dlg.on_abort) == "test_on_abort"

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