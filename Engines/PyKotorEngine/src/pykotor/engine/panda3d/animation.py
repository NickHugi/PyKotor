"""Panda3D implementation of animation system.

This module implements the abstract animation interfaces using Panda3D-specific types.

References:
----------
    Libraries/PyKotor/src/pykotor/engine/animation/base.py - Abstract interfaces
    vendor/KotOR.js/src/odyssey/controllers - Controller implementations
    vendor/reone/src/libs/scene/animation - Animation system
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from panda3d.core import NodePath, Vec3, Quat

from pykotor.engine.animation.base import (
    IAnimationController,
    IAnimationState,
    IAnimationManager,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_data import MDL, MDLAnimation, MDLController, MDLControllerRow
    from pykotor.resource.formats.mdl.mdl_types import MDLControllerType


class Panda3DAnimationController(IAnimationController):
    """Base Panda3D animation controller.
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/engine/animation/base.py:23-53 - IAnimationController
        vendor/KotOR.js/src/odyssey/controllers/OdysseyController.ts:18-47 - Base controller
        /panda3d/panda3d-docs/programming/scene-graph/common-state-changes - NodePath transforms
    """
    
    def __init__(self, mdl_controller: MDLController):
        """Initialize the controller.
        
        Args:
        ----
            mdl_controller: MDL controller data from PyKotor
        """
        self.controller_type = mdl_controller.controller_type
        self.is_bezier = mdl_controller.is_bezier
        self.keyframes: list[tuple[float, Any]] = []
        
        # Convert MDL controller rows to keyframes
        for row in mdl_controller.rows:
            value = self._convert_row_data(row)
            self.keyframes.append((row.time, value))
    
    def _convert_row_data(self, row: MDLControllerRow) -> Any:
        """Convert MDL row to controller-specific format."""
        raise NotImplementedError("Subclasses must implement _convert_row_data")
    
    def get_value_at_time(self, time: float) -> Any:
        """Get interpolated value at time."""
        if not self.keyframes:
            return None
        
        if time <= self.keyframes[0][0]:
            return self.keyframes[0][1]
        if time >= self.keyframes[-1][0]:
            return self.keyframes[-1][1]
        
        # Find surrounding keyframes
        last_idx = 0
        for i, (kf_time, _) in enumerate(self.keyframes):
            if kf_time > time:
                break
            last_idx = i
        
        next_idx = min(last_idx + 1, len(self.keyframes) - 1)
        
        last_time, last_value = self.keyframes[last_idx]
        next_time, next_value = self.keyframes[next_idx]
        
        if last_idx == next_idx:
            return last_value
        
        duration = next_time - last_time
        if duration == 0:
            return last_value
        
        factor = (time - last_time) / duration
        
        return self._interpolate(last_value, next_value, factor)
    
    def _interpolate(self, last_value: Any, next_value: Any, factor: float) -> Any:
        """Interpolate between values."""
        raise NotImplementedError("Subclasses must implement _interpolate")


class Panda3DPositionController(Panda3DAnimationController):
    """Position animation controller using Panda3D Vec3.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/PositionController.ts:17-122
        /panda3d/panda3d-docs - NodePath.setPos()
    """
    
    def _convert_row_data(self, row: MDLControllerRow) -> Vec3:
        """Convert to Panda3D Vec3."""
        if len(row.data) >= 3:
            return Vec3(row.data[0], row.data[1], row.data[2])
        return Vec3(0, 0, 0)
    
    def apply(self, node: NodePath, value: Vec3) -> None:
        """Apply position to node.
        
        References:
        ----------
            /panda3d/panda3d-docs - myNodePath.setPos(X, Y, Z)
        """
        node.setPos(value)
    
    def _interpolate(self, last_value: Vec3, next_value: Vec3, factor: float) -> Vec3:
        """Linear interpolation of Vec3.
        
        References:
        ----------
            vendor/KotOR.js/src/odyssey/controllers/PositionController.ts:106-117
        """
        return Vec3(
            last_value.x + (next_value.x - last_value.x) * factor,
            last_value.y + (next_value.y - last_value.y) * factor,
            last_value.z + (next_value.z - last_value.z) * factor,
        )


class Panda3DOrientationController(Panda3DAnimationController):
    """Orientation animation controller using Panda3D Quat.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/OrientationController.ts:17-97
        /panda3d/panda3d-docs - Quaternion and SLERP
    """
    
    def _convert_row_data(self, row: MDLControllerRow) -> Quat:
        """Convert to Panda3D Quat.
        
        References:
        ----------
            /panda3d/panda3d-docs/programming/physics/ode/worlds-bodies-masses - setQuaternion()
            
        Notes:
        -----
            MDL stores quaternions as (x, y, z, w)
            Panda3D Quat constructor is (w, x, y, z)
        """
        if len(row.data) >= 4:
            # Reorder: MDL (x,y,z,w) -> Panda3D Quat(w,x,y,z)
            return Quat(row.data[3], row.data[0], row.data[1], row.data[2])
        return Quat(1, 0, 0, 0)  # Identity
    
    def apply(self, node: NodePath, value: Quat) -> None:
        """Apply orientation to node.
        
        References:
        ----------
            /panda3d/panda3d-docs - LerpQuatInterval accepts Quat
            
        Notes:
        -----
            We convert Quat to HPR for setHpr() since that's the standard API.
        """
        # Convert quaternion to HPR (heading, pitch, roll)
        hpr = value.getHpr()
        node.setHpr(hpr)
    
    def _interpolate(self, last_value: Quat, next_value: Quat, factor: float) -> Quat:
        """Spherical linear interpolation (SLERP).
        
        References:
        ----------
            vendor/KotOR.js/src/odyssey/controllers/OrientationController.ts:86-87
            vendor/reone/src/libs/scene/animation/orientationchannel.cpp:80-90
            
        Notes:
        -----
            Panda3D doesn't have a built-in SLERP method on Quat,
            so we implement it manually.
        """
        # Compute dot product
        dot = (last_value.getR() * next_value.getR() +
               last_value.getI() * next_value.getI() +
               last_value.getJ() * next_value.getJ() +
               last_value.getK() * next_value.getK())
        
        # If dot product is negative, negate one quaternion to take shorter path
        if dot < 0:
            next_value = Quat(-next_value.getR(), -next_value.getI(), 
                             -next_value.getJ(), -next_value.getK())
            dot = -dot
        
        # Clamp dot product
        if dot > 0.9995:
            # Quaternions are very close, use linear interpolation
            result = Quat(
                last_value.getR() + factor * (next_value.getR() - last_value.getR()),
                last_value.getI() + factor * (next_value.getI() - last_value.getI()),
                last_value.getJ() + factor * (next_value.getJ() - last_value.getJ()),
                last_value.getK() + factor * (next_value.getK() - last_value.getK())
            )
            result.normalize()
            return result
        
        # Calculate angle
        import math
        theta_0 = math.acos(dot)
        theta = theta_0 * factor
        
        sin_theta = math.sin(theta)
        sin_theta_0 = math.sin(theta_0)
        
        s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
        s1 = sin_theta / sin_theta_0
        
        return Quat(
            s0 * last_value.getR() + s1 * next_value.getR(),
            s0 * last_value.getI() + s1 * next_value.getI(),
            s0 * last_value.getJ() + s1 * next_value.getJ(),
            s0 * last_value.getK() + s1 * next_value.getK()
        )


class Panda3DScaleController(Panda3DAnimationController):
    """Scale animation controller.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/ScaleController.ts:17-120
        /panda3d/panda3d-docs - NodePath.setScale()
    """
    
    def _convert_row_data(self, row: MDLControllerRow) -> float:
        """Convert to scale float."""
        if row.data:
            return row.data[0]
        return 1.0
    
    def apply(self, node: NodePath, value: float) -> None:
        """Apply scale to node.
        
        References:
        ----------
            /panda3d/panda3d-docs - myNodePath.setScale(S)
        """
        node.setScale(value, value, value)
    
    def _interpolate(self, last_value: float, next_value: float, factor: float) -> float:
        """Linear interpolation of scale."""
        return last_value + (next_value - last_value) * factor


class Panda3DColorController(Panda3DAnimationController):
    """Color animation controller.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/ColorController.ts:17-110
        /panda3d/panda3d-docs - NodePath.setColor()
    """
    
    def _convert_row_data(self, row: MDLControllerRow) -> Vec3:
        """Convert to RGB Vec3."""
        if len(row.data) >= 3:
            return Vec3(row.data[0], row.data[1], row.data[2])
        return Vec3(1, 1, 1)
    
    def apply(self, node: NodePath, value: Vec3) -> None:
        """Apply color to node.
        
        References:
        ----------
            /panda3d/panda3d-docs - nodePath.setColor(r, g, b, a)
        """
        node.setColor(value.x, value.y, value.z, 1.0)
    
    def _interpolate(self, last_value: Vec3, next_value: Vec3, factor: float) -> Vec3:
        """Linear interpolation of color."""
        return Vec3(
            last_value.x + (next_value.x - last_value.x) * factor,
            last_value.y + (next_value.y - last_value.y) * factor,
            last_value.z + (next_value.z - last_value.z) * factor,
        )


class Panda3DAlphaController(Panda3DAnimationController):
    """Alpha/transparency animation controller.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/AlphaController.ts:17-100
        /panda3d/panda3d-docs - NodePath.setAlphaScale()
    """
    
    def _convert_row_data(self, row: MDLControllerRow) -> float:
        """Convert to alpha float."""
        if row.data:
            return row.data[0]
        return 1.0
    
    def apply(self, node: NodePath, value: float) -> None:
        """Apply alpha to node.
        
        References:
        ----------
            /panda3d/panda3d-docs - myNodePath.setAlphaScale(SA)
        """
        node.setAlphaScale(value)
    
    def _interpolate(self, last_value: float, next_value: float, factor: float) -> float:
        """Linear interpolation of alpha."""
        return last_value + (next_value - last_value) * factor


def create_panda3d_controller(mdl_controller: MDLController) -> Panda3DAnimationController | None:
    """Factory function to create appropriate Panda3D controller.
    
    Args:
    ----
        mdl_controller: MDL controller data from PyKotor
    
    Returns:
    -------
        Panda3D-specific controller or None if unsupported
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/OdysseyControllerFactory.ts:36-150
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py:148-206
    """
    from pykotor.resource.formats.mdl.mdl_types import MDLControllerType
    
    controller_map = {
        MDLControllerType.Position: Panda3DPositionController,
        MDLControllerType.Orientation: Panda3DOrientationController,
        MDLControllerType.Scale: Panda3DScaleController,
        MDLControllerType.Color: Panda3DColorController,
        MDLControllerType.SelfIllumColor: Panda3DColorController,
        MDLControllerType.Alpha: Panda3DAlphaController,
    }
    
    controller_class = controller_map.get(mdl_controller.controller_type)
    if controller_class:
        return controller_class(mdl_controller)
    
    return None


class Panda3DAnimationState(IAnimationState):
    """Panda3D animation state implementation.
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/engine/animation/base.py:56-92 - IAnimationState
        vendor/KotOR.js/src/odyssey/OdysseyModelAnimation.ts:25-100
    """
    
    def __init__(self, animation: MDLAnimation, loop: bool = True, speed: float = 1.0):
        """Initialize animation state."""
        self.animation = animation
        self.current_time: float = 0.0
        self.speed: float = speed
        self.loop: bool = loop
        self.is_playing: bool = False
        self.length: float = animation.length
    
    def update(self, dt: float) -> bool:
        """Update animation state."""
        if not self.is_playing:
            return False
        
        self.current_time += dt * self.speed
        
        if self.current_time >= self.length:
            if self.loop:
                self.current_time = self.current_time % self.length
            else:
                self.current_time = self.length
                self.is_playing = False
                return False
        
        return True
    
    def play(self) -> None:
        """Start playing."""
        self.is_playing = True
    
    def pause(self) -> None:
        """Pause playback."""
        self.is_playing = False
    
    def stop(self) -> None:
        """Stop and reset."""
        self.is_playing = False
        self.current_time = 0.0


class Panda3DAnimationManager(IAnimationManager):
    """Panda3D animation manager implementation.
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/engine/animation/base.py:95-181 - IAnimationManager
        vendor/KotOR.js/src/odyssey/OdysseyModelAnimationManager.ts:18-250
    """
    
    def __init__(self, mdl: MDL, root_node: NodePath):
        """Initialize animation manager."""
        self.mdl = mdl
        self.root_node = root_node
        self.current_animation: Panda3DAnimationState | None = None
        
        # Build node map
        self.node_map: dict[str, tuple[Any, NodePath]] = {}
        self._build_node_map(mdl.root_node, root_node)
        
        # Build controllers
        self.animation_controllers: dict[str, dict[str, list[Panda3DAnimationController]]] = {}
        for animation in mdl.animations:
            self._build_controllers_for_animation(animation)
    
    def _build_node_map(self, mdl_node: Any, node_path: NodePath) -> None:
        """Build map from MDL node names to NodePaths."""
        self.node_map[mdl_node.name] = (mdl_node, node_path)
        
        for child_mdl, child_np in zip(mdl_node.children, node_path.getChildren()):
            self._build_node_map(child_mdl, child_np)
    
    def _build_controllers_for_animation(self, animation: MDLAnimation) -> None:
        """Build controllers for animation."""
        animation_name = animation.name
        self.animation_controllers[animation_name] = {}
        self._build_node_controllers(animation.root_node, animation_name)
    
    def _build_node_controllers(self, mdl_node: Any, animation_name: str) -> None:
        """Build controllers for node recursively."""
        node_controllers: list[Panda3DAnimationController] = []
        for mdl_controller in mdl_node.controllers:
            controller = create_panda3d_controller(mdl_controller)
            if controller:
                node_controllers.append(controller)
        
        if node_controllers:
            self.animation_controllers[animation_name][mdl_node.name] = node_controllers
        
        for child in mdl_node.children:
            self._build_node_controllers(child, animation_name)
    
    def play_animation(self, animation_name: str, loop: bool = True, speed: float = 1.0) -> bool:
        """Play animation by name."""
        animation = None
        for anim in self.mdl.animations:
            if anim.name == animation_name:
                animation = anim
                break
        
        if not animation:
            return False
        
        self.current_animation = Panda3DAnimationState(animation, loop, speed)
        self.current_animation.play()
        
        return True
    
    def pause_animation(self) -> None:
        """Pause current animation."""
        if self.current_animation:
            self.current_animation.pause()
    
    def stop_animation(self) -> None:
        """Stop current animation."""
        if self.current_animation:
            self.current_animation.stop()
            self.current_animation = None
    
    def update(self, dt: float) -> None:
        """Update animation for current frame."""
        if not self.current_animation or not self.current_animation.is_playing:
            return
        
        still_playing = self.current_animation.update(dt)
        self._apply_animation()
        
        if not still_playing and not self.current_animation.loop:
            self.current_animation = None
    
    def _apply_animation(self) -> None:
        """Apply current animation state to nodes."""
        if not self.current_animation:
            return
        
        animation_name = self.current_animation.animation.name
        current_time = self.current_animation.current_time
        
        anim_controllers = self.animation_controllers.get(animation_name, {})
        
        for node_name, controllers in anim_controllers.items():
            if node_name not in self.node_map:
                continue
            
            mdl_node, node_path = self.node_map[node_name]
            
            for controller in controllers:
                value = controller.get_value_at_time(current_time)
                if value is not None:
                    controller.apply(node_path, value)
    
    def get_animation_names(self) -> list[str]:
        """Get all animation names."""
        return [anim.name for anim in self.mdl.animations]
    
    def has_animation(self, name: str) -> bool:
        """Check if animation exists."""
        return name in self.animation_controllers

