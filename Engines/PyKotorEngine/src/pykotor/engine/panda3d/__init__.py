"""Panda3D implementation of PyKotor engine interfaces.

This module contains Panda3D-specific implementations of the abstract engine interfaces
defined in pykotor.engine.

References:
----------
    Libraries/PyKotor/src/pykotor/engine - Abstract interfaces
    vendor/reone - C++ engine architecture
"""

from __future__ import annotations

from pykotor.engine.panda3d.engine import KotorEngine, create_engine
from pykotor.engine.panda3d.scene_graph import Panda3DSceneGraph
from pykotor.engine.panda3d.animation import (
    Panda3DAnimationController,
    Panda3DPositionController,
    Panda3DOrientationController,
    Panda3DScaleController,
    Panda3DColorController,
    Panda3DAlphaController,
    Panda3DAnimationState,
    Panda3DAnimationManager,
    create_panda3d_controller,
)
from pykotor.engine.panda3d.mdl_loader import MDLLoader
from pykotor.engine.panda3d.materials import Panda3DMaterial, Panda3DMaterialManager

__all__ = [
    "KotorEngine",
    "create_engine",
    "Panda3DSceneGraph",
    "Panda3DAnimationController",
    "Panda3DPositionController",
    "Panda3DOrientationController",
    "Panda3DScaleController",
    "Panda3DColorController",
    "Panda3DAlphaController",
    "Panda3DAnimationState",
    "Panda3DAnimationManager",
    "create_panda3d_controller",
    "MDLLoader",
    "Panda3DMaterial",
    "Panda3DMaterialManager",
]
