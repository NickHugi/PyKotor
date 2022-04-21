from __future__ import annotations

import json
import os
from typing import List, Dict, Tuple, NamedTuple

from PyQt5.QtGui import QImage
from pykotor.common.geometry import Vector3
from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import BWM, read_bwm
from pykotor.resource.generics.utd import UTD, read_utd

from utils.misc import get_nums


class Kit:
    def __init__(self, name: str):
        self.name: str = name
        self.components: List[KitComponent] = []
        self.doors: List[KitDoor] = []
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.always: Dict[str, bytes] = {}
        self.side_padding: Dict[int, Dict[int, MDLMDXTuple]] = {}
        self.top_padding: Dict[int, Dict[int, MDLMDXTuple]] = {}


class KitComponent:
    def __init__(self, kit: Kit, name: str, image: QImage, bwm: BWM, mdl: bytes, mdx: bytes):
        self.kit: Kit = kit
        self.image: QImage = image
        self.name: str = name
        self.hooks: List[KitComponentHook] = []

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


def load_kits(path: str) -> List[Kit]:
    kits = []

    kits_path = path
    for filename in [filename for filename in os.listdir(kits_path) if filename.endswith(".json")]:
        kit_json = json.loads(BinaryReader.load_file("{}/{}".format(kits_path, filename)))
        kit = Kit(kit_json["name"])
        kit_identifier = kit_json["id"]

        always_path = "{}/{}/always".format(kits_path, filename[:-5])  # -5 used to remove ".json"
        for always_file in os.listdir(always_path):
            kit.always[always_file] = BinaryReader.load_file("{}/{}".format(always_path, always_file))

        textures_path = "{}/{}/textures".format(kits_path, filename[:-5])
        for texture_file in [filename for filename in os.listdir(textures_path) if filename.endswith(".tga")]:
            texture = texture_file[:-4]
            kit.textures[texture] = BinaryReader.load_file("{}/{}.tga".format(textures_path, texture))
            txi_path = "{}/{}.txi".format(textures_path, texture)
            kit.txis[texture] = BinaryReader.load_file(txi_path) if os.path.exists(txi_path) else b''

        lightmaps_path = "{}/{}/lightmaps".format(kits_path, filename[:-5])
        for lightmap_file in [filename for filename in os.listdir(lightmaps_path) if filename.endswith(".tga")]:
            lightmap = lightmap_file[:-4]
            kit.lightmaps[lightmap] = BinaryReader.load_file("{}/{}.tga".format(lightmaps_path, lightmap))
            txi_path = "{}/{}.txi".format(lightmaps_path, lightmap)
            kit.txis[lightmap] = BinaryReader.load_file(txi_path) if os.path.exists(txi_path) else b''

        doorway_path = "{}/{}/doorway".format(kits_path, filename[:-5])
        for padding_id in [filename[:-4] for filename in os.listdir(doorway_path) if filename.endswith(".mdl")]:
            mdl_path = doorway_path + "/" + padding_id + ".mdl"
            mdx_path = doorway_path + "/" + padding_id + ".mdx"
            mdl, mdx = BinaryReader.load_file(mdl_path), BinaryReader.load_file(mdx_path)
            door_id = get_nums(padding_id)[0]
            padding_size = get_nums(padding_id)[1]

            if padding_id.startswith("side"):
                if door_id not in kit.side_padding:
                    kit.side_padding[door_id] = {}
                kit.side_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)
            if padding_id.startswith("top"):
                if door_id not in kit.top_padding:
                    kit.top_padding[door_id] = {}
                kit.top_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)

        for door_json in kit_json["doors"]:
            utdK1 = read_utd("{}/{}/{}.utd".format(kits_path, kit_identifier, door_json["utd_k1"]))
            utdK2 = read_utd("{}/{}/{}.utd".format(kits_path, kit_identifier, door_json["utd_k2"]))
            width = door_json["width"]
            height = door_json["height"]
            door = KitDoor(utdK1, utdK2, width, height)
            kit.doors.append(door)

        for component_json in kit_json["components"]:
            name = component_json["name"]
            component_identifier = component_json["id"]

            image = QImage("{}/{}/{}.png".format(kits_path, kit_identifier, component_identifier)).mirrored()

            bwm = read_bwm("{}/{}/{}.wok".format(kits_path, kit_identifier, component_identifier))
            mdl = BinaryReader.load_file("{}/{}/{}.mdl".format(kits_path, kit_identifier, component_identifier))
            mdx = BinaryReader.load_file("{}/{}/{}.mdx".format(kits_path, kit_identifier, component_identifier))
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
