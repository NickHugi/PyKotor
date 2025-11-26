"""
Comprehensive tests for UTT Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.utt import UTTEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.utt import UTT, read_utt  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_utt_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    original_utt = read_utt(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Trigger Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert modified_utt.name.get(Language.ENGLISH, Gender.MALE) == "Modified Trigger Name"
    assert modified_utt.name.get(Language.ENGLISH, Gender.MALE) != original_utt.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Trigger Name"

def test_utt_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    original_utt = read_utt(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert modified_utt.tag == "modified_tag"
    assert modified_utt.tag != original_utt.tag
    
    # Load back and verify
    editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_utt_editor_manipulate_resref(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating resref field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify resref
    editor.ui.resrefEdit.setText("modified_resref")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.resref) == "modified_resref"
    
    # Load back and verify
    editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
    assert editor.ui.resrefEdit.text() == "modified_resref"

def test_utt_editor_manipulate_cursor(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating cursor combo box."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test cursor selection
    if editor.ui.cursorSelect.count() > 0:
        for i in range(min(5, editor.ui.cursorSelect.count())):
            editor.ui.cursorSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utt = read_utt(data)
            assert modified_utt.cursor_id == i
            
            # Load back and verify
            editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
            assert editor.ui.cursorSelect.currentIndex() == i

def test_utt_editor_manipulate_type(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating type combo box."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test type selection
    if editor.ui.typeSelect.count() > 0:
        for i in range(min(5, editor.ui.typeSelect.count())):
            editor.ui.typeSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utt = read_utt(data)
            assert modified_utt.type_id == i
            
            # Load back and verify
            editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
            assert editor.ui.typeSelect.currentIndex() == i

# ============================================================================
# ADVANCED FIELDS MANIPULATIONS
# ============================================================================

def test_utt_editor_manipulate_auto_remove_key_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating auto remove key checkbox."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Toggle checkbox
    editor.ui.autoRemoveKeyCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert modified_utt.auto_remove_key
    
    editor.ui.autoRemoveKeyCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert not modified_utt.auto_remove_key

def test_utt_editor_manipulate_key_edit(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating key name field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test various key names
    test_keys = ["", "test_key", "key_001", "special_key_123"]
    for key in test_keys:
        editor.ui.keyEdit.setText(key)
        
        # Save and verify
        data, _ = editor.build()
        modified_utt = read_utt(data)
        assert modified_utt.key_name == key
        
        # Load back and verify
        editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
        assert editor.ui.keyEdit.text() == key

def test_utt_editor_manipulate_faction(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating faction combo box."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test faction selection
    if editor.ui.factionSelect.count() > 0:
        for i in range(min(5, editor.ui.factionSelect.count())):
            editor.ui.factionSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utt = read_utt(data)
            assert modified_utt.faction_id == i

def test_utt_editor_manipulate_highlight_height(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating highlight height spin box."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test various highlight height values
    test_values = [0.0, 1.0, 5.0, 10.0, 50.0]
    for val in test_values:
        editor.ui.highlightHeightSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_utt = read_utt(data)
        assert modified_utt.highlight_height == val
        
        # Load back and verify
        editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
        assert editor.ui.highlightHeightSpin.value() == val

# ============================================================================
# TRAP FIELDS MANIPULATIONS
# ============================================================================

def test_utt_editor_manipulate_is_trap_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating is trap checkbox."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Toggle checkbox
    editor.ui.isTrapCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert modified_utt.is_trap
    
    editor.ui.isTrapCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert not modified_utt.is_trap

def test_utt_editor_manipulate_activate_once_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating activate once checkbox."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Toggle checkbox
    editor.ui.activateOnceCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert modified_utt.trap_once
    
    editor.ui.activateOnceCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert not modified_utt.trap_once

def test_utt_editor_manipulate_detectable_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating detectable checkbox."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Toggle checkbox
    editor.ui.detectableCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert modified_utt.trap_detectable
    
    editor.ui.detectableCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert not modified_utt.trap_detectable

def test_utt_editor_manipulate_detect_dc_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating detect DC spin box."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test various detect DC values
    test_values = [0, 10, 20, 30, 40]
    for val in test_values:
        editor.ui.detectDcSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_utt = read_utt(data)
        assert modified_utt.trap_detect_dc == val
        
        # Load back and verify
        editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
        assert editor.ui.detectDcSpin.value() == val

def test_utt_editor_manipulate_disarmable_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating disarmable checkbox."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Toggle checkbox
    editor.ui.disarmableCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert modified_utt.trap_disarmable
    
    editor.ui.disarmableCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert not modified_utt.trap_disarmable

def test_utt_editor_manipulate_disarm_dc_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating disarm DC spin box."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test various disarm DC values
    test_values = [0, 10, 20, 30, 40]
    for val in test_values:
        editor.ui.disarmDcSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_utt = read_utt(data)
        assert modified_utt.trap_disarm_dc == val
        
        # Load back and verify
        editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
        assert editor.ui.disarmDcSpin.value() == val

def test_utt_editor_manipulate_trap_type(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating trap type combo box."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test trap type selection
    if editor.ui.trapSelect.count() > 0:
        for i in range(min(5, editor.ui.trapSelect.count())):
            editor.ui.trapSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_utt = read_utt(data)
            assert modified_utt.trap_type == i
            
            # Load back and verify
            editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
            assert editor.ui.trapSelect.currentIndex() == i

# ============================================================================
# SCRIPT FIELDS MANIPULATIONS
# ============================================================================

def test_utt_editor_manipulate_on_click_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on click script field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify script
    editor.ui.onClickEdit.set_combo_box_text("test_on_click")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.on_click) == "test_on_click"

def test_utt_editor_manipulate_on_disarm_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on disarm script field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify script
    editor.ui.onDisarmEdit.set_combo_box_text("test_on_disarm")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.on_disarm) == "test_on_disarm"

def test_utt_editor_manipulate_on_enter_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on enter script field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify script
    editor.ui.onEnterSelect.set_combo_box_text("test_on_enter")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.on_enter) == "test_on_enter"

def test_utt_editor_manipulate_on_exit_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on exit script field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify script
    editor.ui.onExitSelect.set_combo_box_text("test_on_exit")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.on_exit) == "test_on_exit"

def test_utt_editor_manipulate_on_heartbeat_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on heartbeat script field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify script
    editor.ui.onHeartbeatSelect.set_combo_box_text("test_on_heartbeat")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.on_heartbeat) == "test_on_heartbeat"

def test_utt_editor_manipulate_on_trap_triggered_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on trap triggered script field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify script
    editor.ui.onTrapTriggeredEdit.set_combo_box_text("test_on_trap_triggered")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.on_trap_triggered) == "test_on_trap_triggered"

def test_utt_editor_manipulate_on_user_defined_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on user defined script field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify script
    editor.ui.onUserDefinedSelect.set_combo_box_text("test_on_user_defined")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    assert str(modified_utt.on_user_defined) == "test_on_user_defined"

def test_utt_editor_manipulate_all_scripts(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all script fields."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify all scripts
    editor.ui.onClickEdit.set_combo_box_text("s_onclick")
    editor.ui.onDisarmEdit.set_combo_box_text("s_ondisarm")
    editor.ui.onEnterSelect.set_combo_box_text("s_onenter")
    editor.ui.onExitSelect.set_combo_box_text("s_onexit")
    editor.ui.onHeartbeatSelect.set_combo_box_text("s_onheartbeat")
    editor.ui.onTrapTriggeredEdit.set_combo_box_text("s_ontrap")
    editor.ui.onUserDefinedSelect.set_combo_box_text("s_onuserdef")
    
    # Save and verify all
    data, _ = editor.build()
    modified_utt = read_utt(data)
    
    assert str(modified_utt.on_click) == "s_onclick"
    assert str(modified_utt.on_disarm) == "s_ondisarm"
    assert str(modified_utt.on_enter) == "s_onenter"
    assert str(modified_utt.on_exit) == "s_onexit"
    assert str(modified_utt.on_heartbeat) == "s_onheartbeat"
    assert str(modified_utt.on_trap_triggered) == "s_ontrap"
    assert str(modified_utt.on_user_defined) == "s_onuserdef"

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_utt_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
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
        modified_utt = read_utt(data)
        assert modified_utt.comment == comment
        
        # Load back and verify
        editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_utt_editor_manipulate_all_basic_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all basic fields simultaneously."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify ALL basic fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Trigger"))
    editor.ui.tagEdit.setText("combined_test")
    editor.ui.resrefEdit.setText("combined_resref")
    if editor.ui.cursorSelect.count() > 0:
        editor.ui.cursorSelect.setCurrentIndex(1)
    if editor.ui.typeSelect.count() > 0:
        editor.ui.typeSelect.setCurrentIndex(1)
    
    # Save and verify all
    data, _ = editor.build()
    modified_utt = read_utt(data)
    
    assert modified_utt.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Trigger"
    assert modified_utt.tag == "combined_test"
    assert str(modified_utt.resref) == "combined_resref"

def test_utt_editor_manipulate_all_trap_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all trap fields simultaneously."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Modify ALL trap fields
    editor.ui.isTrapCheckbox.setChecked(True)
    editor.ui.activateOnceCheckbox.setChecked(True)
    editor.ui.detectableCheckbox.setChecked(True)
    editor.ui.detectDcSpin.setValue(25)
    editor.ui.disarmableCheckbox.setChecked(True)
    editor.ui.disarmDcSpin.setValue(30)
    if editor.ui.trapSelect.count() > 0:
        editor.ui.trapSelect.setCurrentIndex(1)
    
    # Save and verify all
    data, _ = editor.build()
    modified_utt = read_utt(data)
    
    assert modified_utt.is_trap
    assert modified_utt.trap_once
    assert modified_utt.trap_detectable
    assert modified_utt.trap_detect_dc == 25
    assert modified_utt.trap_disarmable
    assert modified_utt.trap_disarm_dc == 30

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_utt_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    # Load original
    original_data = utt_file.read_bytes()
    original_utt = read_utt(original_data)
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_utt = read_utt(data)
    
    # Verify key fields match
    assert saved_utt.tag == original_utt.tag
    assert str(saved_utt.resref) == str(original_utt.resref)
    assert saved_utt.cursor_id == original_utt.cursor_id
    assert saved_utt.type_id == original_utt.type_id
    
    # Load saved data back
    editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_utt.tag
    assert editor.ui.resrefEdit.text() == str(original_utt.resref)

def test_utt_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    # Load original
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.highlightHeightSpin.setValue(5.0)
    editor.ui.isTrapCheckbox.setChecked(True)
    editor.ui.detectDcSpin.setValue(20)
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Save
    data1, _ = editor.build()
    saved_utt1 = read_utt(data1)
    
    # Load saved data
    editor.load(utt_file, "newtransition9", ResourceType.UTT, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.highlightHeightSpin.value() == 5.0
    assert editor.ui.isTrapCheckbox.isChecked()
    assert editor.ui.detectDcSpin.value() == 20
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_utt2 = read_utt(data2)
    
    # Verify second save matches first
    assert saved_utt2.tag == saved_utt1.tag
    assert saved_utt2.highlight_height == saved_utt1.highlight_height
    assert saved_utt2.is_trap == saved_utt1.is_trap
    assert saved_utt2.trap_detect_dc == saved_utt1.trap_detect_dc
    assert saved_utt2.comment == saved_utt1.comment

def test_utt_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        editor.ui.highlightHeightSpin.setValue(1.0 + cycle)
        
        # Save
        data, _ = editor.build()
        saved_utt = read_utt(data)
        
        # Verify
        assert saved_utt.tag == f"cycle_{cycle}"
        assert saved_utt.highlight_height == 1.0 + cycle
        
        # Load back
        editor.load(utt_file, "newtransition9", ResourceType.UTT, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"
        assert editor.ui.highlightHeightSpin.value() == 1.0 + cycle

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_utt_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Set all to minimums
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.keyEdit.setText("")
    editor.ui.highlightHeightSpin.setValue(0.0)
    editor.ui.detectDcSpin.setValue(0)
    editor.ui.disarmDcSpin.setValue(0)
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    
    assert modified_utt.tag == ""
    assert modified_utt.highlight_height == 0.0
    assert modified_utt.trap_detect_dc == 0
    assert modified_utt.trap_disarm_dc == 0

def test_utt_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Set all to maximums
    editor.ui.tagEdit.setText("x" * 32)  # Max tag length
    editor.ui.highlightHeightSpin.setValue(editor.ui.highlightHeightSpin.maximum())
    editor.ui.detectDcSpin.setValue(editor.ui.detectDcSpin.maximum())
    editor.ui.disarmDcSpin.setValue(editor.ui.disarmDcSpin.maximum())
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    
    assert modified_utt.highlight_height == editor.ui.highlightHeightSpin.maximum()
    assert modified_utt.trap_detect_dc == editor.ui.detectDcSpin.maximum()
    assert modified_utt.trap_disarm_dc == editor.ui.disarmDcSpin.maximum()

def test_utt_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.keyEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    editor.ui.onClickEdit.set_combo_box_text("")
    editor.ui.onDisarmEdit.set_combo_box_text("")
    editor.ui.onEnterSelect.set_combo_box_text("")
    editor.ui.onExitSelect.set_combo_box_text("")
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    
    assert modified_utt.tag == ""
    assert str(modified_utt.resref) == ""
    assert modified_utt.key_name == ""
    assert modified_utt.comment == ""
    assert str(modified_utt.on_click) == ""
    assert str(modified_utt.on_disarm) == ""
    assert str(modified_utt.on_enter) == ""
    assert str(modified_utt.on_exit) == ""

def test_utt_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_utt = read_utt(data)
    
    assert modified_utt.tag == special_tag
    assert modified_utt.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_utt_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    # Load original
    original_data = utt_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_utt_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    original_data = utt_file.read_bytes()
    editor.load(utt_file, "newtransition9", ResourceType.UTT, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.highlightHeightSpin.setValue(5.0)
    editor.ui.isTrapCheckbox.setChecked(True)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid UTT
    modified_utt = read_utt(data)
    assert modified_utt.tag == "modified_gff_test"
    assert modified_utt.highlight_height == 5.0
    assert modified_utt.is_trap

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_utt_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new UTT file from scratch."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Trigger"))
    editor.ui.tagEdit.setText("new_trigger")
    editor.ui.resrefEdit.setText("new_trigger")
    editor.ui.highlightHeightSpin.setValue(2.0)
    editor.ui.isTrapCheckbox.setChecked(True)
    editor.ui.detectDcSpin.setValue(15)
    editor.ui.commentsEdit.setPlainText("New trigger comment")
    
    # Build and verify
    data, _ = editor.build()
    new_utt = read_utt(data)
    
    assert new_utt.name.get(Language.ENGLISH, Gender.MALE) == "New Trigger"
    assert new_utt.tag == "new_trigger"
    assert new_utt.highlight_height == 2.0
    assert new_utt.is_trap
    assert new_utt.trap_detect_dc == 15
    assert new_utt.comment == "New trigger comment"

def test_utt_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_utt = read_utt(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_utt.tag, str)
    assert isinstance(new_utt.cursor_id, int)
    assert isinstance(new_utt.type_id, int)
    assert isinstance(new_utt.highlight_height, float)

# ============================================================================
# BUTTON FUNCTIONALITY TESTS
# ============================================================================

def test_utt_editor_generate_tag_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button functionality."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    editor.load(utt_file, "newtransition9", ResourceType.UTT, utt_file.read_bytes())
    
    # Clear tag
    editor.ui.tagEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated
    generated_tag = editor.ui.tagEdit.text()
    assert generated_tag

def test_utt_editor_generate_resref_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button functionality."""
    editor = UTTEditor(None, installation)
    qtbot.addWidget(editor)
    
    utt_file = test_files_dir / "newtransition9.utt"
    if not utt_file.exists():
        pytest.skip("newtransition9.utt not found")
    
    editor.load(utt_file, "newtransition9", ResourceType.UTT, utt_file.read_bytes())
    
    # Clear resref
    editor.ui.resrefEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated
    generated_resref = editor.ui.resrefEdit.text()
    assert generated_resref
