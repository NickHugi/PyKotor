from __future__ import annotations

from typing import Optional

from pykotor.resource.formats.lip import LIP, LIPShape
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter, autoclose


class LIPBinaryReader(ResourceReader):
    def __init__(
            self,
            source: SOURCE_TYPES,
            offset: int = 0,
            size: int = 0
    ):
        super().__init__(source, offset, size)
        self._lip: Optional[LIP] = None

    @autoclose
    def load(
            self,
            auto_close: bool = True
    ) -> LIP:
        self._lip = LIP()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "LIP ":
            raise TypeError("The file type that was loaded is invalid.")

        if file_version != "V1.0":
            raise TypeError("The LIP version that was loaded is not supported.")

        self._lip.length = self._reader.read_single()
        entry_count = self._reader.read_uint32()

        for i in range(entry_count):
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
            target: TARGET_TYPES
    ):
        super().__init__(target)
        self._lip: LIP = lip

    @autoclose
    def write(
            self,
            auto_close: bool = True
    ) -> None:
        self._writer.write_string("LIP ")
        self._writer.write_string("V1.0")
        self._writer.write_single(self._lip.length)
        self._writer.write_uint32(len(self._lip))

        for keyframe in self._lip:
            self._writer.write_single(keyframe.time)
            self._writer.write_uint8(keyframe.shape.value)
