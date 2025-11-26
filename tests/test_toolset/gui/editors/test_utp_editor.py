"""
Comprehensive tests for UTP Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.utp import UTPEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.utp import UTP, read_utp  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_utp_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    # Load original
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    original_utp = read_utp(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Placeable Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.name.get(Language.ENGLISH, Gender.MALE) == "Modified Placeable Name"
    assert modified_utp.name.get(Language.ENGLISH, Gender.MALE) != original_utp.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Placeable Name"

def test_utp_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    original_utp = read_utp(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.tag == "modified_tag"
    assert modified_utp.tag != original_utp.tag
    
    # Load back and verify
    editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_utp_editor_manipulate_tag_generate_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    editor.load(utp_file, "ebcont001", ResourceType.UTP, utp_file.read_bytes())
    
    # Click generate button
    from qtpy.QtWidgets import QPushButton
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated from resname
    assert editor.ui.tagEdit.text() == "ebcont001"
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.tag == "ebcont001"

def test_utp_editor_manipulate_resref(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating resref field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify resref
    editor.ui.resrefEdit.setText("modified_resref")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.resref) == "modified_resref"
    
    # Load back and verify
    editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
    assert editor.ui.resrefEdit.text() == "modified_resref"

def test_utp_editor_manipulate_resref_generate_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    editor.load(utp_file, "ebcont001", ResourceType.UTP, utp_file.read_bytes())
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated from resname
    assert editor.ui.resrefEdit.text() == "ebcont001"
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.resref) == "ebcont001"

def test_utp_editor_manipulate_appearance(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating appearance combo box."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test appearance selection
    if editor.ui.appearanceSelect.count() > 0:
        for i in range(min(5, editor.ui.appearanceSelect.count())):
            editor.ui.appearanceSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utp = read_utp(data)
            assert modified_utp.appearance_id == i
            
            # Load back and verify
            editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
            assert editor.ui.appearanceSelect.currentIndex() == i

def test_utp_editor_manipulate_conversation(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating conversation field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify conversation
    editor.ui.conversationEdit.set_combo_box_text("test_conversation")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.conversation) == "test_conversation"
    
    # Load back and verify
    editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
    assert editor.ui.conversationEdit.currentText() == "test_conversation"

# ============================================================================
# ADVANCED FIELDS MANIPULATIONS
# ============================================================================

def test_utp_editor_manipulate_has_inventory_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating has inventory checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.hasInventoryCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.has_inventory
    
    editor.ui.hasInventoryCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.has_inventory

def test_utp_editor_manipulate_party_interact_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating party interact checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.partyInteractCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.party_interact
    
    editor.ui.partyInteractCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.party_interact

def test_utp_editor_manipulate_useable_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating useable checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.useableCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.useable
    
    editor.ui.useableCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.useable

def test_utp_editor_manipulate_min1_hp_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating min1 HP checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.min1HpCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.min1_hp
    
    editor.ui.min1HpCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.min1_hp

def test_utp_editor_manipulate_plot_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating plot checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.plotCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.plot
    
    editor.ui.plotCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.plot

def test_utp_editor_manipulate_static_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating static checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.staticCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.static
    
    editor.ui.staticCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.static

def test_utp_editor_manipulate_not_blastable_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating not blastable checkbox (TSL only)."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    if not installation.tsl:
        pytest.skip("Not blastable is TSL-only")
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.notBlastableCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.not_blastable
    
    editor.ui.notBlastableCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.not_blastable

def test_utp_editor_manipulate_faction(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating faction combo box."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test faction selection
    if editor.ui.factionSelect.count() > 0:
        for i in range(min(5, editor.ui.factionSelect.count())):
            editor.ui.factionSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utp = read_utp(data)
            assert modified_utp.faction_id == i

def test_utp_editor_manipulate_animation_state(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating animation state spin box."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test various animation state values
    test_values = [0, 1, 2, 5, 10]
    for val in test_values:
        editor.ui.animationState.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.animation_state == val
        
        # Load back and verify
        editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
        assert editor.ui.animationState.value() == val

def test_utp_editor_manipulate_hp_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating HP spin boxes."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test current HP
    test_current_hp = [1, 10, 50, 100, 500]
    for val in test_current_hp:
        editor.ui.currenHpSpin.setValue(val)
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.current_hp == val
    
    # Test maximum HP
    test_max_hp = [1, 10, 100, 500, 1000]
    for val in test_max_hp:
        editor.ui.maxHpSpin.setValue(val)
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.maximum_hp == val

def test_utp_editor_manipulate_save_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating save (hardness, fortitude, reflex, will) spin boxes."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test hardness
    test_values = [0, 5, 10, 20, 50]
    for val in test_values:
        editor.ui.hardnessSpin.setValue(val)
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.hardness == val
    
    # Test fortitude
    for val in test_values:
        editor.ui.fortitudeSpin.setValue(val)
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.fortitude == val
    
    # Test reflex
    for val in test_values:
        editor.ui.reflexSpin.setValue(val)
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.reflex == val
    
    # Test will
    for val in test_values:
        editor.ui.willSpin.setValue(val)
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.will == val

# ============================================================================
# LOCK FIELDS MANIPULATIONS
# ============================================================================

def test_utp_editor_manipulate_locked_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating locked checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.lockedCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.locked
    
    editor.ui.lockedCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.locked

def test_utp_editor_manipulate_need_key_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating need key checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.needKeyCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.key_required
    
    editor.ui.needKeyCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.key_required

def test_utp_editor_manipulate_remove_key_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating remove key checkbox."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Toggle checkbox
    editor.ui.removeKeyCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert modified_utp.auto_remove_key
    
    editor.ui.removeKeyCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert not modified_utp.auto_remove_key

def test_utp_editor_manipulate_key_edit(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating key name field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test various key names
    test_keys = ["", "test_key", "key_001", "special_key_123"]
    for key in test_keys:
        editor.ui.keyEdit.setText(key)
        
        # Save and verify
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.key_name == key
        
        # Load back and verify
        editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
        assert editor.ui.keyEdit.text() == key

def test_utp_editor_manipulate_unlock_dc_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating unlock DC spin boxes."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test unlock DC
    test_values = [0, 10, 20, 30, 40]
    for val in test_values:
        editor.ui.openLockSpin.setValue(val)
        data, _ = editor.build()
        modified_utp = read_utp(data)
        assert modified_utp.unlock_dc == val
    
    # Test difficulty (TSL only)
    if installation.tsl:
        for val in test_values:
            editor.ui.difficultySpin.setValue(val)
            data, _ = editor.build()
            modified_utp = read_utp(data)
            assert modified_utp.unlock_diff == val
    
    # Test difficulty mod (TSL only)
    if installation.tsl:
        for val in test_values:
            editor.ui.difficultyModSpin.setValue(val)
            data, _ = editor.build()
            modified_utp = read_utp(data)
            assert modified_utp.unlock_diff_mod == val

# ============================================================================
# SCRIPT FIELDS MANIPULATIONS
# ============================================================================

def test_utp_editor_manipulate_on_closed_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on closed script field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify script
    editor.ui.onClosedEdit.set_combo_box_text("test_on_closed")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.on_closed) == "test_on_closed"
    
    # Load back and verify
    editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
    assert editor.ui.onClosedEdit.currentText() == "test_on_closed"

def test_utp_editor_manipulate_on_damaged_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on damaged script field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify script
    editor.ui.onDamagedEdit.set_combo_box_text("test_on_damaged")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.on_damaged) == "test_on_damaged"

def test_utp_editor_manipulate_on_death_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on death script field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify script
    editor.ui.onDeathEdit.set_combo_box_text("test_on_death")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.on_death) == "test_on_death"

def test_utp_editor_manipulate_on_heartbeat_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on heartbeat script field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify script
    editor.ui.onHeartbeatSelect.set_combo_box_text("test_on_heartbeat")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.on_heartbeat) == "test_on_heartbeat"

def test_utp_editor_manipulate_on_open_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on open script field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify script
    editor.ui.onOpenEdit.set_combo_box_text("test_on_open")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.on_open) == "test_on_open"

def test_utp_editor_manipulate_on_used_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on used script field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify script
    editor.ui.onUsedEdit.set_combo_box_text("test_on_used")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    assert str(modified_utp.on_used) == "test_on_used"

def test_utp_editor_manipulate_all_scripts(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all script fields."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify all scripts
    editor.ui.onClosedEdit.set_combo_box_text("s_onclosed")
    editor.ui.onDamagedEdit.set_combo_box_text("s_ondamaged")
    editor.ui.onDeathEdit.set_combo_box_text("s_ondeath")
    editor.ui.onEndConversationEdit.set_combo_box_text("s_onendconv")
    editor.ui.onOpenFailedEdit.set_combo_box_text("s_onopenfailed")
    editor.ui.onHeartbeatSelect.set_combo_box_text("s_onheartbeat")
    editor.ui.onInventoryEdit.set_combo_box_text("s_oninventory")
    editor.ui.onMeleeAttackEdit.set_combo_box_text("s_onmelee")
    editor.ui.onSpellEdit.set_combo_box_text("s_onspell")
    editor.ui.onOpenEdit.set_combo_box_text("s_onopen")
    editor.ui.onLockEdit.set_combo_box_text("s_onlock")
    editor.ui.onUnlockEdit.set_combo_box_text("s_onunlock")
    editor.ui.onUsedEdit.set_combo_box_text("s_onused")
    editor.ui.onUserDefinedSelect.set_combo_box_text("s_onuserdef")
    
    # Save and verify all
    data, _ = editor.build()
    modified_utp = read_utp(data)
    
    assert str(modified_utp.on_closed) == "s_onclosed"
    assert str(modified_utp.on_damaged) == "s_ondamaged"
    assert str(modified_utp.on_death) == "s_ondeath"
    assert str(modified_utp.on_end_dialog) == "s_onendconv"
    assert str(modified_utp.on_open_failed) == "s_onopenfailed"
    assert str(modified_utp.on_heartbeat) == "s_onheartbeat"
    assert str(modified_utp.on_inventory) == "s_oninventory"
    assert str(modified_utp.on_melee_attack) == "s_onmelee"
    assert str(modified_utp.on_force_power) == "s_onspell"
    assert str(modified_utp.on_open) == "s_onopen"
    assert str(modified_utp.on_lock) == "s_onlock"
    assert str(modified_utp.on_unlock) == "s_onunlock"
    assert str(modified_utp.on_used) == "s_onused"
    assert str(modified_utp.on_user_defined) == "s_onuserdef"

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_utp_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
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
        modified_utp = read_utp(data)
        assert modified_utp.comment == comment
        
        # Load back and verify
        editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_utp_editor_manipulate_all_basic_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all basic fields simultaneously."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify ALL basic fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Placeable"))
    editor.ui.tagEdit.setText("combined_test")
    editor.ui.resrefEdit.setText("combined_resref")
    if editor.ui.appearanceSelect.count() > 0:
        editor.ui.appearanceSelect.setCurrentIndex(1)
    editor.ui.conversationEdit.set_combo_box_text("test_conv")
    
    # Save and verify all
    data, _ = editor.build()
    modified_utp = read_utp(data)
    
    assert modified_utp.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Placeable"
    assert modified_utp.tag == "combined_test"
    assert str(modified_utp.resref) == "combined_resref"
    assert str(modified_utp.conversation) == "test_conv"

def test_utp_editor_manipulate_all_advanced_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all advanced fields simultaneously."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Modify ALL advanced fields
    editor.ui.hasInventoryCheckbox.setChecked(True)
    editor.ui.partyInteractCheckbox.setChecked(True)
    editor.ui.useableCheckbox.setChecked(True)
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
    modified_utp = read_utp(data)
    
    assert modified_utp.has_inventory
    assert modified_utp.party_interact
    assert modified_utp.useable
    assert modified_utp.min1_hp
    assert modified_utp.plot
    assert modified_utp.static
    assert modified_utp.animation_state == 5
    assert modified_utp.current_hp == 50
    assert modified_utp.maximum_hp == 100
    assert modified_utp.hardness == 10
    assert modified_utp.fortitude == 15
    assert modified_utp.reflex == 20
    assert modified_utp.will == 25

def test_utp_editor_manipulate_all_lock_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all lock fields simultaneously."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
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
    modified_utp = read_utp(data)
    
    assert modified_utp.locked
    assert modified_utp.key_required
    assert modified_utp.auto_remove_key
    assert modified_utp.key_name == "test_key_item"
    assert modified_utp.unlock_dc == 25

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_utp_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    # Load original
    original_data = utp_file.read_bytes()
    original_utp = read_utp(original_data)
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_utp = read_utp(data)
    
    # Verify key fields match
    assert saved_utp.tag == original_utp.tag
    assert str(saved_utp.resref) == str(original_utp.resref)
    assert saved_utp.appearance_id == original_utp.appearance_id
    assert str(saved_utp.conversation) == str(original_utp.conversation)
    assert saved_utp.has_inventory == original_utp.has_inventory
    assert saved_utp.useable == original_utp.useable
    
    # Load saved data back
    editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_utp.tag
    assert editor.ui.resrefEdit.text() == str(original_utp.resref)

def test_utp_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    # Load original
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.currenHpSpin.setValue(75)
    editor.ui.maxHpSpin.setValue(150)
    editor.ui.hasInventoryCheckbox.setChecked(True)
    editor.ui.lockedCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Save
    data1, _ = editor.build()
    saved_utp1 = read_utp(data1)
    
    # Load saved data
    editor.load(utp_file, "ebcont001", ResourceType.UTP, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.currenHpSpin.value() == 75
    assert editor.ui.maxHpSpin.value() == 150
    assert editor.ui.hasInventoryCheckbox.isChecked()
    assert editor.ui.lockedCheckbox.isChecked()
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_utp2 = read_utp(data2)
    
    # Verify second save matches first
    assert saved_utp2.tag == saved_utp1.tag
    assert saved_utp2.current_hp == saved_utp1.current_hp
    assert saved_utp2.maximum_hp == saved_utp1.maximum_hp
    assert saved_utp2.has_inventory == saved_utp1.has_inventory
    assert saved_utp2.locked == saved_utp1.locked
    assert saved_utp2.comment == saved_utp1.comment

def test_utp_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        editor.ui.currenHpSpin.setValue(10 + cycle * 10)
        
        # Save
        data, _ = editor.build()
        saved_utp = read_utp(data)
        
        # Verify
        assert saved_utp.tag == f"cycle_{cycle}"
        assert saved_utp.current_hp == 10 + cycle * 10
        
        # Load back
        editor.load(utp_file, "ebcont001", ResourceType.UTP, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"
        assert editor.ui.currenHpSpin.value() == 10 + cycle * 10

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_utp_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
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
    modified_utp = read_utp(data)
    
    assert modified_utp.tag == ""
    assert modified_utp.current_hp == 0
    assert modified_utp.maximum_hp == 0
    assert modified_utp.hardness == 0

def test_utp_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
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
    modified_utp = read_utp(data)
    
    assert modified_utp.current_hp == editor.ui.currenHpSpin.maximum()
    assert modified_utp.maximum_hp == editor.ui.maxHpSpin.maximum()

def test_utp_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.keyEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    editor.ui.onClosedEdit.set_combo_box_text("")
    editor.ui.onDamagedEdit.set_combo_box_text("")
    editor.ui.onDeathEdit.set_combo_box_text("")
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    
    assert modified_utp.tag == ""
    assert str(modified_utp.resref) == ""
    assert modified_utp.key_name == ""
    assert modified_utp.comment == ""
    assert str(modified_utp.on_closed) == ""
    assert str(modified_utp.on_damaged) == ""
    assert str(modified_utp.on_death) == ""

def test_utp_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_utp = read_utp(data)
    
    assert modified_utp.tag == special_tag
    assert modified_utp.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_utp_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    # Load original
    original_data = utp_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_utp_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    original_data = utp_file.read_bytes()
    editor.load(utp_file, "ebcont001", ResourceType.UTP, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.currenHpSpin.setValue(50)
    editor.ui.hasInventoryCheckbox.setChecked(True)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid UTP
    modified_utp = read_utp(data)
    assert modified_utp.tag == "modified_gff_test"
    assert modified_utp.current_hp == 50
    assert modified_utp.has_inventory

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_utp_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new UTP file from scratch."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Placeable"))
    editor.ui.tagEdit.setText("new_placeable")
    editor.ui.resrefEdit.setText("new_placeable")
    if editor.ui.appearanceSelect.count() > 0:
        editor.ui.appearanceSelect.setCurrentIndex(0)
    editor.ui.currenHpSpin.setValue(100)
    editor.ui.maxHpSpin.setValue(100)
    editor.ui.hasInventoryCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("New placeable comment")
    
    # Build and verify
    data, _ = editor.build()
    new_utp = read_utp(data)
    
    assert new_utp.name.get(Language.ENGLISH, Gender.MALE) == "New Placeable"
    assert new_utp.tag == "new_placeable"
    assert new_utp.current_hp == 100
    assert new_utp.has_inventory
    assert new_utp.comment == "New placeable comment"

def test_utp_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_utp = read_utp(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_utp.tag, str)
    assert isinstance(new_utp.appearance_id, int)
    assert isinstance(new_utp.current_hp, int)
    assert isinstance(new_utp.maximum_hp, int)

# ============================================================================
# BUTTON FUNCTIONALITY TESTS
# ============================================================================

def test_utp_editor_generate_tag_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button functionality."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    editor.load(utp_file, "ebcont001", ResourceType.UTP, utp_file.read_bytes())
    
    # Clear tag
    editor.ui.tagEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated from resname
    assert editor.ui.tagEdit.text() == "ebcont001"

def test_utp_editor_generate_resref_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button functionality."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    editor.load(utp_file, "ebcont001", ResourceType.UTP, utp_file.read_bytes())
    
    # Clear resref
    editor.ui.resrefEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated from resname
    assert editor.ui.resrefEdit.text() == "ebcont001"

def test_utp_editor_conversation_modify_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test conversation modify button exists."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify button exists
    assert hasattr(editor.ui, 'conversationModifyButton')
    
    # Verify signal is connected
    assert editor.ui.conversationModifyButton.receivers(editor.ui.conversationModifyButton.clicked) > 0

def test_utp_editor_inventory_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test inventory button exists."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify button exists
    assert hasattr(editor.ui, 'inventoryButton')
    
    # Verify signal is connected
    assert editor.ui.inventoryButton.receivers(editor.ui.inventoryButton.clicked) > 0

# ============================================================================
# PREVIEW TESTS
# ============================================================================

def test_utp_editor_preview_toggle(qtbot, installation: HTInstallation):
    """Test 3D preview toggle functionality."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify preview toggle action exists
    assert hasattr(editor.ui, 'actionShowPreview')
    
    # Verify toggle method exists
    assert hasattr(editor, 'toggle_preview')
    assert callable(editor.toggle_preview)
    
    # Verify update method exists
    assert hasattr(editor, 'update3dPreview')
    assert callable(editor.update3dPreview)

