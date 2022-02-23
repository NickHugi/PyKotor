"""
This module handles classes relating to editing LYT files.
"""
from __future__ import annotations

from typing import List

from pykotor.resource.type import ResourceType

from pykotor.common.geometry import Vector3, Vector4


class LYT:
    """
    Represents a LYT file.
    """

    BINARY_TYPE = ResourceType.LTR

    def __init__(self):
        self.rooms: List[LYTRoom] = []
        self.tracks: List[LYTTrack] = []
        self.obstacles: List[LYTObstacle] = []
        self.doorhooks: List[LYTDoorHook] = []


class LYTRoom:
    """
    An area model.

    Attributes:
        model: The filename of the area model.
        position: The position of the area model.
    """
    def __init__(self, model: str, position: Vector3):
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(self, other):
        return self.model == other.model and self.position == other.position


class LYTTrack:
    """
    A swoop track booster.

    Unknown if this actually does anything in-game or is just to assist developers.

    Attributes:
        model: The corresponding model filename.
        position: The position.
    """

    def __init__(self, model: str, position: Vector3):
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(self, other):
        return self.model == other.model and self.position == other.position


class LYTObstacle:
    """
    A swoop track obstacle.

    Unknown if this actually does anything in-game or is just to assist developers.

    Attributes:
        model: The corresponding model filename.
        position: The position.
    """

    def __init__(self, model: str, position: Vector3):
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(self, other):
        return self.model == other.model and self.position == other.position


class LYTDoorHook:
    """
    A door hook.

    This is just exists for modelers to assist module designers.

    Attributes:
        room: The corresponding room in the layout.
        door: The door name.
        position: The door position.
        orientation: The door orientation.
    """

    def __init__(self, room: str, door: str, position: Vector3, orientation: Vector4):
        self.room: str = room
        self.door: str = door
        self.position: Vector3 = position
        self.orientation: Vector4 = orientation

    def __eq__(self, other):
        return (self.room == other.room and self.door == other.door and self.position == other.position
                and self.orientation == other.orientation)
