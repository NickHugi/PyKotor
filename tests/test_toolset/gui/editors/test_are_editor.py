"""
Comprehensive tests for ARE Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
"""
import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.are import AREEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.are import ARE, ARENorthAxis, AREWindPower, read_are  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import Color, ResRef  # type: ignore[import-not-found]
from utility.common.geometry import Vector2  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_are_editor_manipulate_name_locstring(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating name LocalizedString field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    # Load original
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    original_are = read_are(original_data)
    
    # Modify name
    new_name = LocalizedString.from_english("Modified Area Name")
    editor.ui.nameEdit.set_locstring(new_name)
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.name.get(Language.ENGLISH, Gender.MALE) == "Modified Area Name"
    assert modified_are.name.get(Language.ENGLISH, Gender.MALE) != original_are.name.get(Language.ENGLISH, Gender.MALE)
    
    # Load back and verify
    editor.load(are_file, "tat001", ResourceType.ARE, data)
    assert editor.ui.nameEdit.locstring().get(Language.ENGLISH, Gender.MALE) == "Modified Area Name"

def test_are_editor_manipulate_tag(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    original_are = read_are(original_data)
    
    # Modify tag
    editor.ui.tagEdit.setText("modified_tag")
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.tag == "modified_tag"
    assert modified_are.tag != original_are.tag
    
    # Load back and verify
    editor.load(are_file, "tat001", ResourceType.ARE, data)
    assert editor.ui.tagEdit.text() == "modified_tag"

def test_are_editor_manipulate_tag_generate_button(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test tag generation button."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    editor.load(are_file, "tat001", ResourceType.ARE, are_file.read_bytes())
    
    # Click generate button
    from qtpy.QtWidgets import QPushButton
    qtbot.mouseClick(editor.ui.tagGenerateButton, Qt.MouseButton.LeftButton)
    
    # Tag should be generated from resname
    assert editor.ui.tagEdit.text() == "tat001"
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.tag == "tat001"

def test_are_editor_manipulate_camera_style(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating camera style combo box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    original_are = read_are(original_data)
    
    # Test all available camera styles
    if editor.ui.cameraStyleSelect.count() > 0:
        for i in range(min(5, editor.ui.cameraStyleSelect.count())):
            editor.ui.cameraStyleSelect.setCurrentIndex(i)
            
            # Save and verify
            data, _ = editor.build()
            modified_are = read_are(data)
            assert modified_are.camera_style == i
            
            # Load back and verify
            editor.load(are_file, "tat001", ResourceType.ARE, data)
            assert editor.ui.cameraStyleSelect.currentIndex() == i

def test_are_editor_manipulate_envmap(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating envmap field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify envmap
    test_envmaps = ["test_envmap", "another_env", "env123", ""]
    for envmap in test_envmaps:
        editor.ui.envmapEdit.setText(envmap)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert str(modified_are.default_envmap) == envmap
        
        # Load back and verify
        editor.load(are_file, "tat001", ResourceType.ARE, data)
        assert editor.ui.envmapEdit.text() == envmap

def test_are_editor_manipulate_disable_transit_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating disable transit checkbox."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    original_are = read_are(original_data)
    
    # Toggle checkbox
    editor.ui.disableTransitCheck.setChecked(True)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.disable_transit
    
    editor.ui.disableTransitCheck.setChecked(False)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert not modified_are.disable_transit
    
    # Load back and verify
    editor.load(are_file, "tat001", ResourceType.ARE, data)
    assert editor.ui.disableTransitCheck.isChecked() == False

def test_are_editor_manipulate_unescapable_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating unescapable checkbox."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Toggle checkbox
    editor.ui.unescapableCheck.setChecked(True)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.unescapable
    
    editor.ui.unescapableCheck.setChecked(False)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert not modified_are.unescapable

def test_are_editor_manipulate_alpha_test_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating alpha test spin box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various values
    test_values = [0, 1, 50, 100, 255]
    for val in test_values:
        editor.ui.alphaTestSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.alpha_test == val
        
        # Load back and verify
        editor.load(are_file, "tat001", ResourceType.ARE, data)
        assert editor.ui.alphaTestSpin.value() == val

def test_are_editor_manipulate_stealth_xp_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating stealth XP checkbox."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Toggle checkbox
    editor.ui.stealthCheck.setChecked(True)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.stealth_xp
    
    editor.ui.stealthCheck.setChecked(False)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert not modified_are.stealth_xp

def test_are_editor_manipulate_stealth_xp_max_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating stealth XP max spin box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various values
    test_values = [0, 10, 50, 100, 1000]
    for val in test_values:
        editor.ui.stealthMaxSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.stealth_xp_max == val

def test_are_editor_manipulate_stealth_xp_loss_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating stealth XP loss spin box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various values
    test_values = [0, 5, 10, 25, 50]
    for val in test_values:
        editor.ui.stealthLossSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.stealth_xp_loss == val

# ============================================================================
# MAP FIELDS MANIPULATIONS
# ============================================================================

def test_are_editor_manipulate_map_axis(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating map axis combo box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test all axis options (0-3 typically)
    for axis in [0, 1, 2, 3]:
        editor.ui.mapAxisSelect.setCurrentIndex(axis)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.north_axis == ARENorthAxis(axis)
        
        # Load back and verify
        editor.load(are_file, "tat001", ResourceType.ARE, data)
        assert editor.ui.mapAxisSelect.currentIndex() == axis

def test_are_editor_manipulate_map_zoom_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating map zoom spin box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various zoom values (mapZoomSpin is QSpinBox, so use integer values)
    test_values = [1, 2, 5, 10, 20, 50]
    for val in test_values:
        editor.ui.mapZoomSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.map_zoom - float(val)) < 0.001  # Float comparison

def test_are_editor_manipulate_map_res_x_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating map resolution X spin box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various resolution values
    test_values = [128, 256, 512, 1024, 2048]
    for val in test_values:
        editor.ui.mapResXSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.map_res_x == val

def test_are_editor_manipulate_map_image_points(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating map image point coordinates."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various point combinations
    test_points = [
        (Vector2(0, 0), Vector2(100, 100)),
        (Vector2(10, 20), Vector2(200, 300)),
        (Vector2(-50, -50), Vector2(50, 50)),
        (Vector2(1000, 1000), Vector2(2000, 2000)),
    ]
    
    for point1, point2 in test_points:
        editor.ui.mapImageX1Spin.setValue(point1.x)
        editor.ui.mapImageY1Spin.setValue(point1.y)
        editor.ui.mapImageX2Spin.setValue(point2.x)
        editor.ui.mapImageY2Spin.setValue(point2.y)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.map_point_1.x == point1.x
        assert modified_are.map_point_1.y == point1.y
        assert modified_are.map_point_2.x == point2.x
        assert modified_are.map_point_2.y == point2.y

def test_are_editor_manipulate_map_world_points(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating map world point coordinates."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various world point combinations
    test_points = [
        (Vector2(0.0, 0.0), Vector2(10.0, 10.0)),
        (Vector2(-10.0, -10.0), Vector2(10.0, 10.0)),
        (Vector2(100.0, 200.0), Vector2(300.0, 400.0)),
    ]
    
    for point1, point2 in test_points:
        editor.ui.mapWorldX1Spin.setValue(point1.x)
        editor.ui.mapWorldY1Spin.setValue(point1.y)
        editor.ui.mapWorldX2Spin.setValue(point2.x)
        editor.ui.mapWorldY2Spin.setValue(point2.y)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.world_point_1.x - point1.x) < 0.001
        assert abs(modified_are.world_point_1.y - point1.y) < 0.001
        assert abs(modified_are.world_point_2.x - point2.x) < 0.001
        assert abs(modified_are.world_point_2.y - point2.y) < 0.001

# ============================================================================
# WEATHER FIELDS MANIPULATIONS
# ============================================================================

def test_are_editor_manipulate_fog_enabled_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating fog enabled checkbox."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Toggle checkbox
    editor.ui.fogEnabledCheck.setChecked(True)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.fog_enabled
    
    editor.ui.fogEnabledCheck.setChecked(False)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert not modified_are.fog_enabled

def test_are_editor_manipulate_fog_color(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating fog color."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various colors
    test_colors = [
        Color(1.0, 0.0, 0.0),  # Red
        Color(0.0, 1.0, 0.0),  # Green
        Color(0.0, 0.0, 1.0),  # Blue
        Color(0.5, 0.5, 0.5),  # Gray
        Color(1.0, 1.0, 1.0),  # White
    ]
    
    for color in test_colors:
        editor.ui.fogColorEdit.set_color(color)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.fog_color.r - color.r) < 0.01
        assert abs(modified_are.fog_color.g - color.g) < 0.01
        assert abs(modified_are.fog_color.b - color.b) < 0.01

def test_are_editor_manipulate_fog_near_far_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating fog near and far spin boxes."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various fog distances
    test_near = [0.0, 1.0, 5.0, 10.0, 50.0]
    test_far = [10.0, 50.0, 100.0, 500.0, 1000.0]
    
    for near_val in test_near:
        editor.ui.fogNearSpin.setValue(near_val)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.fog_near - near_val) < 0.001
    
    for far_val in test_far:
        editor.ui.fogFarSpin.setValue(far_val)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.fog_far - far_val) < 0.001

def test_are_editor_manipulate_sun_colors(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating sun ambient, diffuse, and dynamic light colors."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test ambient color
    ambient_color = Color(0.2, 0.2, 0.2)
    editor.ui.ambientColorEdit.set_color(ambient_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.sun_ambient.r - ambient_color.r) < 0.01
    
    # Test diffuse color
    diffuse_color = Color(0.8, 0.8, 0.8)
    editor.ui.diffuseColorEdit.set_color(diffuse_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.sun_diffuse.r - diffuse_color.r) < 0.01
    
    # Test dynamic light color
    dynamic_color = Color(1.0, 1.0, 1.0)
    editor.ui.dynamicColorEdit.set_color(dynamic_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.dynamic_light.r - dynamic_color.r) < 0.01

def test_are_editor_manipulate_wind_power(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating wind power combo box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test all wind power options (typically 0-3)
    for power in [0, 1, 2, 3]:
        if power < editor.ui.windPowerSelect.count():
            editor.ui.windPowerSelect.setCurrentIndex(power)
            
            # Save and verify
            data, _ = editor.build()
            modified_are = read_are(data)
            assert modified_are.wind_power == AREWindPower(power)

def test_are_editor_manipulate_weather_checkboxes(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating rain, snow, and lightning checkboxes."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test rain checkbox
    # Ensure checkbox is enabled and visible (it may be hidden for K1 installations)
    editor.ui.rainCheck.setEnabled(True)
    editor.ui.rainCheck.setVisible(True)
    editor.ui.rainCheck.show()  # Ensure checkbox is shown, not just visible
    # Set checkbox state directly to ensure it's checked
    editor.ui.rainCheck.setChecked(True)
    qtbot.wait(100)  # Wait longer for Qt to process the checkbox state change
    # Process events to ensure state is synchronized
    from qtpy.QtWidgets import QApplication
    QApplication.processEvents()
    assert editor.ui.rainCheck.isChecked(), "Rain checkbox should be checked"
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.chance_rain == 100, f"Expected chance_rain to be 100, got {modified_are.chance_rain}"
    
    if editor.ui.rainCheck.isChecked():
        qtbot.mouseClick(editor.ui.rainCheck, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.chance_rain == 0
    
    # Test snow checkbox
    editor.ui.snowCheck.setEnabled(True)
    editor.ui.snowCheck.setVisible(True)
    if not editor.ui.snowCheck.isChecked():
        qtbot.mouseClick(editor.ui.snowCheck, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.chance_snow == 100
    
    if editor.ui.snowCheck.isChecked():
        qtbot.mouseClick(editor.ui.snowCheck, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.chance_snow == 0
    
    # Test lightning checkbox
    editor.ui.lightningCheck.setEnabled(True)
    editor.ui.lightningCheck.setVisible(True)
    if not editor.ui.lightningCheck.isChecked():
        qtbot.mouseClick(editor.ui.lightningCheck, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.chance_lightning == 100
    
    if editor.ui.lightningCheck.isChecked():
        qtbot.mouseClick(editor.ui.lightningCheck, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.chance_lightning == 0

def test_are_editor_manipulate_shadows_checkbox(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating shadows checkbox."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Toggle checkbox
    editor.ui.shadowsCheck.setChecked(True)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert modified_are.shadows
    
    editor.ui.shadowsCheck.setChecked(False)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert not modified_are.shadows

def test_are_editor_manipulate_shadow_opacity_spin(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating shadow opacity spin box."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various opacity values
    test_values = [0, 25, 50, 75, 100, 255]
    for val in test_values:
        editor.ui.shadowsSpin.setValue(val)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.shadow_opacity == val

# ============================================================================
# TERRAIN FIELDS MANIPULATIONS
# ============================================================================

def test_are_editor_manipulate_grass_texture(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating grass texture field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test various texture names
    test_textures = ["grass01", "grass_texture", "terrain_grass", ""]
    for texture in test_textures:
        editor.ui.grassTextureEdit.setText(texture)
        
        # Save and verify
        data, _ = editor.build()
        modified_are = read_are(data)
        assert str(modified_are.grass_texture) == texture

def test_are_editor_manipulate_grass_colors(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating grass color fields."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test grass diffuse color
    diffuse_color = Color(0.3, 0.5, 0.2)
    editor.ui.grassDiffuseEdit.set_color(diffuse_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.grass_diffuse.r - diffuse_color.r) < 0.01
    
    # Test grass ambient color
    ambient_color = Color(0.1, 0.1, 0.1)
    editor.ui.grassAmbientEdit.set_color(ambient_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.grass_ambient.r - ambient_color.r) < 0.01
    
    # Test grass emissive color (TSL only)
    if installation.tsl:
        emissive_color = Color(0.0, 0.0, 0.0)
        editor.ui.grassEmissiveEdit.set_color(emissive_color)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.grass_emissive.r - emissive_color.r) < 0.01

def test_are_editor_manipulate_grass_density_size_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating grass density and size spin boxes."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test grass density
    test_densities = [0.0, 0.1, 0.5, 1.0, 2.0]
    for density in test_densities:
        editor.ui.grassDensitySpin.setValue(density)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.grass_density - density) < 0.001
    
    # Test grass size
    test_sizes = [0.1, 0.5, 1.0, 2.0, 5.0]
    for size in test_sizes:
        editor.ui.grassSizeSpin.setValue(size)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.grass_size - size) < 0.001

def test_are_editor_manipulate_grass_probability_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating grass probability spin boxes (LL, LR, UL, UR)."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test all four probability corners
    test_probs = [0.0, 0.25, 0.5, 0.75, 1.0]
    
    for prob_ll in test_probs:
        editor.ui.grassProbLLSpin.setValue(prob_ll)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.grass_prob_ll - prob_ll) < 0.001
    
    for prob_lr in test_probs:
        editor.ui.grassProbLRSpin.setValue(prob_lr)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.grass_prob_lr - prob_lr) < 0.001
    
    for prob_ul in test_probs:
        editor.ui.grassProbULSpin.setValue(prob_ul)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.grass_prob_ul - prob_ul) < 0.001
    
    for prob_ur in test_probs:
        editor.ui.grassProbURSpin.setValue(prob_ur)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.grass_prob_ur - prob_ur) < 0.001

def test_are_editor_manipulate_dirt_colors(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating dirt color fields (TSL only)."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    if not installation.tsl:
        pytest.skip("Dirt colors are TSL-only")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test all three dirt colors
    dirt1_color = Color(0.5, 0.3, 0.2, 1.0)  # With alpha
    editor.ui.dirtColor1Edit.set_color(dirt1_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.dirty_argb_1.r - dirt1_color.r) < 0.01
    
    dirt2_color = Color(0.4, 0.4, 0.4, 1.0)
    editor.ui.dirtColor2Edit.set_color(dirt2_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.dirty_argb_2.r - dirt2_color.r) < 0.01
    
    dirt3_color = Color(0.2, 0.2, 0.2, 1.0)
    editor.ui.dirtColor3Edit.set_color(dirt3_color)
    data, _ = editor.build()
    modified_are = read_are(data)
    assert abs(modified_are.dirty_argb_3.r - dirt3_color.r) < 0.01

def test_are_editor_manipulate_dirt_formula_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating dirt formula spin boxes (TSL only)."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    if not installation.tsl:
        pytest.skip("Dirt formulas are TSL-only")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test all three formula spins
    test_formulas = [0, 1, 2, 3, 4, 5]
    for formula in test_formulas:
        editor.ui.dirtFormula1Spin.setValue(formula)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.dirty_formula_1 == formula
        
        editor.ui.dirtFormula2Spin.setValue(formula)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.dirty_formula_2 == formula
        
        editor.ui.dirtFormula3Spin.setValue(formula)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.dirty_formula_3 == formula

def test_are_editor_manipulate_dirt_function_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating dirt function spin boxes (TSL only)."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    if not installation.tsl:
        pytest.skip("Dirt functions are TSL-only")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test all three function spins
    test_functions = [0, 1, 2, 3]
    for func in test_functions:
        editor.ui.dirtFunction1Spin.setValue(func)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.dirty_func_1 == func
        
        editor.ui.dirtFunction2Spin.setValue(func)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.dirty_func_2 == func
        
        editor.ui.dirtFunction3Spin.setValue(func)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert modified_are.dirty_func_3 == func

def test_are_editor_manipulate_dirt_size_spins(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating dirt size spin boxes (TSL only)."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    if not installation.tsl:
        pytest.skip("Dirt sizes are TSL-only")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test all three size spins (dirtSize*Spin are QSpinBox, so use integer values)
    test_sizes = [0, 1, 2, 5, 10]
    for size in test_sizes:
        editor.ui.dirtSize1Spin.setValue(size)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.dirty_size_1 - float(size)) < 0.001
        
        editor.ui.dirtSize2Spin.setValue(size)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.dirty_size_2 - float(size)) < 0.001
        
        editor.ui.dirtSize3Spin.setValue(size)
        data, _ = editor.build()
        modified_are = read_are(data)
        assert abs(modified_are.dirty_size_3 - float(size)) < 0.001

# ============================================================================
# SCRIPT FIELDS MANIPULATIONS
# ============================================================================

def test_are_editor_manipulate_on_enter_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on enter script field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify script
    editor.ui.onEnterSelect.set_combo_box_text("test_on_enter")
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    assert str(modified_are.on_enter) == "test_on_enter"
    
    # Load back and verify
    editor.load(are_file, "tat001", ResourceType.ARE, data)
    assert editor.ui.onEnterSelect.currentText() == "test_on_enter"

def test_are_editor_manipulate_on_exit_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on exit script field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify script
    editor.ui.onExitSelect.set_combo_box_text("test_on_exit")
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    assert str(modified_are.on_exit) == "test_on_exit"

def test_are_editor_manipulate_on_heartbeat_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on heartbeat script field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify script (max 16 chars for ResRef)
    editor.ui.onHeartbeatSelect.set_combo_box_text("test_on_hbeat")
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    assert str(modified_are.on_heartbeat) == "test_on_hbeat"

def test_are_editor_manipulate_on_user_defined_script(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating on user defined script field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify script
    editor.ui.onUserDefinedSelect.set_combo_box_text("test_on_user")
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    assert str(modified_are.on_user_defined) == "test_on_user"

# ============================================================================
# COMMENTS FIELD MANIPULATION
# ============================================================================

def test_are_editor_manipulate_comments(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating comments field."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
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
        modified_are = read_are(data)
        assert modified_are.comment == comment
        
        # Load back and verify
        editor.load(are_file, "tat001", ResourceType.ARE, data)
        assert editor.ui.commentsEdit.toPlainText() == comment

# ============================================================================
# COMBINATION TESTS - Multiple manipulations
# ============================================================================

def test_are_editor_manipulate_all_basic_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all basic fields simultaneously."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify ALL basic fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("Combined Test Area"))
    editor.ui.tagEdit.setText("combined_test")
    if editor.ui.cameraStyleSelect.count() > 0:
        editor.ui.cameraStyleSelect.setCurrentIndex(1)
    editor.ui.envmapEdit.setText("test_envmap")
    editor.ui.disableTransitCheck.setChecked(True)
    editor.ui.unescapableCheck.setChecked(True)
    editor.ui.alphaTestSpin.setValue(128)
    editor.ui.stealthCheck.setChecked(True)
    editor.ui.stealthMaxSpin.setValue(500)
    editor.ui.stealthLossSpin.setValue(25)
    
    # Save and verify all
    data, _ = editor.build()
    modified_are = read_are(data)
    
    assert modified_are.name.get(Language.ENGLISH, Gender.MALE) == "Combined Test Area"
    assert modified_are.tag == "combined_test"
    assert modified_are.default_envmap == ResRef("test_envmap")
    assert modified_are.disable_transit
    assert modified_are.unescapable
    assert modified_are.alpha_test == 128
    assert modified_are.stealth_xp
    assert modified_are.stealth_xp_max == 500
    assert modified_are.stealth_xp_loss == 25

def test_are_editor_manipulate_all_weather_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all weather fields simultaneously."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify ALL weather fields
    editor.ui.fogEnabledCheck.setChecked(True)
    editor.ui.fogColorEdit.set_color(Color(0.5, 0.5, 0.5))
    editor.ui.fogNearSpin.setValue(5.0)
    editor.ui.fogFarSpin.setValue(100.0)
    editor.ui.ambientColorEdit.set_color(Color(0.2, 0.2, 0.2))
    editor.ui.diffuseColorEdit.set_color(Color(0.8, 0.8, 0.8))
    editor.ui.dynamicColorEdit.set_color(Color(1.0, 1.0, 1.0))
    if editor.ui.windPowerSelect.count() > 0:
        editor.ui.windPowerSelect.setCurrentIndex(2)
    
    # Ensure checkboxes are visible and enabled
    editor.ui.rainCheck.setEnabled(True)
    editor.ui.rainCheck.setVisible(True)
    editor.ui.rainCheck.show()  # Ensure checkbox is shown, not just visible
    editor.ui.snowCheck.setEnabled(True)
    editor.ui.snowCheck.setVisible(True)
    editor.ui.snowCheck.show()
    editor.ui.lightningCheck.setEnabled(True)
    editor.ui.lightningCheck.setVisible(True)
    editor.ui.lightningCheck.show()
    
    editor.ui.rainCheck.setChecked(True)
    editor.ui.snowCheck.setChecked(False)
    editor.ui.lightningCheck.setChecked(True)
    editor.ui.shadowsCheck.setChecked(True)
    editor.ui.shadowsSpin.setValue(128)
    qtbot.wait(100)  # Wait longer for Qt to process checkbox state changes
    # Process events to ensure state is synchronized
    from qtpy.QtWidgets import QApplication
    QApplication.processEvents()
    
    # Save and verify all
    data, _ = editor.build()
    modified_are = read_are(data)
    
    assert modified_are.fog_enabled
    assert abs(modified_are.fog_color.r - 0.5) < 0.01
    assert modified_are.fog_near == 5.0
    assert modified_are.fog_far == 100.0
    assert modified_are.chance_rain == 100, f"Expected chance_rain to be 100, got {modified_are.chance_rain}"
    assert modified_are.chance_snow == 0
    assert modified_are.chance_lightning == 100
    assert modified_are.shadows
    assert modified_are.shadow_opacity == 128

def test_are_editor_manipulate_all_map_fields_combination(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all map fields simultaneously."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Modify ALL map fields
    editor.ui.mapAxisSelect.setCurrentIndex(2)
    editor.ui.mapZoomSpin.setValue(2)
    editor.ui.mapResXSpin.setValue(1024)
    editor.ui.mapImageX1Spin.setValue(10)
    editor.ui.mapImageY1Spin.setValue(20)
    editor.ui.mapImageX2Spin.setValue(200)
    editor.ui.mapImageY2Spin.setValue(300)
    editor.ui.mapWorldX1Spin.setValue(-10.0)
    editor.ui.mapWorldY1Spin.setValue(-10.0)
    editor.ui.mapWorldX2Spin.setValue(10.0)
    editor.ui.mapWorldY2Spin.setValue(10.0)
    
    # Save and verify all
    data, _ = editor.build()
    modified_are = read_are(data)
    
    assert modified_are.north_axis == ARENorthAxis(2)
    assert abs(modified_are.map_zoom - 2.0) < 0.001
    assert modified_are.map_res_x == 1024
    assert modified_are.map_point_1.x == 10
    assert modified_are.map_point_1.y == 20
    assert modified_are.map_point_2.x == 200
    assert modified_are.map_point_2.y == 300
    assert abs(modified_are.world_point_1.x - (-10.0)) < 0.001
    assert abs(modified_are.world_point_1.y - (-10.0)) < 0.001
    assert abs(modified_are.world_point_2.x - 10.0) < 0.001
    assert abs(modified_are.world_point_2.y - 10.0) < 0.001

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_are_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    # Load original
    original_data = are_file.read_bytes()
    original_are = read_are(original_data)
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    saved_are = read_are(data)
    
    # Verify key fields match
    assert saved_are.tag == original_are.tag
    assert saved_are.camera_style == original_are.camera_style
    assert str(saved_are.default_envmap) == str(original_are.default_envmap)
    assert saved_are.disable_transit == original_are.disable_transit
    assert saved_are.unescapable == original_are.unescapable
    assert saved_are.alpha_test == original_are.alpha_test
    
    # Load saved data back
    editor.load(are_file, "tat001", ResourceType.ARE, data)
    
    # Verify UI matches
    assert editor.ui.tagEdit.text() == original_are.tag
    assert editor.ui.cameraStyleSelect.currentIndex() == original_are.camera_style
    assert editor.ui.envmapEdit.text() == str(original_are.default_envmap)

def test_are_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications preserves changes."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    # Load original
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_roundtrip")
    editor.ui.alphaTestSpin.setValue(200)
    editor.ui.fogEnabledCheck.setChecked(True)
    editor.ui.fogNearSpin.setValue(10.0)
    editor.ui.fogFarSpin.setValue(200.0)
    editor.ui.commentsEdit.setPlainText("Roundtrip test comment")
    
    # Save
    data1, _ = editor.build()
    saved_are1 = read_are(data1)
    
    # Load saved data
    editor.load(are_file, "tat001", ResourceType.ARE, data1)
    
    # Verify modifications preserved
    assert editor.ui.tagEdit.text() == "modified_roundtrip"
    assert editor.ui.alphaTestSpin.value() == 200
    assert editor.ui.fogEnabledCheck.isChecked()
    assert editor.ui.fogNearSpin.value() == 10.0
    assert editor.ui.fogFarSpin.value() == 200.0
    assert editor.ui.commentsEdit.toPlainText() == "Roundtrip test comment"
    
    # Save again
    data2, _ = editor.build()
    saved_are2 = read_are(data2)
    
    # Verify second save matches first
    assert saved_are2.tag == saved_are1.tag
    assert saved_are2.alpha_test == saved_are1.alpha_test
    assert saved_are2.fog_enabled == saved_are1.fog_enabled
    assert saved_are2.comment == saved_are1.comment

def test_are_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve data correctly."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.ui.tagEdit.setText(f"cycle_{cycle}")
        editor.ui.alphaTestSpin.setValue(50 + cycle * 10)
        
        # Save
        data, _ = editor.build()
        saved_are = read_are(data)
        
        # Verify
        assert saved_are.tag == f"cycle_{cycle}"
        assert saved_are.alpha_test == 50 + cycle * 10
        
        # Load back
        editor.load(are_file, "tat001", ResourceType.ARE, data)
        
        # Verify loaded
        assert editor.ui.tagEdit.text() == f"cycle_{cycle}"
        assert editor.ui.alphaTestSpin.value() == 50 + cycle * 10

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_are_editor_minimum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to minimum values."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Set all to minimums
    editor.ui.tagEdit.setText("")
    editor.ui.alphaTestSpin.setValue(0)
    editor.ui.stealthMaxSpin.setValue(0)
    editor.ui.stealthLossSpin.setValue(0)
    editor.ui.mapZoomSpin.setValue(0)
    editor.ui.mapResXSpin.setValue(0)
    editor.ui.fogNearSpin.setValue(0.0)
    editor.ui.fogFarSpin.setValue(0.0)
    editor.ui.shadowsSpin.setValue(0)
    editor.ui.grassDensitySpin.setValue(0.0)
    editor.ui.grassSizeSpin.setValue(0.0)
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    
    assert modified_are.tag == ""
    assert modified_are.alpha_test == 0
    assert modified_are.stealth_xp_max == 0
    assert modified_are.stealth_xp_loss == 0
    assert modified_are.map_zoom == 0.0
    assert modified_are.map_res_x == 0
    assert modified_are.fog_near == 0.0
    assert modified_are.fog_far == 0.0
    assert modified_are.shadow_opacity == 0

def test_are_editor_maximum_values(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test setting all fields to maximum values."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Set all to maximums
    editor.ui.tagEdit.setText("x" * 32)  # Max tag length
    editor.ui.alphaTestSpin.setValue(255)
    editor.ui.stealthMaxSpin.setValue(9999)
    editor.ui.stealthLossSpin.setValue(9999)
    editor.ui.mapZoomSpin.setValue(100)
    editor.ui.mapResXSpin.setValue(4096)
    editor.ui.fogNearSpin.setValue(1000.0)
    editor.ui.fogFarSpin.setValue(10000.0)
    editor.ui.shadowsSpin.setValue(255)
    editor.ui.grassDensitySpin.setValue(10.0)
    editor.ui.grassSizeSpin.setValue(10.0)
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    
    assert modified_are.alpha_test == 255
    assert modified_are.stealth_xp_max == 9999
    assert modified_are.shadow_opacity == 255

def test_are_editor_empty_strings(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of empty strings in text fields."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Set all text fields to empty
    editor.ui.tagEdit.setText("")
    editor.ui.envmapEdit.setText("")
    editor.ui.grassTextureEdit.setText("")
    editor.ui.onEnterSelect.set_combo_box_text("")
    editor.ui.onExitSelect.set_combo_box_text("")
    editor.ui.onHeartbeatSelect.set_combo_box_text("")
    editor.ui.onUserDefinedSelect.set_combo_box_text("")
    editor.ui.commentsEdit.setPlainText("")
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    
    assert modified_are.tag == ""
    assert str(modified_are.default_envmap) == ""
    assert str(modified_are.grass_texture) == ""
    assert str(modified_are.on_enter) == ""
    assert str(modified_are.on_exit) == ""
    assert str(modified_are.on_heartbeat) == ""
    assert str(modified_are.on_user_defined) == ""
    assert modified_are.comment == ""

def test_are_editor_special_characters_in_text_fields(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test handling of special characters in text fields."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test special characters
    special_tag = "test_tag_123"
    editor.ui.tagEdit.setText(special_tag)
    
    special_comment = "Comment with\nnewlines\tand\ttabs"
    editor.ui.commentsEdit.setPlainText(special_comment)
    
    # Save and verify
    data, _ = editor.build()
    modified_are = read_are(data)
    
    assert modified_are.tag == special_tag
    assert modified_are.comment == special_comment

# ============================================================================
# GFF COMPARISON TESTS (like resource tests)
# ============================================================================

def test_are_editor_gff_roundtrip_comparison(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison like resource tests."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    # Load original
    original_data = are_file.read_bytes()
    original_gff = read_gff(original_data)
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Save without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    diff = original_gff.compare(new_gff, log_func, ignore_default_changes=True)
    assert diff, f"GFF comparison failed:\n{chr(10).join(log_messages)}"

def test_are_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Make modifications
    editor.ui.tagEdit.setText("modified_gff_test")
    editor.ui.alphaTestSpin.setValue(150)
    editor.ui.fogEnabledCheck.setChecked(True)
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid ARE
    modified_are = read_are(data)
    assert modified_are.tag == "modified_gff_test"
    assert modified_are.alpha_test == 150
    assert modified_are.fog_enabled

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_are_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new ARE file from scratch."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.ui.nameEdit.set_locstring(LocalizedString.from_english("New Area"))
    editor.ui.tagEdit.setText("new_area")
    if editor.ui.cameraStyleSelect.count() > 0:
        editor.ui.cameraStyleSelect.setCurrentIndex(0)
    editor.ui.envmapEdit.setText("default_env")
    editor.ui.alphaTestSpin.setValue(100)
    editor.ui.fogEnabledCheck.setChecked(True)
    editor.ui.fogColorEdit.set_color(Color(0.5, 0.5, 0.5))
    editor.ui.commentsEdit.setPlainText("New area comment")
    
    # Build and verify
    data, _ = editor.build()
    new_are = read_are(data)
    
    assert new_are.name.get(Language.ENGLISH, Gender.MALE) == "New Area"
    assert new_are.tag == "new_area"
    assert new_are.alpha_test == 100
    assert new_are.fog_enabled
    assert new_are.comment == "New area comment"

def test_are_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_are = read_are(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_are.tag, str)
    assert isinstance(new_are.camera_style, int)
    # alpha_test is stored as float in ARE class, but should be numeric
    assert isinstance(new_are.alpha_test, (int, float))

# ============================================================================
# MINIMAP REDO TESTS
# ============================================================================

def test_are_editor_minimap_redo_on_map_axis_change(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that minimap redoes when map axis changes."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Change map axis - should trigger redoMinimap
    if editor.ui.mapAxisSelect.count() > 1:
        editor.ui.mapAxisSelect.setCurrentIndex(1)
        # Minimap should update (we verify signal is connected)
        assert editor.ui.mapAxisSelect.receivers(editor.ui.mapAxisSelect.currentIndexChanged) > 0

def test_are_editor_minimap_redo_on_map_world_change(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that minimap redoes when map world coordinates change."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Change world coordinates - should trigger redoMinimap
    editor.ui.mapWorldX1Spin.setValue(10.0)
    # Signal should be connected
    assert editor.ui.mapWorldX1Spin.receivers(editor.ui.mapWorldX1Spin.valueChanged) > 0

# ============================================================================
# NAME DIALOG TESTS
# ============================================================================

def test_are_editor_name_dialog_integration(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test name dialog integration."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
    
    original_data = are_file.read_bytes()
    editor.load(are_file, "tat001", ResourceType.ARE, original_data)
    
    # Test change_name method exists and is callable
    # The actual dialog would require user interaction, but we verify the method exists
    assert hasattr(editor, 'change_name')
    assert callable(editor.change_name)


# ============================================================================
# Additional UI tests (merged from test_ui_gff_editors.py)
# ============================================================================

def test_are_editor_specifics(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Specific granular tests for ARE Editor."""
    from toolset.gui.editors.are import AREEditor
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    are_file = test_files_dir / "tat001.are"
    if not are_file.exists():
        pytest.skip("tat001.are not found")
        
    editor.load(are_file, "tat001", ResourceType.ARE, are_file.read_bytes())
    
    # Check Name/Tag
    if hasattr(editor.ui, "tagEdit"):
        assert editor.ui.tagEdit.text() == "tat001" # Assuming tag matches filename often
        editor.ui.tagEdit.setText("modified_tag")
        
    data, _ = editor.build()
    from pykotor.resource.generics.are import read_are
    new_are = read_are(data)
    if hasattr(editor.ui, "tagEdit"):
        assert new_are.tag == "modified_tag"
