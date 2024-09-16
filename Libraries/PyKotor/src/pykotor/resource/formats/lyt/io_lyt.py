from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector3, Vector4
from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class LYTAsciiReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._lyt: LYT | None = None
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

            if tokens[0] == "#MAXLAYOUT":
                assert tokens[1] == "ASCII", "Only ASCII LYT files are supported"
            elif tokens[0] == "filedependancy":
                self._lyt.filedependancy = tokens[1]
            elif tokens[0] == "beginlayout":
                self._load_layout(iterator)

        if auto_close:
            self._reader.close()

        return self._lyt

    def _load_layout(self, iterator: Iterator[str]):
        for line in iterator:
            tokens = line.split()

            if tokens[0] == "roomcount":
                self._load_rooms(iterator, int(tokens[1]))
            elif tokens[0] == "trackcount":
                self._load_tracks(iterator, int(tokens[1]))
            elif tokens[0] == "obstaclecount":
                self._load_obstacles(iterator, int(tokens[1]))
            elif tokens[0] == "doorhookcount":
                self._load_doorhooks(iterator, int(tokens[1]))
            elif tokens[0] == "donelayout":
                break

    def _load_rooms(
        self,
        iterator: Iterator[str],
        count: int,
    ):
        for _ in range(count):
            tokens = next(iterator).split()
            model = tokens[0]
            position = Vector3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            # Note: We're not setting the size here as it's not provided in the LYT file
            self._lyt.rooms.append(LYTRoom(model, position, Vector3(0, 0, 0)))

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
        self._writer.write_string("#MAXLAYOUT ASCII\r\n")
        self._writer.write_string(f"filedependancy {self._lyt.filedependancy}\r\n")
        self._writer.write_string("beginlayout\r\n")

        self._writer.write_string(f"   roomcount {len(self._lyt.rooms)}\r\n")
        for room in self._lyt.rooms:
            self._writer.write_string(
                f"      {room.model} {room.position.x:.6f} {room.position.y:.6f} {room.position.z:.6f}\r\n",
            )

        self._writer.write_string(f"   trackcount {len(self._lyt.tracks)}\r\n")
        for track in self._lyt.tracks:
            self._writer.write_string(
                f"      {track.model} {track.position.x:.6f} {track.position.y:.6f} {track.position.z:.6f}\r\n",
            )

        self._writer.write_string(f"   obstaclecount {len(self._lyt.obstacles)}\r\n")
        for obstacle in self._lyt.obstacles:
            self._writer.write_string(
                f"      {obstacle.model} {obstacle.position.x:.6f} {obstacle.position.y:.6f} {obstacle.position.z:.6f}\r\n",
            )

        self._writer.write_string(f"   doorhookcount {len(self._lyt.doorhooks)}\r\n")
        for doorhook in self._lyt.doorhooks:
            self._writer.write_string(
                f"      {doorhook.room} {doorhook.door} 0 {doorhook.position.x:.6f} {doorhook.position.y:.6f} {doorhook.position.z:.6f} {doorhook.orientation.x:.6f} {doorhook.orientation.y:.6f} {doorhook.orientation.z:.6f} {doorhook.orientation.w:.6f}\r\n",
            )

        self._writer.write_string("donelayout")

        if auto_close:
            self._writer.close()
