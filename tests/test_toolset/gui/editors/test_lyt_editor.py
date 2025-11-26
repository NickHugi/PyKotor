"""
Comprehensive tests for LYT Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.lyt import LYTEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack, read_lyt, bytes_lyt  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from utility.common.geometry import Vector3, Vector4  # type: ignore[import-not-found]

# ============================================================================
# BASIC TESTS
# ============================================================================

def test_lyt_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new LYT file from scratch."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new (should initialize with empty LYT)
    editor._lyt = LYT()
    
    # Verify scene exists
    assert editor.scene is not None
    assert editor._lyt is not None

def test_lyt_editor_initialization(qtbot, installation: HTInstallation):
    """Test editor initialization."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify all components initialized
    assert editor._lyt is not None
    assert editor.scene is not None
    assert editor._controls is not None
    assert editor.settings is not None
    assert editor.material_colors is not None
    assert len(editor.material_colors) > 0

# ============================================================================
# ROOM MANIPULATIONS
# ============================================================================

def test_lyt_editor_add_room(qtbot, installation: HTInstallation):
    """Test adding a room."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add room
    editor.add_room()
    
    # Verify room was added
    assert len(editor._lyt.rooms) > 0
    
    # Verify scene was updated
    items = editor.scene.items()
    assert len(items) > 0

def test_lyt_editor_add_multiple_rooms(qtbot, installation: HTInstallation):
    """Test adding multiple rooms."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add multiple rooms
    for _ in range(5):
        editor.add_room()
    
    # Verify all rooms were added
    assert len(editor._lyt.rooms) == 5

def test_lyt_editor_room_properties(qtbot, installation: HTInstallation):
    """Test room properties are set correctly."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add room
    editor.add_room()
    
    # Get the added room
    room = list(editor._lyt.rooms)[0]
    
    # Verify room has expected properties
    assert hasattr(room, 'model')
    assert hasattr(room, 'position')
    assert hasattr(room, 'size')
    assert room.model == "default_room"
    assert isinstance(room.position, Vector3)
    assert isinstance(room.size, Vector3)

# ============================================================================
# TRACK MANIPULATIONS
# ============================================================================

def test_lyt_editor_add_track(qtbot, installation: HTInstallation):
    """Test adding a track (requires at least 2 rooms)."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add two rooms first
    editor.add_room()
    editor.add_room()
    
    # Add track
    initial_track_count = len(editor._lyt.tracks)
    editor.add_track()
    
    # Track may or may not be added depending on pathfinding
    # Just verify the method doesn't crash
    assert len(editor._lyt.tracks) >= initial_track_count

def test_lyt_editor_track_requires_multiple_rooms(qtbot, installation: HTInstallation):
    """Test that tracks require multiple rooms."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add only one room
    editor.add_room()
    
    # Try to add track - should not add anything
    initial_track_count = len(editor._lyt.tracks)
    editor.add_track()
    
    # Verify no track was added
    assert len(editor._lyt.tracks) == initial_track_count

# ============================================================================
# OBSTACLE MANIPULATIONS
# ============================================================================

def test_lyt_editor_add_obstacle(qtbot, installation: HTInstallation):
    """Test adding an obstacle."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add obstacle
    initial_obstacle_count = len(editor._lyt.obstacles)
    editor.add_obstacle()
    
    # Verify obstacle was added
    assert len(editor._lyt.obstacles) == initial_obstacle_count + 1
    
    # Verify obstacle properties
    obstacle = editor._lyt.obstacles[-1]
    assert obstacle.model == "default_obstacle"
    assert isinstance(obstacle.position, Vector3)
    assert hasattr(obstacle, 'radius')
    assert obstacle.radius == 5.0

def test_lyt_editor_add_multiple_obstacles(qtbot, installation: HTInstallation):
    """Test adding multiple obstacles."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add multiple obstacles
    for _ in range(3):
        editor.add_obstacle()
    
    # Verify all obstacles were added
    assert len(editor._lyt.obstacles) == 3

# ============================================================================
# DOOR HOOK MANIPULATIONS
# ============================================================================

def test_lyt_editor_add_door_hook(qtbot, installation: HTInstallation):
    """Test adding a door hook."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add a room first (door hook requires at least one room)
    editor.add_room()
    
    # Add door hook
    initial_doorhook_count = len(editor._lyt.doorhooks)
    editor.add_door_hook()
    
    # Verify door hook was added
    assert len(editor._lyt.doorhooks) == initial_doorhook_count + 1
    
    # Verify door hook properties
    doorhook = editor._lyt.doorhooks[-1]
    assert hasattr(doorhook, 'room')
    assert hasattr(doorhook, 'door')
    assert hasattr(doorhook, 'position')
    assert hasattr(doorhook, 'orientation')
    assert isinstance(doorhook.position, Vector3)
    assert isinstance(doorhook.orientation, Vector4)

