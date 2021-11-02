from __future__ import annotations

from typing import Optional

from pykotor.common.stream import BinaryReader, BinaryWriter

import pykotor.resource.formats.tlk
from pykotor.resource.type import ResourceType


class ERFBinaryReader:
    def __init__(self, reader: BinaryReader):
        self.reader: BinaryReader = reader
        self._erf: Optional[pykotor.resource.formats.erf.ERF] = None

    def load(self) -> pykotor.resource.formats.erf.ERF:
        self._erf = pykotor.resource.formats.erf.ERF()

        file_type = self.reader.read_string(4)
        file_version = self.reader.read_string(4)

        if not any(x for x in pykotor.resource.formats.erf.ERFType if x.value == file_type):
            raise TypeError("Not a valid ERF file.")

        if file_version != "V1.0":
            raise TypeError("The ERF version that was loaded is unsupported.")

        self.reader.skip(8)
        entry_count = self.reader.read_uint32()
        self.reader.skip(4)
        offset_to_keys = self.reader.read_uint32()
        offset_to_resources = self.reader.read_uint32()

        resrefs = []
        resids = []
        restypes = []
        self.reader.seek(offset_to_keys)
        for i in range(entry_count):
            resrefs.append(self.reader.read_string(16))
            resids.append(self.reader.read_uint32())
            restypes.append(self.reader.read_uint16())
            self.reader.skip(2)

        resoffsets = []
        ressizes = []
        self.reader.seek(offset_to_resources)
        for i in range(entry_count):
            resoffsets.append(self.reader.read_uint32())
            ressizes.append(self.reader.read_uint32())

        for i in range(entry_count):
            self.reader.seek(resoffsets[i])
            resdata = self.reader.read_bytes(ressizes[i])
            self._erf.set(resrefs[i], ResourceType.from_id(restypes[i]), resdata)

        self.reader.close()
        return self._erf


class ERFBinaryWriter:
    FILE_HEADER_SIZE = 160
    KEY_ELEMENT_SIZE = 24
    RESOURCE_ELEMENT_SIZE = 8

    def __init__(self, writer: BinaryWriter, erf: pykotor.resource.formats.erf.ERF):
        self.writer: BinaryWriter = writer
        self.erf = erf

    def write(self) -> bytes:
        entry_count = len(self.erf)
        offset_to_keys = ERFBinaryWriter.FILE_HEADER_SIZE
        offset_to_resources = offset_to_keys + ERFBinaryWriter.KEY_ELEMENT_SIZE * entry_count

        self.writer.write_string(self.erf.erf_type.value)
        self.writer.write_string("V1.0")
        self.writer.write_uint32(0)
        self.writer.write_uint32(0)
        self.writer.write_uint32(entry_count)
        self.writer.write_uint32(0)
        self.writer.write_uint32(offset_to_keys)
        self.writer.write_uint32(offset_to_resources)
        self.writer.write_uint32(0)
        self.writer.write_uint32(0)
        self.writer.write_uint32(0xFFFFFFFF)
        self.writer.write_bytes(b'\0' * 116)

        resid = 0
        for resource in self.erf:
            self.writer.write_string(resource.resref.get(), string_length=16)
            self.writer.write_uint32(resid)
            self.writer.write_uint16(resource.restype.type_id)
            self.writer.write_uint16(0)
            resid += 1

        data_offset = offset_to_resources + ERFBinaryWriter.RESOURCE_ELEMENT_SIZE * entry_count
        for resource in self.erf:
            self.writer.write_uint32(data_offset)
            self.writer.write_uint32(len(resource.data))
            data_offset += len(resource.data)

        for resource in self.erf:
            self.writer.write_bytes(resource.data)

        data = self.writer.data()
        self.writer.close()
        return data
