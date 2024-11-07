"""This module handles classes relating to editing LYT files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from pykotor.common.geometry import Vector3
from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.geometry import Vector4


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

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the LYT for common issues."""
        issues: list[str] = []

        # Check for rooms with duplicate models
        room_models: list[str] = [room.model.lower() for room in self.rooms]
        if len(room_models) != len(set(room_models)):
            issues.append("Duplicate room models found")

        # Check for disconnected rooms
        connected_rooms = set()
        if self.rooms:
            self._dfs_rooms(self.rooms[0], connected_rooms)
            if len(connected_rooms) != len(self.rooms):
                issues.append("Disconnected rooms found")

        # Check for overlapping rooms
        overlapping: list[str] = [f"{r1.model} and {r2.model}" for i, r1 in enumerate(self.rooms) for r2 in self.rooms[i + 1 :] if r1.overlaps(r2)]
        if overlapping:
            issues.append(f"Overlapping rooms found: {', '.join(overlapping)}")

        # Check for obstacles outside of any room
        outside_obstacles: list[str] = [obstacle.model for obstacle in self.obstacles if not any(room.contains_point(obstacle.position) for room in self.rooms)]
        if outside_obstacles:
            issues.append(f"Obstacles outside of any room: {', '.join(outside_obstacles)}")

        return len(issues) == 0, issues

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

    def optimize(self) -> LYT:
        """Optimize the LYT by merging nearby rooms and simplifying connections."""
        optimized_lyt = LYT()
        optimized_lyt.rooms = self.rooms.copy()
        optimized_lyt.tracks = self.tracks.copy()
        optimized_lyt.obstacles = self.obstacles.copy()
        optimized_lyt.doorhooks = self.doorhooks.copy()

        # Merge nearby rooms
        merged = True
        while merged:
            merged = False
            for i, room1 in enumerate(optimized_lyt.rooms):
                for j, room2 in enumerate(optimized_lyt.rooms[i + 1 :], i + 1):
                    if room1.can_merge(room2):
                        new_room: LYTRoom = room1.merge(room2)
                        optimized_lyt.rooms[i] = new_room
                        optimized_lyt.rooms.pop(j)
                        optimized_lyt.update_connections(room1, room2, new_room)
                        merged = True
                        break
                if merged:
                    break

        # Simplify connections
        for room in optimized_lyt.rooms:
            room.connections = set(room.connections)  # Remove duplicate connections

        return optimized_lyt

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
            self.connections.append(room)

    def remove_connection(
        self,
        room: LYTRoom,
    ) -> None:
        """Remove a connection to another room."""
        if room in self.connections:
            self.connections.remove(room)

    def overlaps(
        self,
        other: LYTRoom,
    ) -> bool:  # FIXME: the room alone does not understand its size.
        """Check if this room overlaps with another room."""
        return (
            abs(self.position.x - other.position.x) * 2 < (self.size.x + other.size.x)
            and abs(self.position.y - other.position.y) * 2 < (self.size.y + other.size.y)
            and abs(self.position.z - other.position.z) * 2 < (self.size.z + other.size.z)
        )

    def contains_point(
        self,
        point: Vector3,
    ) -> bool:  # FIXME: the room alone does not understand its size.
        """Check if a point is inside this room."""
        half_size = self.size * 0.5
        return abs(point.x - self.position.x) <= half_size.x and abs(point.y - self.position.y) <= half_size.y and abs(point.z - self.position.z) <= half_size.z

    def can_merge(
        self,
        other: LYTRoom,
    ) -> bool:  # FIXME: the room alone does not understand its size.
        """Check if this room can be merged with another room."""
        distance = (self.position - other.position).magnitude()
        return distance < (self.size + other.size).magnitude() * 0.5

    def merge(
        self,
        other: LYTRoom,
    ) -> LYTRoom:  # FIXME: the room alone does not understand its size.
        """Merge this room with another room."""
        new_position = (self.position + other.position) * 0.5
        new_size = Vector3(
            max(self.position.x + self.size.x, other.position.x + other.size.x) - min(self.position.x, other.position.x),
            max(self.position.y + self.size.y, other.position.y + other.size.y) - min(self.position.y, other.position.y),
            max(self.position.z + self.size.z, other.position.z + other.size.z) - min(self.position.z, other.position.z),
        )
        new_room = LYTRoom(f"{self.model}_{other.model}", new_position, new_size)
        new_room.connections = self.connections.union(other.connections)
        return new_room


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

    def get_size(self) -> Vector3:
        """Get the size of the obstacle."""
        # FIXME: unimplemented??
        return Vector3(0, 0, 0)


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
