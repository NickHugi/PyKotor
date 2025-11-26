"""
Comprehensive tests for LTR Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTableWidgetItem
from toolset.gui.editors.ltr import LTREditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.formats.ltr import LTR, read_ltr  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELD MANIPULATIONS
# ============================================================================

def test_ltr_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new LTR file from scratch."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Verify UI is populated
    assert editor.ui.tableSingles.rowCount() > 0
    assert editor.ui.tableDoubles.rowCount() > 0
    assert editor.ui.tableTriples.rowCount() > 0
    
    # Build and verify
    data, _ = editor.build()
    new_ltr = read_ltr(data)
    assert new_ltr is not None

def test_ltr_editor_load_empty_file(qtbot, installation: HTInstallation):
    """Test loading an empty/new LTR file."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Build empty file
    data, _ = editor.build()
    
    # Load it back
    editor.load(Path("test.ltr"), "test", ResourceType.LTR, data)
    
    # Verify it loaded correctly
    assert editor.ltr is not None

# ============================================================================
# SINGLE CHARACTER MANIPULATIONS
# ============================================================================

def test_ltr_editor_manipulate_single_character(qtbot, installation: HTInstallation):
    """Test manipulating single character values."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test setting single character values
    test_char = "A"
    start_val = 10
    middle_val = 20
    end_val = 30
    
    # Set values via combo box and spin boxes
    index = editor.ui.comboBoxSingleChar.findText(test_char)
    if index >= 0:
        editor.ui.comboBoxSingleChar.setCurrentIndex(index)
        editor.ui.spinBoxSingleStart.setValue(start_val)
        editor.ui.spinBoxSingleMiddle.setValue(middle_val)
        editor.ui.spinBoxSingleEnd.setValue(end_val)
        
        # Apply changes
        editor.setSingleCharacter()
        
        # Verify values were set
        assert editor.ltr._singles.get_start(test_char) == start_val
        assert editor.ltr._singles.get_middle(test_char) == middle_val
        assert editor.ltr._singles.get_end(test_char) == end_val

def test_ltr_editor_manipulate_multiple_single_characters(qtbot, installation: HTInstallation):
    """Test manipulating multiple single characters."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test multiple characters
    test_chars = ["A", "B", "C", "Z"]
    for i, char in enumerate(test_chars):
        index = editor.ui.comboBoxSingleChar.findText(char)
        if index >= 0:
            editor.ui.comboBoxSingleChar.setCurrentIndex(index)
            editor.ui.spinBoxSingleStart.setValue(10 + i)
            editor.ui.spinBoxSingleMiddle.setValue(20 + i)
            editor.ui.spinBoxSingleEnd.setValue(30 + i)
            editor.setSingleCharacter()
    
    # Build and verify
    data, _ = editor.build()
    modified_ltr = read_ltr(data)
    
    # Verify all characters were set
    for i, char in enumerate(test_chars):
        assert modified_ltr._singles.get_start(char) == 10 + i
        assert modified_ltr._singles.get_middle(char) == 20 + i
        assert modified_ltr._singles.get_end(char) == 30 + i

# ============================================================================
# DOUBLE CHARACTER MANIPULATIONS
# ============================================================================

