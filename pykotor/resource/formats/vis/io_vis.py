from __future__ import annotations

from typing import Optional, List

from pykotor.resource.formats.vis import VIS
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter


class VISAsciiReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._vis: Optional[VIS] = None
        self._lines: List[str] = self._reader.read_string(self._size).splitlines()

    def load(self, auto_close: bool = True) -> VIS:
        self._vis = VIS()

        pairs = []

        iterator = iter(self._lines)
        for line in iterator:
            tokens = line.split()

            when_inside = tokens[0]
            self._vis.add_room(when_inside)

            count = int(tokens[1])
            for i in range(count):
                show = next(iterator).split()[0]
                pairs.append((when_inside, show))

        for when_inside, show in pairs:
            if when_inside not in self._vis.all_rooms():
                self._vis.add_room(when_inside)
            if show not in self._vis.all_rooms():
                self._vis.add_room(show)
            self._vis.set_visible(when_inside, show, True)

        if auto_close:
            self._reader.close()

        return self._vis


class VISAsciiWriter(ResourceWriter):
    def __init__(self, vis: VIS, target: TARGET_TYPES):
        super().__init__(target)
        self._vis: VIS = vis

    def write(self, auto_close: bool = True) -> None:
        for observer, observed in self._vis:
            self._writer.write_string("{} {}\r\n".format(observer, str(len(observed))))
            for room in observed:
                self._writer.write_string("  {}\r\n".format(room))

        if auto_close:
            self._writer.close()