def test_utp_editor_preview_updates_on_appearance_change(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test preview updates when appearance changes."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    editor.load(utp_file, "ebcont001", ResourceType.UTP, utp_file.read_bytes())
    
    # Change appearance - should trigger preview update
    if editor.ui.appearanceSelect.count() > 1:
        editor.ui.appearanceSelect.setCurrentIndex(1)
        # Signal should be connected
        assert editor.ui.appearanceSelect.receivers(editor.ui.appearanceSelect.currentIndexChanged) > 0

# ============================================================================
# INVENTORY TESTS
# ============================================================================

def test_utp_editor_inventory_functionality(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test inventory functionality."""
    editor = UTPEditor(None, installation)
    qtbot.addWidget(editor)
    
    utp_file = test_files_dir / "ebcont001.utp"
    if not utp_file.exists():
        pytest.skip("ebcont001.utp not found")
    
    editor.load(utp_file, "ebcont001", ResourceType.UTP, utp_file.read_bytes())
    
    # Enable inventory
    editor.ui.hasInventoryCheckbox.setChecked(True)
    
    # Verify inventory method exists
    assert hasattr(editor, 'open_inventory')
    assert callable(editor.open_inventory)
    
    # Verify item count method exists
    assert hasattr(editor, 'update_item_count')
    assert callable(editor.update_item_count)
