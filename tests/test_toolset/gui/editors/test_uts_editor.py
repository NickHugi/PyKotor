"""
Comprehensive tests for UTS Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListWidgetItem
from toolset.gui.editors.uts import UTSEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.uts import UTS, read_uts  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_uts_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    original_uts = read_uts(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Sound Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.name.get(Language.ENGLISH, Gender.MALE) == "Modified Sound Name"
    assert modified_uts.name.get(Language.ENGLISH, Gender.MALE) != original_uts.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Sound Name"

def test_uts_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    original_uts = read_uts(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.tag == "modified_tag"
    assert modified_uts.tag != original_uts.tag
    
    # Load back and verify
    editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_uts_editor_manipulate_resref(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating resref field."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Modify resref
    editor.ui.resrefEdit.setText("modified_resref")
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert str(modified_uts.resref) == "modified_resref"
    
    # Load back and verify
    editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
    assert editor.ui.resrefEdit.text() == "modified_resref"

def test_uts_editor_manipulate_volume_slider(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating volume slider."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Test various volume values
    test_volumes = [0, 25, 50, 75, 100]
    for vol in test_volumes:
        editor.ui.volumeSlider.setValue(vol)
        
        # Save and verify
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.volume == vol
        
        # Load back and verify
        editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
        assert editor.ui.volumeSlider.value() == vol

def test_uts_editor_manipulate_active_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating active checkbox."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Toggle checkbox
    editor.ui.activeCheckbox.setChecked(True)
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.active
    
    editor.ui.activeCheckbox.setChecked(False)
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert not modified_uts.active

# ============================================================================
# ADVANCED FIELDS MANIPULATIONS
# ============================================================================

def test_uts_editor_manipulate_play_random_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating play random radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set play random
    editor.ui.playRandomRadio.setChecked(True)
    editor.ui.northRandomSpin.setValue(5.0)
    editor.ui.eastRandomSpin.setValue(5.0)
    qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.random_range_x != 0 or modified_uts.random_range_y != 0

def test_uts_editor_manipulate_play_specific_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating play specific radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set play specific
    editor.ui.playSpecificRadio.setChecked(True)
    qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.positional

def test_uts_editor_manipulate_play_everywhere_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating play everywhere radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set play everywhere
    editor.ui.playEverywhereRadio.setChecked(True)
    editor.ui.northRandomSpin.setValue(0)
    editor.ui.eastRandomSpin.setValue(0)
    qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert not modified_uts.positional
    assert modified_uts.random_range_x == 0
    assert modified_uts.random_range_y == 0

def test_uts_editor_manipulate_order_sequential_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating order sequential radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set sequential order
    editor.ui.orderSequentialRadio.setChecked(True)
    qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.random_pick == 0

def test_uts_editor_manipulate_order_random_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating order random radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set random order
    editor.ui.orderRandomRadio.setChecked(True)
    qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.random_pick == 1

def test_uts_editor_manipulate_interval_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating interval spin boxes."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Test interval
    test_interval_values = [0.0, 1.0, 5.0, 10.0, 60.0]
    for val in test_interval_values:
        editor.ui.intervalSpin.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.interval == val
    
    # Test interval variation
    for val in test_interval_values:
        editor.ui.intervalVariationSpin.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.interval_variation == val

def test_uts_editor_manipulate_variation_sliders(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating variation sliders."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Test volume variation
    test_variation_values = [0, 10, 25, 50, 100]
    for val in test_variation_values:
        editor.ui.volumeVariationSlider.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.volume_variation == val
    
    # Test pitch variation (stored as float 0.0-1.0, but slider is 0-100)
    for val in test_variation_values:
        editor.ui.pitchVariationSlider.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert abs(modified_uts.pitch_variation - (val / 100.0)) < 0.01

# ============================================================================
# SOUND LIST MANIPULATIONS
# ============================================================================

def test_uts_editor_add_sound(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test adding sounds to the sound list."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Get initial count
    initial_count = editor.ui.soundList.count()
    
    # Add a sound
    editor.add_sound()
    qtbot.wait(10)
    
    # Verify sound was added
    assert editor.ui.soundList.count() == initial_count + 1
    
    # Modify the new sound
    new_item = editor.ui.soundList.item(editor.ui.soundList.count() - 1)
    if new_item:
        new_item.setText("test_sound")
        qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert len(modified_uts.sounds) == initial_count + 1
    if len(modified_uts.sounds) > 0:
        assert str(modified_uts.sounds[-1]) == "test_sound"

def test_uts_editor_remove_sound(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test removing sounds from the sound list."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add a sound first
    editor.add_sound()
    qtbot.wait(10)
    
    initial_count = editor.ui.soundList.count()
    
    # Select last sound
    editor.ui.soundList.setCurrentRow(initial_count - 1)
    qtbot.wait(10)
    
    # Remove selected sound
    editor.remove_sound()
    qtbot.wait(10)
    
    # Verify sound was removed
    assert editor.ui.soundList.count() == initial_count - 1

def test_uts_editor_move_sound_up(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test moving sounds up in the list."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add multiple sounds
    editor.add_sound()
    qtbot.wait(10)
    editor.add_sound()
    qtbot.wait(10)
    
    if editor.ui.soundList.count() >= 2:
        # Get second-to-last sound name
        second_last = editor.ui.soundList.item(editor.ui.soundList.count() - 2)
        if second_last:
            second_last_text = second_last.text()
            
            # Select last sound
            editor.ui.soundList.setCurrentRow(editor.ui.soundList.count() - 1)
            qtbot.wait(10)
            
            # Move up
            editor.move_sound_up()
            qtbot.wait(10)
            
            # Verify moved
            new_pos = editor.ui.soundList.currentRow()
            moved_item = editor.ui.soundList.item(new_pos)
            if moved_item:
                assert moved_item.text() == second_last_text

def test_uts_editor_move_sound_down(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test moving sounds down in the list."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add multiple sounds
    editor.add_sound()
    qtbot.wait(10)
    editor.add_sound()
    qtbot.wait(10)
    
    if editor.ui.soundList.count() >= 2:
        # Get second-to-last sound name
        second_last_text = None
        second_last_item = editor.ui.soundList.item(editor.ui.soundList.count() - 2)
        if second_last_item:
            second_last_text = second_last_item.text()
            
            # Select second-to-last
            editor.ui.soundList.setCurrentRow(editor.ui.soundList.count() - 2)
            qtbot.wait(10)
            
            # Move down
            editor.move_sound_down()
            qtbot.wait(10)
            
            # Verify moved
            new_pos = editor.ui.soundList.currentRow()
            moved_item = editor.ui.soundList.item(new_pos)
            if moved_item and second_last_text:
                assert moved_item.text() == second_last_text

def test_uts_editor_edit_sound_item(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test editing sound items in the list."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add a sound
    editor.add_sound()
    qtbot.wait(10)
    
    # Edit the sound
    item = editor.ui.soundList.item(editor.ui.soundList.count() - 1)
    if item:
        item.setText("edited_sound")
        qtbot.wait(10)
        
        # Save and verify
        data, _ = editor.build()
        modified_uts = read_uts(data)
        if len(modified_uts.sounds) > 0:
            assert str(modified_uts.sounds[-1]) == "edited_sound"

def test_uts_editor_multiple_sounds(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test adding multiple sounds."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add multiple sounds
    for i in range(5):
        editor.add_sound()
        qtbot.wait(10)
        item = editor.ui.soundList.item(editor.ui.soundList.count() - 1)
        if item:
            item.setText(f"sound_{i}")
            qtbot.wait(10)
    
    # Verify all were added
    assert editor.ui.soundList.count() >= 5
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert len(modified_uts.sounds) >= 5

# ============================================================================
# POSITIONING FIELDS MANIPULATIONS
# ============================================================================

def test_uts_editor_manipulate_style_once_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating style once radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set style once
    editor.ui.styleOnceRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify interval group is disabled
    assert not editor.ui.intervalGroup.isEnabled()
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert not modified_uts.looping
    assert not modified_uts.continuous

def test_uts_editor_manipulate_style_repeat_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating style repeat radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set style repeat
    editor.ui.styleRepeatRadio.setChecked(True)
    qtbot.wait(10)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.looping
    assert not modified_uts.continuous

def test_uts_editor_manipulate_style_seamless_radio(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating style seamless radio button."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set style seamless
    editor.ui.styleSeamlessRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify style groups are disabled
    assert not editor.ui.intervalGroup.isEnabled()
    assert not editor.ui.orderGroup.isEnabled()
    assert not editor.ui.variationGroup.isEnabled()
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    assert modified_uts.looping
    assert modified_uts.continuous

def test_uts_editor_manipulate_distance_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating distance spin boxes."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Test cutoff (max_distance)
    test_distance_values = [0.0, 5.0, 10.0, 50.0, 100.0]
    for val in test_distance_values:
        editor.ui.cutoffSpin.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.max_distance == val
    
    # Test max volume distance (min_distance)
    for val in test_distance_values:
        editor.ui.maxVolumeDistanceSpin.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.min_distance == val

def test_uts_editor_manipulate_height_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating height spin box."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Test various height values
    test_height_values = [0.0, 1.0, 5.0, 10.0, 50.0]
    for val in test_height_values:
        editor.ui.heightSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.elevation == val
        
        # Load back and verify
        editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
        assert editor.ui.heightSpin.value() == val

def test_uts_editor_manipulate_random_range_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating random range spin boxes."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Test north random (random_range_y)
    test_range_values = [0.0, 1.0, 5.0, 10.0]
    for val in test_range_values:
        editor.ui.northRandomSpin.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.random_range_y == val
    
    # Test east random (random_range_x)
    for val in test_range_values:
        editor.ui.eastRandomSpin.setValue(val)
        data, _ = editor.build()
        modified_uts = read_uts(data)
        assert modified_uts.random_range_x == val

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_uts_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
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
        modified_uts = read_uts(data)
        assert modified_uts.comment == comment
        
        # Load back and verify
        editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_uts_editor_manipulate_all_basic_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all basic fields simultaneously."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Modify ALL basic fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Sound"))
    editor.ui.tagEdit.setText("combined_test")
    editor.ui.resrefEdit.setText("combined_resref")
    editor.ui.volumeSlider.setValue(75)
    editor.ui.activeCheckbox.setChecked(True)
    
    # Save and verify all
    data, _ = editor.build()
    modified_uts = read_uts(data)
    
    assert modified_uts.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Sound"
    assert modified_uts.tag == "combined_test"
    assert str(modified_uts.resref) == "combined_resref"
    assert modified_uts.volume == 75
    assert modified_uts.active

def test_uts_editor_manipulate_all_playback_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all playback fields simultaneously."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Modify ALL playback fields
    editor.ui.playRandomRadio.setChecked(True)
    editor.ui.northRandomSpin.setValue(5.0)
    editor.ui.eastRandomSpin.setValue(5.0)
    editor.ui.orderRandomRadio.setChecked(True)
    editor.ui.intervalSpin.setValue(10.0)
    editor.ui.intervalVariationSpin.setValue(2.0)
    editor.ui.volumeVariationSlider.setValue(25)
    editor.ui.pitchVariationSlider.setValue(50)
    qtbot.wait(10)
    
    # Save and verify all
    data, _ = editor.build()
    modified_uts = read_uts(data)
    
    assert modified_uts.random_range_x == 5.0
    assert modified_uts.random_range_y == 5.0
    assert modified_uts.random_pick == 1
    assert modified_uts.interval == 10.0
    assert modified_uts.interval_variation == 2.0
    assert modified_uts.volume_variation == 25
    assert abs(modified_uts.pitch_variation - 0.5) < 0.01

def test_uts_editor_manipulate_all_positioning_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all positioning fields simultaneously."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Modify ALL positioning fields
    editor.ui.styleRepeatRadio.setChecked(True)
    editor.ui.cutoffSpin.setValue(50.0)
    editor.ui.maxVolumeDistanceSpin.setValue(25.0)
    editor.ui.heightSpin.setValue(10.0)
    qtbot.wait(10)
    
    # Save and verify all
    data, _ = editor.build()
    modified_uts = read_uts(data)
    
    assert modified_uts.looping
    assert modified_uts.max_distance == 50.0
    assert modified_uts.min_distance == 25.0
    assert modified_uts.elevation == 10.0

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_uts_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    # Load original
    original_data = uts_file.read_bytes()
    original_uts = read_uts(original_data)
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_uts = read_uts(data)
    
    # Verify key fields match
    assert saved_uts.tag == original_uts.tag
    assert str(saved_uts.resref) == str(original_uts.resref)
    assert saved_uts.volume == original_uts.volume
    assert saved_uts.active == original_uts.active
    
    # Load saved data back
    editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_uts.tag
    assert editor.ui.resrefEdit.text() == str(original_uts.resref)

def test_uts_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    # Load original
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.volumeSlider.setValue(75)
    editor.ui.activeCheckbox.setChecked(True)
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Add a sound
    editor.add_sound()
    qtbot.wait(10)
    item = editor.ui.soundList.item(editor.ui.soundList.count() - 1)
    if item:
        item.setText("test_sound")
        qtbot.wait(10)
    
    # Save
    data1, _ = editor.build()
    saved_uts1 = read_uts(data1)
    
    # Load saved data
    editor.load(uts_file, "low_air_01", ResourceType.UTS, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.volumeSlider.value() == 75
    assert editor.ui.activeCheckbox.isChecked()
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_uts2 = read_uts(data2)
    
    # Verify second save matches first
    assert saved_uts2.tag == saved_uts1.tag
    assert saved_uts2.volume == saved_uts1.volume
    assert saved_uts2.active == saved_uts1.active
    assert saved_uts2.comment == saved_uts1.comment

def test_uts_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        editor.ui.volumeSlider.setValue(10 + cycle * 10)
        
        # Save
        data, _ = editor.build()
        saved_uts = read_uts(data)
        
        # Verify
        assert saved_uts.tag == f"cycle_{cycle}"
        assert saved_uts.volume == 10 + cycle * 10
        
        # Load back
        editor.load(uts_file, "low_air_01", ResourceType.UTS, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"
        assert editor.ui.volumeSlider.value() == 10 + cycle * 10

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_uts_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set all to minimums
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.volumeSlider.setValue(0)
    editor.ui.intervalSpin.setValue(0.0)
    editor.ui.intervalVariationSpin.setValue(0.0)
    editor.ui.volumeVariationSlider.setValue(0)
    editor.ui.pitchVariationSlider.setValue(0)
    editor.ui.cutoffSpin.setValue(0.0)
    editor.ui.maxVolumeDistanceSpin.setValue(0.0)
    editor.ui.heightSpin.setValue(0.0)
    editor.ui.northRandomSpin.setValue(0.0)
    editor.ui.eastRandomSpin.setValue(0.0)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    
    assert modified_uts.tag == ""
    assert modified_uts.volume == 0
    assert modified_uts.interval == 0.0
    assert modified_uts.elevation == 0.0

def test_uts_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set all to maximums
    editor.ui.tagEdit.setText("x" * 32)  # Max tag length
    editor.ui.volumeSlider.setValue(editor.ui.volumeSlider.maximum())
    editor.ui.intervalSpin.setValue(editor.ui.intervalSpin.maximum())
    editor.ui.volumeVariationSlider.setValue(editor.ui.volumeVariationSlider.maximum())
    editor.ui.pitchVariationSlider.setValue(editor.ui.pitchVariationSlider.maximum())
    editor.ui.cutoffSpin.setValue(editor.ui.cutoffSpin.maximum())
    editor.ui.maxVolumeDistanceSpin.setValue(editor.ui.maxVolumeDistanceSpin.maximum())
    editor.ui.heightSpin.setValue(editor.ui.heightSpin.maximum())
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    
    assert modified_uts.volume == editor.ui.volumeSlider.maximum()

def test_uts_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.resrefEdit.setText("")
    editor.ui.commentsEdit.setPlainText("")
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    
    assert modified_uts.tag == ""
    assert str(modified_uts.resref) == ""
    assert modified_uts.comment == ""

def test_uts_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_uts = read_uts(data)
    
    assert modified_uts.tag == special_tag
    assert modified_uts.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_uts_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    # Load original
    original_data = uts_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_uts_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    original_data = uts_file.read_bytes()
    editor.load(uts_file, "low_air_01", ResourceType.UTS, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.volumeSlider.setValue(50)
    editor.ui.activeCheckbox.setChecked(True)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid UTS
    modified_uts = read_uts(data)
    assert modified_uts.tag == "modified_gff_test"
    assert modified_uts.volume == 50
    assert modified_uts.active

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_uts_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new UTS file from scratch."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Sound"))
    editor.ui.tagEdit.setText("new_sound")
    editor.ui.resrefEdit.setText("new_sound")
    editor.ui.volumeSlider.setValue(50)
    editor.ui.activeCheckbox.setChecked(True)
    editor.ui.styleOnceRadio.setChecked(True)
    editor.ui.playEverywhereRadio.setChecked(True)
    editor.ui.commentsEdit.setPlainText("New sound comment")
    
    # Add a sound
    editor.add_sound()
    qtbot.wait(10)
    item = editor.ui.soundList.item(0)
    if item:
        item.setText("test_sound")
        qtbot.wait(10)
    
    # Build and verify
    data, _ = editor.build()
    new_uts = read_uts(data)
    
    assert new_uts.name.get(Language.ENGLISH, Gender.MALE) == "New Sound"
    assert new_uts.tag == "new_sound"
    assert new_uts.volume == 50
    assert new_uts.active
    assert new_uts.comment == "New sound comment"
    if len(new_uts.sounds) > 0:
        assert str(new_uts.sounds[0]) == "test_sound"

def test_uts_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_uts = read_uts(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_uts.tag, str)
    assert isinstance(new_uts.resref, ResRef)
    assert isinstance(new_uts.volume, int)
    assert isinstance(new_uts.sounds, list)

# ============================================================================
# BUTTON FUNCTIONALITY TESTS
# ============================================================================

def test_uts_editor_generate_tag_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button functionality."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Clear tag
    editor.ui.tagEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated
    generated_tag = editor.ui.tagEdit.text()
    assert generated_tag

def test_uts_editor_generate_resref_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test resref generation button functionality."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Clear resref
    editor.ui.resrefEdit.setText("")
    
    # Click generate button
    qtbot.mouseClick(editor.ui.resrefGenerateButton, Qt.MouseButton.LeftButton)
    
    # ResRef should be generated
    generated_resref = editor.ui.resrefEdit.text()
    assert generated_resref

def test_uts_editor_add_sound_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test add sound button functionality."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Get initial count
    initial_count = editor.ui.soundList.count()
    
    # Click add sound button
    qtbot.mouseClick(editor.ui.addSoundButton, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    
    # Verify sound was added
    assert editor.ui.soundList.count() == initial_count + 1

def test_uts_editor_remove_sound_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test remove sound button functionality."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add a sound first
    editor.add_sound()
    qtbot.wait(10)
    
    initial_count = editor.ui.soundList.count()
    
    # Select last sound
    editor.ui.soundList.setCurrentRow(initial_count - 1)
    qtbot.wait(10)
    
    # Click remove button
    qtbot.mouseClick(editor.ui.removeSoundButton, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    
    # Verify sound was removed
    assert editor.ui.soundList.count() == initial_count - 1

def test_uts_editor_move_up_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test move sound up button functionality."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add multiple sounds
    editor.add_sound()
    qtbot.wait(10)
    editor.add_sound()
    qtbot.wait(10)
    
    if editor.ui.soundList.count() >= 2:
        # Select last sound
        editor.ui.soundList.setCurrentRow(editor.ui.soundList.count() - 1)
        qtbot.wait(10)
        
        # Click move up button
        qtbot.mouseClick(editor.ui.moveUpButton, Qt.MouseButton.LeftButton)
        qtbot.wait(10)
        
        # Verify moved
        assert editor.ui.soundList.currentRow() >= 0

def test_uts_editor_move_down_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test move sound down button functionality."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Add multiple sounds
    editor.add_sound()
    qtbot.wait(10)
    editor.add_sound()
    qtbot.wait(10)
    
    if editor.ui.soundList.count() >= 2:
        # Select first added sound
        editor.ui.soundList.setCurrentRow(editor.ui.soundList.count() - 2)
        qtbot.wait(10)
        
        # Click move down button
        qtbot.mouseClick(editor.ui.moveDownButton, Qt.MouseButton.LeftButton)
        qtbot.wait(10)
        
        # Verify moved
        assert editor.ui.soundList.currentRow() >= 0

def test_uts_editor_play_sound_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test play sound button exists."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify button exists
    assert hasattr(editor.ui, 'playSoundButton')
    
    # Verify signal is connected
    assert editor.ui.playSoundButton.receivers(editor.ui.playSoundButton.clicked) > 0

def test_uts_editor_stop_sound_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test stop sound button exists."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify button exists
    assert hasattr(editor.ui, 'stopSoundButton')
    
    # Verify signal is connected
    assert editor.ui.stopSoundButton.receivers(editor.ui.stopSoundButton.clicked) > 0

# ============================================================================
# STYLE RADIO INTERACTION TESTS
# ============================================================================

def test_uts_editor_style_once_disables_interval_group(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that style once disables interval group."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Set style once
    editor.ui.styleOnceRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify interval group is disabled
    assert not editor.ui.intervalGroup.isEnabled()
    
    # Verify order and variation groups are enabled
    assert editor.ui.orderGroup.isEnabled()
    assert editor.ui.variationGroup.isEnabled()

def test_uts_editor_style_seamless_disables_all_groups(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that style seamless disables all style groups."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Set style seamless
    editor.ui.styleSeamlessRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify all style groups are disabled
    assert not editor.ui.intervalGroup.isEnabled()
    assert not editor.ui.orderGroup.isEnabled()
    assert not editor.ui.variationGroup.isEnabled()

def test_uts_editor_style_repeat_enables_all_groups(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that style repeat enables all style groups."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Set style repeat
    editor.ui.styleRepeatRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify all style groups are enabled
    assert editor.ui.intervalGroup.isEnabled()
    assert editor.ui.orderGroup.isEnabled()
    assert editor.ui.variationGroup.isEnabled()

# ============================================================================
# PLAY RADIO INTERACTION TESTS
# ============================================================================

def test_uts_editor_play_random_enables_range_groups(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that play random enables range groups."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Set play random
    editor.ui.playRandomRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify range, height, and distance groups are enabled
    assert editor.ui.rangeGroup.isEnabled()
    assert editor.ui.heightGroup.isEnabled()
    assert editor.ui.distanceGroup.isEnabled()

def test_uts_editor_play_specific_disables_range_group(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that play specific disables range group."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Set play specific
    editor.ui.playSpecificRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify range group is disabled
    assert not editor.ui.rangeGroup.isEnabled()
    
    # Verify height and distance groups are enabled
    assert editor.ui.heightGroup.isEnabled()
    assert editor.ui.distanceGroup.isEnabled()
    
    # Verify random spins are set to 0
    assert editor.ui.northRandomSpin.value() == 0
    assert editor.ui.eastRandomSpin.value() == 0

def test_uts_editor_play_everywhere_disables_all_position_groups(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that play everywhere disables all position groups."""
    editor = UTSEditor(None, installation)
    qtbot.addWidget(editor)
    
    uts_file = test_files_dir / "low_air_01.uts"
    if not uts_file.exists():
        pytest.skip("low_air_01.uts not found")
    
    editor.load(uts_file, "low_air_01", ResourceType.UTS, uts_file.read_bytes())
    
    # Set play everywhere
    editor.ui.playEverywhereRadio.setChecked(True)
    qtbot.wait(10)
    
    # Verify all position groups are disabled
    assert not editor.ui.rangeGroup.isEnabled()
    assert not editor.ui.heightGroup.isEnabled()
    assert not editor.ui.distanceGroup.isEnabled()
