from __future__ import annotations

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.lyt.lyt_data import LYT, Room


class LYTUtils:
    @staticmethod
    def find_room_by_name(lyt: LYT, name: str) -> Room | None:
        """Find a room in the LYT by its name."""
        return next((room for room in lyt.rooms if room.name == name), None)

    @staticmethod
    def find_nearest_room(lyt: LYT, position: Vector3) -> Room | None:
        """Find the nearest room to a given position."""
        if not lyt.rooms:
            return None
        return min(lyt.rooms, key=lambda room: (room.position - position).length())

    @staticmethod
    def connect_rooms(lyt: LYT, room1: Room, room2: Room) -> bool:
        """Connect two rooms in the LYT."""
        if room1 not in lyt.rooms or room2 not in lyt.rooms:
            return False
        
        # Check if rooms are already connected
        if room2 in room1.connections or room1 in room2.connections:
            return True

        room1.connections.append(room2)
        room2.connections.append(room1)
        return True

    @staticmethod
    def disconnect_rooms(lyt: LYT, room1: Room, room2: Room) -> bool:
        """Disconnect two rooms in the LYT."""
        if room1 not in lyt.rooms or room2 not in lyt.rooms:
            return False
        
        if room2 in room1.connections:
            room1.connections.remove(room2)
        if room1 in room2.connections:
            room2.connections.remove(room1)
        return True

    @staticmethod
    def find_path(lyt: LYT, start_room: Room, end_room: Room) -> list[Room]:
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
    def validate_lyt(lyt: LYT) -> tuple[bool, list[str]]:
        """Validate the LYT for common issues."""
        issues = []

        # Check for rooms with duplicate names
        room_names = [room.name for room in lyt.rooms]
        if len(room_names) != len(set(room_names)):
            issues.append("Duplicate room names found")

        # Check for disconnected rooms
        connected_rooms = set()
        if lyt.rooms:
            LYTUtils._dfs_rooms(lyt.rooms[0], connected_rooms)
            if len(connected_rooms) != len(lyt.rooms):
                issues.append("Disconnected rooms found")

        # Check for overlapping rooms
        for i, room1 in enumerate(lyt.rooms):
            for room2 in lyt.rooms[i+1:]:
                if LYTUtils._do_rooms_overlap(room1, room2):
                    issues.append(f"Overlapping rooms found: {room1.name} and {room2.name}")

        # Check for tracks without valid start or end rooms
        for track in lyt.tracks:
            if track.start_room not in lyt.rooms or track.end_room not in lyt.rooms:
                issues.append(f"Track {track.name} has invalid start or end room")

        # Check for obstacles outside of any room
        for obstacle in lyt.obstacles:
            if not any(LYTUtils._is_point_in_room(obstacle.position, room) for room in lyt.rooms):
                issues.append(f"Obstacle {obstacle.name} is outside of any room")

        return len(issues) == 0, issues

    @staticmethod
    def _dfs_rooms(room: Room, visited: set):
        """Depth-first search to find connected rooms."""
        visited.add(room)
        for connected_room in room.connections:
            if connected_room not in visited:
                LYTUtils._dfs_rooms(connected_room, visited)

    @staticmethod
    def _do_rooms_overlap(room1: Room, room2: Room) -> bool:
        """Check if two rooms overlap."""
        # This is a simplified check assuming rooms are axis-aligned boxes
        return (abs(room1.position.x - room2.position.x) * 2 < (room1.size.x + room2.size.x) and
                abs(room1.position.y - room2.position.y) * 2 < (room1.size.y + room2.size.y) and
                abs(room1.position.z - room2.position.z) * 2 < (room1.size.z + room2.size.z))

    @staticmethod
    def _is_point_in_room(point: Vector3, room: Room) -> bool:
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
                        LYTUtils._update_tracks(optimized_lyt, room1, room2, new_room)
                        merged = True
                        break
                if merged:
                    break

        # Simplify connections
        for room in optimized_lyt.rooms:
            room.connections = list(set(room.connections))  # Remove duplicate connections

        return optimized_lyt

    @staticmethod
    def _can_merge_rooms(room1: Room, room2: Room) -> bool:
        """Check if two rooms can be merged."""
        distance = (room1.position - room2.position).length()
        return distance < (room1.size + room2.size).length() * 0.5

    @staticmethod
    def _merge_rooms(room1: Room, room2: Room) -> Room:
        """Merge two rooms into one."""
        new_position = (room1.position + room2.position) * 0.5
        new_size = Vector3(
            max(room1.position.x + room1.size.x, room2.position.x + room2.size.x) - min(room1.position.x, room2.position.x),
            max(room1.position.y + room1.size.y, room2.position.y + room2.size.y) - min(room1.position.y, room2.position.y),
            max(room1.position.z + room1.size.z, room2.position.z + room2.size.z) - min(room1.position.z, room2.position.z)
        )
        new_room = Room(f"{room1.name}_{room2.name}", new_position, new_size)
        new_room.connections = list(set(room1.connections + room2.connections))
        return new_room

    @staticmethod
    def _update_connections(lyt: LYT, room1: Room, room2: Room, new_room: Room):
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
    def _update_tracks(lyt: LYT, room1: Room, room2: Room, new_room: Room):
        """Update tracks after merging rooms."""
        for track in lyt.tracks:
            if track.start_room == room1 or track.start_room == room2:
                track.start_room = new_room
            if track.end_room == room1 or track.end_room == room2:
                track.end_room = new_room
