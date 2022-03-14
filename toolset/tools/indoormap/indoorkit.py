from typing import List

from PyQt5.QtGui import QImage
from pykotor.common.geometry import Vector3
from pykotor.resource.formats.bwm import BWM


class Kit:
    def __init__(self, name: str):
        self.name: str = name
        self.components: List[KitComponent] = []
        self.doors: List[KitDoor] = []


class KitComponent:
    def __init__(self, name: str, image: QImage, bwm: BWM, mdl: bytes, mdx: bytes):
        self.image: QImage = image
        self.name: str = name
        self.hooks: List[KitComponentHook] = []

        self.bwm: BWM = bwm
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx


class KitComponentHook:
    def __init__(self, position: Vector3, rotation: float, edge: int, door: int):
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.edge: int = edge
        self.door: int = door


class KitDoor:
    def __init__(self, name: str, width: float, priority: float):
        self.name: str = name
        self.width: float = width
        self.priority: float = priority
