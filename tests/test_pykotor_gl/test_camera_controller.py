"""Tests for the enhanced camera controller.

These tests ensure that:
1. Camera modes are correctly determined from input
2. Orbit, pan, and zoom operations work correctly
3. Input smoothing and acceleration work as expected
4. Edge cases and boundary conditions are handled

The camera controller is critical for the user experience in the 3D level editor,
providing intuitive and smooth camera controls.
"""

from __future__ import annotations

import math
import unittest

from glm import vec3

from pykotor.gl.scene.camera import Camera
from pykotor.gl.scene.camera_controller import (
    CameraController,
    CameraControllerSettings,
    CameraMode,
    CameraState,
    InputState,
)


class TestInputState(unittest.TestCase):
    """Tests for the InputState dataclass."""
    
    def test_default_values(self):
        """Test that InputState has correct default values."""
        state = InputState()
        
        self.assertEqual(state.mouse_x, 0.0)
        self.assertEqual(state.mouse_y, 0.0)
        self.assertEqual(state.mouse_delta_x, 0.0)
        self.assertEqual(state.mouse_delta_y, 0.0)
        self.assertEqual(state.scroll_delta, 0.0)
        
        self.assertFalse(state.left_button)
        self.assertFalse(state.middle_button)
        self.assertFalse(state.right_button)
        
        self.assertFalse(state.shift_held)
        self.assertFalse(state.ctrl_held)
        self.assertFalse(state.alt_held)
        
        self.assertFalse(state.forward_key)
        self.assertFalse(state.backward_key)
        self.assertFalse(state.left_key)
        self.assertFalse(state.right_key)
        self.assertFalse(state.up_key)
        self.assertFalse(state.down_key)


class TestCameraControllerSettings(unittest.TestCase):
    """Tests for the CameraControllerSettings dataclass."""
    
    def test_default_values(self):
        """Test that settings have reasonable defaults."""
        settings = CameraControllerSettings()
        
        self.assertEqual(settings.orbit_sensitivity, 1.0)
        self.assertEqual(settings.pan_sensitivity, 1.0)
        self.assertEqual(settings.zoom_sensitivity, 1.0)
        
        self.assertFalse(settings.orbit_invert_x)
        self.assertFalse(settings.orbit_invert_y)
        
        self.assertTrue(settings.enable_smoothing)
        self.assertTrue(settings.enable_acceleration)
        
        self.assertGreater(settings.speed_boost_multiplier, 1.0)
    
    def test_custom_settings(self):
        """Test that custom settings are applied."""
        settings = CameraControllerSettings(
            orbit_sensitivity=2.0,
            pan_sensitivity=0.5,
            enable_smoothing=False,
        )
        
        self.assertEqual(settings.orbit_sensitivity, 2.0)
        self.assertEqual(settings.pan_sensitivity, 0.5)
        self.assertFalse(settings.enable_smoothing)


class TestCameraState(unittest.TestCase):
    """Tests for the CameraState dataclass."""
    
    def test_default_values(self):
        """Test that CameraState has correct default values."""
        state = CameraState()
        
        self.assertEqual(state.target_yaw, 0.0)
        self.assertEqual(state.target_pitch, math.pi / 2)
        self.assertEqual(state.target_distance, 10.0)
    
    def test_sync_to_camera(self):
        """Test that state syncs correctly with camera."""
        camera = Camera()
        camera.x = 10.0
        camera.y = 20.0
        camera.z = 5.0
        camera.yaw = 1.5
        camera.pitch = 1.0
        camera.distance = 15.0
        
        state = CameraState()
        state.sync_to_camera(camera)
        
        self.assertEqual(state.target_yaw, 1.5)
        self.assertEqual(state.target_pitch, 1.0)
        self.assertEqual(state.target_distance, 15.0)
        self.assertEqual(state.target_focal_point.x, 10.0)
        self.assertEqual(state.target_focal_point.y, 20.0)
        self.assertEqual(state.target_focal_point.z, 5.0)
        
        # Current values should also be synced
        self.assertEqual(state.current_yaw, state.target_yaw)
        self.assertEqual(state.current_pitch, state.target_pitch)
        self.assertEqual(state.current_distance, state.target_distance)


