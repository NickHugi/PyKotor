from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector3, Vector4
from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from collections.abc import Iterator

    from typing_extensions import Literal

    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class LYTAsciiReader(ResourceReader):
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
    def load(
        self,
        auto_close: bool = True,
    ) -> LYT:
        self._lyt = LYT()

        self._lines = self._reader.read_string(self._reader.size()).splitlines()

        iterator = iter(self._lines)
        for line in iterator:
            tokens = line.split()

            if tokens[0] == "roomcount":
                self._load_rooms(iterator, int(tokens[1]))
            if tokens[0] == "trackcount":
                self._load_tracks(iterator, int(tokens[1]))
            if tokens[0] == "obstaclecount":
                self._load_obstacles(iterator, int(tokens[1]))
            if tokens[0] == "doorhookcount":
                self._load_doorhooks(iterator, int(tokens[1]))

        if auto_close:
            self._reader.close()

        return self._lyt

    def _load_rooms(
        self,
        iterator: Iterator[str],
        count: int,
    ):
        for _ in range(count):
            tokens = next(iterator).split()
            model = tokens[0]
            position = Vector3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            self._lyt.rooms.append(LYTRoom(model, position))

    def _load_tracks(
        self,
        iterator: Iterator[str],
        count: int,
    ):
        for _ in range(count):
            tokens = next(iterator).split()
            model = tokens[0]
            position = Vector3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
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
    def __init__(
        self,
        lyt: LYT,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._lyt: LYT = lyt

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ):
        roomcount = len(self._lyt.rooms)
        trackcount = len(self._lyt.tracks)
        obstaclecount = len(self._lyt.obstacles)
        doorhookcount = len(self._lyt.doorhooks)

        self._writer.write_string(f"beginlayout{self.LYT_LINE_SEP}")

        self._writer.write_string(f"{self.LYT_INDENT}roomcount {roomcount}{self.LYT_LINE_SEP}")
        for room in self._lyt.rooms:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{room.model} {room.position.x} {room.position.y} {room.position.z}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string(f"{self.LYT_INDENT}trackcount {trackcount}{self.LYT_LINE_SEP}")
        for track in self._lyt.tracks:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{track.model} {track.position.x} {track.position.y} {track.position.z}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string(f"{self.LYT_INDENT}obstaclecount {obstaclecount}{self.LYT_LINE_SEP}")
        for obstacle in self._lyt.obstacles:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{obstacle.model} {obstacle.position.x} {obstacle.position.y} {obstacle.position.z}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string(f"{self.LYT_INDENT}doorhookcount {doorhookcount}{self.LYT_LINE_SEP}")
        for doorhook in self._lyt.doorhooks:
            self._writer.write_string(
                f"{self.LYT_INDENT*2}{doorhook.room} {doorhook.door} 0 {doorhook.position.x} {doorhook.position.y} {doorhook.position.z} {doorhook.orientation.x} {doorhook.orientation.y} {doorhook.orientation.z} {doorhook.orientation.w}{self.LYT_LINE_SEP}",
            )

        self._writer.write_string("donelayout")

        if auto_close:
            self._writer.close()
