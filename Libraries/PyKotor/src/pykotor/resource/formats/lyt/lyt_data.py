"""This module handles classes relating to editing LYT files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.geometry import Vector3, Vector4


class LYT:
    """Represents a LYT file."""

    BINARY_TYPE: ResourceType = ResourceType.LYT

    def __init__(self):
        self.rooms: list[LYTRoom] = []
        self.tracks: list[LYTTrack] = []
        self.obstacles: list[LYTObstacle] = []
        self.doorhooks: list[LYTDoorHook] = []

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
            parsed_model: str = room.model.strip()
            assert parsed_model == room.model, "room model names cannot contain spaces."
            assert ResRef.is_valid(parsed_model), f"invalid room model: '{room.model}' at room {self.rooms.index(room)}, must conform to resref restrictions."
            yield parsed_model.lower()

    def find_room_by_model(
        self,
        model: str,
    ) -> LYTRoom | None:
        """Find a room in the LYT by its model name."""
        return next(
            (room for room in self.rooms if room.model.lower() == model.lower()),
            None,
        )

    def find_nearest_room(
        self,
        position: Vector3,
    ) -> LYTRoom | None:
        """Find the nearest room to a given position."""
        if not self.rooms:
            return None
        return min(
            self.rooms,
            key=lambda room: (room.position - position).magnitude(),
        )

    def _dfs_rooms(
        self,
        room: LYTRoom,
        visited: set,
    ):
        """Depth-first search to find connected rooms."""
        visited.add(room)
        for connected_room in room.connections:
            if connected_room not in visited:
                self._dfs_rooms(connected_room, visited)

    def update_connections(
        self,
        room1: LYTRoom,
        room2: LYTRoom,
        new_room: LYTRoom,
    ):
        """Update connections after merging rooms."""
        for room in self.rooms:
            if room1 in room.connections:
                room.connections.remove(room1)
                room.connections.append(new_room)
            if room2 in room.connections:
                room.connections.remove(room2)
                if new_room not in room.connections:
                    room.connections.append(new_room)


class LYTRoom:
    """An area model."""

    def __init__(
        self,
        model: str,
        position: Vector3,
    ):
        self.model: str = model
        self.position: Vector3 = position
        self.connections: set[LYTRoom] = set()

    def __add__(
        self,
        other: LYTRoom,
    ) -> LYTRoom:
        """Merge this room with another room using the + operator."""
        new_position = (self.position + other.position) * 0.5
        new_room = LYTRoom(f"{self.model}_{other.model}", new_position)
        new_room.connections = self.connections.union(other.connections)
        return new_room

    def __eq__(self, other: LYTRoom) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTRoom):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))

    def add_connection(
        self,
        room: LYTRoom,
    ) -> None:
        """Add a connection to another room."""
        if room not in self.connections:
            self.connections.add(room)

    def remove_connection(
        self,
        room: LYTRoom,
    ) -> None:
        """Remove a connection to another room."""
        if room in self.connections:
            self.connections.discard(room)


class LYTTrack:
    """A swoop track booster."""

    def __init__(
        self,
        model: str,
        position: Vector3,
    ):
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(
        self,
        other: LYTTrack,
    ) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTTrack):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))


class LYTObstacle:
    """A swoop track obstacle."""

    def __init__(
        self,
        model: str,
        position: Vector3,
    ):
        self.model: str = model
        self.position: Vector3 = position

    def __eq__(
        self,
        other: LYTObstacle,
    ) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTObstacle):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))


class LYTDoorHook:
    """A door hook."""

    def __init__(
        self,
        room: str,
        door: str,
        position: Vector3,
        orientation: Vector4,
    ):
        self.room: str = room
        self.door: str = door
        self.position: Vector3 = position
        self.orientation: Vector4 = orientation

    def __eq__(
        self,
        other: LYTDoorHook,
    ) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTDoorHook):
            return NotImplemented
        return self.room == other.room and self.door == other.door and self.position == other.position and self.orientation == other.orientation

    def __hash__(self) -> int:
        return hash(
            (
                self.room,
                self.door,
                self.position,
                self.orientation,
            )
        )
