from __future__ import annotations

from pykotor.resource.formats.erf import ERF, ERFType
from pykotor.resource.type import (
    SOURCE_TYPES,
    TARGET_TYPES,
    ResourceReader,
    ResourceType,
    ResourceWriter,
    autoclose,
)


class ERFBinaryReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._erf: ERF | None = None

    @autoclose
    def load(self, auto_close: bool = True) -> ERF:
        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        erf_type_map = {x.value: x for x in ERFType}

        if file_type not in erf_type_map:
            msg = f"Not a valid ERF file: '{file_type}'"
            raise ValueError(msg)

        self._erf = ERF(erf_type_map.get(file_type))  # type: ignore  # noqa: PGH003

        if file_version != "V1.0":
            msg = f"ERF version '{file_version}' is unsupported."
            raise ValueError(msg)

        self._reader.skip(8)
        entry_count = self._reader.read_uint32()
        self._reader.skip(4)
        offset_to_keys = self._reader.read_uint32()
        offset_to_resources = self._reader.read_uint32()

        resrefs = [None] * entry_count
        resids = [None] * entry_count
        restypes = [None] * entry_count
        self._reader.seek(offset_to_keys)
        keys_data = self._reader.read_bytes(
            24 * entry_count,
        )  # 16 bytes for resref, 4 for resid, 2 for restype, 2 skipped

        for i in range(entry_count):
            resref_data = keys_data[i * 24 : i * 24 + 16].split(b"\0")[0]
            resrefs[i] = resref_data.decode("windows-1252")
            resids[i] = int.from_bytes(
                keys_data[i * 24 + 16 : i * 24 + 20],
                byteorder="little",
            )
            restypes[i] = int.from_bytes(
                keys_data[i * 24 + 20 : i * 24 + 22],
                byteorder="little",
            )

        resoffsets = [None] * entry_count
        ressizes = [None] * entry_count
        self._reader.seek(offset_to_resources)
        resources_data = self._reader.read_bytes(8 * entry_count)

        for i in range(entry_count):
            resoffsets[i] = int.from_bytes(
                resources_data[i * 8 : i * 8 + 4],
                byteorder="little",
            )
            ressizes[i] = int.from_bytes(
                resources_data[i * 8 + 4 : i * 8 + 8],
                byteorder="little",
            )

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
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.erf = erf

    @autoclose
    def write(
        self,
        auto_close: bool = True,
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
        self._writer.write_bytes(b"\0" * 116)

        for resid, resource in enumerate(self.erf):
            self._writer.write_string(resource.resref.get(), string_length=16)
            self._writer.write_uint32(resid)
            self._writer.write_uint16(resource.restype.type_id)
            self._writer.write_uint16(0)
        data_offset = offset_to_resources + ERFBinaryWriter.RESOURCE_ELEMENT_SIZE * entry_count
        for resource in self.erf:
            self._writer.write_uint32(data_offset)
            self._writer.write_uint32(len(resource.data))
            data_offset += len(resource.data)

        for resource in self.erf:
            self._writer.write_bytes(resource.data)
