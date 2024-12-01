"""Core data structures for LYT editing."""
from __future__ import annotations

from uuid import uuid4

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack


class ExtendedLYTRoom(LYTRoom):
    """Extended LYTRoom with additional attributes needed for editing."""

    def __init__(self):
        super().__init__()
        self.size: Vector3 = Vector3(10, 10, 3)  # Default size
        self.id: str = str(uuid4())  # Unique identifier
        self.texture: str = ""  # Texture reference
        self.orientation: Vector3 = Vector3(0, 0, 0)  # Rotation angles
        self.is_highlighted: bool = False
        self.is_selected: bool = False
        self.connection_points: list[Vector3] = []

    def serialize(self) -> dict:
        """Serialize room data to dict."""
        data = super().serialize()
        data.update({
            "size": self.size.serialize(),
            "id": self.id,
            "texture": self.texture,
            "orientation": self.orientation.serialize()
        })
        return data

    def deserialize(self, data: dict) -> None:
        """Deserialize room data from dict."""
        super().deserialize(data)
        self.size = Vector3.deserialize(data.get("size", Vector3(10, 10, 3).serialize()))
        self.id = data.get("id", str(uuid4()))
        self.texture = data.get("texture", "")
        self.orientation = Vector3.deserialize(data.get("orientation", Vector3(0, 0, 0).serialize()))

class ExtendedLYTTrack(LYTTrack):
    """Extended LYTTrack with additional attributes needed for editing."""

    def __init__(self):
        super().__init__()
        self.id: str = str(uuid4())
        self.texture: str = ""
        self.is_highlighted: bool = False
        self.is_selected: bool = False

    def serialize(self) -> dict:
        data = super().serialize()
        data.update({
            "id": self.id,
            "texture": self.texture
        })
        return data

    def deserialize(self, data: dict) -> None:
        super().deserialize(data)
        self.id = data.get("id", str(uuid4()))
        self.texture = data.get("texture", "")

class ExtendedLYTObstacle(LYTObstacle):
    """Extended LYTObstacle with additional attributes needed for editing."""

    def __init__(self):
        super().__init__()
        self.id: str = str(uuid4())
        self.radius: float = 5.0  # Default radius
        self.is_highlighted: bool = False
        self.is_selected: bool = False

    def serialize(self) -> dict:
        data = super().serialize()
        data.update({
            "id": self.id,
            "radius": self.radius
        })
        return data

    def deserialize(self, data: dict) -> None:
        super().deserialize(data)
        self.id = data.get("id", str(uuid4()))
        self.radius = float(data.get("radius", 5.0))

class ExtendedLYTDoorHook(LYTDoorHook):
    """Extended LYTDoorHook with additional attributes needed for editing."""

    def __init__(self):
        super().__init__()
        self.id: str = str(uuid4())
        self.is_highlighted: bool = False
        self.is_selected: bool = False

    def serialize(self) -> dict:
        data = super().serialize()
        data.update({
            "id": self.id
        })
        return data

    def deserialize(self, data: dict) -> None:
        super().deserialize(data)
        self.id = data.get("id", str(uuid4()))

class ExtendedLYT(LYT):
    """Extended LYT with additional functionality for editing."""

    def __init__(self):
        super().__init__()
        self.rooms: list[ExtendedLYTRoom] = []
        self.tracks: list[ExtendedLYTTrack] = []
        self.obstacles: list[ExtendedLYTObstacle] = []
        self.doorhooks: list[ExtendedLYTDoorHook] = []

    def serialize(self) -> dict:
        """Serialize all LYT data."""
        return {
            "rooms": [room.serialize() for room in self.rooms],
            "tracks": [track.serialize() for track in self.tracks],
            "obstacles": [obstacle.serialize() for obstacle in self.obstacles],
            "doorhooks": [doorhook.serialize() for doorhook in self.doorhooks]
        }

    def deserialize(self, data: dict) -> None:
        """Deserialize all LYT data."""
        self.rooms = []
        self.tracks = []
        self.obstacles = []
        self.doorhooks = []

        for room_data in data.get("rooms", []):
            room = ExtendedLYTRoom()
            room.deserialize(room_data)
            self.rooms.append(room)

        for track_data in data.get("tracks", []):
            track = ExtendedLYTTrack()
            track.deserialize(track_data)
            self.tracks.append(track)

        for obstacle_data in data.get("obstacles", []):
            obstacle = ExtendedLYTObstacle()
            obstacle.deserialize(obstacle_data)
            self.obstacles.append(obstacle)

        for doorhook_data in data.get("doorhooks", []):
            doorhook = ExtendedLYTDoorHook()
            doorhook.deserialize(doorhook_data)
            self.doorhooks.append(doorhook)
