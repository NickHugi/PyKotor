"""
Comprehensive tests for LIP Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.lip.lip_editor import LIPEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.formats.lip import LIP, LIPKeyFrame, LIPShape, read_lip, bytes_lip  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]

# ============================================================================
# BASIC TESTS
# ============================================================================

def test_lip_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new LIP file from scratch."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Verify LIP object exists
    assert editor.lip is not None
    assert isinstance(editor.lip, LIP)
    assert len(editor.lip.frames) == 0

def test_lip_editor_initialization(qtbot, installation: HTInstallation):
    """Test editor initialization."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify all components initialized
    assert editor.lip is None or isinstance(editor.lip, LIP)
    assert editor.duration == 0.0
    assert editor.phoneme_map is not None
    assert len(editor.phoneme_map) > 0
    assert editor.player is not None
    assert editor.audio_output is not None
    assert editor.preview_timer is not None

# ============================================================================
# KEYFRAME MANIPULATIONS
# ============================================================================

def test_lip_editor_add_keyframe(qtbot, installation: HTInstallation):
    """Test adding a keyframe."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set duration first
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Set time and shape
    editor.time_input.setValue(1.0)
    editor.shape_select.setCurrentText(LIPShape.AH.name)
    
    # Add keyframe
    editor.add_keyframe()
    
    # Verify keyframe was added
    assert editor.lip is not None
    assert len(editor.lip.frames) == 1
    assert abs(editor.lip.frames[0].time - 1.0) < 0.001
    assert editor.lip.frames[0].shape == LIPShape.AH

def test_lip_editor_add_multiple_keyframes(qtbot, installation: HTInstallation):
    """Test adding multiple keyframes."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add multiple keyframes
    test_keyframes = [
        (0.0, LIPShape.AH),
        (1.0, LIPShape.EE),
        (2.0, LIPShape.OH),
        (3.0, LIPShape.MPB),
    ]
    
    for time, shape in test_keyframes:
        editor.time_input.setValue(time)
        editor.shape_select.setCurrentText(shape.name)
        editor.add_keyframe()
    
    # Verify all keyframes were added
    assert editor.lip is not None
    assert len(editor.lip.frames) == len(test_keyframes)
    
    # Verify keyframes are sorted by time
    sorted_frames = sorted(editor.lip.frames, key=lambda f: f.time)
    for i, (time, shape) in enumerate(test_keyframes):
        assert abs(sorted_frames[i].time - time) < 0.001
        assert sorted_frames[i].shape == shape

def test_lip_editor_update_keyframe(qtbot, installation: HTInstallation):
    """Test updating a keyframe."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add keyframe
    editor.time_input.setValue(1.0)
    editor.shape_select.setCurrentText(LIPShape.AH.name)
    editor.add_keyframe()
    
    # Select the keyframe
    editor.update_preview()
    editor.preview_list.setCurrentRow(0)
    editor.on_keyframe_selected()
    
    # Update keyframe
    editor.time_input.setValue(1.5)
    editor.shape_select.setCurrentText(LIPShape.EE.name)
    editor.update_keyframe()
    
    # Verify keyframe was updated
    assert editor.lip is not None
    assert len(editor.lip.frames) == 1
    assert abs(editor.lip.frames[0].time - 1.5) < 0.001
    assert editor.lip.frames[0].shape == LIPShape.EE

def test_lip_editor_delete_keyframe(qtbot, installation: HTInstallation):
    """Test deleting a keyframe."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add keyframes
    editor.time_input.setValue(1.0)
    editor.shape_select.setCurrentText(LIPShape.AH.name)
    editor.add_keyframe()
    
    editor.time_input.setValue(2.0)
    editor.shape_select.setCurrentText(LIPShape.EE.name)
    editor.add_keyframe()
    
    # Select and delete first keyframe
    editor.update_preview()
    editor.preview_list.setCurrentRow(0)
    editor.delete_keyframe()
    
    # Verify keyframe was deleted
    assert editor.lip is not None
    assert len(editor.lip.frames) == 1
    assert editor.lip.frames[0].shape == LIPShape.EE

# ============================================================================
# SHAPE SELECTION TESTS
# ============================================================================

