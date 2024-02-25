"""This module handles classes relating to editing LYT files."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.geometry import Vector3, Vector4


class LYT:
    """Represents a LYT file."""

    BINARY_TYPE = ResourceType.LTR

    def __init__(
        self,
    ):
        self.rooms: list[LYTRoom] = []
        self.tracks: list[LYTTrack] = []
        self.obstacles: list[LYTObstacle] = []
        self.doorhooks: list[LYTDoorHook] = []


class LYTRoom:
    """An area model.

    Attributes:
    ----------
        model: The filename of the area model.
        position: The position of the area model.
    """

    def __init__(
        self,
        model: str,
        position: Vector3,
    ):
        self.model: str = model  # TODO: find out if this is case-insensitive and implement via __eq__.
        self.position: Vector3 = position

    def __eq__(
        self,
        other: LYTRoom,
    ):
        if not isinstance(other, LYTRoom):
            return NotImplemented
        return self.model == other.model and self.position == other.position

    def __hash__(
        self,
    ):
        return hash(self.model)


class LYTTrack:
    """A swoop track booster.

    Unknown if this actually does anything in-game or is just to assist developers.

    Attributes:
    ----------
        model: The corresponding model filename.
        position: The position.
    """

    def __init__(
        self,
        model: str,
        position: Vector3,
    ):
        self.model: str = model  # TODO: find out if this is case-insensitive and implement via __eq__.
        self.position: Vector3 = position

    def __eq__(
        self,
        other: LYTTrack,
    ):
        if not isinstance(other, LYTTrack):
            return NotImplemented
        return self.model == other.model and self.position == other.position


class LYTObstacle:
    """A swoop track obstacle.

    Unknown if this actually does anything in-game or is just to assist developers.

    Attributes:
    ----------
        model: The corresponding model filename.
        position: The position.
    """

    def __init__(
        self,
        model: str,
        position: Vector3,
    ):
        self.model: str = model  # TODO: find out if this is case-insensitive and implement via __eq__.
        self.position: Vector3 = position

    def __eq__(
        self,
        other: LYTObstacle,
    ):
        if not isinstance(other, LYTObstacle):
            return NotImplemented
        return self.model == other.model and self.position == other.position


class LYTDoorHook:
    """A door hook.

    This just exists for modelers to assist module designers.

    Attributes:
    ----------
        room: The corresponding room in the layout.
        door: The door name.
        position: The door position.
        orientation: The door orientation.
    """

    def __init__(
        self,
        room: str,
        door: str,
        position: Vector3,
        orientation: Vector4,
    ):
        self.room: str = room  # TODO: find out if this is case-insensitive and implement via __eq__.
        self.door: str = door  # TODO: find out if this is case-insensitive and implement via __eq__.
        self.position: Vector3 = position
        self.orientation: Vector4 = orientation

    def __eq__(
        self,
        other: LYTDoorHook,
    ):
        if not isinstance(other, LYTDoorHook):
            return NotImplemented
        return (
            self.room == other.room
            and self.door == other.door
            and self.position == other.position
            and self.orientation == other.orientation
        )
