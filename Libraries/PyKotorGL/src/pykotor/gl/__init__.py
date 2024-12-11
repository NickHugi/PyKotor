"""PyKotorGL - Panda3D-based rendering for KotOR."""
from __future__ import annotations

from pykotor.gl.panda3d import (
    KotorRenderer,
    load_mdl,
    load_tpc,
)

__all__ = [
    # Main renderer
    "KotorRenderer",

    # MDL/TPC loading
    "load_mdl",
    "load_tpc",
]

