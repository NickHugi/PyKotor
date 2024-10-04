# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
from __future__ import annotations

import pathlib

from typing import TYPE_CHECKING

import bpy

from loggerplus import RobustLogger

from pykotor.resource.formats.mdl.reference_only.constants import UV_MAP_LIGHTMAP, WALKMESH_MATERIALS
from pykotor.resource.formats.mdl.reference_only.utils import (
    color_to_hex,
    float_to_byte,
    int_to_hex,
    is_aabb_mesh,
    is_not_null,
    is_null,
)
from pykotor.resource.formats.tpc.tpc_auto import read_tpc

if TYPE_CHECKING:
    import os

    from typing_extensions import Literal

    from pykotor.resource.formats.tpc.tpc_data import TPC, TPCGetResult


class NodeName:
    DIFFUSE_TEX: Literal["diffuse_tex"] = "diffuse_tex"
    BUMPMAP_TEX: Literal["bumpmap_tex"] = "bumpmap_tex"
    LIGHTMAP_TEX: Literal["lightmap_tex"] = "lightmap_tex"
    WHITE: Literal["white"] = "white"
    NORMAL_MAP: Literal["normal_map"] = "normal_map"
    MUL_DIFFUSE_LIGHTMAP: Literal["mul_diffuse_lightmap"] = "mul_diffuse_lightmap"
    MUL_DIFFUSE_SELFILLUM: Literal["mul_diffuse_selfillum"] = "mul_diffuse_selfillum"
    DIFFUSE_BSDF: Literal["diffuse_bsdf"] = "diffuse_bsdf"
    DIFF_LM_EMISSION: Literal["diff_lm_emission"] = "diff_lm_emission"
    SELFILLUM_EMISSION: Literal["selfillum_emission"] = "selfillum_emission"
    GLOSSY_BSDF: Literal["glossy_bsdf"] = "glossy_bsdf"
    ADD_DIFFUSE_EMISSION: Literal["add_diffuse_emission"] = "add_diffuse_emission"
    MIX_MATTE_GLOSSY: Literal["mix_matte_glossy"] = "mix_matte_glossy"
    OBJECT_ALPHA: Literal["object_alpha"] = "object_alpha"
    MUL_DIFFUSE_OBJECT_ALPHA: Literal["mul_diffuse_object_alpha"] = "mul_diffuse_object_alpha"
    TRANSPARENT_BSDF: Literal["transparent_bsdf"] = "transparent_bsdf"
    MIX_OPAQUE_TRANSPARENT: Literal["mix_opaque_transparent"] = "mix_opaque_transparent"
    ADD_OPAQUE_TRANSPARENT: Literal["add_opaque_transparent"] = "add_opaque_transparent"


class WalkmeshNodeName:
    COLOR: Literal["color"] = "color"
    OPACITY: Literal["opacity"] = "opacity"


def rebuild_object_materials(
    obj: bpy.types.Object,
    texture_search_paths: list[str] | None = None,
    lightmap_search_paths: list[str] | None = None,
):
    mesh: bpy.types.Mesh = obj.data
    polygon_materials: list[int] = [
        polygon.material_index
        for polygon in mesh.polygons
    ]
    mesh.materials.clear()

    if is_aabb_mesh(obj):
        rebuild_walkmesh_materials(obj)
        mesh.polygons.foreach_set("material_index", polygon_materials)
        return

    material = get_or_create_material(get_material_name(obj))
    mesh.materials.append(material)

    if obj.kb.bitmap == "NULL" and obj.kb.bitmap2 == "NULL":
        rebuild_material_solid(material, obj)
    else:
        rebuild_material_textured(material, obj, texture_search_paths, lightmap_search_paths)


def rebuild_walkmesh_materials(
    obj: bpy.types.Object,
):
    mesh: bpy.types.Mesh = obj.data

    for name, color, _ in WALKMESH_MATERIALS:
        material = get_or_create_material(name)
        material.use_nodes = True
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"

        nodes = material.node_tree.nodes
        nodes.clear()
        links = material.node_tree.links
        links.clear()

        x = 0

        color_node = nodes.new("ShaderNodeRGB")
        color_node.name = WalkmeshNodeName.COLOR
        color_node.location = (x, 300)
        color_node.outputs[0].default_value = [*color, 1.0]

        x += 300

        opacity = nodes.new("ShaderNodeValue")
        opacity.name = WalkmeshNodeName.OPACITY
        opacity.location = (x, 300)
        opacity.outputs[0].default_value = 1.0

        transparent_bsdf = nodes.new("ShaderNodeBsdfTransparent")
        transparent_bsdf.location = (x, 150)
        links.new(transparent_bsdf.inputs["Color"], color_node.outputs[0])

        emission = nodes.new("ShaderNodeEmission")
        emission.location = (x, 0)
        links.new(emission.inputs["Color"], color_node.outputs[0])

        x += 300

        mix_shader = nodes.new("ShaderNodeMixShader")
        mix_shader.location = (x, 0)
        links.new(mix_shader.inputs[0], opacity.outputs[0])
        links.new(mix_shader.inputs[1], transparent_bsdf.outputs[0])
        links.new(mix_shader.inputs[2], emission.outputs[0])

        x += 300

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (x, 0)
        links.new(output.inputs[0], mix_shader.outputs[0])

        mesh.materials.append(material)


