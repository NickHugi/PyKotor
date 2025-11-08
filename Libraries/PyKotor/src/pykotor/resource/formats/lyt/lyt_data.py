"""This module handles classes relating to editing LYT files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from utility.common.geometry import Vector3, Vector4


class LYT(ComparableMixin):
    """Represents a LYT file."""

    BINARY_TYPE = ResourceType.LYT
    COMPARABLE_SEQUENCE_FIELDS = ("rooms", "tracks", "obstacles", "doorhooks")

    def __init__(self):
        self.rooms: list[LYTRoom] = []
        self.tracks: list[LYTTrack] = []
        self.obstacles: list[LYTObstacle] = []
        self.doorhooks: list[LYTDoorHook] = []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LYT):
            return NotImplemented
        return (
            self.rooms == other.rooms
            and self.tracks == other.tracks
            and self.obstacles == other.obstacles
            and self.doorhooks == other.doorhooks
        )

    def __hash__(self) -> int:
        return hash(
            (
                tuple(self.rooms),
                tuple(self.tracks),
                tuple(self.obstacles),
                tuple(self.doorhooks),
            ),
        )

    def iter_resource_identifiers(self) -> Generator[ResourceIdentifier, Any, None]:
        """Generate resources that utilise this LYT."""
        for room in self.rooms:
            yield ResourceIdentifier(room.model, ResourceType.MDL)
            yield ResourceIdentifier(room.model, ResourceType.MDX)
            yield ResourceIdentifier(room.model, ResourceType.WOK)

    def all_room_models(self) -> Generator[str, Any, None]:
        """Return all models used by this LYT."""
        for room in self.rooms:
            parsed_model: str = room.model.strip()
            assert parsed_model == room.model, "room model names cannot contain spaces."
            assert ResRef.is_valid(parsed_model), (
                f"invalid room model: '{room.model}' at room {self.rooms.index(room)}, "
                "must conform to resref restrictions."
            )
            yield parsed_model.lower()

    def find_room_by_model(self, model: str) -> LYTRoom | None:
        """Find a room in the LYT by its model name."""
        return next((room for room in self.rooms if room.model.lower() == model.lower()), None)

    def find_nearest_room(self, position: Vector3) -> LYTRoom | None:
        """Find the nearest room to a given position."""
        if not self.rooms:
            return None
        return min(self.rooms, key=lambda room: (room.position - position).magnitude())

    def _dfs_rooms(self, room: LYTRoom, visited: set[LYTRoom]) -> None:
        """Depth-first search to find connected rooms."""
        visited.add(room)
        for connected_room in room.connections:
            if connected_room not in visited:
                self._dfs_rooms(connected_room, visited)

    def update_connections(self, room1: LYTRoom, room2: LYTRoom, new_room: LYTRoom) -> None:
        """Update connections after merging rooms."""
        for room in self.rooms:
            if room1 in room.connections:
                room.connections.remove(room1)
                room.connections.add(new_room)
            if room2 in room.connections:
                room.connections.remove(room2)
                room.connections.add(new_room)


class LYTRoom(ComparableMixin):
    """An area model."""

    COMPARABLE_FIELDS = ("model", "position")

    def __init__(self, model: str, position: Vector3):
        self.model: str = model
        self.position: Vector3 = position
        self.connections: set[LYTRoom] = set()

    def __add__(self, other: LYTRoom) -> LYTRoom:
        """Merge this room with another room using the + operator."""
        new_position = (self.position + other.position) * 0.5
        new_room = LYTRoom(f"{self.model}_{other.model}", new_position)
        new_room.connections = self.connections.union(other.connections)
        return new_room

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTRoom):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))

    def add_connection(self, room: LYTRoom) -> None:
        """Add a connection to another room."""
        if room not in self.connections:
            self.connections.add(room)

    def remove_connection(self, room: LYTRoom) -> None:
        """Remove a connection to another room."""
        if room in self.connections:
            self.connections.discard(room)


class LYTTrack(ComparableMixin):
    """A swoop track booster."""

    COMPARABLE_FIELDS = ("model", "position")

    def __init__(self, model: str, position: Vector3):
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTTrack):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))


class LYTObstacle(ComparableMixin):
    """A swoop track obstacle."""

    COMPARABLE_FIELDS = ("model", "position")

    def __init__(self, model: str, position: Vector3):
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTObstacle):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))


class LYTDoorHook(ComparableMixin):
    """A door hook."""

    COMPARABLE_FIELDS = ("room", "door", "position", "orientation")

    def __init__(self, room: str, door: str, position: Vector3, orientation: Vector4):
        self.room: str = room  # TODO(th3w1zard1): determine case sensitivity.
        self.door: str = door  # TODO(th3w1zard1): determine case sensitivity.
        self.position: Vector3 = position
        self.orientation: Vector4 = orientation

    def __eq__(self, other: object) -> bool:
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

    def __hash__(self) -> int:
        return hash((self.room, self.door, self.position, self.orientation))