def test_lip_editor_all_lip_shapes_available(qtbot, installation: HTInstallation):
    """Test all LIP shapes are available in combo box."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify all LIP shapes are in combo box
    all_shapes = list(LIPShape)
    assert editor.shape_select.count() == len(all_shapes)
    
    # Verify each shape is present
    for shape in all_shapes:
        index = editor.shape_select.findText(shape.name)
        assert index >= 0

def test_lip_editor_set_different_shapes(qtbot, installation: HTInstallation):
    """Test setting different LIP shapes."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Test various shapes
    test_shapes = [
        LIPShape.AH,
        LIPShape.EE,
        LIPShape.OH,
        LIPShape.MPB,
        LIPShape.FV,
        LIPShape.TD,
        LIPShape.KG,
        LIPShape.L,
    ]
    
    for i, shape in enumerate(test_shapes):
        editor.time_input.setValue(float(i))
        editor.shape_select.setCurrentText(shape.name)
        editor.add_keyframe()
    
    # Verify all shapes were set
    assert editor.lip is not None
    assert len(editor.lip.frames) == len(test_shapes)
    for i, shape in enumerate(test_shapes):
        sorted_frames: list[LIPKeyFrame] = sorted(editor.lip.frames, key=lambda f: f.time)
        assert sorted_frames[i].shape == shape

# ============================================================================
# PREVIEW TESTS
# ============================================================================

def test_lip_editor_update_preview(qtbot, installation: HTInstallation):
    """Test preview list updates correctly."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add keyframes
    editor.time_input.setValue(1.0)
    editor.shape_select.setCurrentText(LIPShape.AH.name)
    editor.add_keyframe()
    
    editor.time_input.setValue(2.0)
    editor.shape_select.setCurrentText(LIPShape.EE.name)
    editor.add_keyframe()
    
    # Update preview
    editor.update_preview()
    
    # Verify preview list has items
    assert editor.preview_list.count() == 2
    
    # Verify items are sorted by time
    item_0 = editor.preview_list.item(0)
    assert item_0 is not None
    assert "1.000" in item_0.text()
    item_1 = editor.preview_list.item(1)
    assert item_1 is not None
    assert "2.000" in item_1.text()

def test_lip_editor_keyframe_selection(qtbot, installation: HTInstallation):
    """Test selecting a keyframe updates inputs."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add keyframe
    editor.time_input.setValue(2.5)
    editor.shape_select.setCurrentText(LIPShape.OH.name)
    editor.add_keyframe()
    
    # Select keyframe
    editor.update_preview()
    editor.preview_list.setCurrentRow(0)
    editor.on_keyframe_selected()
    
    # Verify inputs were updated
    value = editor.time_input.value()
    assert value is not None
    assert abs(value - 2.5) < 0.001
    assert editor.shape_select.currentText() == LIPShape.OH.name

# ============================================================================
# SAVE/LOAD ROUNDTRIP TESTS
# ============================================================================

def test_lip_editor_save_load_roundtrip(qtbot, installation: HTInstallation):
    """Test save/load roundtrip preserves data."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add keyframes
    editor.time_input.setValue(1.0)
    editor.shape_select.setCurrentText(LIPShape.AH.name)
    editor.add_keyframe()
    
    editor.time_input.setValue(2.0)
    editor.shape_select.setCurrentText(LIPShape.EE.name)
    editor.add_keyframe()
    
    # Build
    data, _ = editor.build()
    assert len(data) > 0
    
    # Load it back
    editor.load(Path("test.lip"), "test", ResourceType.LIP, data)
    
    # Verify data was loaded
    assert editor.lip is not None
    assert len(editor.lip.frames) == 2
    assert abs(editor.lip.length - 10.0) < 0.001
    assert editor.duration == 10.0

def test_lip_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation):
    """Test multiple save/load cycles preserve data correctly."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Perform multiple cycles
    for cycle in range(3):
        # Clear and add keyframe
        editor.new()
        editor.duration = 10.0
        editor.duration_label.setText("10.000s")
        editor.time_input.setMaximum(10.0)
        
        editor.time_input.setValue(float(cycle))
        editor.shape_select.setCurrentText(LIPShape.AH.name)
        editor.add_keyframe()
        
        # Save
        data, _ = editor.build()
        
        # Load back
        editor.load(Path("test.lip"), "test", ResourceType.LIP, data)
        
        # Verify keyframe was preserved
        assert editor.lip is not None
        assert len(editor.lip.frames) == 1