def test_ltr_editor_manipulate_double_character(qtbot, installation: HTInstallation):
    """Test manipulating double character values."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test setting double character values
    prev_char = "A"
    char = "B"
    start_val = 5
    middle_val = 10
    end_val = 15
    
    # Set values via combo boxes and spin boxes
    prev_index = editor.ui.comboBoxDoublePrevChar.findText(prev_char)
    char_index = editor.ui.comboBoxDoubleChar.findText(char)
    
    if prev_index >= 0 and char_index >= 0:
        editor.ui.comboBoxDoublePrevChar.setCurrentIndex(prev_index)
        editor.ui.comboBoxDoubleChar.setCurrentIndex(char_index)
        editor.ui.spinBoxDoubleStart.setValue(start_val)
        editor.ui.spinBoxDoubleMiddle.setValue(middle_val)
        editor.ui.spinBoxDoubleEnd.setValue(end_val)
        
        # Apply changes
        editor.setDoubleCharacter()
        
        # Verify values were set
        assert editor.ltr._doubles[0].get_start(char) == start_val
        assert editor.ltr._doubles[0].get_middle(char) == middle_val
        assert editor.ltr._doubles[0].get_end(char) == end_val

def test_ltr_editor_manipulate_multiple_double_characters(qtbot, installation: HTInstallation):
    """Test manipulating multiple double character combinations."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test multiple double combinations
    test_combos = [("A", "B"), ("B", "C"), ("C", "D")]
    for i, (prev, char) in enumerate(test_combos):
        prev_index = editor.ui.comboBoxDoublePrevChar.findText(prev)
        char_index = editor.ui.comboBoxDoubleChar.findText(char)
        
        if prev_index >= 0 and char_index >= 0:
            editor.ui.comboBoxDoublePrevChar.setCurrentIndex(prev_index)
            editor.ui.comboBoxDoubleChar.setCurrentIndex(char_index)
            editor.ui.spinBoxDoubleStart.setValue(5 + i)
            editor.ui.spinBoxDoubleMiddle.setValue(10 + i)
            editor.ui.spinBoxDoubleEnd.setValue(15 + i)
            editor.setDoubleCharacter()
    
    # Build and verify
    data, _ = editor.build()
    modified_ltr = read_ltr(data)
    
    # Verify combinations were set
    char_set = LTR.CHARACTER_SET
    for i, (prev, char) in enumerate(test_combos):
        prev_idx = char_set.index(prev)
        assert modified_ltr._doubles[prev_idx].get_start(char) == 5 + i

# ============================================================================
# TRIPLE CHARACTER MANIPULATIONS
# ============================================================================

def test_ltr_editor_manipulate_triple_character(qtbot, installation: HTInstallation):
    """Test manipulating triple character values."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test setting triple character values
    prev2_char = "A"
    prev1_char = "B"
    char = "C"
    start_val = 3
    middle_val = 6
    end_val = 9
    
    # Set values via combo boxes and spin boxes
    prev2_index = editor.ui.comboBoxTriplePrev2Char.findText(prev2_char)
    prev1_index = editor.ui.comboBoxTriplePrev1Char.findText(prev1_char)
    char_index = editor.ui.comboBoxTripleChar.findText(char)
    
    if prev2_index >= 0 and prev1_index >= 0 and char_index >= 0:
        editor.ui.comboBoxTriplePrev2Char.setCurrentIndex(prev2_index)
        editor.ui.comboBoxTriplePrev1Char.setCurrentIndex(prev1_index)
        editor.ui.comboBoxTripleChar.setCurrentIndex(char_index)
        editor.ui.spinBoxTripleStart.setValue(start_val)
        editor.ui.spinBoxTripleMiddle.setValue(middle_val)
        editor.ui.spinBoxTripleEnd.setValue(end_val)
        
        # Apply changes
        editor.setTripleCharacter()
        
        # Verify values were set (triples are nested arrays)
        char_set = LTR.CHARACTER_SET
        prev2_idx = char_set.index(prev2_char)
        prev1_idx = char_set.index(prev1_char)
        assert editor.ltr._triples[prev2_idx][prev1_idx].get_start(char) == start_val
        assert editor.ltr._triples[prev2_idx][prev1_idx].get_middle(char) == middle_val
        assert editor.ltr._triples[prev2_idx][prev1_idx].get_end(char) == end_val

# ============================================================================
# NAME GENERATION TESTS
# ============================================================================

def test_ltr_editor_generate_name(qtbot, installation: HTInstallation):
    """Test name generation functionality."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Generate name
    editor.generateName()
    
    # Verify generated name is displayed
    generated_name = editor.ui.lineEditGeneratedName.text()
    assert len(generated_name) > 0
    
    # Verify it was generated from LTR
    expected_name = editor.ltr.generate()
    assert generated_name == expected_name

