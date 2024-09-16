from __future__ import annotations

from typing import List, Tuple

from pykotor.common.geometry import Vector3, Vector4
from pykotor.resource.formats.lyt.lyt_data import LYT, LYTRoom, LYTTrack, LYTObstacle, LYTDoorHook


class LYTUtils:
    @staticmethod
    def find_room_by_model(lyt: LYT, model: str) -> LYTRoom | None:
        """Find a room in the LYT by its model name."""
        return next((room for room in lyt.rooms if room.model.lower() == model.lower()), None)

    @staticmethod
    def find_nearest_room(lyt: LYT, position: Vector3) -> LYTRoom | None:
        """Find the nearest room to a given position."""
        if not lyt.rooms:
            return None
        return min(lyt.rooms, key=lambda room: (room.position - position).length())

    @staticmethod
    def connect_rooms(room1: LYTRoom, room2: LYTRoom) -> None:
        """Connect two rooms in the LYT."""
        room1.add_connection(room2)
        room2.add_connection(room1)

    @staticmethod
    def disconnect_rooms(room1: LYTRoom, room2: LYTRoom) -> None:
        """Disconnect two rooms in the LYT."""
        room1.remove_connection(room2)
        room2.remove_connection(room1)

    @staticmethod
    def find_path(start_room: LYTRoom, end_room: LYTRoom) -> List[LYTRoom]:
        """Find a path between two rooms using breadth-first search."""
        queue = [(start_room, [start_room])]
        visited = set()

        while queue:
            (room, path) = queue.pop(0)
            if room not in visited:
                visited.add(room)

                if room == end_room:
                    return path

                for next_room in room.connections:
                    if next_room not in visited:
                        queue.append((next_room, path + [next_room]))

        return []  # No path found

    @staticmethod
    def validate_lyt(lyt: LYT) -> Tuple[bool, List[str]]:
        """Validate the LYT for common issues."""
        issues = []

        # Check for rooms with duplicate models
        room_models = [room.model.lower() for room in lyt.rooms]
        if len(room_models) != len(set(room_models)):
            issues.append("Duplicate room models found")

        # Check for disconnected rooms
        connected_rooms = set()
        if lyt.rooms:
            LYTUtils._dfs_rooms(lyt.rooms[0], connected_rooms)
            if len(connected_rooms) != len(lyt.rooms):
                issues.append("Disconnected rooms found")

        # Check for overlapping rooms
        overlapping = [
            f"{r1.model} and {r2.model}"
            for i, r1 in enumerate(lyt.rooms)
            for r2 in lyt.rooms[i + 1:]
            if LYTUtils._do_rooms_overlap(r1, r2)
        ]
        if overlapping:
            issues.append(f"Overlapping rooms found: {', '.join(overlapping)}")

        # Check for obstacles outside of any room
        outside_obstacles = [
            obstacle.model
            for obstacle in lyt.obstacles
            if not any(LYTUtils._is_point_in_room(obstacle.position, room) for room in lyt.rooms)
        ]
        if outside_obstacles:
            issues.append(f"Obstacles outside of any room: {', '.join(outside_obstacles)}")

        return len(issues) == 0, issues

    @staticmethod
    def _dfs_rooms(room: LYTRoom, visited: set):
        """Depth-first search to find connected rooms."""
        visited.add(room)
        for connected_room in room.connections:
            if connected_room not in visited:
                LYTUtils._dfs_rooms(connected_room, visited)

    @staticmethod
    def _do_rooms_overlap(room1: LYTRoom, room2: LYTRoom) -> bool:
        """Check if two rooms overlap."""
        return (abs(room1.position.x - room2.position.x) * 2 < (room1.size.x + room2.size.x) and
                abs(room1.position.y - room2.position.y) * 2 < (room1.size.y + room2.size.y) and
                abs(room1.position.z - room2.position.z) * 2 < (room1.size.z + room2.size.z))

    @staticmethod
    def _is_point_in_room(point: Vector3, room: LYTRoom) -> bool:
        """Check if a point is inside a room."""
        half_size = room.size * 0.5
        return (abs(point.x - room.position.x) <= half_size.x and
                abs(point.y - room.position.y) <= half_size.y and
                abs(point.z - room.position.z) <= half_size.z)

    @staticmethod
    def optimize_lyt(lyt: LYT) -> LYT:
        """Optimize the LYT by merging nearby rooms and simplifying connections."""
        optimized_lyt = LYT()
        optimized_lyt.rooms = lyt.rooms.copy()
        optimized_lyt.tracks = lyt.tracks.copy()
        optimized_lyt.obstacles = lyt.obstacles.copy()
        optimized_lyt.doorhooks = lyt.doorhooks.copy()

        # Merge nearby rooms
        merged = True
        while merged:
            merged = False
            for i, room1 in enumerate(optimized_lyt.rooms):
                for j, room2 in enumerate(optimized_lyt.rooms[i+1:], i+1):
                    if LYTUtils._can_merge_rooms(room1, room2):
                        new_room = LYTUtils._merge_rooms(room1, room2)
                        optimized_lyt.rooms[i] = new_room
                        optimized_lyt.rooms.pop(j)
                        LYTUtils._update_connections(optimized_lyt, room1, room2, new_room)
                        merged = True
                        break
                if merged:
                    break

        # Simplify connections
        for room in optimized_lyt.rooms:
            room.connections = list(set(room.connections))  # Remove duplicate connections

        return optimized_lyt

    @staticmethod
    def _can_merge_rooms(room1: LYTRoom, room2: LYTRoom) -> bool:
        """Check if two rooms can be merged."""
        distance = (room1.position - room2.position).length()
        return distance < (room1.size + room2.size).length() * 0.5

    @staticmethod
    def _merge_rooms(room1: LYTRoom, room2: LYTRoom) -> LYTRoom:
        """Merge two rooms into one."""
        new_position = (room1.position + room2.position) * 0.5
        new_size = Vector3(
            max(room1.position.x + room1.size.x, room2.position.x + room2.size.x) - min(room1.position.x, room2.position.x),
            max(room1.position.y + room1.size.y, room2.position.y + room2.size.y) - min(room1.position.y, room2.position.y),
            max(room1.position.z + room1.size.z, room2.position.z + room2.size.z) - min(room1.position.z, room2.position.z)
        )
        new_room = LYTRoom(f"{room1.model}_{room2.model}", new_position, new_size)
        new_room.connections = list(set(room1.connections + room2.connections))
        return new_room

    @staticmethod
    def _update_connections(lyt: LYT, room1: LYTRoom, room2: LYTRoom, new_room: LYTRoom):
        """Update connections after merging rooms."""
        for room in lyt.rooms:
            if room1 in room.connections:
                room.connections.remove(room1)
                room.connections.append(new_room)
            if room2 in room.connections:
                room.connections.remove(room2)
                if new_room not in room.connections:
                    room.connections.append(new_room)

    @staticmethod
    def add_track(lyt: LYT, model: str, position: Vector3) -> None:
        """Add a new track to the LYT."""
        new_track = LYTTrack(model, position)
        lyt.add_track(new_track)

    @staticmethod
    def remove_track(lyt: LYT, track: LYTTrack) -> None:
        """Remove a track from the LYT."""
        lyt.remove_track(track)

    @staticmethod
    def add_obstacle(lyt: LYT, model: str, position: Vector3) -> None:
        """Add a new obstacle to the LYT."""
        new_obstacle = LYTObstacle(model, position)
        lyt.add_obstacle(new_obstacle)

    @staticmethod
    def remove_obstacle(lyt: LYT, obstacle: LYTObstacle) -> None:
        """Remove an obstacle from the LYT."""
        lyt.remove_obstacle(obstacle)

    @staticmethod
    def add_doorhook(lyt: LYT, room: str, door: str, position: Vector3, orientation: Vector4) -> None:
        """Add a new doorhook to the LYT."""
        new_doorhook = LYTDoorHook(room, door, position, orientation)
        lyt.add_doorhook(new_doorhook)

    @staticmethod
    def remove_doorhook(lyt: LYT, doorhook: LYTDoorHook) -> None:
        """Remove a doorhook from the LYT."""
        lyt.remove_doorhook(doorhook)