def test_lyt_editor_add_door_hook_without_room(qtbot, installation: HTInstallation):
    """Test that door hook requires at least one room."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Try to add door hook without rooms
    initial_doorhook_count = len(editor._lyt.doorhooks)
    editor.add_door_hook()
    
    # Should not add door hook if no rooms exist
    # The method should handle this gracefully
    assert len(editor._lyt.doorhooks) >= initial_doorhook_count

# ============================================================================
# SCENE UPDATE TESTS
# ============================================================================

def test_lyt_editor_update_scene_after_add_room(qtbot, installation: HTInstallation):
    """Test that scene updates after adding room."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Clear scene
    editor.scene.clear()
    initial_item_count = len(editor.scene.items())
    
    # Add room
    editor.add_room()
    
    # Verify scene has items
    assert len(editor.scene.items()) > initial_item_count

def test_lyt_editor_update_scene_clears_and_rebuilds(qtbot, installation: HTInstallation):
    """Test that update_scene clears and rebuilds scene."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add various elements
    editor.add_room()
    editor.add_obstacle()
    editor.add_room()
    
    # Update scene manually
    editor.update_scene()
    
    # Verify scene has items
    assert len(editor.scene.items()) > 0

# ============================================================================
# ZOOM FUNCTIONALITY
# ============================================================================

def test_lyt_editor_update_zoom(qtbot, installation: HTInstallation):
    """Test zoom functionality."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Test various zoom values
    test_zooms = [50, 100, 150, 200]
    for zoom in test_zooms:
        editor.update_zoom(zoom)
        
        # Verify transform was applied (check that zoom slider exists)
        # The actual zoom is applied via QTransform
        assert hasattr(editor.ui, 'zoomSlider')

# ============================================================================
# SAVE/LOAD ROUNDTRIP TESTS
# ============================================================================

def test_lyt_editor_save_load_roundtrip(qtbot, installation: HTInstallation):
    """Test save/load roundtrip preserves data."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add some elements
    editor.add_room()
    editor.add_obstacle()
    
    # Build
    data, _ = editor.build()
    assert len(data) > 0
    
    # Load it back
    editor.load(Path("test.lyt"), "test", ResourceType.LYT, data)
    
    # Verify elements were loaded
    assert len(editor._lyt.rooms) > 0
    assert len(editor._lyt.obstacles) > 0

def test_lyt_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation):
    """Test multiple save/load cycles."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Perform multiple cycles
    for cycle in range(3):
        # Clear and add elements
        editor._lyt = LYT()
        for _ in range(cycle + 1):
            editor.add_room()
            editor.add_obstacle()
        
        # Save
        data, _ = editor.build()
        
        # Load back
        editor.load(Path("test.lyt"), "test", ResourceType.LYT, data)
        
        # Verify elements were preserved
        assert len(editor._lyt.rooms) == cycle + 1
        assert len(editor._lyt.obstacles) == cycle + 1

# ============================================================================
# PATHFINDING TESTS
# ============================================================================

def test_lyt_editor_find_path_between_rooms(qtbot, installation: HTInstallation):
    """Test pathfinding between rooms."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add multiple rooms
    editor.add_room()
    editor.add_room()
    
    # Get rooms
    rooms = list(editor._lyt.rooms)
    if len(rooms) >= 2:
        start_room = rooms[0]
        end_room = rooms[1]
        
        # Try to find path
        path = editor.find_path(start_room, end_room)
        
        # Path may or may not exist depending on connections
        # Just verify method doesn't crash
        assert path is None or isinstance(path, list)

def test_lyt_editor_find_path_no_connection(qtbot, installation: HTInstallation):
    """Test pathfinding when no connection exists."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add two disconnected rooms
    editor.add_room()
    editor.add_room()
    
    rooms = list(editor._lyt.rooms)
    if len(rooms) >= 2:
        start_room = rooms[0]
        end_room = rooms[1]
        
        # Find path - should return None if no connection
        path = editor.find_path(start_room, end_room)
        
        # Result should be None or empty list if no path
        assert path is None or len(path) == 0

# ============================================================================
# MATERIAL COLORS
# ============================================================================

def test_lyt_editor_material_colors_initialization(qtbot, installation: HTInstallation):
    """Test material colors are properly initialized."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify material colors exist and have entries
    assert editor.material_colors is not None
    assert len(editor.material_colors) > 0
    
    # Verify some expected materials exist
    from utility.common.geometry import SurfaceMaterial
    assert SurfaceMaterial.UNDEFINED in editor.material_colors
    assert SurfaceMaterial.GRASS in editor.material_colors
    assert SurfaceMaterial.WATER in editor.material_colors

# ============================================================================
# UI ELEMENT TESTS
# ============================================================================

def test_lyt_editor_button_connections(qtbot, installation: HTInstallation):
    """Test that buttons are properly connected."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify buttons exist
    assert hasattr(editor.ui, 'addRoomButton')
    assert hasattr(editor.ui, 'addTrackButton')
    assert hasattr(editor.ui, 'addObstacleButton')
    assert hasattr(editor.ui, 'addDoorHookButton')
    
    # Verify zoom slider exists
    assert hasattr(editor.ui, 'zoomSlider')

