from __future__ import annotations

from typing import List, Dict

from PyQt5.QtGui import QImage
from pykotor.common.geometry import Vector3
from pykotor.common.misc import CaseInsensitiveDict
from pykotor.resource.formats.bwm import BWM
from pykotor.resource.generics.utd import UTD


class Kit:
    def __init__(self, name: str):
        self.name: str = name
        self.components: List[KitComponent] = []
        self.doors: List[KitDoor] = []
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.always: Dict[str, bytes] = {}


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
        self.priority: float = height
