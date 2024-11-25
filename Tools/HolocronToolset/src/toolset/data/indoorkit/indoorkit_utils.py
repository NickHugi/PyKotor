from __future__ import annotations

from typing import TYPE_CHECKING

from toolset.data.indoorkit.indoorkit_base import MDLMDXTuple

if TYPE_CHECKING:
    from pathlib import Path

    from toolset.data.indoorkit import Kit


def process_padding_file(
    kit: Kit,
    doorway_path: Path,  # noqa: ARG001
    padding_id: str,
    door_id: int,
    padding_size: int,
    mdl: bytes,
    mdx: bytes,
) -> None:
    """Process padding file and update kit's padding dictionaries.

    Args:
    ----
        kit: Kit object to update
        doorway_path: Path to the doorway directory
        padding_id: ID of the padding file
        door_id: ID of the door
        padding_size: Size of the padding
        mdl: MDL file contents
        mdx: MDX file contents
    """
    if padding_id.lower().startswith("side"):
        if door_id not in kit.side_padding:
            kit.side_padding[door_id] = {}
        kit.side_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)
    if padding_id.lower().startswith("top"):
        if door_id not in kit.top_padding:
            kit.top_padding[door_id] = {}
        kit.top_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)


def process_texture_file(
    kit: Kit,
    textures_path: Path,
    texture_file: Path,
) -> None:
    """Process texture file and update kit's texture dictionaries.

    Args:
    ----
        kit: Kit object to update
        textures_path: Path to the textures directory
        texture_file: Path to the texture file
    """
    texture: str = texture_file.stem.upper()
    kit.textures[texture] = texture_file.read_bytes()
    txi_path: Path = textures_path / f"{texture}.txi"
    kit.txis[texture] = txi_path.read_bytes() if txi_path.is_file() else b""


def process_lightmap_file(
    kit: Kit,
    lightmaps_path: Path,
    lightmap_file: Path,
) -> None:
    """Process lightmap file and update kit's lightmap dictionaries.

    Args:
    ----
        kit: Kit object to update
        lightmaps_path: Path to the lightmaps directory
        lightmap_file: Path to the lightmap file
    """
    lightmap: str = lightmap_file.stem.upper()
    kit.lightmaps[lightmap] = lightmap_file.read_bytes()
    txi_path: Path = lightmaps_path / f"{lightmap_file.stem}.txi"
    kit.txis[lightmap] = txi_path.read_bytes() if txi_path.is_file() else b""


def process_skybox_file(
    kit: Kit,
    skyboxes_path: Path,
    skybox_resref_str: str,
) -> None:
    """Process skybox file and update kit's skybox dictionary.

    Args:
    ----
        kit: Kit object to update
        skyboxes_path: Path to the skyboxes directory
        skybox_resref_str: Skybox resource reference string
    """
    mdl_path: Path = skyboxes_path / f"{skybox_resref_str}.mdl"
    mdx_path: Path = skyboxes_path / f"{skybox_resref_str}.mdx"
    mdl, mdx = mdl_path.read_bytes(), mdx_path.read_bytes()
    kit.skyboxes[skybox_resref_str] = MDLMDXTuple(mdl, mdx)
