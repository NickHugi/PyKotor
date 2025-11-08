"""Panda3D-based rendering implementation for KotOR."""
from __future__ import annotations

from pykotor.gl.panda3d.loader import load_mdl, load_tpc
from pykotor.gl.panda3d.scene import KotorRenderer

__all__ = [
    # Main renderer
    "KotorRenderer",

    # MDL/TPC loading
    "load_mdl",
    "load_tpc",
]
