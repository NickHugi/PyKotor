"""Abstract engine interfaces for PyKotor.

This module provides abstract base classes and interfaces that can be implemented
by different rendering backends (OpenGL, Qt5, Panda3D, etc.).

All backend-specific implementations should inherit from these base classes to ensure
compatibility and code reuse across different rendering systems.

References:
----------
    vendor/reone/include/reone/graphics - Graphics abstraction interfaces
    vendor/xoreos/src/graphics - Graphics backend abstraction
"""

from __future__ import annotations

__all__ = []