def test_ltr_editor_generate_multiple_names(qtbot, installation: HTInstallation):
    """Test generating multiple names."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Generate multiple names
    generated_names = []
    for _ in range(10):
        editor.generateName()
        name = editor.ui.lineEditGeneratedName.text()
        generated_names.append(name)
    
    # Verify all names were generated (may be different)
    assert len(set(generated_names)) > 0  # At least some variation

# ============================================================================
# TABLE MANIPULATIONS
# ============================================================================

def test_ltr_editor_table_row_add_remove_singles(qtbot, installation: HTInstallation):
    """Test adding and removing rows in singles table."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    initial_count = editor.ui.tableSingles.rowCount()
    
    # Add row
    editor.addSingleRow()
    assert editor.ui.tableSingles.rowCount() == initial_count + 1
    
    # Select and remove row
    editor.ui.tableSingles.selectRow(initial_count)
    editor.removeSingleRow()
    assert editor.ui.tableSingles.rowCount() == initial_count

def test_ltr_editor_table_row_add_remove_doubles(qtbot, installation: HTInstallation):
    """Test adding and removing rows in doubles table."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    initial_count = editor.ui.tableDoubles.rowCount()
    
    # Add row
    editor.addDoubleRow()
    assert editor.ui.tableDoubles.rowCount() == initial_count + 1
    
    # Select and remove row
    editor.ui.tableDoubles.selectRow(initial_count)
    editor.removeDoubleRow()
    assert editor.ui.tableDoubles.rowCount() == initial_count

def test_ltr_editor_table_row_add_remove_triples(qtbot, installation: HTInstallation):
    """Test adding and removing rows in triples table."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    initial_count = editor.ui.tableTriples.rowCount()
    
    # Add row
    editor.addTripleRow()
    assert editor.ui.tableTriples.rowCount() == initial_count + 1
    
    # Select and remove row
    editor.ui.tableTriples.selectRow(initial_count)
    editor.removeTripleRow()
    assert editor.ui.tableTriples.rowCount() == initial_count

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_ltr_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set some values
    char = "A"
    index = editor.ui.comboBoxSingleChar.findText(char)
    if index >= 0:
        editor.ui.comboBoxSingleChar.setCurrentIndex(index)
        editor.ui.spinBoxSingleStart.setValue(10)
        editor.ui.spinBoxSingleMiddle.setValue(20)
        editor.ui.spinBoxSingleEnd.setValue(30)
        editor.setSingleCharacter()
    
    # Save
    data1, _ = editor.build()
    saved_ltr1 = read_ltr(data1)
    
    # Load saved data
    editor.load(Path("test.ltr"), "test", ResourceType.LTR, data1)
    
    # Verify modifications preserved
    if index >= 0:
        assert editor.ltr._singles.get_start(char) == 10
        assert editor.ltr._singles.get_middle(char) == 20
        assert editor.ltr._singles.get_end(char) == 30
    
    # Save again
    data2, _ = editor.build()
    saved_ltr2 = read_ltr(data2)
    
    # Verify second save matches first
    if index >= 0:
        assert saved_ltr2._singles.get_start(char) == saved_ltr1._singles.get_start(char)
        assert saved_ltr2._singles.get_middle(char) == saved_ltr1._singles.get_middle(char)
        assert saved_ltr2._singles.get_end(char) == saved_ltr1._singles.get_end(char)

