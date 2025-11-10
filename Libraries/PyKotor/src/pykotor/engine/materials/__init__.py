"""Abstract material system interfaces.

This package defines backend-agnostic interfaces for material handling that can
be implemented by different rendering engines (OpenGL, Qt5, Panda3D, etc.).

References:
----------
    vendor/reone/src/libs/graphics/material.h - Material interfaces
    vendor/xoreos/src/graphics/aurora/renderqueue.h - Material abstraction
"""

from __future__ import annotations

from pykotor.engine.materials.base import IMaterial, IMaterialManager

__all__ = [
    "IMaterial",
    "IMaterialManager",
]

