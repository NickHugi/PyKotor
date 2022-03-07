from __future__ import annotations

from typing import Optional

from pykotor.resource.formats.rim import RIM
from pykotor.resource.type import ResourceType, SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter


class RIMBinaryReader(ResourceReader):
    def __init__(
            self,
            source: SOURCE_TYPES,
            offset: int = 0,
            size: int = 0
    ):
        super().__init__(source, offset, size)
        self._rim: Optional[RIM] = None

    def load(
            self,
            auto_close: bool = True
    ) -> RIM:
        self._rim = RIM()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "RIM ":
            raise TypeError("The RIM file type that was loaded was unrecognized.")

        if file_version != "V1.0":
            raise TypeError("The RIM version that was loaded is not supported.")

        self._reader.skip(4)
        entry_count = self._reader.read_uint32()
        offset_to_keys = self._reader.read_uint32()

        resrefs = []
        resids = []
        restypes = []
        resoffsets = []
        ressizes = []
        self._reader.seek(offset_to_keys)
        for i in range(entry_count):
            resrefs.append(self._reader.read_string(16))
            restypes.append(self._reader.read_uint32())
            resids.append(self._reader.read_uint32())
            resoffsets.append(self._reader.read_uint32())
            ressizes.append(self._reader.read_uint32())

        for i in range(entry_count):
            self._reader.seek(resoffsets[i])
            resdata = self._reader.read_bytes(ressizes[i])
            self._rim.set(resrefs[i], ResourceType.from_id(restypes[i]), resdata)

        if auto_close:
            self._reader.close()

        return self._rim


class RIMBinaryWriter(ResourceWriter):
    FILE_HEADER_SIZE = 120
    KEY_ELEMENT_SIZE = 32

    def __init__(
            self,
            rim: RIM,
            target: TARGET_TYPES
    ):
        super().__init__(target)
        self._rim = rim

    def write(
            self,
            auto_close: bool = True
    ) -> None:
        entry_count = len(self._rim)
        offset_to_keys = RIMBinaryWriter.FILE_HEADER_SIZE

        self._writer.write_string("RIM ")
        self._writer.write_string("V1.0")
        self._writer.write_uint32(0)
        self._writer.write_uint32(entry_count)
        self._writer.write_uint32(offset_to_keys)
        self._writer.write_bytes(b'\0' * 100)

        resid = 0
        data_offset = offset_to_keys + RIMBinaryWriter.KEY_ELEMENT_SIZE * entry_count
        for resource in self._rim:
            self._writer.write_string(resource.resref.get(), string_length=16)
            self._writer.write_uint32(resource.restype.type_id)
            self._writer.write_uint32(resid)
            self._writer.write_uint32(data_offset)
            self._writer.write_uint32(len(resource.data))
            resid += 1
            data_offset += len(resource.data)

        for resource in self._rim:
            self._writer.write_bytes(resource.data)

        if auto_close:
            self._writer.close()
