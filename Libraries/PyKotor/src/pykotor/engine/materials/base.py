"""Abstract material system base classes.

These interfaces define how materials should be represented and applied within
the engine in a backend-agnostic manner.

References:
----------
    vendor/reone/src/libs/graphics/material.h - Material interfaces
    vendor/xoreos/src/graphics/aurora/material.h - Material abstraction
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol

if False:  # pragma: no cover - typing imports only
    from pykotor.resource.formats.mdl.mdl_data import MDLMesh


class TextureLoader(Protocol):
    """Protocol for resource loaders capable of loading textures/image assets."""

    def load_texture(self, path: str) -> Any:  # pragma: no cover - protocol
        ...


class IMaterial(ABC):
    """Abstract material representation.

    Materials encapsulate all data required to shade a mesh (textures, colours,
    shader parameters, etc.) in a backend-agnostic way.
    """

    @abstractmethod
    def load_resources(self, loader: TextureLoader, base_path: Path) -> None:
        """Load any external resources (textures) required by the material."""

    @abstractmethod
    def apply(self, node: Any) -> None:
        """Apply this material to the provided backend-specific node."""


class IMaterialManager(ABC):
    """Abstract material manager responsible for creating and applying materials."""

    @abstractmethod
    def create_material_from_mesh(self, mesh: "MDLMesh") -> IMaterial:
        """Create a material definition from an MDL mesh."""

    @abstractmethod
    def apply_material(self, node: Any, material: IMaterial) -> None:
        """Apply the provided material to the backend-specific node."""

