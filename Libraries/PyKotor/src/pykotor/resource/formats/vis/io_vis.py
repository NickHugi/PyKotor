from __future__ import annotations

import os

from typing import TYPE_CHECKING

from pykotor.resource.formats.vis.vis_data import VIS
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class VISAsciiReader(ResourceReader):
    """Reads VIS (Visibility) files.
    
    VIS files define which rooms are visible from other rooms, used for occlusion culling
    and level-of-detail management in KotOR modules.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/visreader.cpp (VIS reading)
    """
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._vis: VIS | None = None
        self._lines: list[str] = []

    @autoclose
    def load(self, *, auto_close: bool = True) -> VIS:  # noqa: FBT001, FBT002, ARG002
        self._vis = VIS()
        self._lines = self._reader.read_string(self._reader.size()).splitlines()

        pairs = []

        iterator = iter(self._lines)
        for line in iterator:
            tokens: list[str] = line.split()

            # Skip empty lines
            if not tokens:
                continue

            # Use a named constant for the magic value 2
            VERSION_HEADER_TOKEN_INDEX = 1  # Index in VIS ASCII lines where a version string may appear
            # Check if this is a version header line (e.g., "room V3.28")
            if len(tokens) >= VERSION_HEADER_TOKEN_INDEX + 1 and tokens[VERSION_HEADER_TOKEN_INDEX].startswith("V"):
                # This is a version header, skip it
                # Format appears to be: roomname Version
                continue

            when_inside: str = tokens[0]
            self._vis.add_room(when_inside)

            # Try to parse the count, provide better error if it fails
            try:
                count = int(tokens[1])
            except (ValueError, IndexError) as e:
                msg = f"Invalid VIS format: expected room count, got '{tokens[1] if len(tokens) > 1 else '(missing)'}' for room '{when_inside}'"
                raise ValueError(msg) from e

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
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        for observer, observed in self._vis:
            self._writer.write_string(f"{observer} {len(observed)}{os.linesep}")
            for room in observed:
                self._writer.write_string(f"  {room}{os.linesep}")
