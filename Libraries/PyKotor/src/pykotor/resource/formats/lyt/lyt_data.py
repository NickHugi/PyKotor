"""This module handles classes relating to editing LYT files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.geometry import Vector3, Vector4


class LYT(ComparableMixin):
    """Represents a LYT file."""

    BINARY_TYPE = ResourceType.LTR
    COMPARABLE_SEQUENCE_FIELDS = ("rooms", "tracks", "obstacles", "doorhooks")

    def __init__(
        self,
    ):
        self.rooms: list[LYTRoom] = []
        self.tracks: list[LYTTrack] = []
        self.obstacles: list[LYTObstacle] = []
        self.doorhooks: list[LYTDoorHook] = []

    def __eq__(self, other):
        if not isinstance(other, LYT):
            return NotImplemented
        return (
            self.rooms == other.rooms
            and self.tracks == other.tracks
            and self.obstacles == other.obstacles
            and self.doorhooks == other.doorhooks
        )

    def __hash__(self):
        return hash(
            (
                tuple(self.rooms),
                tuple(self.tracks),
                tuple(self.obstacles),
                tuple(self.doorhooks),
            ),
        )

    def iter_resource_identifiers(self) -> Generator[ResourceIdentifier, Any, None]:
        """Generates resources that utilize this LYT.

        Does not guarantee the ResourceType exists, only the resname/resref.
        """
        for room in self.rooms:
            yield ResourceIdentifier(room.model, ResourceType.MDL)
            yield ResourceIdentifier(room.model, ResourceType.MDX)
            yield ResourceIdentifier(room.model, ResourceType.WOK)

    def all_room_models(self) -> Generator[str, Any, None]:
        """Returns all models used by this LYT."""
        for room in self.rooms:
            parsed_model = room.model.strip()
            assert parsed_model == room.model, "room model names cannot contain spaces."
            assert ResRef.is_valid(parsed_model), f"invalid room model: '{room.model}' at room {self.rooms.index(room)}, must conform to resref restrictions."
            yield parsed_model.lower()


class LYTRoom(ComparableMixin):
    COMPARABLE_FIELDS = ("model", "position")
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
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(
        self,
        other,
    ):
        if self is other:
            return True
        if not isinstance(other, LYTRoom):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(
        self,
    ):
        return hash((self.model.lower(), self.position))


class LYTTrack(ComparableMixin):
    COMPARABLE_FIELDS = ("model", "position")
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
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(
        self,
        other,
    ):
        if self is other:
            return True
        if not isinstance(other, LYTTrack):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self):
        return hash((self.model.lower(), self.position))


class LYTObstacle(ComparableMixin):
    COMPARABLE_FIELDS = ("model", "position")
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
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(
        self,
        other,
    ):
        if self is other:
            return True
        if not isinstance(other, LYTObstacle):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self):
        return hash((self.model.lower(), self.position))


class LYTDoorHook(ComparableMixin):
    COMPARABLE_FIELDS = ("room", "door", "position", "orientation")
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
        self.room: str = room  # TODO(th3w1zard1): find out if this is case-insensitive and implement via __eq__.
        self.door: str = door  # TODO(th3w1zard1): find out if this is case-insensitive and implement via __eq__.
        self.position: Vector3 = position
        self.orientation: Vector4 = orientation

    def __eq__(
        self,
        other,
    ):
        if self is other:
            return True
        if not isinstance(other, LYTDoorHook):
            return NotImplemented
        return (
            self.room == other.room
            and self.door == other.door
            and self.position == other.position
            and self.orientation == other.orientation
        )

    def __hash__(self):
        return hash((self.room, self.door, self.position, self.orientation))
