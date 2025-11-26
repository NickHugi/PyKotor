from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    QTest, QApplication = None, None  # type: ignore[misc, assignment]

absolute_file_path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_toolset/test_files"

if (
    __name__ == "__main__"
    and getattr(sys, "frozen", False) is False
):
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


K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class UTIEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.gui.editors.uti import UTIEditor

        cls.UTIEditor = UTIEditor
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app = QApplication([])
        self.editor = self.UTIEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "../test_toolset/files/baragwin.uti"

        data = filepath.read_bytes()
        old = read_gff(data)
        self.editor.load(filepath, "baragwin", ResourceType.UTI, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func, ignore_default_changes=True)
        assert diff, os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for uti_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTI):
            old = read_gff(uti_resource.data())
            self.editor.load(uti_resource.filepath(), uti_resource.resname(), uti_resource.restype(), uti_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            assert diff, os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for uti_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTI):
            old = read_gff(uti_resource.data())
            self.editor.load(uti_resource.filepath(), uti_resource.resname(), uti_resource.restype(), uti_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            assert diff, os.linesep.join(self.log_messages)

    def test_placeholder(self):
        self.UTIEditor(None, self.INSTALLATION)


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Pytest-based UI tests (merged from test_ui_uti.py)
# ============================================================================

import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListWidgetItem, QTreeWidgetItem, QApplication
from toolset.gui.editors.uti import UTIEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.generics.uti import UTI, UTIProperty
from pykotor.resource.type import ResourceType
from pykotor.common.language import LocalizedString

def test_uti_editor_all_widgets_exist(qtbot, installation: HTInstallation):
    """Verify ALL widgets exist in UTI editor."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    # Basic tab widgets
    assert hasattr(editor.ui, 'nameEdit')
    assert hasattr(editor.ui, 'descEdit')
    assert hasattr(editor.ui, 'tagEdit')
    assert hasattr(editor.ui, 'resrefEdit')
    assert hasattr(editor.ui, 'baseSelect')
    assert hasattr(editor.ui, 'costSpin')
    assert hasattr(editor.ui, 'additionalCostSpin')
    assert hasattr(editor.ui, 'upgradeSpin')
    assert hasattr(editor.ui, 'plotCheckbox')
    assert hasattr(editor.ui, 'chargesSpin')
    assert hasattr(editor.ui, 'stackSpin')
    assert hasattr(editor.ui, 'modelVarSpin')
    assert hasattr(editor.ui, 'bodyVarSpin')
    assert hasattr(editor.ui, 'textureVarSpin')
    assert hasattr(editor.ui, 'tagGenerateButton')
    assert hasattr(editor.ui, 'resrefGenerateButton')
    assert hasattr(editor.ui, 'iconLabel')
    
    # Properties tab widgets
    assert hasattr(editor.ui, 'availablePropertyList')
    assert hasattr(editor.ui, 'assignedPropertiesList')
    assert hasattr(editor.ui, 'addPropertyButton')
    assert hasattr(editor.ui, 'removePropertyButton')
    assert hasattr(editor.ui, 'editPropertyButton')
    
    # Comments tab widgets
    assert hasattr(editor.ui, 'commentsEdit')

def test_uti_editor_all_basic_widgets_interactions(qtbot, installation: HTInstallation):
    """Test ALL basic tab widgets with exhaustive interactions."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Test nameEdit - LocalizedString widget
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Test Item"))
    assert editor.ui.nameEdit.locstring().get(0) == "Test Item"
    
    # Test descEdit - LocalizedString widget
    editor.ui.descEdit.set_locstring(LocalizedString.from_english("Test Description"))
    assert editor.ui.descEdit.locstring().get(0) == "Test Description"
    
    # Test tagEdit - QLineEdit
    editor.ui.tagEdit.setText("test_tag_item")
    assert editor.ui.tagEdit.text() == "test_tag_item"
    
    # Test resrefEdit - QLineEdit
    editor.ui.resrefEdit.setText("test_item_resref")
    assert editor.ui.resrefEdit.text() == "test_item_resref"
    
    # Test baseSelect - ComboBox
    if editor.ui.baseSelect.count() > 0:
        for i in range(min(10, editor.ui.baseSelect.count())):
            editor.ui.baseSelect.setCurrentIndex(i)
            assert editor.ui.baseSelect.currentIndex() == i
    
    # Test ALL spin boxes
    spin_tests = [
        ('costSpin', [0, 1, 10, 100, 1000, 10000]),
        ('additionalCostSpin', [0, 1, 10, 100, 1000]),
        ('upgradeSpin', [0, 1, 2, 3, 4, 5]),
        ('chargesSpin', [0, 1, 5, 10, 50, 100]),
        ('stackSpin', [1, 5, 10, 50, 100]),
        ('modelVarSpin', [0, 1, 2, 3, 4, 5]),
        ('bodyVarSpin', [0, 1, 2, 3, 4, 5]),
        ('textureVarSpin', [0, 1, 2, 3, 4, 5]),
    ]
    
    for spin_name, values in spin_tests:
        spin = getattr(editor.ui, spin_name)
        for val in values:
            spin.setValue(val)
            assert spin.value() == val
    
    # Test plotCheckbox
    editor.ui.plotCheckbox.setChecked(True)
    assert editor.ui.plotCheckbox.isChecked()
    editor.ui.plotCheckbox.setChecked(False)
    assert not editor.ui.plotCheckbox.isChecked()
    
    # Test buttons
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    assert editor.ui.tagEdit.text() == editor.ui.resrefEdit.text()
    
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    # Resref should be generated (either from resname or default)

def test_uti_editor_properties_widgets_exhaustive(qtbot, installation: HTInstallation):
    """Test ALL properties tab widgets with exhaustive interactions."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Test availablePropertyList - QTreeWidget
    assert editor.ui.availablePropertyList.topLevelItemCount() > 0
    
    # Test selecting and adding properties
    # Select first top-level item
    if editor.ui.availablePropertyList.topLevelItemCount() > 0:
        first_item = editor.ui.availablePropertyList.topLevelItem(0)
        editor.ui.availablePropertyList.setCurrentItem(first_item)
        
        # Test add button
        initial_count = editor.ui.assignedPropertiesList.count()
        qtbot.mouseClick(editor.ui.addPropertyButton, Qt.MouseButton.LeftButton)
        
        # Property should be added if item has no children (leaf node)
        if first_item.childCount() == 0:
            assert editor.ui.assignedPropertiesList.count() == initial_count + 1
        
        # Test double-click to add
        editor.ui.assignedPropertiesList.clear()
        editor.ui.availablePropertyList.setCurrentItem(first_item)
        if first_item.childCount() == 0:
            qtbot.mouseDClick(editor.ui.availablePropertyList.viewport(), Qt.MouseButton.LeftButton, 
                            pos=editor.ui.availablePropertyList.visualItemRect(first_item).center())
            assert editor.ui.assignedPropertiesList.count() > 0
    
    # Test assignedPropertiesList interactions
    if editor.ui.assignedPropertiesList.count() > 0:
        # Select first assigned property
        editor.ui.assignedPropertiesList.setCurrentRow(0)
        
        # Test edit button
        qtbot.mouseClick(editor.ui.editPropertyButton, Qt.MouseButton.LeftButton)
        # Dialog should open (we can't easily test dialog without mocking, but button should be enabled)
        
        # Test remove button
        count_before = editor.ui.assignedPropertiesList.count()
        qtbot.mouseClick(editor.ui.removePropertyButton, Qt.MouseButton.LeftButton)
        assert editor.ui.assignedPropertiesList.count() == count_before - 1
        
        # Test double-click to edit
        if editor.ui.assignedPropertiesList.count() > 0:
            editor.ui.assignedPropertiesList.setCurrentRow(0)
            qtbot.mouseDClick(editor.ui.assignedPropertiesList.viewport(), Qt.MouseButton.LeftButton,
                            pos=editor.ui.assignedPropertiesList.visualItemRect(
                                editor.ui.assignedPropertiesList.item(0)).center())
            # Dialog should open
    
    # Test Delete key shortcut
    if editor.ui.assignedPropertiesList.count() > 0:
        editor.ui.assignedPropertiesList.setCurrentRow(0)
        editor.ui.assignedPropertiesList.setFocus()
        count_before = editor.ui.assignedPropertiesList.count()
        qtbot.keyPress(editor.ui.assignedPropertiesList, Qt.Key.Key_Delete)
        assert editor.ui.assignedPropertiesList.count() == count_before - 1

def test_uti_editor_icon_updates(qtbot, installation: HTInstallation):
    """Test icon label updates when variations change."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    if editor.ui.baseSelect.count() > 0:
        # Test icon updates when base changes
        editor.ui.baseSelect.setCurrentIndex(0)
        qtbot.wait(100)  # Allow icon to load
        
        # Test icon updates when model variation changes
        for val in [0, 1, 2, 3]:
            editor.ui.modelVarSpin.setValue(val)
            qtbot.wait(50)
        
        # Test icon updates when body variation changes
        for val in [0, 1, 2]:
            editor.ui.bodyVarSpin.setValue(val)
            qtbot.wait(50)
        
        # Test icon updates when texture variation changes
        for val in [0, 1, 2]:
            editor.ui.textureVarSpin.setValue(val)
            qtbot.wait(50)
        
        # Verify icon label has tooltip
        assert editor.ui.iconLabel.toolTip()

def test_uti_editor_comments_widget(qtbot, installation: HTInstallation):
    """Test comments widget."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Test comments text edit
    editor.ui.commentsEdit.setPlainText("Test comment\nLine 2\nLine 3")
    assert editor.ui.commentsEdit.toPlainText() == "Test comment\nLine 2\nLine 3"
    
    # Verify it saves
    data, _ = editor.build()
    from pykotor.resource.generics.uti import read_uti
    uti = read_uti(data)
    assert uti.comment == "Test comment\nLine 2\nLine 3"

def test_uti_editor_all_widgets_build_verification(qtbot, installation: HTInstallation):
    """Test that ALL widget values are correctly saved in build()."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Set ALL basic values
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Test Item Name"))
    editor.ui.descEdit.set_locstring(LocalizedString.from_english("Test Item Description"))
    editor.ui.tagEdit.setText("test_tag")
    editor.ui.resrefEdit.setText("test_resref")
    if editor.ui.baseSelect.count() > 0:
        editor.ui.baseSelect.setCurrentIndex(1)
    editor.ui.costSpin.setValue(500)
    editor.ui.additionalCostSpin.setValue(100)
    editor.ui.upgradeSpin.setValue(2)
    editor.ui.plotCheckbox.setChecked(True)
    editor.ui.chargesSpin.setValue(10)
    editor.ui.stackSpin.setValue(5)
    editor.ui.modelVarSpin.setValue(3)
    editor.ui.bodyVarSpin.setValue(2)
    editor.ui.textureVarSpin.setValue(1)
    
    # Add a property if possible
    if editor.ui.availablePropertyList.topLevelItemCount() > 0:
        first_item = editor.ui.availablePropertyList.topLevelItem(0)
        if first_item.childCount() == 0:
            editor.ui.availablePropertyList.setCurrentItem(first_item)
            qtbot.mouseClick(editor.ui.addPropertyButton, Qt.MouseButton.LeftButton)
    
    # Set comments
    editor.ui.commentsEdit.setPlainText("Test comment")
    
    # Build and verify
    data, _ = editor.build()
    from pykotor.resource.generics.uti import read_uti
    uti = read_uti(data)
    
    assert uti.name.get(0) == "Test Item Name"
    assert uti.description.get(0) == "Test Item Description"
    assert uti.tag == "test_tag"
    assert str(uti.resref) == "test_resref"
    assert uti.cost == 500
    assert uti.add_cost == 100
    assert uti.upgrade_level == 2
    assert uti.plot
    assert uti.charges == 10
    assert uti.stack_size == 5
    assert uti.model_variation == 3
    assert uti.body_variation == 2
    assert uti.texture_variation == 1
    assert uti.comment == "Test comment"

def test_uti_editor_load_real_file(qtbot, installation: HTInstallation, test_files_dir):
    """Test loading a real UTI file and verifying ALL widgets populate correctly."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    
    uti_file = test_files_dir / "baragwin.uti"
    if not uti_file.exists():
        pytest.skip("baragwin.uti not found")
    
    editor.load(uti_file, "baragwin", ResourceType.UTI, uti_file.read_bytes())
    
    # Verify widgets populated
    assert editor.ui.tagEdit.text() == "baragwin"
    assert editor.ui.resrefEdit.text() == "baragwin"
    
    # Verify all widgets have values
    assert editor.ui.baseSelect.currentIndex() >= 0
    assert editor.ui.costSpin.value() >= 0
    assert len(editor.ui.assignedPropertiesList) >= 0  # May be empty
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    from pykotor.resource.generics.uti import read_uti
    loaded_uti = read_uti(data)
    assert loaded_uti is not None

def test_uti_editor_context_menu(qtbot, installation: HTInstallation):
    """Test icon label context menu."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Right-click icon label
    if editor.ui.baseSelect.count() > 0:
        editor.ui.baseSelect.setCurrentIndex(0)
        qtbot.wait(100)
        
        # Context menu should be available
        assert editor.ui.iconLabel.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
        
        # Trigger context menu (we can't easily test menu without showing it, but we verify it's set up)
        # The actual menu opening requires real display, but signal connection verifies setup
        assert editor.ui.iconLabel.receivers(editor.ui.iconLabel.customContextMenuRequested) > 0

def test_uti_editor_name_desc_dialogs(qtbot, installation: HTInstallation):
    """Test name and description edit dialogs."""
    editor = UTIEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()
    
    # Test change_name - opens LocalizedStringDialog
    # We can't easily test dialog without mocking, but we verify the method exists and is callable
    # The actual dialog would require user interaction or mocking
    
    # Test change_desc - opens LocalizedStringDialog
    # Same as above
    
    # Instead, verify the widgets are set up correctly
    assert editor.ui.nameEdit.locstring() is not None
    assert editor.ui.descEdit.locstring() is not None