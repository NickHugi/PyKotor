from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.type import ResourceReader, ResourceType, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.formats.bif.bif_data import BIF, BIFResource
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

BIFF_ID = b"BIFF"
V1_ID = b"V1  "


class BIFBinaryReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._bif: BIF | None = None

    @autoclose
    def load(self) -> BIF:
        from pykotor.resource.formats.bif.bif_data import BIF, BIFResource, BIFType

        self._bif = BIF()

        # Read header
        file_type = self._reader.read_bytes(4)
        file_version = self._reader.read_bytes(4)

        if file_type not in (BIFF_ID, b"BZF "):
            raise ValueError(f"Not a BIF/BZF file: {file_type}")
        if file_version != V1_ID:
            raise ValueError(f"Unsupported BIF/BZF version: {file_version}")

        self._bif.bif_type = BIFType.BZF if file_type == b"BZF " else BIFType.BIF

        var_res_count = self._reader.read_uint32()
        fix_res_count = self._reader.read_uint32()
        offset_to_resource_table = self._reader.read_uint32()

        if fix_res_count != 0:
            raise NotImplementedError("Fixed BIF/BZF resources are not supported yet")

        # Read resource table
        self._reader.seek(offset_to_resource_table)
        for _ in range(var_res_count):
            resource = BIFResource()
            resource.offset = self._reader.read_uint32()
            resource.size = self._reader.read_uint32()
            resource.restype = ResourceType(self._reader.read_uint32())
            self._bif._resources.append(resource)

        # Calculate packed sizes for BZF
        if self._bif.bif_type == BIFType.BZF:
            for i in range(len(self._bif._resources) - 1):
                self._bif._resources[i].packed_size = self._bif._resources[i + 1].offset - self._bif._resources[i].offset

            if self._bif._resources:
                self._bif._resources[-1].packed_size = self._reader.size() - self._bif._resources[-1].offset

        return self._bif


class BIFBinaryWriter(ResourceWriter):
    FILE_HEADER_SIZE = 20
    RESOURCE_ELEMENT_SIZE = 12

    def __init__(self, bif: BIF, target: TARGET_TYPES):
        super().__init__(target)
        self._bif: BIF = bif
        self._max_files: int = len(self._bif._resources)
        self._current_files: int = 0
        self._data_offset: int = 0

    @autoclose
    def write(self):
        # Write header
        self._writer.write_bytes(BIFF_ID if self._bif.bif_type == self._bif.BIFType.BIF else b"BZF ")
        self._writer.write_bytes(V1_ID)
        self._writer.write_uint32(self._max_files)
        self._writer.write_uint32(0)  # Fixed resource count
        self._writer.write_uint32(self.FILE_HEADER_SIZE)

        # Reserve space for resource table
        self._writer.write_bytes(b"\0" * (self._max_files * self.RESOURCE_ELEMENT_SIZE))

        # Write resource data
        for resource in self._bif._resources:
            self._write_resource(resource)

    def _write_resource(self, resource: BIFResource):
        if self._current_files >= self._max_files:
            raise ValueError("Attempt to write more files than maximum")

        # Write resource data
        self._writer.seek(0, 2)  # Seek to end of file
        data_offset = self._writer.position()
        self._writer.write_bytes(resource.data)

        # Write resource table entry
        self._writer.seek(self.FILE_HEADER_SIZE + self._current_files * self.RESOURCE_ELEMENT_SIZE)
        self._writer.write_uint32(data_offset)  # Data offset
        self._writer.write_uint32(len(resource.data))  # File size
        self._writer.write_uint32(resource.restype.value)  # Type

        self._current_files += 1
        self._data_offset += len(resource.data)

    def size(self) -> int:
        return self._writer.position()
