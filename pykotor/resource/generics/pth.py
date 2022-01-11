from __future__ import annotations

from contextlib import suppress
from typing import List, Optional

from pykotor.common.geometry import Vector2
from pykotor.common.misc import Game
from pykotor.resource.formats.gff import GFF, GFFList


class PTH:
    """
    Stores the path data for a module.
    """

    def __init__(self):
        self._points: List[Vector2] = []
        self._connections: List[PTHEdge] = []

    def __iter__(self):
        for point in self._points:
            yield point

    def __len__(self):
        return len(self._points)

    def __getitem__(self, item: int):
        return self._points[int]

    def add(self, x: float, y: float) -> int:
        self._points.append(Vector2(x, y))
        return len(self._points) - 1

    def remove(self, index: int) -> None:
        self._points.pop(index)

        self._connections = [x for x in self._connections if x.source != index and x.target != index]

        for i, connection in enumerate(self._connections):
            connection.source = connection.source-1 if connection.source > index else connection.source
            connection.target = connection.target-1 if connection.target > index else connection.target

    def get(self, index: int) -> Optional[Vector2]:
        with suppress(Exception):
            return self._points[index]
        return None

    def find(self, point: Vector2) -> Optional[int]:
        return next([x for x in self._points if x == point], None)

    def connect(self, source: int, target: int) -> None:
        self._connections.append(PTHEdge(source, target))

    def disconnect(self, source: int, target: int) -> None:
        self._connections.remove(PTHEdge(source, target))

    def is_connected(self, source: int, target: int) -> bool:
        return any(x for x in self._connections if x == PTHEdge(source, target))

    def outgoing(self, source: int) -> List[PTHEdge]:
        connections = []
        for connection in self._connections:
            if connection.source == source:
                connections.append(connection)
        return connections

    def incoming(self, target: int) -> List[PTHEdge]:
        connections = []
        for connection in self._connections:
            if connection.target == target:
                connections.append(connection)
        return connections


class PTHEdge:
    def __init__(self, source: int, target: int):
        self.source = source
        self.target = target

    def __eq__(self, other: PTHEdge):
        if not isinstance(other, PTHEdge):
            raise NotImplemented

        return self.source == other.source and self.target == other.target


def construct_pth(gff: GFF) -> PTH:
    pth = PTH()

    connections_list = gff.root.acquire("Path_Conections", GFFList())

    for point_struct in gff.root.acquire("Path_Points", GFFList()):
        connections = point_struct.acquire("Conections", 0)
        first_connection = point_struct.acquire("First_Conection", 0)
        x = point_struct.acquire("X", 0.0)
        y = point_struct.acquire("Y", 0.0)

        source = pth.add(x, y)

        for i in range(first_connection, first_connection + connections):
            target = connections_list.at(i).acquire("Destination", 0)
            pth.connect(source, target)

    return pth


def dismantle_pth(pth: PTH, game: Game = Game.K2, *, use_deprecated: bool = True) -> GFF:
    gff = GFF()

    connections_list = gff.root.set_list("Path_Conections", GFFList())
    points_list = gff.root.set_list("Path_Points", GFFList())

    for i, point in enumerate(pth):
        outgoings = pth.outgoing(i)

        point_struct = points_list.add(2)
        point_struct.set_uint32("Conections", len(outgoings))
        point_struct.set_uint32("First_Conection", len(connections_list))
        point_struct.set_single("X", point.x)
        point_struct.set_single("Y", point.y)

        for outgoing in outgoings:
            connection_struct = connections_list.add(3)
            connection_struct.set_uint32("Destination", outgoing.target)

    return gff
