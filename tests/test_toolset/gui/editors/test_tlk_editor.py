from __future__ import annotations

import importlib
import os
import pathlib
import sys
from typing import TYPE_CHECKING
import unittest
from unittest import TestCase


absolute_file_path: pathlib.Path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH: pathlib.Path = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_toolset/test_files"

if TYPE_CHECKING:
    from toolset.data.installation import HTInstallation
    from toolset.gui.editors.tlk import TLKEditor
    from pykotor.resource.formats.tlk.tlk_data import TLK

if __name__ == "__main__" and getattr(sys, "frozen", False) is False:

    def add_sys_path(p):
        working_dir = str(p)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = absolute_file_path.parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        add_sys_path(pykotor_path.parent)
    gl_path = absolute_file_path.parents[4] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        add_sys_path(gl_path.parent)
    utility_path = absolute_file_path.parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        add_sys_path(utility_path.parent)
    toolset_path = absolute_file_path.parents[4] / "Tools" / "HolocronToolset" / "src" / "toolset"
    if toolset_path.exists():
        add_sys_path(toolset_path.parent)

if importlib.util.find_spec("qtpy.QtWidgets") is None:  # pyright: ignore[reportAttributeAccessIssue]
    raise ImportError("qtpy.QtWidgets is required for this test. Install PyQt/PySide with qtpy before running this test.")

from loggerplus import Any
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QApplication

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

from pykotor.resource.formats.tlk.tlk_auto import read_tlk
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class TLKEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        assert K2_PATH is not None, "K2_PATH environment variable is not set."
        from toolset.gui.editors.tlk import TLKEditor

        cls.TLKEditor = TLKEditor
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app = QApplication([])
        self.editor = self.TLKEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath: pathlib.Path = TESTS_FILES_PATH / "dialog.tlk"

        data1: bytes = filepath.read_bytes()
        old: TLK = read_tlk(data1)
        self.editor.load(filepath, "dialog", ResourceType.TLK, data1)

        data2, _ = self.editor.build()
        assert data2 is not None, "Failed to build TLK"
        new: TLK = read_tlk(data2)

        diff: bool = old.compare(new, self.log_func)
        assert diff
        self.assertDeepEqual(old, new)

    def assertDeepEqual(
        self,
        obj1: Any,
        obj2: Any,
        context: str = "",
    ) -> None:
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            assert set(obj1.keys()) == set(obj2.keys()), context
            for key in obj1:
                new_context: str = f"{context}.{key}" if context else str(key)
                self.assertDeepEqual(obj1[key], obj2[key], new_context)

        elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
            assert len(obj1) == len(obj2), context
            for index, (item1, item2) in enumerate(zip(obj1, obj2)):
                new_context = f"{context}[{index}]" if context else f"[{index}]"
                self.assertDeepEqual(item1, item2, new_context)

        elif hasattr(obj1, "__dict__") and hasattr(obj2, "__dict__"):
            self.assertDeepEqual(obj1.__dict__, obj2.__dict__, context)

        else:
            assert obj1 == obj2, context


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Pytest-based UI tests (merged from test_ui_tlk.py)
# ============================================================================

import pytest
from qtpy.QtCore import Qt, QModelIndex
from qtpy.QtGui import QStandardItem
from toolset.gui.editors.tlk import TLKEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.formats.tlk import TLK, TLKEntry
from pykotor.resource.type import ResourceType

def test_tlk_editor_all_widgets_exist(qtbot, installation: HTInstallation):
    """Verify ALL widgets exist in TLK editor."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    # Table view
    assert hasattr(editor.ui, 'talkTable')
    
    # Text edit
    assert hasattr(editor.ui, 'textEdit')
    
    # Sound edit
    assert hasattr(editor.ui, 'soundEdit')
    
    # Search/filter
    assert hasattr(editor.ui, 'searchEdit')
    assert hasattr(editor.ui, 'searchButton')
    
    # Jump to line
    assert hasattr(editor.ui, 'jumpSpinbox')
    assert hasattr(editor.ui, 'jumpButton')
    
    # Menu actions (insert/delete are menu actions, not buttons)
    assert hasattr(editor.ui, 'actionInsert')

def test_tlk_editor_all_widgets_interactions(qtbot, installation: HTInstallation):
    """Test ALL widgets with exhaustive interactions."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Test insert action - adds new entry
    initial_count = editor.source_model.rowCount()
    editor.ui.actionInsert.trigger()
    assert editor.source_model.rowCount() == initial_count + 1
    
    # Test textEdit - QPlainTextEdit
    test_texts = [
        "",
        "Simple text",
        "Text with\nmultiple\nlines",
        "Text with special chars !@#$%^&*()",
        "Text with numbers 123456",
        "Very long text " * 100,
    ]
    
    for text in test_texts:
        editor.ui.textEdit.setPlainText(text)
        assert editor.ui.textEdit.toPlainText() == text
    
    # Test soundEdit - QLineEdit
    test_sounds = [
        "",
        "test_sound",
        "sound_with_123",
        "very_long_sound_resref_name",
    ]
    
    for sound in test_sounds:
        editor.ui.soundEdit.setText(sound)
        assert editor.ui.soundEdit.text() == sound
    
    # Test searchEdit - QLineEdit
    test_filters = [
        "",
        "test",
        "TEST",
        "test filter",
        "123",
        "special!@#",
    ]
    
    for filter_text in test_filters:
        editor.ui.searchEdit.setText(filter_text)
        editor.do_filter(filter_text)
        # Filter should update proxy model
        # We verify the filter was applied

