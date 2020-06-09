from __future__ import annotations

from enum import IntEnum
from typing import List, Union

from pykotor.data.vertex import Vertex


class WalkmeshType(IntEnum):
    DoorOrPlaceable = 0
    Area = 1


class Material(IntEnum):
    Undefined = 0
    Dirt = 1
    Obscuring = 2
    Grass = 3
    Stone = 4
    Wood = 5
    Water = 6
    NonWalk = 7
    Transparent = 8
    Carpet = 9
    Metal = 10
    Puddles = 11
    Swamp = 12
    Mud = 13
    Leaves = 14
    Lava = 15
    BottomlessPit = 16
    DeepWater = 17
    Door = 18
    NonWalkGrass = 19
    Trigger = 30


class Face:
    def __init__(self):
        self.vertices: List[Vertex] = [Vertex(), Vertex(), Vertex()]
        self.material: Material = Material.Undefined
        self.adjacencies: List[Union[int, Face]] = [-1, -1, -1]


class WOK:
    @staticmethod
    def load_binary(data: bytes) -> WOK:
        return _WOKReader.load(data)

    @staticmethod
    def build_binary(self) -> bytes:
        return _WOKWriter.build(self)

    def __init__(self):
        self.walkmesh_type: WalkmeshType = WalkmeshType.Area
        self.position: Vertex = Vertex()
        self.faces: List[Face] = []


class _WOKReader:
    @staticmethod
    def load(data: bytes) -> WOK:
        pass
        # TODO


class _WOKWriter:
    @staticmethod
    def build(wok: WOK) -> bytes:
        pass
        # TODO
