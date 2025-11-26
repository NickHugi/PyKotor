"""
Comprehensive tests for UTE Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.ute import UTEEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.ute import UTE, read_ute  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_ute_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    original_ute = read_ute(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Encounter Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert modified_ute.name.get(Language.ENGLISH, Gender.MALE) == "Modified Encounter Name"
    assert modified_ute.name.get(Language.ENGLISH, Gender.MALE) != original_ute.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(ute_file, "newtransition", ResourceType.UTE, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Encounter Name"

def test_ute_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    original_ute = read_ute(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert modified_ute.tag == "modified_tag"
    assert modified_ute.tag != original_ute.tag
    
    # Load back and verify
    editor.load(ute_file, "newtransition", ResourceType.UTE, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_ute_editor_manipulate_resref(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating resref field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify resref
    editor.ui.resrefEdit.setText("modified_resref")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert str(modified_ute.resref) == "modified_resref"
    
    # Load back and verify
    editor.load(ute_file, "newtransition", ResourceType.UTE, data)
    assert editor.ui.resrefEdit.text() == "modified_resref"

def test_ute_editor_manipulate_difficulty(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating difficulty combo box."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Test difficulty selection
    if editor.ui.difficultySelect.count() > 0:
        for i in range(min(5, editor.ui.difficultySelect.count())):
            editor.ui.difficultySelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_ute = read_ute(data)
            assert modified_ute.difficulty_id == i
            
            # Load back and verify
            editor.load(ute_file, "newtransition", ResourceType.UTE, data)
            assert editor.ui.difficultySelect.currentIndex() == i

def test_ute_editor_manipulate_spawn_select(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating spawn select (single shot/continuous)."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Test spawn select
    for i in range(editor.ui.spawnSelect.count()):
        editor.ui.spawnSelect.setCurrentIndex(i)
        
        # Save and verify
        data, _ = editor.build()
        modified_ute = read_ute(data)
        assert modified_ute.single_shot == bool(i)
        
        # Load back and verify
        editor.load(ute_file, "newtransition", ResourceType.UTE, data)
        assert editor.ui.spawnSelect.currentIndex() == i

def test_ute_editor_manipulate_creature_counts(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating min/max creature count spin boxes."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Test min creature count
    test_min_values = [1, 2, 3, 5, 10]
    for val in test_min_values:
        editor.ui.minCreatureSpin.setValue(val)
        data, _ = editor.build()
        modified_ute = read_ute(data)
        assert modified_ute.rec_creatures == val
    
    # Test max creature count
    test_max_values = [1, 3, 5, 10, 20]
    for val in test_max_values:
        editor.ui.maxCreatureSpin.setValue(val)
        data, _ = editor.build()
        modified_ute = read_ute(data)
        assert modified_ute.max_creatures == val

# ============================================================================
# ADVANCED FIELDS MANIPULATIONS
# ============================================================================

def test_ute_editor_manipulate_active_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating active checkbox."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Toggle checkbox
    editor.ui.activeCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert modified_ute.active
    
    editor.ui.activeCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert not modified_ute.active

def test_ute_editor_manipulate_player_only_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating player only checkbox."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Toggle checkbox
    editor.ui.playerOnlyCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert modified_ute.player_only
    
    editor.ui.playerOnlyCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert not modified_ute.player_only

def test_ute_editor_manipulate_faction(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating faction combo box."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Test faction selection
    if editor.ui.factionSelect.count() > 0:
        for i in range(min(5, editor.ui.factionSelect.count())):
            editor.ui.factionSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_ute = read_ute(data)
            assert modified_ute.faction_id == i

def test_ute_editor_manipulate_respawns_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating respawns checkbox."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Toggle checkbox
    editor.ui.respawnsCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert modified_ute.reset
    
    editor.ui.respawnsCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert not modified_ute.reset

def test_ute_editor_manipulate_infinite_respawn_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating infinite respawn checkbox."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Enable infinite respawn
    editor.ui.infiniteRespawnCheckbox.setChecked(True)
    qtbot.wait(10)
    
    # Verify respawn count spin is disabled and value is -1
    assert not editor.ui.respawnCountSpin.isEnabled()
    assert editor.ui.respawnCountSpin.value() == -1
    
    # Disable infinite respawn
    editor.ui.infiniteRespawnCheckbox.setChecked(False)
    qtbot.wait(10)
    
    # Verify respawn count spin is enabled
    assert editor.ui.respawnCountSpin.isEnabled()

def test_ute_editor_manipulate_respawn_counts(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating respawn count and time spin boxes."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Disable infinite respawn first
    editor.ui.infiniteRespawnCheckbox.setChecked(False)
    qtbot.wait(10)
    
    # Test respawn count
    test_values = [0, 1, 5, 10, 50]
    for val in test_values:
        editor.ui.respawnCountSpin.setValue(val)
        data, _ = editor.build()
        modified_ute = read_ute(data)
        assert modified_ute.respawns == val
    
    # Test respawn time
    test_time_values = [0.0, 1.0, 5.0, 10.0, 60.0]
    for val in test_time_values:
        editor.ui.respawnTimeSpin.setValue(val)
        data, _ = editor.build()
        modified_ute = read_ute(data)
        assert modified_ute.reset_time == val

# ============================================================================
# CREATURE TABLE MANIPULATIONS
# ============================================================================

def test_ute_editor_add_creature(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test adding creatures to the creature table."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Get initial row count
    initial_rows = editor.ui.creatureTable.rowCount()
    
    # Add a creature
    editor.add_creature(resname="test_creature", appearance_id=1, challenge=2.0, single=False)
    qtbot.wait(10)
    
    # Verify row was added
    assert editor.ui.creatureTable.rowCount() == initial_rows + 1
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert len(modified_ute.creatures) == initial_rows + 1
    assert str(modified_ute.creatures[-1].resref) == "test_creature"

def test_ute_editor_remove_creature(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test removing creatures from the creature table."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Add a creature first
    editor.add_creature(resname="test_creature_remove", appearance_id=1, challenge=2.0, single=False)
    qtbot.wait(10)
    
    initial_rows = editor.ui.creatureTable.rowCount()
    
    # Select last row
    editor.ui.creatureTable.selectRow(initial_rows - 1)
    qtbot.wait(10)
    
    # Remove selected creature
    editor.remove_selected_creature()
    qtbot.wait(10)
    
    # Verify row was removed
    assert editor.ui.creatureTable.rowCount() == initial_rows - 1

def test_ute_editor_modify_creature_properties(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test modifying creature properties in the table."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Add a creature
    editor.add_creature(resname="test_creature", appearance_id=1, challenge=2.0, single=False)
    qtbot.wait(10)
    
    # Modify creature properties via table widgets
    row = editor.ui.creatureTable.rowCount() - 1
    
    # Modify single checkbox
    from qtpy.QtWidgets import QCheckBox
    single_checkbox = editor.ui.creatureTable.cellWidget(row, 0)
    if isinstance(single_checkbox, QCheckBox):
        single_checkbox.setChecked(True)
        qtbot.wait(10)
    
    # Modify challenge rating
    from qtpy.QtWidgets import QDoubleSpinBox
    challenge_spin = editor.ui.creatureTable.cellWidget(row, 1)
    if isinstance(challenge_spin, QDoubleSpinBox):
        challenge_spin.setValue(5.0)
        qtbot.wait(10)
    
    # Modify appearance
    from qtpy.QtWidgets import QSpinBox
    appearance_spin = editor.ui.creatureTable.cellWidget(row, 2)
    if isinstance(appearance_spin, QSpinBox):
        appearance_spin.setValue(10)
        qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    if len(modified_ute.creatures) > 0:
        creature = modified_ute.creatures[-1]
        assert creature.challenge_rating == 5.0
        assert creature.appearance_id == 10

def test_ute_editor_multiple_creatures(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test adding multiple creatures."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Add multiple creatures
    for i in range(5):
        editor.add_creature(resname=f"creature_{i}", appearance_id=i, challenge=float(i), single=(i % 2 == 0))
        qtbot.wait(10)
    
    # Verify all were added
    assert editor.ui.creatureTable.rowCount() >= 5
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert len(modified_ute.creatures) >= 5

# ============================================================================
# SCRIPT FIELDS MANIPULATIONS
# ============================================================================

def test_ute_editor_manipulate_on_enter_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on enter script field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify script
    editor.ui.onEnterSelect.set_combo_box_text("test_on_enter")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert str(modified_ute.on_entered) == "test_on_enter"

def test_ute_editor_manipulate_on_exit_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on exit script field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify script
    editor.ui.onExitSelect.set_combo_box_text("test_on_exit")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert str(modified_ute.on_exit) == "test_on_exit"

def test_ute_editor_manipulate_on_exhausted_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on exhausted script field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify script
    editor.ui.onExhaustedEdit.set_combo_box_text("test_on_exhausted")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert str(modified_ute.on_exhausted) == "test_on_exhausted"

def test_ute_editor_manipulate_on_heartbeat_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on heartbeat script field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify script
    editor.ui.onHeartbeatSelect.set_combo_box_text("test_on_heartbeat")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert str(modified_ute.on_heartbeat) == "test_on_heartbeat"

def test_ute_editor_manipulate_on_user_defined_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on user defined script field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify script
    editor.ui.onUserDefinedSelect.set_combo_box_text("test_on_user_defined")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    assert str(modified_ute.on_user_defined) == "test_on_user_defined"

def test_ute_editor_manipulate_all_scripts(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all script fields."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify all scripts
    editor.ui.onEnterSelect.set_combo_box_text("s_onenter")
    editor.ui.onExitSelect.set_combo_box_text("s_onexit")
    editor.ui.onExhaustedEdit.set_combo_box_text("s_onexhausted")
    editor.ui.onHeartbeatSelect.set_combo_box_text("s_onheartbeat")
    editor.ui.onUserDefinedSelect.set_combo_box_text("s_onuserdef")
    
    # Save and verify all
    data, _ = editor.build()
    modified_ute = read_ute(data)
    
    assert str(modified_ute.on_entered) == "s_onenter"
    assert str(modified_ute.on_exit) == "s_onexit"
    assert str(modified_ute.on_exhausted) == "s_onexhausted"
    assert str(modified_ute.on_heartbeat) == "s_onheartbeat"
    assert str(modified_ute.on_user_defined) == "s_onuserdef"

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_ute_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
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
        modified_ute = read_ute(data)
        assert modified_ute.comment == comment
        
        # Load back and verify
        editor.load(ute_file, "newtransition", ResourceType.UTE, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_ute_editor_manipulate_all_basic_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all basic fields simultaneously."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify ALL basic fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Encounter"))
    editor.ui.tagEdit.setText("combined_test")
    editor.ui.resrefEdit.setText("combined_resref")
    if editor.ui.difficultySelect.count() > 0:
        editor.ui.difficultySelect.setCurrentIndex(1)
    editor.ui.spawnSelect.setCurrentIndex(1)
    editor.ui.minCreatureSpin.setValue(2)
    editor.ui.maxCreatureSpin.setValue(5)
    
    # Save and verify all
    data, _ = editor.build()
    modified_ute = read_ute(data)
    
    assert modified_ute.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Encounter"
    assert modified_ute.tag == "combined_test"
    assert str(modified_ute.resref) == "combined_resref"
    assert modified_ute.single_shot is True
    assert modified_ute.rec_creatures == 2
    assert modified_ute.max_creatures == 5

def test_ute_editor_manipulate_all_advanced_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all advanced fields simultaneously."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Modify ALL advanced fields
    editor.ui.activeCheckbox.setChecked(True)
    editor.ui.playerOnlyCheckbox.setChecked(True)
    if editor.ui.factionSelect.count() > 0:
        editor.ui.factionSelect.setCurrentIndex(1)
    editor.ui.respawnsCheckbox.setChecked(True)
    editor.ui.infiniteRespawnCheckbox.setChecked(False)
    editor.ui.respawnCountSpin.setValue(10)
    editor.ui.respawnTimeSpin.setValue(30.0)
    
    # Save and verify all
    data, _ = editor.build()
    modified_ute = read_ute(data)
    
    assert modified_ute.active
    assert modified_ute.player_only
    assert modified_ute.reset
    assert modified_ute.respawns == 10
    assert modified_ute.reset_time == 30.0

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_ute_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    # Load original
    original_data = ute_file.read_bytes()
    original_ute = read_ute(original_data)
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_ute = read_ute(data)
    
    # Verify key fields match
    assert saved_ute.tag == original_ute.tag
    assert str(saved_ute.resref) == str(original_ute.resref)
    assert saved_ute.difficulty_id == original_ute.difficulty_id
    assert saved_ute.active == original_ute.active
    
    # Load saved data back
    editor.load(ute_file, "newtransition", ResourceType.UTE, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_ute.tag
    assert editor.ui.resrefEdit.text() == str(original_ute.resref)

def test_ute_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    # Load original
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.minCreatureSpin.setValue(3)
    editor.ui.maxCreatureSpin.setValue(6)
    editor.ui.activeCheckbox.setChecked(True)
    editor.ui.respawnsCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Save
    data1, _ = editor.build()
    saved_ute1 = read_ute(data1)
    
    # Load saved data
    editor.load(ute_file, "newtransition", ResourceType.UTE, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.minCreatureSpin.value() == 3
    assert editor.ui.maxCreatureSpin.value() == 6
    assert editor.ui.activeCheckbox.isChecked()
    assert editor.ui.respawnsCheckbox.isChecked()
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_ute2 = read_ute(data2)
    
    # Verify second save matches first
    assert saved_ute2.tag == saved_ute1.tag
    assert saved_ute2.rec_creatures == saved_ute1.rec_creatures
    assert saved_ute2.max_creatures == saved_ute1.max_creatures
    assert saved_ute2.active == saved_ute1.active
    assert saved_ute2.reset == saved_ute1.reset
    assert saved_ute2.comment == saved_ute1.comment

def test_ute_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        editor.ui.minCreatureSpin.setValue(1 + cycle)
        
        # Save
        data, _ = editor.build()
        saved_ute = read_ute(data)
        
        # Verify
        assert saved_ute.tag == f"cycle_{cycle}"
        assert saved_ute.rec_creatures == 1 + cycle
        
        # Load back
        editor.load(ute_file, "newtransition", ResourceType.UTE, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"
        assert editor.ui.minCreatureSpin.value() == 1 + cycle

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_ute_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Set all to minimums
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.minCreatureSpin.setValue(0)
    editor.ui.maxCreatureSpin.setValue(0)
    editor.ui.respawnTimeSpin.setValue(0.0)
    
    # Disable infinite respawn to set count
    editor.ui.infiniteRespawnCheckbox.setChecked(False)
    qtbot.wait(10)
    editor.ui.respawnCountSpin.setValue(0)
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    
    assert modified_ute.tag == ""
    assert modified_ute.rec_creatures == 0
    assert modified_ute.max_creatures == 0
    assert modified_ute.reset_time == 0.0

def test_ute_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Set all to maximums
    editor.ui.tagEdit.setText("x" * 32)  # Max tag length
    editor.ui.minCreatureSpin.setValue(editor.ui.minCreatureSpin.maximum())
    editor.ui.maxCreatureSpin.setValue(editor.ui.maxCreatureSpin.maximum())
    editor.ui.respawnTimeSpin.setValue(editor.ui.respawnTimeSpin.maximum())
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    
    assert modified_ute.rec_creatures == editor.ui.minCreatureSpin.maximum()
    assert modified_ute.max_creatures == editor.ui.maxCreatureSpin.maximum()

def test_ute_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    editor.ui.onEnterSelect.set_combo_box_text("")
    editor.ui.onExitSelect.set_combo_box_text("")
    editor.ui.onExhaustedEdit.set_combo_box_text("")
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    
    assert modified_ute.tag == ""
    assert str(modified_ute.resref) == ""
    assert modified_ute.comment == ""
    assert str(modified_ute.on_entered) == ""
    assert str(modified_ute.on_exit) == ""
    assert str(modified_ute.on_exhausted) == ""

def test_ute_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_ute = read_ute(data)
    
    assert modified_ute.tag == special_tag
    assert modified_ute.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_ute_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    # Load original
    original_data = ute_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_ute_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    original_data = ute_file.read_bytes()
    editor.load(ute_file, "newtransition", ResourceType.UTE, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.minCreatureSpin.setValue(3)
    editor.ui.activeCheckbox.setChecked(True)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid UTE
    modified_ute = read_ute(data)
    assert modified_ute.tag == "modified_gff_test"
    assert modified_ute.rec_creatures == 3
    assert modified_ute.active

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_ute_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new UTE file from scratch."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Encounter"))
    editor.ui.tagEdit.setText("new_encounter")
    editor.ui.resrefEdit.setText("new_encounter")
    editor.ui.minCreatureSpin.setValue(2)
    editor.ui.maxCreatureSpin.setValue(4)
    editor.ui.activeCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("New encounter comment")
    
    # Add a creature
    editor.add_creature(resname="test_creature", appearance_id=1, challenge=2.0, single=False)
    qtbot.wait(10)
    
    # Build and verify
    data, _ = editor.build()
    new_ute = read_ute(data)
    
    assert new_ute.name.get(Language.ENGLISH, Gender.MALE) == "New Encounter"
    assert new_ute.tag == "new_encounter"
    assert new_ute.rec_creatures == 2
    assert new_ute.max_creatures == 4
    assert new_ute.active
    assert new_ute.comment == "New encounter comment"
    assert len(new_ute.creatures) >= 1

def test_ute_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_ute = read_ute(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_ute.tag, str)
    assert isinstance(new_ute.difficulty_id, int)
    assert isinstance(new_ute.rec_creatures, int)
    assert isinstance(new_ute.max_creatures, int)

# ============================================================================
# BUTTON FUNCTIONALITY TESTS
# ============================================================================

def test_ute_editor_generate_tag_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button functionality."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Clear tag
    editor.ui.tagEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated
    generated_tag = editor.ui.tagEdit.text()
    assert generated_tag

def test_ute_editor_generate_resref_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button functionality."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Clear resref
    editor.ui.resrefEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated
    generated_resref = editor.ui.resrefEdit.text()
    assert generated_resref

def test_ute_editor_add_creature_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test add creature button functionality."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Get initial row count
    initial_rows = editor.ui.creatureTable.rowCount()
    
    # Click add creature button
    qtbot.mouseClick(editor.ui.addCreatureButton, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    
    # Verify row was added
    assert editor.ui.creatureTable.rowCount() == initial_rows + 1

def test_ute_editor_remove_creature_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test remove creature button functionality."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Add a creature first
    editor.add_creature(resname="test_remove", appearance_id=1, challenge=2.0, single=False)
    qtbot.wait(10)
    
    initial_rows = editor.ui.creatureTable.rowCount()
    
    # Select last row
    editor.ui.creatureTable.selectRow(initial_rows - 1)
    qtbot.wait(10)
    
    # Click remove button
    qtbot.mouseClick(editor.ui.removeCreatureButton, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    
    # Verify row was removed
    assert editor.ui.creatureTable.rowCount() == initial_rows - 1

# ============================================================================
# CONTINUOUS SPAWN TESTS
# ============================================================================

def test_ute_editor_continuous_spawn_enables_respawn_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that continuous spawn enables respawn fields."""
    editor = UTEEditor(None, installation)
    qtbot.addWidget(editor)
    
    ute_file = test_files_dir / "newtransition.ute"
    if not ute_file.exists():
        pytest.skip("newtransition.ute not found")
    
    editor.load(ute_file, "newtransition", ResourceType.UTE, ute_file.read_bytes())
    
    # Set to continuous spawn
    editor.ui.spawnSelect.setCurrentIndex(1)  # Continuous
    qtbot.wait(10)
    
    # Verify respawn fields are enabled
    assert editor.ui.respawnsCheckbox.isEnabled()
    assert editor.ui.infiniteRespawnCheckbox.isEnabled()
    assert editor.ui.respawnCountSpin.isEnabled()
    assert editor.ui.respawnTimeSpin.isEnabled()
    
    # Set back to single shot
    editor.ui.spawnSelect.setCurrentIndex(0)  # Single shot
    qtbot.wait(10)
    
    # Verify respawn fields are disabled
    assert not editor.ui.respawnsCheckbox.isEnabled()
    assert not editor.ui.infiniteRespawnCheckbox.isEnabled()
    assert not editor.ui.respawnCountSpin.isEnabled()
    assert not editor.ui.respawnTimeSpin.isEnabled()
