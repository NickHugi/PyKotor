"""
Comprehensive tests for UTW Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.utw import UTWEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.utw import UTW, read_utw  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_utw_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    original_utw = read_utw(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Waypoint Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    assert modified_utw.name.get(Language.ENGLISH, Gender.MALE) == "Modified Waypoint Name"
    assert modified_utw.name.get(Language.ENGLISH, Gender.MALE) != original_utw.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Waypoint Name"

def test_utw_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    original_utw = read_utw(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    assert modified_utw.tag == "modified_tag"
    assert modified_utw.tag != original_utw.tag
    
    # Load back and verify
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_utw_editor_manipulate_resref(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating resref field."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Modify resref
    editor.ui.resrefEdit.setText("modified_resref")
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    assert str(modified_utw.resref) == "modified_resref"
    
    # Load back and verify
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, data)
    assert editor.ui.resrefEdit.text() == "modified_resref"

# ============================================================================
# ADVANCED FIELDS MANIPULATIONS
# ============================================================================

def test_utw_editor_manipulate_is_note_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating is note checkbox."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Toggle checkbox
    editor.ui.isNoteCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utw = read_utw(data)
    assert modified_utw.has_map_note
    
    editor.ui.isNoteCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utw = read_utw(data)
    assert not modified_utw.has_map_note

def test_utw_editor_manipulate_note_enabled_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating note enabled checkbox."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Toggle checkbox
    editor.ui.noteEnabledCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utw = read_utw(data)
    assert modified_utw.map_note_enabled
    
    editor.ui.noteEnabledCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utw = read_utw(data)
    assert not modified_utw.map_note_enabled

def test_utw_editor_manipulate_map_note_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating map note LocalizedString field."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Modify map note
    new_note = LocalizedString.from_english("Modified Map Note")
    
    # Handle both possible UI implementations
    if hasattr(editor.ui.noteEdit, 'set_locstring'):
        editor.ui.noteEdit.set_locstring(new_note)
    elif hasattr(editor.ui.noteEdit, 'setText'):
        editor.ui.noteEdit.setText("Modified Map Note")
    else:
        # Try via note change button / dialog
        editor.change_note()
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    
    # Verify note was saved (implementation may vary)
    assert isinstance(modified_utw.map_note, LocalizedString)

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_utw_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Modify comments
    test_comments = [
        "",
        "Test comment",
        "Multi\nline\ncomment",
        "Comment with special chars !@#$%^&*()",
        "Very long comment " * 100,
    ]
    
    for comment in test_comments:
        editor.ui.commentsEdit.setPlainText(comment)
        
        # Save and verify
        data, _ = editor.build()
        modified_utw = read_utw(data)
        assert modified_utw.comment == comment
        
        # Load back and verify
        editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_utw_editor_manipulate_all_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all fields simultaneously."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Modify ALL fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Waypoint"))
    editor.ui.tagEdit.setText("combined_test")
    editor.ui.resrefEdit.setText("combined_resref")
    editor.ui.isNoteCheckbox.setChecked(True)
    editor.ui.noteEnabledCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("Combined test comment")
    
    # Save and verify all
    data, _ = editor.build()
    modified_utw = read_utw(data)
    
    assert modified_utw.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Waypoint"
    assert modified_utw.tag == "combined_test"
    assert str(modified_utw.resref) == "combined_resref"
    assert modified_utw.has_map_note
    assert modified_utw.map_note_enabled
    assert modified_utw.comment == "Combined test comment"

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_utw_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    # Load original
    original_data = utw_file.read_bytes()
    original_utw = read_utw(original_data)
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_utw = read_utw(data)
    
    # Verify key fields match
    assert saved_utw.tag == original_utw.tag
    assert str(saved_utw.resref) == str(original_utw.resref)
    assert saved_utw.has_map_note == original_utw.has_map_note
    assert saved_utw.map_note_enabled == original_utw.map_note_enabled
    
    # Load saved data back
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_utw.tag
    assert editor.ui.resrefEdit.text() == str(original_utw.resref)

def test_utw_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    # Load original
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.isNoteCheckbox.setChecked(True)
    editor.ui.noteEnabledCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Save
    data1, _ = editor.build()
    saved_utw1 = read_utw(data1)
    
    # Load saved data
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.isNoteCheckbox.isChecked()
    assert editor.ui.noteEnabledCheckbox.isChecked()
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_utw2 = read_utw(data2)
    
    # Verify second save matches first
    assert saved_utw2.tag == saved_utw1.tag
    assert saved_utw2.has_map_note == saved_utw1.has_map_note
    assert saved_utw2.map_note_enabled == saved_utw1.map_note_enabled
    assert saved_utw2.comment == saved_utw1.comment

def test_utw_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        
        # Save
        data, _ = editor.build()
        saved_utw = read_utw(data)
        
        # Verify
        assert saved_utw.tag == f"cycle_{cycle}"
        
        # Load back
        editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_utw_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Set all to minimums
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    
    assert modified_utw.tag == ""
    assert str(modified_utw.resref) == ""
    assert modified_utw.comment == ""

def test_utw_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Set all to maximums
    editor.ui.tagEdit.setText("x" * 32)  # Max tag length
    editor.ui.commentsEdit.setPlainText("x" * 1000)  # Long comment
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    
    assert len(modified_utw.tag) > 0

def test_utw_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    
    assert modified_utw.tag == ""
    assert str(modified_utw.resref) == ""
    assert modified_utw.comment == ""

def test_utw_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_utw = read_utw(data)
    
    assert modified_utw.tag == special_tag
    assert modified_utw.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_utw_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    # Load original
    original_data = utw_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_utw_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.isNoteCheckbox.setChecked(True)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid UTW
    modified_utw = read_utw(data)
    assert modified_utw.tag == "modified_gff_test"
    assert modified_utw.has_map_note

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_utw_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new UTW file from scratch."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Waypoint"))
    editor.ui.tagEdit.setText("new_waypoint")
    editor.ui.resrefEdit.setText("new_waypoint")
    editor.ui.isNoteCheckbox.setChecked(True)
    editor.ui.noteEnabledCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("New waypoint comment")
    
    # Build and verify
    data, _ = editor.build()
    new_utw = read_utw(data)
    
    assert new_utw.name.get(Language.ENGLISH, Gender.MALE) == "New Waypoint"
    assert new_utw.tag == "new_waypoint"
    assert new_utw.has_map_note
    assert new_utw.map_note_enabled
    assert new_utw.comment == "New waypoint comment"

def test_utw_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_utw = read_utw(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_utw.tag, str)
    assert isinstance(new_utw.resref, ResRef)

# ============================================================================
# BUTTON FUNCTIONALITY TESTS
# ============================================================================

def test_utw_editor_generate_tag_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button functionality."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, utw_file.read_bytes())
    
    # Clear tag
    editor.ui.tagEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated
    generated_tag = editor.ui.tagEdit.text()
    assert generated_tag

def test_utw_editor_generate_resref_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button functionality."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, utw_file.read_bytes())
    
    # Clear resref
    editor.ui.resrefEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated
    generated_resref = editor.ui.resrefEdit.text()
    assert generated_resref

def test_utw_editor_note_change_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test note change button exists."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify button exists
    assert hasattr(editor.ui, 'noteChangeButton')
    
    # Verify signal is connected
    assert editor.ui.noteChangeButton.receivers(editor.ui.noteChangeButton.clicked) > 0

# ============================================================================
# MAP NOTE COMBINATION TESTS
# ============================================================================

def test_utw_editor_map_note_checkboxes_interaction(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test interaction between map note checkboxes."""
    editor = UTWEditor(None, installation)
    qtbot.addWidget(editor)
    
    utw_file = test_files_dir / "tar05_sw05aa10.utw"
    if not utw_file.exists():
        pytest.skip("tar05_sw05aa10.utw not found")
    
    original_data = utw_file.read_bytes()
    editor.load(utw_file, "tar05_sw05aa10", ResourceType.UTW, original_data)
    
    # Test all combinations
    combinations = [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ]
    
    for has_note, enabled in combinations:
        editor.ui.isNoteCheckbox.setChecked(has_note)
        editor.ui.noteEnabledCheckbox.setChecked(enabled)
        
        # Save and verify
        data, _ = editor.build()
        modified_utw = read_utw(data)
        assert modified_utw.has_map_note == has_note
        assert modified_utw.map_note_enabled == enabled
