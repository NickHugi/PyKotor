"""Panda3D implementation of scene graph management.

This module implements the abstract ISceneGraph interface using Panda3D's NodePath system.

References:
----------
    Libraries/PyKotor/src/pykotor/engine/scene/base.py - Abstract interface
    vendor/reone/src/libs/scene/graph.cpp - Reference implementation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from panda3d.core import (
    NodePath,
    AmbientLight,
    DirectionalLight,
    PointLight,
    Vec3,
    Vec4,
)

from pykotor.engine.scene.base import ISceneGraph, FogProperties

if TYPE_CHECKING:
    from panda3d.core import Camera


class Panda3DSceneGraph(ISceneGraph):
    """Panda3D implementation of KotOR scene graph.
    
    This class implements the abstract ISceneGraph interface using Panda3D's
    NodePath system for scene management.
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/engine/scene/base.py:52-181 - ISceneGraph interface
        vendor/reone/src/libs/scene/graph.cpp:30-800 - Reference implementation
    """
    
    def __init__(self, name: str, root: NodePath):
        """Initialize the Panda3D scene graph.
        
        Args:
        ----
            name: Name of this scene graph
            root: Root NodePath to attach scene content to
        """
        super().__init__(name)
        self.root = root
        
        # Model roots
        self._model_roots: list[NodePath] = []
        self._walkmesh_roots: list[NodePath] = []
        
        # Lighting
        self._ambient_light_color: Vec3 = Vec3(0.5, 0.5, 0.5)
        self._ambient_light: NodePath | None = None
        self._dynamic_lights: list[NodePath] = []
        
        # Fog
        self._fog = FogProperties()
        
        # Initialize lighting
        self._setup_default_lighting()
    
    def _setup_default_lighting(self) -> None:
        """Set up default ambient lighting."""
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(
            self._ambient_light_color.x,
            self._ambient_light_color.y,
            self._ambient_light_color.z,
            1.0
        ))
        self._ambient_light = self.root.attachNewNode(ambient)
        self.root.setLight(self._ambient_light)
    
    def clear(self) -> None:
        """Clear all scene graph content."""
        for model_np in self._model_roots:
            model_np.removeNode()
        self._model_roots.clear()
        
        for walkmesh_np in self._walkmesh_roots:
            walkmesh_np.removeNode()
        self._walkmesh_roots.clear()
        
        for light_np in self._dynamic_lights:
            self.root.clearLight(light_np)
            light_np.removeNode()
        self._dynamic_lights.clear()
    
    def update(self, dt: float) -> None:
        """Update the scene graph for the current frame."""
        # Panda3D handles most updates automatically via task system
        pass
    
    def add_model_root(self, model_np: NodePath) -> None:
        """Add a model root to the scene."""
        if model_np not in self._model_roots:
            self._model_roots.append(model_np)
            model_np.reparentTo(self.root)
    
    def remove_model_root(self, model_np: NodePath) -> None:
        """Remove a model root from the scene."""
        if model_np in self._model_roots:
            self._model_roots.remove(model_np)
            model_np.removeNode()
    
    def set_ambient_light_color(self, color: tuple[float, float, float]) -> None:
        """Set the ambient light color."""
        self._ambient_light_color = Vec3(color[0], color[1], color[2])
        if self._ambient_light:
            light = self._ambient_light.node()
            if isinstance(light, AmbientLight):
                light.setColor(Vec4(color[0], color[1], color[2], 1.0))
    
    def add_directional_light(
        self,
        name: str,
        color: tuple[float, float, float],
        direction: tuple[float, float, float]
    ) -> NodePath:
        """Add a directional light to the scene."""
        light = DirectionalLight(name)
        light.setColor(Vec4(color[0], color[1], color[2], 1.0))
        
        light_np = self.root.attachNewNode(light)
        light_np.lookAt(direction[0], direction[1], direction[2])
        
        self.root.setLight(light_np)
        self._dynamic_lights.append(light_np)
        
        return light_np
    
    def add_point_light(
        self,
        name: str,
        color: tuple[float, float, float],
        position: tuple[float, float, float],
        radius: float
    ) -> NodePath:
        """Add a point light to the scene."""
        light = PointLight(name)
        light.setColor(Vec4(color[0], color[1], color[2], 1.0))
        light.setAttenuation(Vec3(1, 0, 0))
        
        light_np = self.root.attachNewNode(light)
        light_np.setPos(position[0], position[1], position[2])
        light.setMaxDistance(radius)
        
        self.root.setLight(light_np)
        self._dynamic_lights.append(light_np)
        
        return light_np
    
    def set_fog(
        self,
        enabled: bool,
        color: tuple[float, float, float] | None = None,
        near: float | None = None,
        far: float | None = None
    ) -> None:
        """Set fog properties for the scene."""
        self._fog.enabled = enabled
        if color is not None:
            self._fog.color = color
        if near is not None:
            self._fog.near_plane = near
        if far is not None:
            self._fog.far_plane = far
    
    def get_fog(self) -> FogProperties:
        """Get current fog properties."""
        return self._fog