def get_or_create_material(name: str) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    return bpy.data.materials.new(name)


def get_material_name(obj: bpy.types.Object) -> str:
    if is_null(obj.kb.bitmap) and is_null(obj.kb.bitmap2):
        diffuse = color_to_hex(obj.kb.diffuse)
        alpha = int_to_hex(float_to_byte(obj.kb.alpha))
        name = f"D{diffuse}__A{alpha}"
    else:
        name = obj.name
    return name


def rebuild_material_solid(
    material: bpy.types.Material,
    obj: bpy.types.Object,
):
    material.use_nodes = False
    material.diffuse_color = [*obj.kb.diffuse, 1.0]


def rebuild_material_textured(
    material: bpy.types.Material,
    obj: bpy.types.Object,
    texture_search_paths: list[str] | None = None,
    lightmap_search_paths: list[str] | None = None,
):
    material.use_nodes = True

    links: bpy.types.NodeLinks = material.node_tree.links
    links.clear()

    nodes: bpy.types.Nodes = material.node_tree.nodes
    nodes.clear()

    x: int = 0
    envmapped: bool = False
    bumpmapped: bool = False
    additive: bool = False
    decal: bool = False

    # Diffuse texture
    if obj.kb.bitmap != "NULL":
        diffuse_tex = nodes.new("ShaderNodeTexImage")
        diffuse_tex.name = NodeName.DIFFUSE_TEX
        diffuse_tex.location = (x, 0)
        diffuse_tex.image = get_or_create_texture(obj.kb.bitmap, texture_search_paths).image
        envmapped = diffuse_tex.image.kb.envmap
        if diffuse_tex.image.kb.bumpmap:
            bumpmapped = True
            bumpmap_tex = nodes.new("ShaderNodeTexImage")
            bumpmap_tex.name = NodeName.BUMPMAP_TEX
            bumpmap_tex.location = (x, 300)
            bumpmap_tex.image = get_or_create_texture(diffuse_tex.image.kb.bumpmap, texture_search_paths).image
            normal_map = nodes.new("ShaderNodeNormalMap")
            normal_map.name = NodeName.NORMAL_MAP
            normal_map.location = (x + 300, 300)
            links.new(normal_map.inputs[1], bumpmap_tex.outputs[0])
        additive = diffuse_tex.image.kb.additive
        decal = diffuse_tex.image.kb.decal

    # Lightmap texture
    if obj.kb.bitmap2 != "NULL":
        lightmap_uv = nodes.new("ShaderNodeUVMap")
        lightmap_uv.location = (x - 300, -300)
        lightmap_uv.uv_map = UV_MAP_LIGHTMAP

        lightmap_tex = nodes.new("ShaderNodeTexImage")
        lightmap_tex.name = NodeName.LIGHTMAP_TEX
        lightmap_tex.location = (x, -300)
        lightmap_tex.image = get_or_create_texture(obj.kb.bitmap2, lightmap_search_paths).image
        links.new(lightmap_tex.inputs[0], lightmap_uv.outputs[0])

    x += 300

    # White color
    white: bpy.types.ShaderNodeRGB = nodes.new("ShaderNodeRGB")
    white.name = NodeName.WHITE
    white.location = (x, 0)
    white.outputs[0].default_value = [1.0] * 4

    # Multiply diffuse color by lightmap color
    mul_diffuse_lightmap: bpy.types.ShaderNodeVectorMath = nodes.new("ShaderNodeVectorMath")
    mul_diffuse_lightmap.name = NodeName.MUL_DIFFUSE_LIGHTMAP
    mul_diffuse_lightmap.location = (x, -300)
    mul_diffuse_lightmap.operation = "MULTIPLY"
    mul_diffuse_lightmap.inputs[1].default_value = [1.0] * 3
    links.new(mul_diffuse_lightmap.inputs[0], diffuse_tex.outputs[0])
    if is_not_null(obj.kb.bitmap2):
        links.new(mul_diffuse_lightmap.inputs[1], lightmap_tex.outputs[0])

    # Multiply diffuse color by self-illumination color
    mul_diffuse_selfillum: bpy.types.ShaderNodeVectorMath = nodes.new("ShaderNodeVectorMath")
    mul_diffuse_selfillum.name = NodeName.MUL_DIFFUSE_SELFILLUM
    mul_diffuse_selfillum.location = (x, -600)
    mul_diffuse_selfillum.operation = "MULTIPLY"
    mul_diffuse_selfillum.inputs[1].default_value = obj.kb.selfillumcolor
    links.new(mul_diffuse_selfillum.inputs[0], diffuse_tex.outputs[0])

    x += 300

    # Diffuse BSDF
    diffuse_bsdf: bpy.types.ShaderNodeBsdfDiffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse_bsdf.name = NodeName.DIFFUSE_BSDF
    diffuse_bsdf.location = (x, 0)
    links.new(diffuse_bsdf.inputs["Color"], diffuse_tex.outputs[0])
    if bumpmapped:
        links.new(diffuse_bsdf.inputs["Normal"], normal_map.outputs[0])

    # Emission from diffuse * lightmap
    diff_lm_emission: bpy.types.ShaderNodeEmission = nodes.new("ShaderNodeEmission")
    diff_lm_emission.name = NodeName.DIFF_LM_EMISSION
    diff_lm_emission.location = (x, -300)
    links.new(diff_lm_emission.inputs["Color"], mul_diffuse_lightmap.outputs[0])

    # Emission from self-illumination
    selfillum_emission: bpy.types.ShaderNodeEmission = nodes.new("ShaderNodeEmission")
    selfillum_emission.name = NodeName.SELFILLUM_EMISSION
    selfillum_emission.location = (x, -600)
    links.new(selfillum_emission.inputs["Color"], mul_diffuse_selfillum.outputs[0])

    x += 300

    # Object alpha
    object_alpha: bpy.types.ShaderNodeValue = nodes.new("ShaderNodeValue")
    object_alpha.name = NodeName.OBJECT_ALPHA
    object_alpha.location = (x, 300)
    object_alpha.outputs[0].default_value = obj.kb.alpha

    # Glossy BSDF
    glossy_bsdf: bpy.types.ShaderNodeBsdfGlossy = nodes.new("ShaderNodeBsdfGlossy")
    glossy_bsdf.name = NodeName.GLOSSY_BSDF
    glossy_bsdf.location = (x, 0)
    glossy_bsdf.inputs["Roughness"].default_value = 0.2
    if bumpmapped:
        links.new(glossy_bsdf.inputs["Normal"], normal_map.outputs[0])

    # Combine diffuse or diffuse * lightmap, and self-illumination emission
    add_diffuse_emission: bpy.types.ShaderNodeAddShader = nodes.new("ShaderNodeAddShader")
    add_diffuse_emission.name = NodeName.ADD_DIFFUSE_EMISSION
    add_diffuse_emission.location = (x, -300)
    if obj.kb.lightmapped:
        links.new(add_diffuse_emission.inputs[0], diff_lm_emission.outputs[0])
    else:
        links.new(add_diffuse_emission.inputs[0], diffuse_bsdf.outputs[0])
    links.new(add_diffuse_emission.inputs[1], selfillum_emission.outputs[0])

    x += 300

    # Multiply diffuse texture alpha by object alpha
    mul_diff_obj_alpha: bpy.types.ShaderNodeMath = nodes.new("ShaderNodeMath")
    mul_diff_obj_alpha.name = NodeName.MUL_DIFFUSE_OBJECT_ALPHA
    mul_diff_obj_alpha.operation = "MULTIPLY"
    mul_diff_obj_alpha.location = (x, 300)
    mul_diff_obj_alpha.inputs[1].default_value = 1.0
    links.new(mul_diff_obj_alpha.inputs[0], object_alpha.outputs[0])
    if not envmapped and not bumpmapped:
        links.new(mul_diff_obj_alpha.inputs[1], diffuse_tex.outputs[1])

    # Transparent BSDF
    transparent_bsdf: bpy.types.ShaderNodeBsdfTransparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent_bsdf.name = NodeName.TRANSPARENT_BSDF
    transparent_bsdf.location = (x, 0)

    # Mix matte and glossy
    mix_matte_glossy: bpy.types.ShaderNodeMixShader = nodes.new("ShaderNodeMixShader")
    mix_matte_glossy.name = NodeName.MIX_MATTE_GLOSSY
    mix_matte_glossy.location = (x, -300)
    mix_matte_glossy.inputs[0].default_value = 1.0
    if envmapped:
        links.new(mix_matte_glossy.inputs[0], diffuse_tex.outputs[1])
    links.new(mix_matte_glossy.inputs[1], glossy_bsdf.outputs[0])
    links.new(mix_matte_glossy.inputs[2], add_diffuse_emission.outputs[0])

    x += 300

    # Add opaque and transparent
    add_opaque_transparent: bpy.types.ShaderNodeAddShader = nodes.new("ShaderNodeAddShader")
    add_opaque_transparent.name = NodeName.ADD_OPAQUE_TRANSPARENT
    add_opaque_transparent.location = (x, 0)
    links.new(add_opaque_transparent.inputs[0], transparent_bsdf.outputs[0])
    links.new(add_opaque_transparent.inputs[1], mix_matte_glossy.outputs[0])

    # Mix opaque and transparent
    mix_opaque_transparent: bpy.types.ShaderNodeMixShader = nodes.new("ShaderNodeMixShader")
    mix_opaque_transparent.name = NodeName.MIX_OPAQUE_TRANSPARENT
    mix_opaque_transparent.location = (x, -300)
    links.new(mix_opaque_transparent.inputs[0], mul_diff_obj_alpha.outputs[0])
    links.new(mix_opaque_transparent.inputs[1], transparent_bsdf.outputs[0])
    links.new(mix_opaque_transparent.inputs[2], mix_matte_glossy.outputs[0])

    x += 300

    # Material output node
    material_output: bpy.types.ShaderNodeOutputMaterial = nodes.new("ShaderNodeOutputMaterial")
    material_output.location = (x, 0)
    if additive:
        links.new(
            input=material_output.inputs[0],
            output=add_opaque_transparent.outputs[0],
            verify_limits=False,
        )
    else:
        links.new(
            input=material_output.inputs[0],
            output=mix_opaque_transparent.outputs[0],
            verify_limits=False,
        )

    material.use_backface_culling = not decal
    material.blend_method = "BLEND" if additive else "HASHED"


