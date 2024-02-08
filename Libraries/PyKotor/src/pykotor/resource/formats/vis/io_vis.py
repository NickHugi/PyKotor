from __future__ import annotations

import os

from pykotor.resource.formats.vis.vis_data import VIS
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter, autoclose


class VISAsciiReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._vis: VIS | None = None
        self._lines: list[str] = []

    @autoclose
    def load(self, auto_close: bool = True) -> VIS:
        self._vis = VIS()
        self._lines = self._reader.read_string(self._reader.size()).splitlines()

        pairs = []

        iterator = iter(self._lines)
        for line in iterator:
            tokens: list[str] = line.split()

            when_inside: str = tokens[0]
            self._vis.add_room(when_inside)

            count = int(tokens[1])
            for _ in range(count):
                show = next(iterator).split()[0]
                pairs.append((when_inside, show))

        for when_inside, show in pairs:
            if when_inside not in self._vis.all_rooms():
                self._vis.add_room(when_inside)
            if show not in self._vis.all_rooms():
                self._vis.add_room(show)
            self._vis.set_visible(when_inside, show, visible=True)

        return self._vis


class VISAsciiWriter(ResourceWriter):
    def __init__(self, vis: VIS, target: TARGET_TYPES):
        super().__init__(target)
        self._vis: VIS = vis

    @autoclose
    def write(self, auto_close: bool = True):
        for observer, observed in self._vis:
            self._writer.write_string(f"{observer} {len(observed)}{os.linesep}")
            for room in observed:
                self._writer.write_string(f"  {room}{os.linesep}")
