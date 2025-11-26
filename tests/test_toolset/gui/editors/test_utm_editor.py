"""
Comprehensive tests for UTM Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.utm import UTMEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.utm import UTM, read_utm  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_utm_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    original_utm = read_utm(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Merchant Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    assert modified_utm.name.get(Language.ENGLISH, Gender.MALE) == "Modified Merchant Name"
    assert modified_utm.name.get(Language.ENGLISH, Gender.MALE) != original_utm.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(utm_file, "m_chano", ResourceType.UTM, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Merchant Name"

def test_utm_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    original_utm = read_utm(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    assert modified_utm.tag == "modified_tag"
    assert modified_utm.tag != original_utm.tag
    
    # Load back and verify
    editor.load(utm_file, "m_chano", ResourceType.UTM, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_utm_editor_manipulate_resref(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating resref field."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Modify resref
    editor.ui.resrefEdit.setText("modified_resref")
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    assert str(modified_utm.resref) == "modified_resref"
    
    # Load back and verify
    editor.load(utm_file, "m_chano", ResourceType.UTM, data)
    assert editor.ui.resrefEdit.text() == "modified_resref"

def test_utm_editor_manipulate_id_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating ID spin box."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Test various ID values
    test_id_values = [0, 1, 5, 10, 100, 255]
    for val in test_id_values:
        editor.ui.idSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_utm = read_utm(data)
        assert modified_utm.id == val
        
        # Load back and verify
        editor.load(utm_file, "m_chano", ResourceType.UTM, data)
        assert editor.ui.idSpin.value() == val

def test_utm_editor_manipulate_markup_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating markup spin boxes."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Test mark up
    test_markup_values = [0, 10, 25, 50, 100, 200]
    for val in test_markup_values:
        editor.ui.markUpSpin.setValue(val)
        data, _ = editor.build()
        modified_utm = read_utm(data)
        assert modified_utm.mark_up == val
    
    # Test mark down
    for val in test_markup_values:
        editor.ui.markDownSpin.setValue(val)
        data, _ = editor.build()
        modified_utm = read_utm(data)
        assert modified_utm.mark_down == val

def test_utm_editor_manipulate_on_open_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on open script field."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Modify script
    editor.ui.onOpenEdit.setText("test_on_open")
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    assert str(modified_utm.on_open) == "test_on_open"
    
    # Load back and verify
    editor.load(utm_file, "m_chano", ResourceType.UTM, data)
    assert editor.ui.onOpenEdit.text() == "test_on_open"

def test_utm_editor_manipulate_store_flag_select(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating store flag combo box."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Test all store flag combinations
    # Index 0: Can buy only (1 & 1 = 1, 1 & 2 = 0)
    # Index 1: Can sell only (2 & 1 = 0, 2 & 2 = 2)
    # Index 2: Both (3 & 1 = 1, 3 & 2 = 2)
    # Index -1 (default): Neither (0 & 1 = 0, 0 & 2 = 0)
    
    for i in range(editor.ui.storeFlagSelect.count()):
        editor.ui.storeFlagSelect.setCurrentIndex(i)
        
        # Save and verify
        data, _ = editor.build()
        modified_utm = read_utm(data)
        
        # Verify flags match expected bitwise operation
        expected_can_buy = bool((i + 1) & 1)
        expected_can_sell = bool((i + 1) & 2)
        assert modified_utm.can_buy == expected_can_buy
        assert modified_utm.can_sell == expected_can_sell
        
        # Load back and verify
        editor.load(utm_file, "m_chano", ResourceType.UTM, data)
        assert editor.ui.storeFlagSelect.currentIndex() == i

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_utm_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
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
        modified_utm = read_utm(data)
        assert modified_utm.comment == comment
        
        # Load back and verify
        editor.load(utm_file, "m_chano", ResourceType.UTM, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_utm_editor_manipulate_all_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all fields simultaneously."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Modify ALL fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Merchant"))
    editor.ui.tagEdit.setText("combined_test")
    editor.ui.resrefEdit.setText("combined_resref")
    editor.ui.idSpin.setValue(50)
    editor.ui.markUpSpin.setValue(25)
    editor.ui.markDownSpin.setValue(10)
    editor.ui.onOpenEdit.setText("test_script")
    if editor.ui.storeFlagSelect.count() > 0:
        editor.ui.storeFlagSelect.setCurrentIndex(2)  # Both buy and sell
    editor.ui.commentsEdit.setPlainText("Combined test comment")
    
    # Save and verify all
    data, _ = editor.build()
    modified_utm = read_utm(data)
    
    assert modified_utm.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Merchant"
    assert modified_utm.tag == "combined_test"
    assert str(modified_utm.resref) == "combined_resref"
    assert modified_utm.id == 50
    assert modified_utm.mark_up == 25
    assert modified_utm.mark_down == 10
    assert str(modified_utm.on_open) == "test_script"
    assert modified_utm.can_buy
    assert modified_utm.can_sell
    assert modified_utm.comment == "Combined test comment"

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_utm_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    # Load original
    original_data = utm_file.read_bytes()
    original_utm = read_utm(original_data)
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_utm = read_utm(data)
    
    # Verify key fields match
    assert saved_utm.tag == original_utm.tag
    assert str(saved_utm.resref) == str(original_utm.resref)
    assert saved_utm.id == original_utm.id
    assert saved_utm.mark_up == original_utm.mark_up
    assert saved_utm.mark_down == original_utm.mark_down
    
    # Load saved data back
    editor.load(utm_file, "m_chano", ResourceType.UTM, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_utm.tag
    assert editor.ui.resrefEdit.text() == str(original_utm.resref)

def test_utm_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    # Load original
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.idSpin.setValue(100)
    editor.ui.markUpSpin.setValue(50)
    editor.ui.markDownSpin.setValue(25)
    if editor.ui.storeFlagSelect.count() > 0:
        editor.ui.storeFlagSelect.setCurrentIndex(2)  # Both
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Save
    data1, _ = editor.build()
    saved_utm1 = read_utm(data1)
    
    # Load saved data
    editor.load(utm_file, "m_chano", ResourceType.UTM, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.idSpin.value() == 100
    assert editor.ui.markUpSpin.value() == 50
    assert editor.ui.markDownSpin.value() == 25
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_utm2 = read_utm(data2)
    
    # Verify second save matches first
    assert saved_utm2.tag == saved_utm1.tag
    assert saved_utm2.id == saved_utm1.id
    assert saved_utm2.mark_up == saved_utm1.mark_up
    assert saved_utm2.mark_down == saved_utm1.mark_down
    assert saved_utm2.can_buy == saved_utm1.can_buy
    assert saved_utm2.can_sell == saved_utm1.can_sell
    assert saved_utm2.comment == saved_utm1.comment

def test_utm_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        editor.ui.idSpin.setValue(cycle * 10)
        
        # Save
        data, _ = editor.build()
        saved_utm = read_utm(data)
        
        # Verify
        assert saved_utm.tag == f"cycle_{cycle}"
        assert saved_utm.id == cycle * 10
        
        # Load back
        editor.load(utm_file, "m_chano", ResourceType.UTM, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"
        assert editor.ui.idSpin.value() == cycle * 10

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_utm_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Set all to minimums
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.idSpin.setValue(0)
    editor.ui.markUpSpin.setValue(0)
    editor.ui.markDownSpin.setValue(0)
    editor.ui.onOpenEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    
    assert modified_utm.tag == ""
    assert modified_utm.id == 0
    assert modified_utm.mark_up == 0
    assert modified_utm.mark_down == 0
    assert str(modified_utm.on_open) == ""

def test_utm_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Set all to maximums
    editor.ui.tagEdit.setText("x" * 32)  # Max tag length
    editor.ui.idSpin.setValue(editor.ui.idSpin.maximum())
    editor.ui.markUpSpin.setValue(editor.ui.markUpSpin.maximum())
    editor.ui.markDownSpin.setValue(editor.ui.markDownSpin.maximum())
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    
    assert modified_utm.id == editor.ui.idSpin.maximum()
    assert modified_utm.mark_up == editor.ui.markUpSpin.maximum()
    assert modified_utm.mark_down == editor.ui.markDownSpin.maximum()

def test_utm_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.onOpenEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    
    assert modified_utm.tag == ""
    assert str(modified_utm.resref) == ""
    assert str(modified_utm.on_open) == ""
    assert modified_utm.comment == ""

def test_utm_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_utm = read_utm(data)
    
    assert modified_utm.tag == special_tag
    assert modified_utm.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_utm_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    # Load original
    original_data = utm_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_utm_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    original_data = utm_file.read_bytes()
    editor.load(utm_file, "m_chano", ResourceType.UTM, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.idSpin.setValue(100)
    editor.ui.markUpSpin.setValue(50)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid UTM
    modified_utm = read_utm(data)
    assert modified_utm.tag == "modified_gff_test"
    assert modified_utm.id == 100
    assert modified_utm.mark_up == 50

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_utm_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new UTM file from scratch."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Merchant"))
    editor.ui.tagEdit.setText("new_merchant")
    editor.ui.resrefEdit.setText("new_merchant")
    editor.ui.idSpin.setValue(1)
    editor.ui.markUpSpin.setValue(10)
    editor.ui.markDownSpin.setValue(5)
    editor.ui.onOpenEdit.setText("test_script")
    if editor.ui.storeFlagSelect.count() > 0:
        editor.ui.storeFlagSelect.setCurrentIndex(2)  # Both
    editor.ui.commentsEdit.setPlainText("New merchant comment")
    
    # Build and verify
    data, _ = editor.build()
    new_utm = read_utm(data)
    
    assert new_utm.name.get(Language.ENGLISH, Gender.MALE) == "New Merchant"
    assert new_utm.tag == "new_merchant"
    assert new_utm.id == 1
    assert new_utm.mark_up == 10
    assert new_utm.mark_down == 5
    assert str(new_utm.on_open) == "test_script"
    assert new_utm.comment == "New merchant comment"

def test_utm_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_utm = read_utm(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_utm.tag, str)
    assert isinstance(new_utm.id, int)
    assert isinstance(new_utm.mark_up, int)
    assert isinstance(new_utm.mark_down, int)

# ============================================================================
# BUTTON FUNCTIONALITY TESTS
# ============================================================================

def test_utm_editor_generate_tag_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button functionality."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    editor.load(utm_file, "m_chano", ResourceType.UTM, utm_file.read_bytes())
    
    # Clear tag
    editor.ui.tagEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated
    generated_tag = editor.ui.tagEdit.text()
    assert generated_tag

def test_utm_editor_generate_resref_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button functionality."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    editor.load(utm_file, "m_chano", ResourceType.UTM, utm_file.read_bytes())
    
    # Clear resref
    editor.ui.resrefEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated
    generated_resref = editor.ui.resrefEdit.text()
    assert generated_resref

def test_utm_editor_inventory_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test inventory button exists and is connected."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify button exists
    assert hasattr(editor.ui, 'inventoryButton')
    
    # Verify signal is connected
    assert editor.ui.inventoryButton.receivers(editor.ui.inventoryButton.clicked) > 0
    
    # Verify method exists
    assert hasattr(editor, 'open_inventory')
    assert callable(editor.open_inventory)

# ============================================================================
# STORE FLAG COMBINATIONS TESTS
# ============================================================================

def test_utm_editor_store_flag_combinations(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test all store flag combinations."""
    editor = UTMEditor(None, installation)
    qtbot.addWidget(editor)
    
    utm_file = test_files_dir / "m_chano.utm"
    if not utm_file.exists():
        pytest.skip("m_chano.utm not found")
    
    editor.load(utm_file, "m_chano", ResourceType.UTM, utm_file.read_bytes())
    
    # Test all combinations
    # The storeFlagSelect uses index to encode flags:
    # Index 0: Can buy (1)
    # Index 1: Can sell (2)
    # Index 2: Both (3)
    # Default/None: Neither (0)
    
    combinations = []
    if editor.ui.storeFlagSelect.count() >= 3:
        combinations = [
            (0, True, False),   # Can buy only
            (1, False, True),   # Can sell only
            (2, True, True),    # Both
        ]
    elif editor.ui.storeFlagSelect.count() > 0:
        # Test whatever options are available
        for i in range(editor.ui.storeFlagSelect.count()):
            editor.ui.storeFlagSelect.setCurrentIndex(i)
            data, _ = editor.build()
            modified_utm = read_utm(data)
            # Just verify it saves/loads correctly
            assert isinstance(modified_utm.can_buy, bool)
            assert isinstance(modified_utm.can_sell, bool)
    
    # Test each combination
    for index, can_buy, can_sell in combinations:
        editor.ui.storeFlagSelect.setCurrentIndex(index)
        
        # Save and verify
        data, _ = editor.build()
        modified_utm = read_utm(data)
        assert modified_utm.can_buy == can_buy
        assert modified_utm.can_sell == can_sell
        
        # Load back and verify
        editor.load(utm_file, "m_chano", ResourceType.UTM, data)
        assert editor.ui.storeFlagSelect.currentIndex() == index