class TestCameraController(unittest.TestCase):
    """Tests for the CameraController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.camera = Camera()
        self.camera.x = 0.0
        self.camera.y = 0.0
        self.camera.z = 0.0
        self.camera.yaw = 0.0
        self.camera.pitch = math.pi / 2
        self.camera.distance = 10.0
        
        self.controller = CameraController(self.camera)
    
    def test_initialization(self):
        """Test that controller initializes correctly."""
        self.assertIsNotNone(self.controller.camera)
        self.assertIsNotNone(self.controller.settings)
        self.assertIsNotNone(self.controller.state)
        self.assertEqual(self.controller.mode, CameraMode.NONE)
    
    def test_mode_detection_orbit_middle_mouse(self):
        """Test that middle mouse triggers orbit mode."""
        input_state = InputState(middle_button=True)
        self.controller._determine_mode(input_state)
        
        self.assertEqual(self.controller.mode, CameraMode.ORBIT)
    
    def test_mode_detection_orbit_left_mouse(self):
        """Test that left mouse triggers orbit mode."""
        input_state = InputState(left_button=True)
        self.controller._determine_mode(input_state)
        
        self.assertEqual(self.controller.mode, CameraMode.ORBIT)
    
    def test_mode_detection_orbit_alt_left(self):
        """Test that Alt+Left mouse triggers orbit mode."""
        input_state = InputState(alt_held=True, left_button=True)
        self.controller._determine_mode(input_state)
        
        self.assertEqual(self.controller.mode, CameraMode.ORBIT)
    
    def test_mode_detection_pan_shift_middle(self):
        """Test that Shift+Middle mouse triggers pan mode."""
        input_state = InputState(middle_button=True, shift_held=True)
        self.controller._determine_mode(input_state)
        
        self.assertEqual(self.controller.mode, CameraMode.PAN)
    
    def test_mode_detection_pan_ctrl_left(self):
        """Test that Ctrl+Left mouse triggers pan mode."""
        input_state = InputState(ctrl_held=True, left_button=True)
        self.controller._determine_mode(input_state)
        
        self.assertEqual(self.controller.mode, CameraMode.PAN)
    
    def test_mode_detection_zoom_right_mouse(self):
        """Test that right mouse triggers zoom mode."""
        input_state = InputState(right_button=True)
        self.controller._determine_mode(input_state)
        
        self.assertEqual(self.controller.mode, CameraMode.ZOOM)
    
    def test_mode_detection_none(self):
        """Test that no input results in NONE mode."""
        input_state = InputState()
        self.controller._determine_mode(input_state)
        
        self.assertEqual(self.controller.mode, CameraMode.NONE)
    
    def test_orbit_changes_rotation(self):
        """Test that orbit mode changes camera rotation."""
        initial_yaw = self.controller.state.target_yaw
        initial_pitch = self.controller.state.target_pitch
        
        # Simulate orbit input
        input_state = InputState(
            middle_button=True,
            mouse_delta_x=50.0,
            mouse_delta_y=30.0,
        )
        
        self.controller.update(input_state, delta_time=0.016)
        
        # Values should have changed
        self.assertNotEqual(self.controller.state.target_yaw, initial_yaw)
        self.assertNotEqual(self.controller.state.target_pitch, initial_pitch)
    
    def test_pan_changes_position(self):
        """Test that pan mode changes camera position."""
        initial_focal = vec3(
            self.controller.state.target_focal_point.x,
            self.controller.state.target_focal_point.y,
            self.controller.state.target_focal_point.z,
        )
        
        # Simulate pan input
        input_state = InputState(
            middle_button=True,
            shift_held=True,
            mouse_delta_x=50.0,
            mouse_delta_y=30.0,
        )
        
        self.controller.update(input_state, delta_time=0.016)
        
        # Position should have changed
        final_focal = self.controller.state.target_focal_point
        position_changed = (
            final_focal.x != initial_focal.x or
            final_focal.y != initial_focal.y or
            final_focal.z != initial_focal.z
        )
        self.assertTrue(position_changed, "Pan should change focal point")
    
    def test_zoom_scroll_changes_distance(self):
        """Test that scroll wheel changes camera distance."""
        initial_distance = self.controller.state.target_distance
        
        # Simulate scroll input
        input_state = InputState(scroll_delta=120.0)
        
        self.controller.update(input_state, delta_time=0.016)
        
        # Distance should have changed
        self.assertNotEqual(
            self.controller.state.target_distance,
            initial_distance,
            "Scroll should change distance"
        )
    
    def test_zoom_clamps_to_limits(self):
        """Test that zoom respects min/max distance limits."""
        # Try to zoom way out
        input_state = InputState(scroll_delta=-10000.0)
        self.controller.update(input_state, delta_time=0.016)
        
        self.assertLessEqual(
            self.controller.state.target_distance,
            self.controller.settings.max_distance,
        )
        
        # Try to zoom way in
        input_state = InputState(scroll_delta=10000.0)
        self.controller.update(input_state, delta_time=0.016)
        
        self.assertGreaterEqual(
            self.controller.state.target_distance,
            self.controller.settings.min_distance,
        )
    
    def test_pitch_clamps_to_limits(self):
        """Test that pitch doesn't go beyond limits (prevent gimbal lock)."""
        # Try extreme upward rotation
        input_state = InputState(
            middle_button=True,
            mouse_delta_y=-10000.0,
        )
        self.controller.update(input_state, delta_time=0.016)
        
        # Pitch should be clamped near 0 (but not exactly 0)
        self.assertGreater(self.controller.state.target_pitch, 0.001)
        
        # Try extreme downward rotation
        input_state = InputState(
            middle_button=True,
            mouse_delta_y=10000.0,
        )
        self.controller.update(input_state, delta_time=0.016)
        
        # Pitch should be clamped near pi (but not exactly pi)
        self.assertLess(self.controller.state.target_pitch, math.pi - 0.001)
    
    def test_smoothing_interpolates_values(self):
        """Test that smoothing creates gradual transitions."""
        settings = CameraControllerSettings(
            enable_smoothing=True,
            smoothing_factor=0.5,  # Significant smoothing
        )
        controller = CameraController(self.camera, settings)
        
        # Set a target position far from current
        controller.state.target_focal_point = vec3(100, 100, 100)
        controller.state.current_focal_point = vec3(0, 0, 0)
        
        # Apply smoothing with a frame update
        controller._apply_smoothing(0.016)
        
        # Current should move towards target, but not reach it
        current = controller.state.current_focal_point
        self.assertGreater(current.x, 0)
        self.assertLess(current.x, 100)
    
    def test_no_smoothing_instant_update(self):
        """Test that disabling smoothing gives instant updates."""
        settings = CameraControllerSettings(enable_smoothing=False)
        controller = CameraController(self.camera, settings)
        
        # Set a target position far from current
        controller.state.target_focal_point = vec3(100, 100, 100)
        controller.state.current_focal_point = vec3(0, 0, 0)
        
        # Apply smoothing with a frame update
        controller._apply_smoothing(0.016)
        
        # Current should instantly match target
        current = controller.state.current_focal_point
        self.assertEqual(current.x, 100)
        self.assertEqual(current.y, 100)
        self.assertEqual(current.z, 100)
    
    def test_input_acceleration(self):
        """Test that input acceleration works correctly."""
        settings = CameraControllerSettings(
            enable_acceleration=True,
            acceleration_power=2.0,  # Quadratic acceleration
        )
        controller = CameraController(self.camera, settings)
        
        # Small input should stay linear
        small_result = controller._apply_input_acceleration(1.0)
        self.assertAlmostEqual(small_result, 1.0, places=2)
        
        # Large input should be amplified
        large_result = controller._apply_input_acceleration(10.0)
        # With power=2.0, result should be larger than linear
        self.assertGreater(large_result, 10.0)
        
        # Negative values should preserve sign
        negative_result = controller._apply_input_acceleration(-5.0)
        self.assertLess(negative_result, 0)
    
    def test_focus_on_point(self):
        """Test that focus_on_point moves camera to target."""
        self.controller.focus_on_point(50, 60, 70, distance=20.0, instant=True)
        
        self.assertEqual(self.controller.state.target_focal_point.x, 50)
        self.assertEqual(self.controller.state.target_focal_point.y, 60)
        self.assertEqual(self.controller.state.target_focal_point.z, 70)
        self.assertEqual(self.controller.state.target_distance, 20.0)
    
    def test_reset_to_default(self):
        """Test that reset_to_default resets camera state."""
        # Change camera state
        self.controller.state.target_yaw = 5.0
        self.controller.state.target_pitch = 2.0
        self.controller.state.target_distance = 100.0
        
        # Reset
        self.controller.reset_to_default()
        
        # Verify reset
        self.assertEqual(self.controller.state.target_yaw, 0.0)
        self.assertEqual(self.controller.state.target_pitch, math.pi / 2)
        self.assertEqual(self.controller.state.target_distance, 10.0)
    
    def test_camera_is_updated(self):
        """Test that camera values are updated after controller update."""
        # Disable smoothing for immediate updates
        self.controller.settings.enable_smoothing = False
        
        # Change focal point
        self.controller.set_focal_point(25, 35, 45, instant=True)
        
        # Camera should be updated
        self.assertEqual(self.camera.x, 25)
        self.assertEqual(self.camera.y, 35)
        self.assertEqual(self.camera.z, 45)


class TestCameraModeEnum(unittest.TestCase):
    """Tests for the CameraMode enum."""
    
    def test_all_modes_exist(self):
        """Test that all expected modes exist."""
        self.assertIsNotNone(CameraMode.NONE)
        self.assertIsNotNone(CameraMode.ORBIT)
        self.assertIsNotNone(CameraMode.PAN)
        self.assertIsNotNone(CameraMode.ZOOM)
        self.assertIsNotNone(CameraMode.FLY)
    
    def test_modes_are_distinct(self):
        """Test that all modes have distinct values."""
        modes = [
            CameraMode.NONE,
            CameraMode.ORBIT,
            CameraMode.PAN,
            CameraMode.ZOOM,
            CameraMode.FLY,
        ]
        values = [m.value for m in modes]
        self.assertEqual(len(values), len(set(values)))


if __name__ == "__main__":
    unittest.main()