def get_or_create_texture(
    name: str,
    search_paths: list[str] | None = None,
) -> bpy.types.Texture:
    if name in bpy.data.textures:
        return bpy.data.textures[name]

    if name in bpy.data.images:
        image = bpy.data.images[name]
    else:
        image = create_image(name, search_paths)

    texture = bpy.data.textures.new(name, type="IMAGE")
    texture.image = image
    texture.use_fake_user = True

    return texture


def create_image(
    name: str,
    search_paths: list[os.PathLike | str],
) -> bpy.types.Image:
    for search_path in search_paths:
        search_path_obj = pathlib.Path(search_path)
        if not search_path_obj.exists():
            continue
        for path in search_path_obj.iterdir():
            if (
                path.exists()
                and path.is_file()
                and path.suffix.lower().strip() in {".tga", ".tpc"}
            ):
                RobustLogger().info(f"Loading image: '{path}'")
                tpc: TPC = read_tpc(path)
                tpc_data: TPCGetResult = tpc.get()
                image = bpy.data.images.new(name, tpc._width, tpc._height)  # noqa: SLF001
                image.pixels = [float(x) / 255 for x in tpc_data.data].as_array()
                image.update()
                apply_txi_to_image(tpc.txi, image)
                return image

    return bpy.data.images.new(name, 512, 512)