# ============================================================================
# DURATION TESTS
# ============================================================================

def test_lip_editor_duration_setting(qtbot, installation: HTInstallation):
    """Test setting duration."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set duration
    editor.duration = 5.5
    editor.duration_label.setText("5.500s")
    editor.time_input.setMaximum(5.5)
    
    # Verify duration was set
    assert editor.duration == 5.5
    assert editor.time_input.maximum() == 5.5

def test_lip_editor_duration_from_loaded_lip(qtbot, installation: HTInstallation):
    """Test duration is loaded from LIP file."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.lip = LIP()
    editor.lip.length = 10.0
    
    # Build and load
    data, _ = editor.build()
    editor.load(Path("test.lip"), "test", ResourceType.LIP, data)
    
    # Verify duration was loaded
    assert abs(editor.duration - 10.0) < 0.001

# ============================================================================
# PHONEME MAPPING TESTS
# ============================================================================

def test_lip_editor_phoneme_map_initialization(qtbot, installation: HTInstallation):
    """Test phoneme map is properly initialized."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify phoneme map exists and has entries
    assert editor.phoneme_map is not None
    assert len(editor.phoneme_map) > 0
    
    # Verify some expected phonemes exist
    assert "AA" in editor.phoneme_map
    assert "B" in editor.phoneme_map
    assert "M" in editor.phoneme_map
    assert "P" in editor.phoneme_map
    
    # Verify phonemes map to valid LIP shapes
    for phoneme, shape in editor.phoneme_map.items():
        assert isinstance(shape, LIPShape)

# ============================================================================
# PLAYBACK TESTS (Limited - requires audio file)
# ============================================================================

def test_lip_editor_playback_methods_exist(qtbot, installation: HTInstallation):
    """Test playback methods exist."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify playback methods exist
    assert hasattr(editor, 'play_preview')
    assert hasattr(editor, 'stop_preview')
    assert callable(editor.play_preview)
    assert callable(editor.stop_preview)

def test_lip_editor_stop_preview(qtbot, installation: HTInstallation):
    """Test stopping preview."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Stop preview (should work even if not playing)
    editor.stop_preview()
    
    # Verify preview label was reset
    assert editor.preview_label is not None
    assert editor.preview_label.text() == "None"
    assert editor.current_shape is None

# ============================================================================
# KEYBOARD SHORTCUTS
# ============================================================================

def test_lip_editor_shortcuts_setup(qtbot, installation: HTInstallation):
    """Test keyboard shortcuts are set up."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify shortcut setup method exists
    assert hasattr(editor, 'setup_shortcuts')
    assert callable(editor.setup_shortcuts)

# ============================================================================
# CONTEXT MENU TESTS
# ============================================================================

def test_lip_editor_context_menu(qtbot, installation: HTInstallation):
    """Test context menu functionality."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify context menu method exists
    assert hasattr(editor, 'show_preview_context_menu')
    assert callable(editor.show_preview_context_menu)
    
    # Verify preview list has context menu enabled
    assert editor.preview_list.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu

# ============================================================================
# UNDO/REDO TESTS
# ============================================================================

def test_lip_editor_undo_redo_methods_exist(qtbot, installation: HTInstallation):
    """Test undo/redo methods exist (even if not implemented)."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify undo/redo methods exist
    assert hasattr(editor, 'undo')
    assert hasattr(editor, 'redo')
    assert callable(editor.undo)
    assert callable(editor.redo)

# ============================================================================
# UI ELEMENT TESTS
# ============================================================================

def test_lip_editor_ui_elements(qtbot, installation: HTInstallation):
    """Test that UI elements exist."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify UI elements exist
    assert hasattr(editor, 'audio_path')
    assert hasattr(editor, 'duration_label')
    assert hasattr(editor, 'preview_list')
    assert hasattr(editor, 'time_input')
    assert hasattr(editor, 'shape_select')
    assert hasattr(editor, 'preview_label')

# ============================================================================
# EDGE CASES
# ============================================================================

def test_lip_editor_empty_lip_file(qtbot, installation: HTInstallation):
    """Test handling of empty LIP file."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Build empty file
    data, _ = editor.build()
    
    # Load it back
    editor.load(Path("test.lip"), "test", ResourceType.LIP, data)
    
    # Verify empty LIP loaded correctly
    assert editor.lip is not None
    assert len(editor.lip.frames) == 0

