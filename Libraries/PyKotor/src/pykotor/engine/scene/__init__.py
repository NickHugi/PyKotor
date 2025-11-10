"""Abstract scene graph interfaces.

This module provides abstract base classes for scene graph management that can be
implemented by different rendering backends.

References:
----------
    vendor/reone/include/reone/scene/graph.h - SceneGraph interface
"""

from __future__ import annotations

from pykotor.engine.scene.base import ISceneGraph, FogProperties

__all__ = [
    "ISceneGraph",
    "FogProperties",
]

