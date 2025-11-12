from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.lip.lip_data import LIP, LIPShape
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class LIPBinaryReader(ResourceReader):
    """Reads LIP (Lip Sync) files.
    
    LIP files store lip-sync animation data for character speech, mapping time points
    to mouth shapes for synchronized lip movement during voice-over playback.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/lipreader.cpp:26-50 (LIP reading)
        vendor/reone/src/libs/graphics/format/lipwriter.cpp (LIP writing)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._lip: LIP | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> LIP:  # noqa: FBT001, FBT002, ARG002
        self._lip = LIP()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "LIP ":
            msg = "The file type that was loaded is invalid."
            raise TypeError(msg)

        if file_version != "V1.0":
            msg = "The LIP version that was loaded is not supported."
            raise TypeError(msg)

        self._lip.length = self._reader.read_single()
        entry_count = self._reader.read_uint32()

        # vendor/reone/src/libs/graphics/format/lipreader.cpp:35-45
        for _ in range(entry_count):
            time = self._reader.read_single()
            shape = LIPShape(self._reader.read_uint8())
            self._lip.add(time, shape)

        return self._lip


class LIPBinaryWriter(ResourceWriter):
    HEADER_SIZE = 16
    LIP_ENTRY_SIZE = 5

    def __init__(
        self,
        lip: LIP,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._lip: LIP = lip

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        self._writer.write_string("LIP ")
        self._writer.write_string("V1.0")
        self._writer.write_single(self._lip.length)
        self._writer.write_uint32(len(self._lip))

        for keyframe in self._lip:
            self._writer.write_single(keyframe.time)
            self._writer.write_uint8(keyframe.shape.value)
