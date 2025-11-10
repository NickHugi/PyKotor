"""Panda3D material manager implementation.

References:
----------
    Libraries/PyKotor/src/pykotor/engine/materials/base.py - Abstract interfaces
    vendor/reone/src/libs/graphics/mesh.cpp:100-280 - Material conversion
    vendor/xoreos/src/graphics/aurora/model_kotor.cpp:200-350 - Rendering pipeline
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from panda3d.core import (  # type: ignore[import]
    Shader,
    Texture,
    TextureStage,
    NodePath,
)

from pykotor.engine.materials.base import IMaterial, IMaterialManager

if TYPE_CHECKING:
    from direct.showbase.Loader import Loader  # type: ignore[import]
    from pykotor.resource.formats.mdl.mdl_data import MDLMesh


class Panda3DMaterial(IMaterial):
    """Concrete Panda3D material implementation."""

    def __init__(
        self,
        diffuse_texture: str | None,
        normal_texture: str | None,
        lightmap_texture: str | None,
        has_alpha: bool,
    ):
        self.diffuse_texture_path = diffuse_texture
        self.normal_texture_path = normal_texture
        self.lightmap_texture_path = lightmap_texture
        self.has_alpha = has_alpha

        self.diffuse_texture: Texture | None = None
        self.normal_texture: Texture | None = None
        self.lightmap_texture: Texture | None = None

    def load_resources(self, loader: "Loader", base_path: Path) -> None:
        """Load textures required by this material.

        References:
        ----------
            vendor/reone/src/libs/graphics/texture.cpp:50-100 - Texture loading
            /panda3d/panda3d-docs/programming/texturing/creating-texture - loader.loadTexture()
        """
        if self.diffuse_texture_path:
            tex_file = self._find_texture(base_path, self.diffuse_texture_path)
            if tex_file:
                self.diffuse_texture = loader.loadTexture(str(tex_file))
                if self.diffuse_texture:
                    # /panda3d/panda3d-docs/programming/texturing/texture-filtering
                    self.diffuse_texture.setMinfilter(Texture.FTLinearMipmapLinear)
                    self.diffuse_texture.setMagfilter(Texture.FTLinear)

        if self.normal_texture_path:
            tex_file = self._find_texture(base_path, self.normal_texture_path)
            if tex_file:
                self.normal_texture = loader.loadTexture(str(tex_file))
                if self.normal_texture:
                    self.normal_texture.setMinfilter(Texture.FTLinearMipmapLinear)
                    self.normal_texture.setMagfilter(Texture.FTLinear)

        if self.lightmap_texture_path:
            tex_file = self._find_texture(base_path, self.lightmap_texture_path)
            if tex_file:
                self.lightmap_texture = loader.loadTexture(str(tex_file))
                if self.lightmap_texture:
                    self.lightmap_texture.setMinfilter(Texture.FTLinearMipmapLinear)
                    self.lightmap_texture.setMagfilter(Texture.FTLinear)

    def apply(self, node: NodePath) -> None:
        """Apply loaded textures to the provided node.

        References:
        ----------
            /panda3d/panda3d-docs/programming/shaders/shader-basics.rst - model.setShader()
            /panda3d/panda3d-docs/programming/texturing/texture-modes.rst - TextureStage.MNormal
            /panda3d/panda3d-docs/programming/shaders/coordinate-spaces.rst - setShaderInput()
        """
        if self.diffuse_texture:
            # /panda3d/panda3d-docs/programming/shaders/cg-shader-tutorial/part-1.rst
            node.setTexture(self.diffuse_texture)

        if self.normal_texture:
            normal_stage = TextureStage("normal")
            normal_stage.setMode(TextureStage.MNormal)
            node.setTexture(normal_stage, self.normal_texture)

        if self.lightmap_texture:
            lightmap_stage = TextureStage("lightmap")
            lightmap_stage.setMode(TextureStage.MModulate)
            node.setTexture(lightmap_stage, self.lightmap_texture)

        node.setShaderInput("has_normal_map", bool(self.normal_texture))
        node.setShaderInput("has_lightmap", bool(self.lightmap_texture))
        node.setShaderInput("has_alpha", self.has_alpha)

    @staticmethod
    def _find_texture(base_path: Path, texture_name: str) -> Path | None:
        """Search for a texture file with common extensions."""
        stem = Path(texture_name).stem
        for ext in (".tga", ".png", ".tpc", ".dds", ".jpg"):
            candidate = base_path / f"{stem}{ext}"
            if candidate.exists():
                return candidate
        return None


class Panda3DMaterialManager(IMaterialManager):
    """Material manager responsible for compiling shaders and applying materials."""

    def __init__(self, loader: "Loader", texture_base_path: Path | None = None):
        self.loader = loader
        self.texture_base_path = texture_base_path or Path(".")
        self.shader = self._load_shader()

    def _load_shader(self) -> Shader:
        """Compile the KotOR material shader."""
        shader_dir = Path(__file__).parent
        vert = shader_dir / "kotor_shader.vert"
        frag = shader_dir / "kotor_shader.frag"
        shader = Shader.load(Shader.SL_GLSL, vertex=str(vert), fragment=str(frag))
        if not shader:
            raise RuntimeError("Failed to load KotOR material shader")
        return shader

    def create_material_from_mesh(self, mesh: "MDLMesh") -> Panda3DMaterial:
        """Create a Panda3DMaterial from MDL mesh data."""
        diffuse = mesh.texture_1 if mesh.texture_1 else None
        lightmap = mesh.texture_2 if mesh.has_lightmap and mesh.texture_2 else None
        # TODO: detect normal maps based on naming convention or metadata
        normal = None
        return Panda3DMaterial(diffuse, normal, lightmap, mesh.render)

    def apply_material(self, node: NodePath, material: IMaterial) -> None:
        """Apply shader and material to the node."""
        node.setShader(self.shader)
        if not isinstance(material, Panda3DMaterial):
            raise TypeError("Expected Panda3DMaterial instance")
        material.apply(node)

