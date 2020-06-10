from __future__ import annotations

from typing import List

from pykotor.data.quaternion import Quaternion
from pykotor.data.vertex import Vertex


class LYT:
    @staticmethod
    def load(data: str) -> LYT:
        return _LYTReader.load(data)

    def build(self) -> str:
        return _LYTWriter.build(self)

    def __init__(self):
        self.rooms: List[Room] = []
        self.doors: List[Door] = []
        self.obstacles: List[SwoopObstacle] = []
        self.tracks: List[SwoopTrack] = []


class Room:
    @staticmethod
    def new(model: str, x: float, y: float, z: float):
        room = Room()
        room.model = model
        room.position = Vertex.from_position(x, y, z)
        return room

    def __init__(self):
        self.model: str = ""
        self.position: Vertex = Vertex()


class Door:
    @staticmethod
    def new(model: str, name: str, px: float, py: float, pz: float, qx: float, qy: float, qz: float, qw: float):
        door = Door()
        door.model = model
        door.name = name
        door.position = Vertex.from_position(px, py, pz)
        door.orientation = Quaternion.from_rotation(qx, qy, qz, qw)
        return door

    def __init__(self):
        self.model: str = ""
        self.name: str = ""
        self.unknown: int = 0
        self.position: Vertex = Vertex()
        self.orientation: Quaternion = Quaternion()


class SwoopObstacle:
    @staticmethod
    def new(name: str, x: float, y: float, z: float):
        swoop = SwoopObstacle()
        swoop.name = name
        swoop.position = Vertex.from_position(x, y, z)
        return swoop

    def __init__(self):
        self.name: str = ""
        self.position: Vertex = Vertex()


class SwoopTrack:
    @staticmethod
    def new(name: str, x: float, y: float, z: float):
        track = SwoopTrack()
        track.name = name
        track.position = Vertex.from_position(x, y, z)
        return track

    def __init__(self):
        self.name: str = ""
        self.position: Vertex = Vertex()


class _LYTReader:
    @staticmethod
    def load(data: str) -> LYT:
        pass
        # TODO


class _LYTWriter:
    @staticmethod
    def build(lyt: LYT) -> str:
        pass
        # TODO
