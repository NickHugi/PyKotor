from __future__ import annotations

from typing import Optional

from pykotor.resource.formats.erf import ERF, ERFType
from pykotor.resource.type import ResourceType, TARGET_TYPES, ResourceReader, SOURCE_TYPES, ResourceWriter, autoclose


class ERFBinaryReader(ResourceReader):
    def __init__(
            self,
            source: SOURCE_TYPES,
            offset: int = 0,
            size: int = 0
    ):
        super().__init__(source, offset, size)
        self._erf: Optional[ERF] = None

    @autoclose
    def load(
            self,
            auto_close: bool = True
    ) -> ERF:
        self._erf = ERF()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if not any(x for x in ERFType if x.value == file_type):
            raise ValueError("Not a valid ERF file.")

        if file_version != "V1.0":
            raise ValueError("The ERF version that was loaded is unsupported.")

        self._reader.skip(8)
        entry_count = self._reader.read_uint32()
        self._reader.skip(4)
        offset_to_keys = self._reader.read_uint32()
        offset_to_resources = self._reader.read_uint32()

        resrefs = []
        resids = []
        restypes = []
        self._reader.seek(offset_to_keys)
        for i in range(entry_count):
            resrefs.append(self._reader.read_string(16))
            resids.append(self._reader.read_uint32())
            restypes.append(self._reader.read_uint16())
            self._reader.skip(2)

        resoffsets = []
        ressizes = []
        self._reader.seek(offset_to_resources)
        for i in range(entry_count):
            resoffsets.append(self._reader.read_uint32())
            ressizes.append(self._reader.read_uint32())

        for i in range(entry_count):
            self._reader.seek(resoffsets[i])
            resdata = self._reader.read_bytes(ressizes[i])
            self._erf.set(resrefs[i], ResourceType.from_id(restypes[i]), resdata)

        return self._erf


class ERFBinaryWriter(ResourceWriter):
    FILE_HEADER_SIZE = 160
    KEY_ELEMENT_SIZE = 24
    RESOURCE_ELEMENT_SIZE = 8

    def __init__(
            self,
            erf: ERF,
            target: TARGET_TYPES
    ):
        super().__init__(target)
        self.erf = erf

    @autoclose
    def write(
            self,
            auto_close: bool = True
    ) -> None:
        entry_count = len(self.erf)
        offset_to_keys = ERFBinaryWriter.FILE_HEADER_SIZE
        offset_to_resources = offset_to_keys + ERFBinaryWriter.KEY_ELEMENT_SIZE * entry_count

        self._writer.write_string(self.erf.erf_type.value)
        self._writer.write_string("V1.0")
        self._writer.write_uint32(0)
        self._writer.write_uint32(0)
        self._writer.write_uint32(entry_count)
        self._writer.write_uint32(0)
        self._writer.write_uint32(offset_to_keys)
        self._writer.write_uint32(offset_to_resources)
        self._writer.write_uint32(0)
        self._writer.write_uint32(0)
        self._writer.write_uint32(0xFFFFFFFF)
        self._writer.write_bytes(b'\0' * 116)

        resid = 0
        for resource in self.erf:
            self._writer.write_string(resource.resref.get(), string_length=16)
            self._writer.write_uint32(resid)
            self._writer.write_uint16(resource.restype.type_id)
            self._writer.write_uint16(0)
            resid += 1

        data_offset = offset_to_resources + ERFBinaryWriter.RESOURCE_ELEMENT_SIZE * entry_count
        for resource in self.erf:
            self._writer.write_uint32(data_offset)
            self._writer.write_uint32(len(resource.data))
            data_offset += len(resource.data)

        for resource in self.erf:
            self._writer.write_bytes(resource.data)
