from __future__ import annotations

import json

from pathlib import Path
from typing import TYPE_CHECKING, Any

from qtpy.QtGui import QImage

from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.generics.utd import read_utd
from toolset.data.indoorkit.indoorkit_base import Kit, KitComponent, KitComponentHook, KitDoor, MDLMDXTuple
from toolset.utils.misc import get_nums
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.utd import UTD


def load_kits(  # noqa: C901, PLR0912, PLR0915
    path: os.PathLike | str,
) -> list[Kit]:
    """Loads kits from a given path.

    Args:
    ----
        path: os.PathLike | str: The path to load kits from

    Returns:
    -------
        list[Kit]: A list of loaded Kit objects

    Processing Logic:
    ----------------
        - Loops through files in the path to load kit data
        - Loads kit JSON and populates Kit object
        - Loads always, textures, lightmaps, skyboxes, doors, components
        - Populates KitComponent hooks from JSON
        - Adds loaded Kit to return list.
    """
    kits: list[Kit] = []

    kits_path = Path(path)
    if not kits_path.is_dir():
        kits_path.mkdir(parents=True)
    for file in (
        file
        for file in kits_path.iterdir()
        if file.suffix.lower() == ".json"
    ):
        try:
            kit_json_raw: Any = json.loads(file.read_bytes())
        except json.JSONDecodeError:
            # Skip invalid JSON files
            continue
        
        # Skip files that aren't dicts (e.g., available_kits.json which is a list)
        if not isinstance(kit_json_raw, dict):
            continue
        
        # Skip dicts that don't have required kit fields
        if "name" not in kit_json_raw or "id" not in kit_json_raw:
            continue
        
        kit_json: dict[str, Any] = kit_json_raw
        kit = Kit(kit_json["name"])
        kit_identifier: str = kit_json["id"]

        always_path: Path = kits_path / file.stem / "always"
        if always_path.is_dir():
            for always_file in always_path.iterdir():
                kit.always[always_file] = always_file.read_bytes()

        textures_path: Path = kits_path / file.stem / "textures"
        for texture_file in (file for file in textures_path.iterdir() if file.suffix.lower() == ".tga"):
            texture: str = texture_file.stem.upper()
            kit.textures[texture] = texture_file.read_bytes()
            txi_path: Path = textures_path / f"{texture}.txi"
            kit.txis[texture] = txi_path.read_bytes() if txi_path.is_file() else b""

        lightmaps_path: Path = kits_path / file.stem / "lightmaps"
        for lightmap_file in (file for file in lightmaps_path.iterdir() if file.suffix.lower() == ".tga"):
            lightmap: str = lightmap_file.stem.upper()
            kit.lightmaps[lightmap] = lightmap_file.read_bytes()
            txi_path: Path = lightmaps_path / f"{lightmap_file.stem}.txi"
            kit.txis[lightmap] = txi_path.read_bytes() if txi_path.is_file() else b""

        skyboxes_path: Path = kits_path / file.stem / "skyboxes"
        if skyboxes_path.is_dir():
            for skybox_resref_str in (file.stem.upper() for file in skyboxes_path.iterdir() if file.suffix.lower() == ".mdl"):
                mdl_path: Path = skyboxes_path / f"{skybox_resref_str}.mdl"
                mdx_path: Path = skyboxes_path / f"{skybox_resref_str}.mdx"
                mdl, mdx = mdl_path.read_bytes(), mdx_path.read_bytes()
                kit.skyboxes[skybox_resref_str] = MDLMDXTuple(mdl, mdx)

        doorway_path = kits_path / file.stem / "doorway"
        if doorway_path.is_dir():
            for padding_id in (file.stem for file in doorway_path.iterdir() if file.suffix.lower() == ".mdl"):
                mdl_path = doorway_path / f"{padding_id}.mdl"
                mdx_path = doorway_path / f"{padding_id}.mdx"
                mdl: bytes = mdl_path.read_bytes()
                mdx: bytes = mdx_path.read_bytes()
                door_id: int = get_nums(padding_id)[0]
                padding_size: int = get_nums(padding_id)[1]

                if padding_id.lower().startswith("side"):
                    if door_id not in kit.side_padding:
                        kit.side_padding[door_id] = {}
                    kit.side_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)
                if padding_id.lower().startswith("top"):
                    if door_id not in kit.top_padding:
                        kit.top_padding[door_id] = {}
                    kit.top_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)

        for door_json in kit_json["doors"]:
            utd_k1: UTD = read_utd(kits_path / kit_identifier / f'{door_json["utd_k1"]}.utd')
            utd_k2: UTD = read_utd(kits_path / kit_identifier / f'{door_json["utd_k2"]}.utd')
            width: int = door_json["width"]
            height: int = door_json["height"]
            door: KitDoor = KitDoor(utd_k1, utd_k2, width, height)
            kit.doors.append(door)

        for component_json in kit_json["components"]:
            name = component_json["name"]
            component_identifier = component_json["id"]

            image: QImage = QImage(str(kits_path / kit_identifier / f"{component_identifier}.png")).mirrored()

            bwm: BWM = read_bwm(kits_path / kit_identifier / f"{component_identifier}.wok")
            mdl: bytes = (kits_path / str(kit_identifier) / f"{component_identifier}.mdl").read_bytes()
            mdx: bytes = (kits_path / str(kit_identifier) / f"{component_identifier}.mdx").read_bytes()
            component = KitComponent(kit, name, image, bwm, mdl, mdx)

            for hook_json in component_json["doorhooks"]:
                position: Vector3 = Vector3(hook_json["x"], hook_json["y"], hook_json["z"])
                rotation: float = hook_json["rotation"]
                door: KitDoor = kit.doors[hook_json["door"]]
                edge: str = hook_json["edge"]
                hook: KitComponentHook = KitComponentHook(position, rotation, edge, door)
                component.hooks.append(hook)

            kit.components.append(component)

        kits.append(kit)

    return kits