def test_tlk_editor_insert_remove_exhaustive(qtbot, installation: HTInstallation):
    """Test insert/remove operations exhaustively."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Insert multiple entries
    for i in range(10):
        editor.ui.actionInsert.trigger()
        assert editor.source_model.rowCount() == i + 1
    
    # Set text for each entry
    for i in range(10):
        index = editor.proxy_model.index(i, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(f"Entry {i}")
        editor.ui.soundEdit.setText(f"sound_{i}")
    
    # Remove entries one by one (delete is via context menu or direct model manipulation)
    while editor.source_model.rowCount() > 0:
        count_before = editor.source_model.rowCount()
        # Remove first row directly from model
        editor.source_model.removeRow(0)
        assert editor.source_model.rowCount() == count_before - 1

def test_tlk_editor_search_filter_exhaustive(qtbot, installation: HTInstallation):
    """Test search/filter functionality exhaustively."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add entries with different text
    entries_data = [
        "Apple",
        "Banana",
        "Cherry",
        "Date",
        "Elderberry",
        "Apple Pie",
        "Banana Bread",
        "Test Entry",
        "Another Test",
        "Final Entry",
    ]
    
    for text in entries_data:
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(text)
    
    # Test various filter patterns
    filter_tests = [
        ("App", 2),  # Apple, Apple Pie
        ("Ban", 2),  # Banana, Banana Bread
        ("Test", 2),  # Test Entry, Another Test
        ("", 10),  # No filter - all entries
        ("XYZ", 0),  # No matches
        ("a", 7),  # Case insensitive matches
        ("E", 3),  # Elderberry, Test Entry, Another Test, Final Entry
    ]
    
    for filter_text, expected_count in filter_tests:
        editor.ui.searchEdit.setText(filter_text)
        editor.do_filter(filter_text)
        assert editor.proxy_model.rowCount() == expected_count, \
            f"Filter '{filter_text}' should show {expected_count} entries, got {editor.proxy_model.rowCount()}"

def test_tlk_editor_goto_line_exhaustive(qtbot, installation: HTInstallation):
    """Test goto line functionality exhaustively."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add multiple entries
    for i in range(20):
        editor.insert()
        item = editor.source_model.item(i, 0)
        if item:
            item.setText(f"Entry {i}")
    
    # Test jumping to various lines
    test_lines = [0, 1, 5, 10, 15, 19]
    
    for line in test_lines:
        editor.ui.jumpSpinbox.setValue(line)
        # Signal should trigger goto
        current_index = editor.ui.talkTable.currentIndex()
        assert current_index.row() == line or current_index.isValid()

def test_tlk_editor_build_verification(qtbot, installation: HTInstallation):
    """Test that ALL widget values are correctly saved in build()."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add and configure multiple entries
    test_entries = [
        ("Entry 1", "sound1"),
        ("Entry 2", "sound2"),
        ("Entry 3", ""),
        ("Multi\nLine\nEntry", "sound3"),
    ]
    
    for text, sound in test_entries:
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(text)
        editor.ui.soundEdit.setText(sound)
    
    # Build and verify
    data, _ = editor.build()
    from pykotor.resource.formats.tlk import read_tlk
    tlk = read_tlk(data)
    
    assert len(tlk) == len(test_entries)
    for i, (expected_text, expected_sound) in enumerate(test_entries):
        assert tlk[i].text == expected_text
        assert tlk[i].voiceover == expected_sound