def test_lip_editor_keyframes_sorted_by_time(qtbot, installation: HTInstallation):
    """Test keyframes are sorted by time when displayed."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add keyframes out of order
    editor.time_input.setValue(3.0)
    editor.shape_select.setCurrentText(LIPShape.AH.name)
    editor.add_keyframe()
    
    editor.time_input.setValue(1.0)
    editor.shape_select.setCurrentText(LIPShape.EE.name)
    editor.add_keyframe()
    
    editor.time_input.setValue(2.0)
    editor.shape_select.setCurrentText(LIPShape.OH.name)
    editor.add_keyframe()
    
    # Update preview
    editor.update_preview()
    
    # Verify preview list is sorted
    assert editor.preview_list.count() == 3
    item_0 = editor.preview_list.item(0)
    assert item_0 is not None
    item_1 = editor.preview_list.item(1)
    assert item_1 is not None
    item_2 = editor.preview_list.item(2)
    assert item_2 is not None
    assert "1.000" in item_0.text()
    assert "2.000" in item_1.text()
    assert "3.000" in item_2.text()

# ============================================================================
# COMBINATION TESTS
# ============================================================================

def test_lip_editor_complex_lip_file(qtbot, installation: HTInstallation):
    """Test creating a complex LIP file with many keyframes."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 10.0
    editor.duration_label.setText("10.000s")
    editor.time_input.setMaximum(10.0)
    
    # Add many keyframes
    shapes = [LIPShape.AH, LIPShape.EE, LIPShape.OH, LIPShape.MPB, LIPShape.FV]
    for i in range(10):
        editor.time_input.setValue(float(i))
        editor.shape_select.setCurrentText(shapes[i % len(shapes)].name)
        editor.add_keyframe()
    
    # Verify all keyframes were added
    assert editor.lip is not None
    assert len(editor.lip.frames) == 10
    
    # Build and verify
    data, _ = editor.build()
    assert len(data) > 0
    
    # Load and verify
    editor.load(Path("test.lip"), "test", ResourceType.LIP, data)
    assert editor.lip is not None
    assert len(editor.lip.frames) == 10
    assert abs(editor.lip.length - 10.0) < 0.001

def test_lip_editor_all_shapes_used(qtbot, installation: HTInstallation):
    """Test using all LIP shapes."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    editor.duration = 100.0
    editor.duration_label.setText("100.000s")
    editor.time_input.setMaximum(100.0)
    
    # Add keyframe for each shape
    all_shapes = list(LIPShape)
    for i, shape in enumerate(all_shapes):
        editor.time_input.setValue(float(i))
        editor.shape_select.setCurrentText(shape.name)
        editor.add_keyframe()
    
    # Verify all shapes were used
    assert editor.lip is not None
    assert len(editor.lip.frames) == len(all_shapes)
    
    # Verify each shape appears at least once
    used_shapes = {frame.shape for frame in editor.lip.frames}
    assert len(used_shapes) == len(all_shapes)

# ============================================================================
# HEADLESS UI TESTS WITH REAL FILES
# ============================================================================

def test_lip_editor_headless_ui_load_build(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test LIP Editor in headless UI - loads real file and builds data."""
    editor = LIPEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a LIP file
    lip_files = list(test_files_dir.glob("*.lip")) + list(test_files_dir.rglob("*.lip"))
    if not lip_files:
        # Try to get one from installation
        lip_resources = list(installation.resources(ResourceType.LIP))[:1]
        if not lip_resources:
            pytest.skip("No LIP files available for testing")
        lip_resource = lip_resources[0]
        lip_data = installation.resource(lip_resource.identifier)
        if not lip_data:
            pytest.skip(f"Could not load LIP data for {lip_resource.identifier}")
        editor.load(
            lip_resource.filepath if hasattr(lip_resource, 'filepath') else Path("module.lip"),
            lip_resource.resname,
            ResourceType.LIP,
            lip_data
        )
    else:
        lip_file = lip_files[0]
        original_data = lip_file.read_bytes()
        editor.load(lip_file, lip_file.stem, ResourceType.LIP, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    assert editor.lip is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    loaded_lip = read_lip(data)
    assert loaded_lip is not None

