from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose
from utility.common.geometry import Vector3, Vector4

if TYPE_CHECKING:
    from collections.abc import Iterator

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class LYTAsciiReader(ResourceReader):
    """Reads LYT (Layout) files.
    
    LYT files define the layout of rooms, tracks, obstacles, and door hooks in KotOR modules.
    Used for area loading and spatial organization.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/lytreader.cpp (LYT reading)
    """
    ROOM_COUNT_KEY: str = "roomcount"
    TRACK_COUNT_KEY: str = "trackcount"
    OBSTACLE_COUNT_KEY: str = "obstaclecount"
    DOORHOOK_COUNT_KEY: str = "doorhookcount"

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._lyt: LYT = LYT()
        self._lines: list[str] = []

    @autoclose
    def load(self, *, auto_close: bool = True) -> LYT:  # noqa: FBT001, FBT002, ARG002
        self._lyt = LYT()

        self._lines: list[str] = self._reader.read_string(self._reader.size()).splitlines()

        iterator: Iterator[str] = iter(self._lines)
        for line in iterator:
            tokens: list[str] = line.split()

            if tokens[0] == self.ROOM_COUNT_KEY:
                self._load_rooms(iterator, int(tokens[1]))
            if tokens[0] == self.TRACK_COUNT_KEY:
                self._load_tracks(iterator, int(tokens[1]))
            if tokens[0] == self.OBSTACLE_COUNT_KEY:
                self._load_obstacles(iterator, int(tokens[1]))
            if tokens[0] == self.DOORHOOK_COUNT_KEY:
                self._load_doorhooks(iterator, int(tokens[1]))

        return self._lyt

    def _load_rooms(
        self,
        iterator: Iterator[str],
        count: int,
    ):
        for _ in range(count):
            tokens: list[str] = next(iterator).split()
            model: str = tokens[0]
            position: Vector3 = Vector3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            room = LYTRoom(model, position)
            self._lyt.rooms.append(room)

    def _load_tracks(
        self,
        iterator: Iterator[str],
        count: int,
    ):
        for _ in range(count):
            tokens: list[str] = next(iterator).split()
            model: str = tokens[0]
            position: Vector3 = Vector3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            self._lyt.tracks.append(LYTTrack(model, position))

    def _load_obstacles(
        self,
        iterator: Iterator[str],
        count: int,
    ):
        for _ in range(count):
            tokens: list[str] = next(iterator).split()
            model: str = tokens[0]
            position = Vector3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            self._lyt.obstacles.append(LYTObstacle(model, position))

    def _load_doorhooks(
        self,
        iterator: Iterator[str],
        count: int,
    ):
        for _i in range(count):
            tokens: list[str] = next(iterator).split()
            room: str = tokens[0]
            door: str = tokens[1]
            position = Vector3(float(tokens[3]), float(tokens[4]), float(tokens[5]))
            orientation = Vector4(
                float(tokens[6]),
                float(tokens[7]),
                float(tokens[8]),
                float(tokens[9]),
            )
            self._lyt.doorhooks.append(LYTDoorHook(room, door, position, orientation))


class LYTAsciiWriter(ResourceWriter):
    LYT_LINE_SEP: Literal["\r\n"] = "\r\n"
    LYT_INDENT: Literal["   "] = "   "
    ROOM_COUNT_KEY: str = "roomcount"
    TRACK_COUNT_KEY: str = "trackcount"
    OBSTACLE_COUNT_KEY: str = "obstaclecount"
    DOORHOOK_COUNT_KEY: str = "doorhookcount"

    def __init__(
        self,
        lyt: LYT,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._lyt: LYT = lyt

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        roomcount: int = len(self._lyt.rooms)
        trackcount: int = len(self._lyt.tracks)
        obstaclecount: int = len(self._lyt.obstacles)
        doorhookcount: int = len(self._lyt.doorhooks)

        self._writer.write_string(f"beginlayout{self.LYT_LINE_SEP}")

        self._writer.write_string(f"{self.LYT_INDENT}{self.ROOM_COUNT_KEY} {roomcount}{self.LYT_LINE_SEP}")
        for room in self._lyt.rooms:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{room.model} {room.position.x} {room.position.y} {room.position.z}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string(f"{self.LYT_INDENT}{self.TRACK_COUNT_KEY} {trackcount}{self.LYT_LINE_SEP}")
        for track in self._lyt.tracks:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{track.model} {track.position.x} {track.position.y} {track.position.z}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string(f"{self.LYT_INDENT}{self.OBSTACLE_COUNT_KEY} {obstaclecount}{self.LYT_LINE_SEP}")
        for obstacle in self._lyt.obstacles:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{obstacle.model} {obstacle.position.x} {obstacle.position.y} {obstacle.position.z}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string(f"{self.LYT_INDENT}{self.DOORHOOK_COUNT_KEY} {doorhookcount}{self.LYT_LINE_SEP}")
        for doorhook in self._lyt.doorhooks:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{doorhook.room} {doorhook.door} 0 {doorhook.position.x} {doorhook.position.y} {doorhook.position.z} {doorhook.orientation.x} {doorhook.orientation.y} {doorhook.orientation.z} {doorhook.orientation.w}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string("donelayout")