def apply_txi_to_image(
    txi: str,
    image: bpy.types.Image,
):
    for line in txi:
        tokens = line.split()
        if not tokens:
            continue
        lower_token = tokens[0]
        if lower_token in {"envmaptexture", "bumpyshinytexture"}:
            image.kb.envmap = tokens[1]
        elif lower_token == "bumpmaptexture":  # noqa: S105
            image.kb.bumpmap = tokens[1]
        elif lower_token == "blending":  # noqa: S105
            image.kb.additive = tokens[1].lower() == "additive"
        elif lower_token == "decal":  # noqa: S105
            image.kb.decal = bool(int(tokens[1]))


def get_or_create_material(name: str) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    return bpy.data.materials.new(name)


def get_or_create_image(
    name: str,
    width: int = 512,
    height: int = 512,
    *,
    alpha: bool = False,
    float_buffer: bool = False,
    stereo3d: bool = False,
    is_data: bool = False,
    tiled: bool = False,
) -> bpy.types.Image:
    if name in bpy.data.images:
        return bpy.data.images[name]
    return bpy.data.images.new(
        name=name,
        width=width,
        height=height,
        alpha=alpha,
        float_buffer=float_buffer,
        stereo3d=stereo3d,
        is_data=is_data,
        tiled=tiled,
    )