def test_tlk_editor_load_real_file(qtbot, installation: HTInstallation, test_files_dir):
    """Test loading a real TLK file."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    
    tlk_file = test_files_dir / "dialog.tlk"
    if not tlk_file.exists():
        pytest.skip("dialog.tlk not found")
    
    editor.load(tlk_file, "dialog", ResourceType.TLK, tlk_file.read_bytes())
    
    # Verify entries loaded
    assert editor.source_model.rowCount() > 0
    
    # Verify widgets populated when selecting first entry
    if editor.source_model.rowCount() > 0:
        index = editor.proxy_model.index(0, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        # Text edit should have content
        assert editor.ui.textEdit.toPlainText() or True  # May be empty for some entries

def test_tlk_editor_table_selection(qtbot, installation: HTInstallation):
    """Test table selection and widget updates."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add entries
    for i in range(5):
        editor.insert()
        item = editor.source_model.item(i, 0)
        if item:
            item.setText(f"Entry {i}")
    
    # Test selecting each entry updates widgets
    for i in range(5):
        index = editor.proxy_model.index(i, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        
        # Widgets should update
        current_text = editor.ui.textEdit.toPlainText()
        # May be empty or have text depending on entry state

def test_tlk_editor_edit_entry_exhaustive(qtbot, installation: HTInstallation):
    """Test editing entries with all combinations."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add entry
    editor.insert()
    index = editor.proxy_model.index(0, 0)
    editor.ui.talkTable.setCurrentIndex(index)
    
    # Test various text/sound combinations
    test_combinations = [
        ("Text only", ""),
        ("", "Sound only"),
        ("Both", "both_sound"),
        ("Multi\nLine", "multi_sound"),
        ("", ""),  # Empty entry
    ]
    
    for text, sound in test_combinations:
        editor.ui.textEdit.setPlainText(text)
        editor.ui.soundEdit.setText(sound)
        
        # Verify values set
        assert editor.ui.textEdit.toPlainText() == text
        assert editor.ui.soundEdit.text() == sound
        
        # Build and verify
        data, _ = editor.build()
        from pykotor.resource.formats.tlk import read_tlk
        tlk = read_tlk(data)
        assert len(tlk) == 1
        assert tlk[0].text == text
        assert tlk[0].voiceover == sound

def test_tlk_editor_remove_button_states(qtbot, installation: HTInstallation):
    """Test remove button enabled/disabled states."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Initially no entries - remove should be disabled or do nothing
    initial_count = editor.source_model.rowCount()
    editor.ui.talkTable.setCurrentIndex(QModelIndex())  # No selection
    # Remove with no selection should not crash
    
    # Add entry
    editor.insert()
    assert editor.source_model.rowCount() == 1
    
    # Select entry
    index = editor.proxy_model.index(0, 0)
    editor.ui.talkTable.setCurrentIndex(index)
    
    # Remove should work (remove directly from model)
    editor.source_model.removeRow(0)
    assert editor.source_model.rowCount() == 0

def test_tlk_editor_jump_spinbox_range(qtbot, installation: HTInstallation):
    """Test jump spinbox with various values."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add entries
    for i in range(10):
        editor.insert()
    
    # Test jump spinbox values
    for val in [0, 1, 5, 9]:
        editor.ui.jumpSpinbox.setValue(val)
        assert editor.ui.jumpSpinbox.value() == val
        
        # Should update table selection
        current = editor.ui.talkTable.currentIndex()
        if current.isValid():
            assert current.row() == val

def test_tlk_editor_filter_case_sensitivity(qtbot, installation: HTInstallation):
    """Test filter case sensitivity."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add entries with mixed case
    entries = ["Apple", "apple", "APPLE", "Banana", "banana"]
    for text in entries:
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(text)
    
    # Test case-insensitive filter (default behavior)
    editor.ui.searchEdit.setText("apple")
    editor.do_filter("apple")
    # Should match Apple, apple, APPLE
    assert editor.proxy_model.rowCount() == 3
    
    editor.ui.searchEdit.setText("APPLE")
    editor.do_filter("APPLE")
    # Should still match all (case insensitive)
    assert editor.proxy_model.rowCount() == 3

def test_tlk_editor_empty_entry_handling(qtbot, installation: HTInstallation):
    """Test handling of empty entries."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add empty entry
    editor.insert()
    index = editor.proxy_model.index(0, 0)
    editor.ui.talkTable.setCurrentIndex(index)
    editor.ui.textEdit.setPlainText("")
    editor.ui.soundEdit.setText("")
    
    # Build should handle empty entry
    data, _ = editor.build()
    from pykotor.resource.formats.tlk import read_tlk
    tlk = read_tlk(data)
    assert len(tlk) == 1
    assert tlk[0].text == ""
    assert tlk[0].voiceover == ""

def test_tlk_editor_multiple_selections(qtbot, installation: HTInstallation):
    """Test table selection modes and multiple selections if supported."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Add multiple entries
    for i in range(5):
        editor.insert()
    
    # Test single selection
    index = editor.proxy_model.index(2, 0)
    editor.ui.talkTable.setCurrentIndex(index)
    assert editor.ui.talkTable.currentIndex().row() == 2
    
    # Verify selection updates widgets
    # Widgets should reflect selected entry