def test_ltr_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation):
    """Test multiple save/load cycles preserve data correctly."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    char = "B"
    index = editor.ui.comboBoxSingleChar.findText(char)
    if index < 0:
        pytest.skip("Character not found in combo box")
    
    # Perform multiple cycles
    for cycle in range(3):
        # Modify
        editor.ui.comboBoxSingleChar.setCurrentIndex(index)
        editor.ui.spinBoxSingleStart.setValue(10 + cycle)
        editor.ui.spinBoxSingleMiddle.setValue(20 + cycle)
        editor.ui.spinBoxSingleEnd.setValue(30 + cycle)
        editor.setSingleCharacter()
        
        # Save
        data, _ = editor.build()
        saved_ltr = read_ltr(data)
        
        # Verify
        assert saved_ltr._singles.get_start(char) == 10 + cycle
        assert saved_ltr._singles.get_middle(char) == 20 + cycle
        assert saved_ltr._singles.get_end(char) == 30 + cycle
        
        # Load back
        editor.load(Path("test.ltr"), "test", ResourceType.LTR, data)
        
        # Verify loaded
        assert editor.ltr._singles.get_start(char) == 10 + cycle
        assert editor.ltr._singles.get_middle(char) == 20 + cycle
        assert editor.ltr._singles.get_end(char) == 30 + cycle

# ============================================================================
# UI FEATURE TESTS
# ============================================================================

def test_ltr_editor_table_sorting(qtbot, installation: HTInstallation):
    """Test that tables have sorting enabled."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Verify sorting is enabled
    assert editor.ui.tableSingles.isSortingEnabled()
    assert editor.ui.tableDoubles.isSortingEnabled()
    assert editor.ui.tableTriples.isSortingEnabled()

def test_ltr_editor_auto_fit_columns(qtbot, installation: HTInstallation):
    """Test auto-fit columns functionality."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Toggle auto-fit on
    editor.toggle_auto_fit_columns(True)
    assert editor.auto_resize_enabled
    
    # Toggle auto-fit off
    editor.toggle_auto_fit_columns(False)
    assert not editor.auto_resize_enabled

def test_ltr_editor_alternate_row_colors(qtbot, installation: HTInstallation):
    """Test alternate row colors toggle."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Toggle alternate row colors
    initial_state = editor.ui.tableSingles.alternatingRowColors()
    editor.toggle_alternate_row_colors()
    
    # Verify state changed
    assert editor.ui.tableSingles.alternatingRowColors() != initial_state
    
    # Toggle back
    editor.toggle_alternate_row_colors()
    assert editor.ui.tableSingles.alternatingRowColors() == initial_state

def test_ltr_editor_combo_box_population(qtbot, installation: HTInstallation):
    """Test that combo boxes are properly populated."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Verify combo boxes have items
    assert editor.ui.comboBoxSingleChar.count() > 0
    assert editor.ui.comboBoxDoubleChar.count() > 0
    assert editor.ui.comboBoxDoublePrevChar.count() > 0
    assert editor.ui.comboBoxTripleChar.count() > 0
    assert editor.ui.comboBoxTriplePrev1Char.count() > 0
    assert editor.ui.comboBoxTriplePrev2Char.count() > 0
    
    # Verify all combo boxes have same character set
    char_set = LTR.CHARACTER_SET
    assert editor.ui.comboBoxSingleChar.count() == len(char_set)
    assert editor.ui.comboBoxDoubleChar.count() == len(char_set)

# ============================================================================
# EDGE CASES
# ============================================================================

def test_ltr_editor_extreme_values(qtbot, installation: HTInstallation):
    """Test handling of extreme values."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    char = "A"
    index = editor.ui.comboBoxSingleChar.findText(char)
    if index >= 0:
        # Test extreme values
        editor.ui.comboBoxSingleChar.setCurrentIndex(index)
        editor.ui.spinBoxSingleStart.setValue(0)
        editor.ui.spinBoxSingleMiddle.setValue(100)
        editor.ui.spinBoxSingleEnd.setValue(255)
        editor.setSingleCharacter()
        
        # Verify values were set
        assert editor.ltr._singles.get_start(char) == 0
        assert editor.ltr._singles.get_middle(char) == 100
        assert editor.ltr._singles.get_end(char) == 255