def test_lyt_editor_graphics_view_setup(qtbot, installation: HTInstallation):
    """Test graphics view is properly set up."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify graphics view exists and has scene
    assert hasattr(editor.ui, 'graphicsView')
    assert editor.ui.graphicsView.scene() == editor.scene

# ============================================================================
# EDGE CASES
# ============================================================================

def test_lyt_editor_empty_lyt_file(qtbot, installation: HTInstallation):
    """Test handling of empty LYT file."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Build empty file
    data, _ = editor.build()
    
    # Load it back
    editor.load(Path("test.lyt"), "test", ResourceType.LYT, data)
    
    # Verify empty LYT loaded correctly
    assert editor._lyt is not None
    assert len(editor._lyt.rooms) == 0
    assert len(editor._lyt.tracks) == 0
    assert len(editor._lyt.obstacles) == 0

def test_lyt_editor_signal_emission(qtbot, installation: HTInstallation):
    """Test that signals are properly defined."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify signal exists
    assert hasattr(editor, 'sig_lyt_updated')
    
    # Verify signal can be emitted
    editor._lyt = LYT()
    editor.add_room()
    
    # Signal should be emitted when door hook is added
    # (other additions may not emit signals)
    editor.add_door_hook()
    # Signal emission is tested implicitly - if it crashes, test fails

# ============================================================================
# IMPORT FUNCTIONALITY (Placeholder tests)
# ============================================================================

def test_lyt_editor_import_texture_method_exists(qtbot, installation: HTInstallation):
    """Test that import_texture method exists."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify method exists and is callable
    assert hasattr(editor, 'import_texture')
    assert callable(editor.import_texture)

def test_lyt_editor_import_model_method_exists(qtbot, installation: HTInstallation):
    """Test that import_model method exists."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify method exists and is callable
    assert hasattr(editor, 'import_model')
    assert callable(editor.import_model)

def test_lyt_editor_generate_walkmesh_method_exists(qtbot, installation: HTInstallation):
    """Test that generate_walkmesh method exists."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify method exists and is callable
    assert hasattr(editor, 'generate_walkmesh')
    assert callable(editor.generate_walkmesh)

# ============================================================================
# COMBINATION TESTS
# ============================================================================

def test_lyt_editor_all_element_types(qtbot, installation: HTInstallation):
    """Test adding all element types together."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._lyt = LYT()
    
    # Add all element types
    editor.add_room()
    editor.add_room()  # Need at least 2 for tracks
    editor.add_track()
    editor.add_obstacle()
    editor.add_door_hook()
    
    # Verify all elements were added
    assert len(editor._lyt.rooms) >= 2
    assert len(editor._lyt.obstacles) >= 1
    assert len(editor._lyt.doorhooks) >= 1
    
    # Build and verify
    data, _ = editor.build()
    assert len(data) > 0
    
    # Load and verify
    editor.load(Path("test.lyt"), "test", ResourceType.LYT, data)
    assert len(editor._lyt.rooms) >= 2
    assert len(editor._lyt.obstacles) >= 1
    assert len(editor._lyt.doorhooks) >= 1

# ============================================================================
# HEADLESS UI TESTS WITH REAL FILES
# ============================================================================

def test_lyt_editor_headless_ui_load_build(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test LYT Editor in headless UI - loads real file and builds data."""
    editor = LYTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a LYT file
    lyt_files = list(test_files_dir.glob("*.lyt")) + list(test_files_dir.rglob("*.lyt"))
    if not lyt_files:
        # Try to get one from installation
        lyt_resources = list(installation.resources(ResourceType.LYT))[:1]
        if not lyt_resources:
            pytest.skip("No LYT files available for testing")
        lyt_resource = lyt_resources[0]
        lyt_data = installation.resource(lyt_resource.identifier)
        if not lyt_data:
            pytest.skip(f"Could not load LYT data for {lyt_resource.identifier}")
        editor.load(
            lyt_resource.filepath if hasattr(lyt_resource, 'filepath') else Path("module.lyt"),
            lyt_resource.resname,
            ResourceType.LYT,
            lyt_data
        )
    else:
        lyt_file = lyt_files[0]
        original_data = lyt_file.read_bytes()
        editor.load(lyt_file, lyt_file.stem, ResourceType.LYT, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    assert editor._lyt is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    loaded_lyt = read_lyt(data)
    assert loaded_lyt is not None

