from __future__ import annotations

import json
from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.geometry import Vector3
from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import BWM, read_bwm
from pykotor.resource.generics.utd import UTD, read_utd
from PyQt5.QtGui import QImage
from toolset.utils.misc import get_nums
from utility.path import Path

if TYPE_CHECKING:
    import os


class Kit:
    def __init__(self, name: str):
        self.name: str = name
        self.components: list[KitComponent] = []
        self.doors: list[KitDoor] = []
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.always: dict[Path, bytes] = {}
        self.side_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.top_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.skyboxes: dict[str, MDLMDXTuple] = {}


class KitComponent:
    def __init__(self, kit: Kit, name: str, image: QImage, bwm: BWM, mdl: bytes, mdx: bytes):
        self.kit: Kit = kit
        self.image: QImage = image
        self.name: str = name
        self.hooks: list[KitComponentHook] = []

        self.bwm: BWM = bwm
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx


class KitComponentHook:
    def __init__(self, position: Vector3, rotation: float, edge: int, door: KitDoor):
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.edge: int = edge
        self.door: KitDoor = door


class KitDoor:
    def __init__(self, utdK1: UTD, utdK2: UTD, width: float, height: float):
        self.utdK1: UTD = utdK1
        self.utdK2: UTD = utdK2
        self.width: float = width
        self.height: float = height


class MDLMDXTuple(NamedTuple):
    mdl: bytes
    mdx: bytes


def load_kits(path: os.PathLike | str) -> list[Kit]:
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
    kits = []

    kits_path = Path(path)
    if not kits_path.exists():
        kits_path.mkdir(parents=True)
    for file in (file for file in kits_path.iterdir() if file.suffix.lower() == ".json"):
        kit_json = json.loads(BinaryReader.load_file(file))
        kit = Kit(kit_json["name"])
        kit_identifier = kit_json["id"]

        always_path = kits_path / file.stem / "always"
        if always_path.exists():
            for always_file in always_path.iterdir():
                kit.always[always_file] = BinaryReader.load_file(always_file)

        textures_path = kits_path / file.stem / "textures"
        for texture_file in (file for file in textures_path.iterdir() if file.suffix.lower() == ".tga"):
            texture = texture_file.stem.upper()
            kit.textures[texture] = BinaryReader.load_file(textures_path / f"{texture}.tga")
            txi_path = textures_path / f"{texture}.txi"
            kit.txis[texture] = BinaryReader.load_file(txi_path) if txi_path.exists() else b""

        lightmaps_path = kits_path / file.stem / "lightmaps"
        for lightmap_file in (file for file in lightmaps_path.iterdir() if file.suffix.lower() == ".tga"):
            lightmap = lightmap_file.stem.upper()
            kit.lightmaps[lightmap] = BinaryReader.load_file(lightmaps_path / f"{lightmap}.tga")
            txi_path = lightmaps_path / f"{lightmap_file.stem}.txi"
            kit.txis[lightmap] = BinaryReader.load_file(txi_path) if txi_path.exists() else b""

        skyboxes_path = kits_path / file.stem / "skyboxes"
        if skyboxes_path.exists():
            for skybox_name in (file.stem.upper() for file in skyboxes_path.safe_iterdir() if file.suffix.lower() == ".mdl"):
                mdl_path = skyboxes_path / f"{skybox_name}.mdl"
                mdx_path = skyboxes_path / f"{skybox_name}.mdx"
                mdl, mdx = BinaryReader.load_file(mdl_path), BinaryReader.load_file(mdx_path)
                kit.skyboxes[skybox_name] = MDLMDXTuple(mdl, mdx)

        doorway_path = kits_path / file.stem / "doorway"
        if doorway_path.exists():
            for padding_id in (file.stem for file in doorway_path.safe_iterdir() if file.suffix.lower() == ".mdl"):
                mdl_path = doorway_path / f"{padding_id}.mdl"
                mdx_path = doorway_path / f"{padding_id}.mdx"
                mdl, mdx = BinaryReader.load_file(mdl_path), BinaryReader.load_file(mdx_path)
                door_id = get_nums(padding_id)[0]
                padding_size = get_nums(padding_id)[1]

                if padding_id.lower().startswith("side"):
                    if door_id not in kit.side_padding:
                        kit.side_padding[door_id] = {}
                    kit.side_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)
                if padding_id.lower().startswith("top"):
                    if door_id not in kit.top_padding:
                        kit.top_padding[door_id] = {}
                    kit.top_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)

        for door_json in kit_json["doors"]:
            utdK1 = read_utd(kits_path / kit_identifier / f'{door_json["utd_k1"]}.utd')
            utdK2 = read_utd(kits_path / kit_identifier / f'{door_json["utd_k2"]}.utd')
            width = door_json["width"]
            height = door_json["height"]
            door = KitDoor(utdK1, utdK2, width, height)
            kit.doors.append(door)

        for component_json in kit_json["components"]:
            name = component_json["name"]
            component_identifier = component_json["id"]

            image = QImage(str(kits_path / kit_identifier / f"{component_identifier}.png")).mirrored()

            bwm = read_bwm(kits_path / kit_identifier / f"{component_identifier}.wok")
            mdl = BinaryReader.load_file(kits_path / kit_identifier / f"{component_identifier}.mdl")
            mdx = BinaryReader.load_file(kits_path / kit_identifier / f"{component_identifier}.mdx")
            component = KitComponent(kit, name, image, bwm, mdl, mdx)

            for hook_json in component_json["doorhooks"]:
                position = Vector3(hook_json["x"], hook_json["y"], hook_json["z"])
                rotation = hook_json["rotation"]
                door = kit.doors[hook_json["door"]]
                edge = hook_json["edge"]
                hook = KitComponentHook(position, rotation, edge, door)
                component.hooks.append(hook)

            kit.components.append(component)

        kits.append(kit)

    return kits