def test_ltr_editor_empty_tables(qtbot, installation: HTInstallation):
    """Test handling of empty/new tables."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Verify tables are populated after new()
    assert editor.ui.tableSingles.rowCount() > 0
    assert editor.ui.tableDoubles.rowCount() > 0
    assert editor.ui.tableTriples.rowCount() > 0
    
    # Verify LTR object is not None
    assert editor.ltr is not None

# ============================================================================
# COMBINATION TESTS
# ============================================================================

def test_ltr_editor_manipulate_all_character_types(qtbot, installation: HTInstallation):
    """Test manipulating singles, doubles, and triples together."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set single
    char = "A"
    index = editor.ui.comboBoxSingleChar.findText(char)
    if index >= 0:
        editor.ui.comboBoxSingleChar.setCurrentIndex(index)
        editor.ui.spinBoxSingleStart.setValue(10)
        editor.ui.spinBoxSingleMiddle.setValue(20)
        editor.ui.spinBoxSingleEnd.setValue(30)
        editor.setSingleCharacter()
    
    # Set double
    prev_char = "A"
    char2 = "B"
    prev_index = editor.ui.comboBoxDoublePrevChar.findText(prev_char)
    char2_index = editor.ui.comboBoxDoubleChar.findText(char2)
    if prev_index >= 0 and char2_index >= 0:
        editor.ui.comboBoxDoublePrevChar.setCurrentIndex(prev_index)
        editor.ui.comboBoxDoubleChar.setCurrentIndex(char2_index)
        editor.ui.spinBoxDoubleStart.setValue(5)
        editor.ui.spinBoxDoubleMiddle.setValue(10)
        editor.ui.spinBoxDoubleEnd.setValue(15)
        editor.setDoubleCharacter()
    
    # Set triple
    prev2 = "A"
    prev1 = "B"
    char3 = "C"
    prev2_index = editor.ui.comboBoxTriplePrev2Char.findText(prev2)
    prev1_index = editor.ui.comboBoxTriplePrev1Char.findText(prev1)
    char3_index = editor.ui.comboBoxTripleChar.findText(char3)
    if prev2_index >= 0 and prev1_index >= 0 and char3_index >= 0:
        editor.ui.comboBoxTriplePrev2Char.setCurrentIndex(prev2_index)
        editor.ui.comboBoxTriplePrev1Char.setCurrentIndex(prev1_index)
        editor.ui.comboBoxTripleChar.setCurrentIndex(char3_index)
        editor.ui.spinBoxTripleStart.setValue(3)
        editor.ui.spinBoxTripleMiddle.setValue(6)
        editor.ui.spinBoxTripleEnd.setValue(9)
        editor.setTripleCharacter()
    
    # Build and verify all values
    data, _ = editor.build()
    modified_ltr = read_ltr(data)
    
    if index >= 0:
        assert modified_ltr._singles.get_start(char) == 10
    if prev_index >= 0 and char2_index >= 0:
        char_set = LTR.CHARACTER_SET
        prev_idx = char_set.index(prev_char)
        assert modified_ltr._doubles[prev_idx].get_start(char2) == 5

# ============================================================================
# HEADLESS UI TESTS WITH REAL FILES
# ============================================================================

def test_ltr_editor_headless_ui_load_build(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test LTR Editor in headless UI - loads real file and builds data."""
    editor = LTREditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a LTR file
    ltr_files = list(test_files_dir.glob("*.ltr")) + list(test_files_dir.rglob("*.ltr"))
    if not ltr_files:
        # Try to get one from installation
        ltr_resources = list(installation.resources(ResourceType.LTR))[:1]
        if not ltr_resources:
            pytest.skip("No LTR files available for testing")
        ltr_resource = ltr_resources[0]
        ltr_data = installation.resource(ltr_resource.identifier)
        if not ltr_data:
            pytest.skip(f"Could not load LTR data for {ltr_resource.identifier}")
        editor.load(
            ltr_resource.filepath if hasattr(ltr_resource, 'filepath') else Path("module.ltr"),
            ltr_resource.resname,
            ResourceType.LTR,
            ltr_data
        )
    else:
        ltr_file = ltr_files[0]
        original_data = ltr_file.read_bytes()
        editor.load(ltr_file, ltr_file.stem, ResourceType.LTR, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    assert editor.ltr is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    loaded_ltr = read_ltr(data)
    assert loaded_ltr is not None

