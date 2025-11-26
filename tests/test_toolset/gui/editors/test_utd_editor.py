"""
Comprehensive tests for UTD Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.utd import UTDEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.utd import UTD, read_utd  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_utd_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    original_utd = read_utd(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Door Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.name.get(Language.ENGLISH, Gender.MALE) == "Modified Door Name"
    assert modified_utd.name.get(Language.ENGLISH, Gender.MALE) != original_utd.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Door Name"

def test_utd_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    original_utd = read_utd(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.tag == "modified_tag"
    assert modified_utd.tag != original_utd.tag
    
    # Load back and verify
    editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_utd_editor_manipulate_tag_generate_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    editor.load(utd_file, "naldoor001", ResourceType.UTD, utd_file.read_bytes())
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated from resname or resref
    generated_tag = editor.ui.tagEdit.text()
    assert generated_tag
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.tag == generated_tag

def test_utd_editor_manipulate_resref(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating resref field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify resref
    editor.ui.resrefEdit.setText("modified_resref")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.resref) == "modified_resref"
    
    # Load back and verify
    editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
    assert editor.ui.resrefEdit.text() == "modified_resref"

def test_utd_editor_manipulate_resref_generate_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    editor.load(utd_file, "naldoor001", ResourceType.UTD, utd_file.read_bytes())
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated from resname or default
    generated_resref = editor.ui.resrefEdit.text()
    assert generated_resref
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.resref) == generated_resref

def test_utd_editor_manipulate_appearance(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating appearance combo box."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test appearance selection
    if editor.ui.appearanceSelect.count() > 0:
        for i in range(min(5, editor.ui.appearanceSelect.count())):
            editor.ui.appearanceSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utd = read_utd(data)
            assert modified_utd.appearance_id == i
            
            # Load back and verify
            editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
            assert editor.ui.appearanceSelect.currentIndex() == i

def test_utd_editor_manipulate_conversation(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating conversation field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify conversation
    editor.ui.conversationEdit.set_combo_box_text("test_conversation")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.conversation) == "test_conversation"
    
    # Load back and verify
    editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
    assert editor.ui.conversationEdit.currentText() == "test_conversation"

# ============================================================================
# ADVANCED FIELDS MANIPULATIONS
# ============================================================================

def test_utd_editor_manipulate_min1_hp_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating min1 HP checkbox."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Toggle checkbox
    editor.ui.min1HpCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.min1_hp
    
    editor.ui.min1HpCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert not modified_utd.min1_hp

def test_utd_editor_manipulate_plot_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating plot checkbox."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Toggle checkbox
    editor.ui.plotCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.plot
    
    editor.ui.plotCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert not modified_utd.plot

def test_utd_editor_manipulate_static_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating static checkbox."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Toggle checkbox
    editor.ui.staticCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.static
    
    editor.ui.staticCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert not modified_utd.static

def test_utd_editor_manipulate_not_blastable_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating not blastable checkbox (TSL only)."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    if not installation.tsl:
        pytest.skip("Not blastable is TSL-only")
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Toggle checkbox
    editor.ui.notBlastableCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.not_blastable
    
    editor.ui.notBlastableCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert not modified_utd.not_blastable

def test_utd_editor_manipulate_faction(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating faction combo box."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test faction selection
    if editor.ui.factionSelect.count() > 0:
        for i in range(min(5, editor.ui.factionSelect.count())):
            editor.ui.factionSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utd = read_utd(data)
            assert modified_utd.faction_id == i

def test_utd_editor_manipulate_animation_state(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating animation state spin box."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test various animation state values
    test_values = [0, 1, 2, 5, 10]
    for val in test_values:
        editor.ui.animationState.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.animation_state == val
        
        # Load back and verify
        editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
        assert editor.ui.animationState.value() == val

def test_utd_editor_manipulate_hp_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating HP spin boxes."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test current HP
    test_current_hp = [1, 10, 50, 100, 500]
    for val in test_current_hp:
        editor.ui.currenHpSpin.setValue(val)
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.current_hp == val
    
    # Test maximum HP
    test_max_hp = [1, 10, 100, 500, 1000]
    for val in test_max_hp:
        editor.ui.maxHpSpin.setValue(val)
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.maximum_hp == val

def test_utd_editor_manipulate_save_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating save (hardness, fortitude, reflex, will) spin boxes."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test hardness
    test_values = [0, 5, 10, 20, 50]
    for val in test_values:
        editor.ui.hardnessSpin.setValue(val)
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.hardness == val
    
    # Test fortitude
    for val in test_values:
        editor.ui.fortitudeSpin.setValue(val)
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.fortitude == val
    
    # Test reflex
    for val in test_values:
        editor.ui.reflexSpin.setValue(val)
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.reflex == val
    
    # Test willpower
    for val in test_values:
        editor.ui.willSpin.setValue(val)
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.willpower == val

# ============================================================================
# LOCK FIELDS MANIPULATIONS
# ============================================================================

def test_utd_editor_manipulate_locked_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating locked checkbox."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Toggle checkbox
    editor.ui.lockedCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.locked
    
    editor.ui.lockedCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert not modified_utd.locked

def test_utd_editor_manipulate_need_key_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating need key checkbox."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Toggle checkbox
    editor.ui.needKeyCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.key_required
    
    editor.ui.needKeyCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert not modified_utd.key_required

def test_utd_editor_manipulate_remove_key_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating remove key checkbox."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Toggle checkbox
    editor.ui.removeKeyCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert modified_utd.auto_remove_key
    
    editor.ui.removeKeyCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert not modified_utd.auto_remove_key

def test_utd_editor_manipulate_key_edit(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating key name field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test various key names
    test_keys = ["", "test_key", "key_001", "special_key_123"]
    for key in test_keys:
        editor.ui.keyEdit.setText(key)
        
        # Save and verify
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.key_name == key
        
        # Load back and verify
        editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
        assert editor.ui.keyEdit.text() == key

def test_utd_editor_manipulate_unlock_dc_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating unlock DC spin boxes."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test unlock DC
    test_values = [0, 10, 20, 30, 40]
    for val in test_values:
        editor.ui.openLockSpin.setValue(val)
        data, _ = editor.build()
        modified_utd = read_utd(data)
        assert modified_utd.unlock_dc == val
    
    # Test difficulty (TSL only)
    if installation.tsl:
        for val in test_values:
            editor.ui.difficultySpin.setValue(val)
            data, _ = editor.build()
            modified_utd = read_utd(data)
            assert modified_utd.unlock_diff == val
    
    # Test difficulty mod (TSL only)
    if installation.tsl:
        for val in test_values:
            editor.ui.difficultyModSpin.setValue(val)
            data, _ = editor.build()
            modified_utd = read_utd(data)
            assert modified_utd.unlock_diff_mod == val

# ============================================================================
# SCRIPT FIELDS MANIPULATIONS
# ============================================================================

def test_utd_editor_manipulate_on_click_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on click script field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify script
    editor.ui.onClickEdit.set_combo_box_text("test_on_click")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.on_click) == "test_on_click"

def test_utd_editor_manipulate_on_closed_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on closed script field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify script
    editor.ui.onClosedEdit.set_combo_box_text("test_on_closed")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.on_closed) == "test_on_closed"

def test_utd_editor_manipulate_on_damaged_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on damaged script field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify script
    editor.ui.onDamagedEdit.set_combo_box_text("test_on_damaged")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.on_damaged) == "test_on_damaged"

def test_utd_editor_manipulate_on_death_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on death script field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify script
    editor.ui.onDeathEdit.set_combo_box_text("test_on_death")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.on_death) == "test_on_death"

def test_utd_editor_manipulate_on_open_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on open script field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify script
    editor.ui.onOpenEdit.set_combo_box_text("test_on_open")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.on_open) == "test_on_open"

def test_utd_editor_manipulate_on_open_failed_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on open failed script field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify script
    editor.ui.onOpenFailedEdit.set_combo_box_text("test_on_open_failed")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.on_open_failed) == "test_on_open_failed"

def test_utd_editor_manipulate_on_unlock_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on unlock script field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify script
    editor.ui.onUnlockEdit.set_combo_box_text("test_on_unlock")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    assert str(modified_utd.on_unlock) == "test_on_unlock"

def test_utd_editor_manipulate_all_scripts(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all script fields."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify all scripts
    editor.ui.onClickEdit.set_combo_box_text("s_onclick")
    editor.ui.onClosedEdit.set_combo_box_text("s_onclosed")
    editor.ui.onDamagedEdit.set_combo_box_text("s_ondamaged")
    editor.ui.onDeathEdit.set_combo_box_text("s_ondeath")
    editor.ui.onOpenFailedEdit.set_combo_box_text("s_onopenfailed")
    editor.ui.onHeartbeatSelect.set_combo_box_text("s_onheartbeat")
    editor.ui.onMeleeAttackEdit.set_combo_box_text("s_onmelee")
    editor.ui.onSpellEdit.set_combo_box_text("s_onspell")
    editor.ui.onOpenEdit.set_combo_box_text("s_onopen")
    editor.ui.onUnlockEdit.set_combo_box_text("s_onunlock")
    editor.ui.onUserDefinedSelect.set_combo_box_text("s_onuserdef")
    
    # Save and verify all
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert str(modified_utd.on_click) == "s_onclick"
    assert str(modified_utd.on_closed) == "s_onclosed"
    assert str(modified_utd.on_damaged) == "s_ondamaged"
    assert str(modified_utd.on_death) == "s_ondeath"
    assert str(modified_utd.on_open_failed) == "s_onopenfailed"
    assert str(modified_utd.on_heartbeat) == "s_onheartbeat"
    assert str(modified_utd.on_melee) == "s_onmelee"
    assert str(modified_utd.on_power) == "s_onspell"
    assert str(modified_utd.on_open) == "s_onopen"
    assert str(modified_utd.on_unlock) == "s_onunlock"
    assert str(modified_utd.on_user_defined) == "s_onuserdef"

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_utd_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
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
        modified_utd = read_utd(data)
        assert modified_utd.comment == comment
        
        # Load back and verify
        editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_utd_editor_manipulate_all_basic_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all basic fields simultaneously."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify ALL basic fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Door"))
    editor.ui.tagEdit.setText("combined_test")
    editor.ui.resrefEdit.setText("combined_resref")
    if editor.ui.appearanceSelect.count() > 0:
        editor.ui.appearanceSelect.setCurrentIndex(1)
    editor.ui.conversationEdit.set_combo_box_text("test_conv")
    
    # Save and verify all
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert modified_utd.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Door"
    assert modified_utd.tag == "combined_test"
    assert str(modified_utd.resref) == "combined_resref"
    assert str(modified_utd.conversation) == "test_conv"

def test_utd_editor_manipulate_all_advanced_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all advanced fields simultaneously."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify ALL advanced fields
    editor.ui.min1HpCheckbox.setChecked(True)
    editor.ui.plotCheckbox.setChecked(True)
    editor.ui.staticCheckbox.setChecked(True)
    if installation.tsl:
        editor.ui.notBlastableCheckbox.setChecked(True)
    if editor.ui.factionSelect.count() > 0:
        editor.ui.factionSelect.setCurrentIndex(1)
    editor.ui.animationState.setValue(5)
    editor.ui.currenHpSpin.setValue(50)
    editor.ui.maxHpSpin.setValue(100)
    editor.ui.hardnessSpin.setValue(10)
    editor.ui.fortitudeSpin.setValue(15)
    editor.ui.reflexSpin.setValue(20)
    editor.ui.willSpin.setValue(25)
    
    # Save and verify all
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert modified_utd.min1_hp
    assert modified_utd.plot
    assert modified_utd.static
    assert modified_utd.animation_state == 5
    assert modified_utd.current_hp == 50
    assert modified_utd.maximum_hp == 100
    assert modified_utd.hardness == 10
    assert modified_utd.fortitude == 15
    assert modified_utd.reflex == 20
    assert modified_utd.willpower == 25

def test_utd_editor_manipulate_all_lock_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all lock fields simultaneously."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Modify ALL lock fields
    editor.ui.lockedCheckbox.setChecked(True)
    editor.ui.needKeyCheckbox.setChecked(True)
    editor.ui.removeKeyCheckbox.setChecked(True)
    editor.ui.keyEdit.setText("test_key_item")
    editor.ui.openLockSpin.setValue(25)
    if installation.tsl:
        editor.ui.difficultySpin.setValue(15)
        editor.ui.difficultyModSpin.setValue(5)
    
    # Save and verify all
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert modified_utd.locked
    assert modified_utd.key_required
    assert modified_utd.auto_remove_key
    assert modified_utd.key_name == "test_key_item"
    assert modified_utd.unlock_dc == 25

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_utd_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    # Load original
    original_data = utd_file.read_bytes()
    original_utd = read_utd(original_data)
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_utd = read_utd(data)
    
    # Verify key fields match
    assert saved_utd.tag == original_utd.tag
    assert str(saved_utd.resref) == str(original_utd.resref)
    assert saved_utd.appearance_id == original_utd.appearance_id
    assert str(saved_utd.conversation) == str(original_utd.conversation)
    assert saved_utd.static == original_utd.static
    
    # Load saved data back
    editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_utd.tag
    assert editor.ui.resrefEdit.text() == str(original_utd.resref)

def test_utd_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    # Load original
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.currenHpSpin.setValue(75)
    editor.ui.maxHpSpin.setValue(150)
    editor.ui.lockedCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Save
    data1, _ = editor.build()
    saved_utd1 = read_utd(data1)
    
    # Load saved data
    editor.load(utd_file, "naldoor001", ResourceType.UTD, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.currenHpSpin.value() == 75
    assert editor.ui.maxHpSpin.value() == 150
    assert editor.ui.lockedCheckbox.isChecked()
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_utd2 = read_utd(data2)
    
    # Verify second save matches first
    assert saved_utd2.tag == saved_utd1.tag
    assert saved_utd2.current_hp == saved_utd1.current_hp
    assert saved_utd2.maximum_hp == saved_utd1.maximum_hp
    assert saved_utd2.locked == saved_utd1.locked
    assert saved_utd2.comment == saved_utd1.comment

def test_utd_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        editor.ui.currenHpSpin.setValue(10 + cycle * 10)
        
        # Save
        data, _ = editor.build()
        saved_utd = read_utd(data)
        
        # Verify
        assert saved_utd.tag == f"cycle_{cycle}"
        assert saved_utd.current_hp == 10 + cycle * 10
        
        # Load back
        editor.load(utd_file, "naldoor001", ResourceType.UTD, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"
        assert editor.ui.currenHpSpin.value() == 10 + cycle * 10

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_utd_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Set all to minimums
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.keyEdit.setText("")
    editor.ui.currenHpSpin.setValue(0)
    editor.ui.maxHpSpin.setValue(0)
    editor.ui.hardnessSpin.setValue(0)
    editor.ui.fortitudeSpin.setValue(0)
    editor.ui.reflexSpin.setValue(0)
    editor.ui.willSpin.setValue(0)
    editor.ui.animationState.setValue(0)
    editor.ui.openLockSpin.setValue(0)
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert modified_utd.tag == ""
    assert modified_utd.current_hp == 0
    assert modified_utd.maximum_hp == 0
    assert modified_utd.hardness == 0

def test_utd_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Set all to maximums
    editor.ui.tagEdit.setText("x" * 32)  # Max tag length
    editor.ui.currenHpSpin.setValue(editor.ui.currenHpSpin.maximum())
    editor.ui.maxHpSpin.setValue(editor.ui.maxHpSpin.maximum())
    editor.ui.hardnessSpin.setValue(editor.ui.hardnessSpin.maximum())
    editor.ui.fortitudeSpin.setValue(editor.ui.fortitudeSpin.maximum())
    editor.ui.reflexSpin.setValue(editor.ui.reflexSpin.maximum())
    editor.ui.willSpin.setValue(editor.ui.willSpin.maximum())
    editor.ui.openLockSpin.setValue(editor.ui.openLockSpin.maximum())
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert modified_utd.current_hp == editor.ui.currenHpSpin.maximum()
    assert modified_utd.maximum_hp == editor.ui.maxHpSpin.maximum()

def test_utd_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.keyEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    editor.ui.onClickEdit.set_combo_box_text("")
    editor.ui.onClosedEdit.set_combo_box_text("")
    editor.ui.onDamagedEdit.set_combo_box_text("")
    editor.ui.onDeathEdit.set_combo_box_text("")
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert modified_utd.tag == ""
    assert str(modified_utd.resref) == ""
    assert modified_utd.key_name == ""
    assert modified_utd.comment == ""
    assert str(modified_utd.on_click) == ""
    assert str(modified_utd.on_closed) == ""
    assert str(modified_utd.on_damaged) == ""
    assert str(modified_utd.on_death) == ""

def test_utd_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_utd = read_utd(data)
    
    assert modified_utd.tag == special_tag
    assert modified_utd.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_utd_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    # Load original
    original_data = utd_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_utd_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    original_data = utd_file.read_bytes()
    editor.load(utd_file, "naldoor001", ResourceType.UTD, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.currenHpSpin.setValue(50)
    editor.ui.lockedCheckbox.setChecked(True)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid UTD
    modified_utd = read_utd(data)
    assert modified_utd.tag == "modified_gff_test"
    assert modified_utd.current_hp == 50
    assert modified_utd.locked

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_utd_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new UTD file from scratch."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Door"))
    editor.ui.tagEdit.setText("new_door")
    editor.ui.resrefEdit.setText("new_door")
    if editor.ui.appearanceSelect.count() > 0:
        editor.ui.appearanceSelect.setCurrentIndex(0)
    editor.ui.currenHpSpin.setValue(100)
    editor.ui.maxHpSpin.setValue(100)
    editor.ui.lockedCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("New door comment")
    
    # Build and verify
    data, _ = editor.build()
    new_utd = read_utd(data)
    
    assert new_utd.name.get(Language.ENGLISH, Gender.MALE) == "New Door"
    assert new_utd.tag == "new_door"
    assert new_utd.current_hp == 100
    assert new_utd.locked
    assert new_utd.comment == "New door comment"

def test_utd_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_utd = read_utd(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_utd.tag, str)
    assert isinstance(new_utd.appearance_id, int)
    assert isinstance(new_utd.current_hp, int)
    assert isinstance(new_utd.maximum_hp, int)

# ============================================================================
# BUTTON FUNCTIONALITY TESTS
# ============================================================================

def test_utd_editor_generate_tag_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button functionality."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    editor.load(utd_file, "naldoor001", ResourceType.UTD, utd_file.read_bytes())
    
    # Clear tag
    editor.ui.tagEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated
    generated_tag = editor.ui.tagEdit.text()
    assert generated_tag

def test_utd_editor_generate_resref_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button functionality."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    editor.load(utd_file, "naldoor001", ResourceType.UTD, utd_file.read_bytes())
    
    # Clear resref
    editor.ui.resrefEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated
    generated_resref = editor.ui.resrefEdit.text()
    assert generated_resref

def test_utd_editor_conversation_modify_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test conversation modify button exists."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify button exists
    assert hasattr(editor.ui, 'conversationModifyButton')
    
    # Verify signal is connected
    assert editor.ui.conversationModifyButton.receivers(editor.ui.conversationModifyButton.clicked) > 0

# ============================================================================
# PREVIEW TESTS
# ============================================================================

def test_utd_editor_preview_toggle(qtbot, installation: HTInstallation):
    """Test 3D preview toggle functionality."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify preview toggle action exists
    assert hasattr(editor.ui, 'actionShowPreview')
    
    # Verify toggle method exists
    assert hasattr(editor, 'toggle_preview')
    assert callable(editor.toggle_preview)
    
    # Verify update method exists
    assert hasattr(editor, 'update3dPreview')
    assert callable(editor.update3dPreview)

def test_utd_editor_preview_updates_on_appearance_change(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test preview updates when appearance changes."""
    editor = UTDEditor(None, installation)
    qtbot.addWidget(editor)
    
    utd_file = test_files_dir / "naldoor001.utd"
    if not utd_file.exists():
        pytest.skip("naldoor001.utd not found")
    
    editor.load(utd_file, "naldoor001", ResourceType.UTD, utd_file.read_bytes())
    
    # Change appearance - should trigger preview update
    if editor.ui.appearanceSelect.count() > 1:
        editor.ui.appearanceSelect.setCurrentIndex(1)
        # Signal should be connected
        assert editor.ui.appearanceSelect.receivers(editor.ui.appearanceSelect.currentIndexChanged) > 0
