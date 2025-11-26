"""Enhanced camera controller for PyKotorGL.

This module provides industry-standard 3D editor camera controls with:
- Orbit mode (rotate around a focal point)
- Pan mode (move camera parallel to view plane)
- Zoom (dolly/scroll wheel)
- Smooth interpolation and input acceleration

Controls design inspired by:
- Blender (middle mouse orbit, shift+middle pan)
- Unity Scene View (alt+left orbit, alt+middle pan, scroll zoom)
- Unreal Engine Viewport controls

Reference implementations:
- reone: src/graphics/camera.cpp
- kotor.js: src/engine/orbitalcamera.ts
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

import glm

from glm import vec3

if TYPE_CHECKING:
    from pykotor.gl.scene import Camera


class CameraMode(Enum):
    """Camera interaction modes."""
    NONE = auto()
    ORBIT = auto()      # Rotate camera around focal point
    PAN = auto()        # Move camera parallel to view plane
    ZOOM = auto()       # Move camera towards/away from focal point
    FLY = auto()        # Free camera movement (WASD style)


@dataclass
class InputState:
    """Current state of input devices for camera control."""
    # Mouse state
    mouse_x: float = 0.0
    mouse_y: float = 0.0
    mouse_delta_x: float = 0.0
    mouse_delta_y: float = 0.0
    scroll_delta: float = 0.0
    
    # Mouse buttons
    left_button: bool = False
    middle_button: bool = False
    right_button: bool = False
    
    # Modifier keys
    shift_held: bool = False
    ctrl_held: bool = False
    alt_held: bool = False
    
    # Movement keys (WASD)
    forward_key: bool = False
    backward_key: bool = False
    left_key: bool = False
    right_key: bool = False
    up_key: bool = False
    down_key: bool = False


@dataclass
class CameraControllerSettings:
    """Settings for camera controller behavior.
    
    All sensitivity values are normalized to 1.0 = default speed.
    """
    # Orbit settings
    orbit_sensitivity: float = 1.0
    orbit_invert_x: bool = False
    orbit_invert_y: bool = False
    
    # Pan settings
    pan_sensitivity: float = 1.0
    pan_invert_x: bool = False
    pan_invert_y: bool = False
    
    # Zoom settings
    zoom_sensitivity: float = 1.0
    zoom_invert: bool = False
    zoom_to_cursor: bool = True  # Zoom towards mouse cursor position
    min_distance: float = 0.5
    max_distance: float = 500.0
    
    # Smoothing settings
    enable_smoothing: bool = True
    smoothing_factor: float = 0.15  # 0 = instant, 1 = very slow
    
    # Acceleration curves
    enable_acceleration: bool = True
    acceleration_power: float = 1.5  # Power curve for input acceleration
    
    # Speed boost (shift key)
    speed_boost_multiplier: float = 3.0
    
    # Fly mode settings
    fly_speed: float = 10.0
    fly_boost_speed: float = 30.0


@dataclass
class CameraState:
    """Internal state for smooth camera transitions."""
    # Target values (what we're interpolating towards)
    target_yaw: float = 0.0
    target_pitch: float = math.pi / 2
    target_distance: float = 10.0
    target_focal_point: vec3 = field(default_factory=lambda: vec3(0, 0, 0))
    
    # Current values (smoothly interpolated)
    current_yaw: float = 0.0
    current_pitch: float = math.pi / 2
    current_distance: float = 10.0
    current_focal_point: vec3 = field(default_factory=lambda: vec3(0, 0, 0))
    
    # Timing
    last_update_time: float = 0.0
    
    def sync_to_camera(self, camera: Camera) -> None:
        """Synchronize state with camera values."""
        self.current_yaw = self.target_yaw = camera.yaw
        self.current_pitch = self.target_pitch = camera.pitch
        self.current_distance = self.target_distance = camera.distance
        # Focal point is where the camera is looking at
        self.current_focal_point = self.target_focal_point = vec3(camera.x, camera.y, camera.z)


class CameraController:
    """Enhanced camera controller with orbit, pan, and zoom modes.
    
    This controller provides smooth, intuitive camera controls similar to
    professional 3D editing software. It supports:
    
    - **Orbit Mode**: Rotate the camera around a focal point (like examining an object)
      - Default: Middle mouse button OR Left mouse button
      - The camera maintains its distance while rotating around the focal point
      
    - **Pan Mode**: Move the camera parallel to the view plane
      - Default: Middle mouse + Shift OR Ctrl + Left mouse
      - Useful for repositioning the view without changing orientation
      
    - **Zoom**: Move closer to or further from the focal point
      - Default: Mouse scroll wheel OR Right mouse drag up/down
      - Can optionally zoom towards the cursor position
      
    - **Fly Mode**: Free camera movement (WASD style)
      - Default: Press 'F' to toggle, then WASD to move
      
    Usage:
        controller = CameraController(camera)
        
        # In your update loop:
        input_state = InputState(
            mouse_delta_x=dx,
            mouse_delta_y=dy,
            middle_button=True,
            # ... etc
        )
        controller.update(input_state, delta_time)
    """
    
    def __init__(
        self,
        camera: Camera,
        settings: CameraControllerSettings | None = None,
    ):
        """Initialize the camera controller.
        
        Args:
            camera: The camera to control.
            settings: Optional settings. Uses defaults if not provided.
        """
        self.camera = camera
        self.settings = settings or CameraControllerSettings()
        self.state = CameraState()
        self.mode = CameraMode.NONE
        
        # Sync initial state
        self.state.sync_to_camera(camera)
        self.state.last_update_time = time.time()
    
    def update(self, input_state: InputState, delta_time: float | None = None) -> None:
        """Update the camera based on input state.
        
        Args:
            input_state: Current input state (mouse, keys, modifiers).
            delta_time: Time since last update. If None, calculates automatically.
        """
        # Calculate delta time
        current_time = time.time()
        if delta_time is None:
            delta_time = current_time - self.state.last_update_time
        self.state.last_update_time = current_time
        
        # Clamp delta time to prevent large jumps
        delta_time = min(delta_time, 0.1)
        
        # Determine active mode based on input
        self._determine_mode(input_state)
        
        # Process input based on mode
        if self.mode == CameraMode.ORBIT:
            self._process_orbit(input_state, delta_time)
        elif self.mode == CameraMode.PAN:
            self._process_pan(input_state, delta_time)
        elif self.mode == CameraMode.ZOOM:
            self._process_zoom_drag(input_state, delta_time)
        elif self.mode == CameraMode.FLY:
            self._process_fly(input_state, delta_time)
        
        # Always process scroll wheel for zoom
        if abs(input_state.scroll_delta) > 0.01:
            self._process_zoom_scroll(input_state)
        
        # Apply smoothing and update camera
        self._apply_smoothing(delta_time)
        self._update_camera()
    
    def _determine_mode(self, input_state: InputState) -> None:
        """Determine the camera mode based on input state."""
        # Priority: Fly > Pan > Zoom > Orbit > None
        
        # Pan: Middle mouse + Shift OR Ctrl + Left mouse
        if (input_state.middle_button and input_state.shift_held) or \
           (input_state.ctrl_held and input_state.left_button):
            self.mode = CameraMode.PAN
            return
        
        # Zoom: Right mouse (drag mode)
        if input_state.right_button and not input_state.shift_held and not input_state.ctrl_held:
            self.mode = CameraMode.ZOOM
            return
        
        # Orbit: Middle mouse (without shift) OR Left mouse (without modifiers)
        if input_state.middle_button and not input_state.shift_held:
            self.mode = CameraMode.ORBIT
            return
        
        if input_state.left_button and not input_state.ctrl_held and not input_state.shift_held and not input_state.alt_held:
            self.mode = CameraMode.ORBIT
            return
        
        # Alt + Left mouse for orbit (Unity/Blender style)
        if input_state.alt_held and input_state.left_button:
            self.mode = CameraMode.ORBIT
            return
        
        # Alt + Middle mouse for pan (Unity/Blender style)
        if input_state.alt_held and input_state.middle_button:
            self.mode = CameraMode.PAN
            return
        
        self.mode = CameraMode.NONE
    
    def _apply_input_acceleration(self, value: float) -> float:
        """Apply acceleration curve to input value.
        
        Makes small movements more precise while allowing fast movements.
        
        Args:
            value: Raw input value.
            
        Returns:
            Accelerated value.
        """
        if not self.settings.enable_acceleration:
            return value
        
        # Apply power curve while preserving sign
        sign = 1 if value >= 0 else -1
        magnitude = abs(value)
        accelerated = math.pow(magnitude, self.settings.acceleration_power)
        return sign * accelerated
    
    def _process_orbit(self, input_state: InputState, delta_time: float) -> None:
        """Process orbit mode input.
        
        Rotates the camera around the focal point while maintaining distance.
        """
        sensitivity = self.settings.orbit_sensitivity * 0.005
        
        # Apply acceleration
        dx = self._apply_input_acceleration(input_state.mouse_delta_x)
        dy = self._apply_input_acceleration(input_state.mouse_delta_y)
        
        # Apply inversion
        if self.settings.orbit_invert_x:
            dx = -dx
        if self.settings.orbit_invert_y:
            dy = -dy
        
        # Update target rotation
        self.state.target_yaw += dx * sensitivity
        self.state.target_pitch += dy * sensitivity
        
        # Clamp pitch to prevent gimbal lock
        self.state.target_pitch = max(0.01, min(math.pi - 0.01, self.state.target_pitch))
        
        # Normalize yaw
        while self.state.target_yaw > math.pi:
            self.state.target_yaw -= 2 * math.pi
        while self.state.target_yaw < -math.pi:
            self.state.target_yaw += 2 * math.pi
    
    def _process_pan(self, input_state: InputState, delta_time: float) -> None:
        """Process pan mode input.
        
        Moves the camera and focal point together parallel to the view plane.
        """
        # Scale sensitivity based on distance (pan speed increases with distance)
        distance_scale = max(0.1, self.state.current_distance * 0.1)
        sensitivity = self.settings.pan_sensitivity * 0.002 * distance_scale
        
        # Apply speed boost
        if input_state.shift_held:
            sensitivity *= self.settings.speed_boost_multiplier
        
        # Apply acceleration
        dx = self._apply_input_acceleration(input_state.mouse_delta_x)
        dy = self._apply_input_acceleration(input_state.mouse_delta_y)
        
        # Apply inversion
        if self.settings.pan_invert_x:
            dx = -dx
        if self.settings.pan_invert_y:
            dy = -dy
        
        # Calculate pan vectors in world space
        # Right vector
        right = vec3(
            math.cos(self.state.current_yaw - math.pi / 2),
            math.sin(self.state.current_yaw - math.pi / 2),
            0,
        )
        
        # Up vector (world up for most intuitive panning)
        up = vec3(0, 0, 1)
        
        # Calculate pan offset
        offset = right * (-dx * sensitivity) + up * (dy * sensitivity)
        
        # Update target focal point
        self.state.target_focal_point = vec3(
            self.state.target_focal_point.x + offset.x,
            self.state.target_focal_point.y + offset.y,
            self.state.target_focal_point.z + offset.z,
        )
    
    def _process_zoom_drag(self, input_state: InputState, delta_time: float) -> None:
        """Process zoom from mouse drag (right mouse button)."""
        sensitivity = self.settings.zoom_sensitivity * 0.01
        
        # Apply speed boost
        if input_state.shift_held:
            sensitivity *= self.settings.speed_boost_multiplier
        
        # Use vertical mouse movement for zoom
        dy = self._apply_input_acceleration(input_state.mouse_delta_y)
        
        if self.settings.zoom_invert:
            dy = -dy
        
        # Calculate new distance
        zoom_delta = dy * sensitivity * self.state.current_distance
        new_distance = self.state.target_distance + zoom_delta
        
        # Clamp to limits
        self.state.target_distance = max(
            self.settings.min_distance,
            min(self.settings.max_distance, new_distance),
        )
    
    def _process_zoom_scroll(self, input_state: InputState) -> None:
        """Process zoom from scroll wheel."""
        sensitivity = self.settings.zoom_sensitivity * 0.1
        
        # Apply speed boost
        if input_state.shift_held:
            sensitivity *= self.settings.speed_boost_multiplier
        
        scroll = input_state.scroll_delta
        
        if self.settings.zoom_invert:
            scroll = -scroll
        
        # Exponential zoom for consistent feel at all distances
        zoom_factor = 1.0 - scroll * sensitivity
        new_distance = self.state.target_distance * zoom_factor
        
        # Clamp to limits
        self.state.target_distance = max(
            self.settings.min_distance,
            min(self.settings.max_distance, new_distance),
        )
    
    def _process_fly(self, input_state: InputState, delta_time: float) -> None:
        """Process fly mode input (WASD movement)."""
        speed = self.settings.fly_speed
        if input_state.shift_held:
            speed = self.settings.fly_boost_speed
        
        # Calculate movement direction
        forward = vec3(
            math.cos(self.state.current_yaw) * math.cos(self.state.current_pitch - math.pi / 2),
            math.sin(self.state.current_yaw) * math.cos(self.state.current_pitch - math.pi / 2),
            math.sin(self.state.current_pitch - math.pi / 2),
        )
        forward = glm.normalize(forward)
        
        right = vec3(
            math.cos(self.state.current_yaw - math.pi / 2),
            math.sin(self.state.current_yaw - math.pi / 2),
            0,
        )
        right = glm.normalize(right)
        
        up = vec3(0, 0, 1)
        
        # Calculate velocity
        velocity = vec3(0, 0, 0)
        if input_state.forward_key:
            velocity = velocity + forward
        if input_state.backward_key:
            velocity = velocity - forward
        if input_state.right_key:
            velocity = velocity + right
        if input_state.left_key:
            velocity = velocity - right
        if input_state.up_key:
            velocity = velocity + up
        if input_state.down_key:
            velocity = velocity - up
        
        # Normalize if moving diagonally
        if glm.length(velocity) > 0.01:
            velocity = glm.normalize(velocity) * speed * delta_time
        
        # Update focal point
        self.state.target_focal_point = vec3(
            self.state.target_focal_point.x + velocity.x,
            self.state.target_focal_point.y + velocity.y,
            self.state.target_focal_point.z + velocity.z,
        )
    
    def _apply_smoothing(self, delta_time: float) -> None:
        """Apply smoothing interpolation to camera values."""
        if not self.settings.enable_smoothing:
            # No smoothing - instant updates
            self.state.current_yaw = self.state.target_yaw
            self.state.current_pitch = self.state.target_pitch
            self.state.current_distance = self.state.target_distance
            self.state.current_focal_point = self.state.target_focal_point
            return
        
        # Calculate smoothing factor based on frame time
        # Higher factor = slower interpolation
        t = 1.0 - math.pow(self.settings.smoothing_factor, delta_time * 60)
        t = max(0.0, min(1.0, t))
        
        # Interpolate rotation
        self.state.current_yaw = self._lerp_angle(
            self.state.current_yaw,
            self.state.target_yaw,
            t,
        )
        self.state.current_pitch = self._lerp(
            self.state.current_pitch,
            self.state.target_pitch,
            t,
        )
        
        # Interpolate distance
        self.state.current_distance = self._lerp(
            self.state.current_distance,
            self.state.target_distance,
            t,
        )
        
        # Interpolate focal point
        self.state.current_focal_point = vec3(
            self._lerp(self.state.current_focal_point.x, self.state.target_focal_point.x, t),
            self._lerp(self.state.current_focal_point.y, self.state.target_focal_point.y, t),
            self._lerp(self.state.current_focal_point.z, self.state.target_focal_point.z, t),
        )
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation between two values."""
        return a + (b - a) * t
    
    def _lerp_angle(self, a: float, b: float, t: float) -> float:
        """Linear interpolation between two angles (handles wraparound)."""
        diff = b - a
        
        # Handle wraparound
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        
        return a + diff * t
    
    def _update_camera(self) -> None:
        """Apply current state to the camera."""
        self.camera.yaw = self.state.current_yaw
        self.camera.pitch = self.state.current_pitch
        self.camera.distance = self.state.current_distance
        self.camera.x = self.state.current_focal_point.x
        self.camera.y = self.state.current_focal_point.y
        self.camera.z = self.state.current_focal_point.z
    
    def set_focal_point(self, x: float, y: float, z: float, *, instant: bool = False) -> None:
        """Set the camera's focal point.
        
        Args:
            x, y, z: World coordinates of the focal point.
            instant: If True, skip smoothing.
        """
        self.state.target_focal_point = vec3(x, y, z)
        if instant:
            self.state.current_focal_point = self.state.target_focal_point
            self._update_camera()
    
    def set_distance(self, distance: float, *, instant: bool = False) -> None:
        """Set the camera distance from focal point.
        
        Args:
            distance: Distance in world units.
            instant: If True, skip smoothing.
        """
        self.state.target_distance = max(
            self.settings.min_distance,
            min(self.settings.max_distance, distance),
        )
        if instant:
            self.state.current_distance = self.state.target_distance
            self._update_camera()
    
    def set_rotation(self, yaw: float, pitch: float, *, instant: bool = False) -> None:
        """Set the camera rotation.
        
        Args:
            yaw: Horizontal rotation in radians.
            pitch: Vertical rotation in radians.
            instant: If True, skip smoothing.
        """
        self.state.target_yaw = yaw
        self.state.target_pitch = max(0.01, min(math.pi - 0.01, pitch))
        if instant:
            self.state.current_yaw = self.state.target_yaw
            self.state.current_pitch = self.state.target_pitch
            self._update_camera()
    
    def focus_on_point(
        self,
        x: float,
        y: float,
        z: float,
        distance: float | None = None,
        *,
        instant: bool = False,
    ) -> None:
        """Move camera to focus on a specific point.
        
        Args:
            x, y, z: World coordinates to focus on.
            distance: Optional distance from the point.
            instant: If True, skip smoothing.
        """
        self.set_focal_point(x, y, z, instant=instant)
        if distance is not None:
            self.set_distance(distance, instant=instant)
    
    def reset_to_default(self) -> None:
        """Reset camera to default position and orientation."""
        self.state.target_yaw = 0.0
        self.state.target_pitch = math.pi / 2
        self.state.target_distance = 10.0
        self.state.target_focal_point = vec3(0, 0, 0)
        self.state.current_yaw = self.state.target_yaw
        self.state.current_pitch = self.state.target_pitch
        self.state.current_distance = self.state.target_distance
        self.state.current_focal_point = self.state.target_focal_point
        self._update_camera()

