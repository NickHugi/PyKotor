from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.type import ResourceReader, ResourceType, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class RIMBinaryReader(ResourceReader):
    """Reads RIM (Resource Information Manager) files.
    
    RIM files are container formats similar to ERF files, used for module resources.
    They store multiple game resources with ResRef, type, and data.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/rimreader.cpp:26-58 (RIM reading)
        vendor/reone/src/libs/resource/format/rimwriter.cpp (RIM writing)
        vendor/xoreos-tools/src/unrim.cpp (RIM extraction tool)
    
    Missing Features:
    ----------------
        - ResRef lowercasing (reone lowercases resrefs at rimreader.cpp:47)
        - Field order difference: PyKotor reads restype, resids, resoffsets, ressizes
          vs reone which reads resRef, type (uint16), skips 6 bytes, offset, size
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._rim: RIM | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> RIM:  # noqa: FBT001, FBT002, ARG002
        self._rim = RIM()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "RIM ":
            msg = "The RIM file type that was loaded was unrecognized."
            raise ValueError(msg)

        if file_version != "V1.0":
            msg = "The RIM version that was loaded is not supported."
            raise ValueError(msg)

        self._reader.skip(4)
        entry_count = self._reader.read_uint32()
        offset_to_keys = self._reader.read_uint32()

        resrefs: list[str] = []
        resids: list[int] = []
        restypes: list[int] = []
        resoffsets: list[int] = []
        ressizes: list[int] = []
        self._reader.seek(offset_to_keys)
        for _ in range(entry_count):
            # vendor/reone/src/libs/resource/format/rimreader.cpp:46-58
            # reone lowercases resref at line 47
            # NOTE: Field order differs - PyKotor reads restype before resids, reone reads differently
            resref_str = self._reader.read_string(16).rstrip("\0")
            resrefs.append(resref_str.lower())
            restypes.append(self._reader.read_uint32())
            resids.append(self._reader.read_uint32())
            resoffsets.append(self._reader.read_uint32())
            ressizes.append(self._reader.read_uint32())

        for i in range(entry_count):
            self._reader.seek(resoffsets[i])
            resdata = self._reader.read_bytes(ressizes[i])
            self._rim.set_data(resrefs[i], ResourceType.from_id(restypes[i]), resdata)

        return self._rim


class RIMBinaryWriter(ResourceWriter):
    FILE_HEADER_SIZE = 120
    KEY_ELEMENT_SIZE = 32

    def __init__(
        self,
        rim: RIM,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._rim: RIM = rim

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        entry_count = len(self._rim)
        offset_to_keys = RIMBinaryWriter.FILE_HEADER_SIZE

        self._writer.write_string("RIM ")
        self._writer.write_string("V1.0")
        self._writer.write_uint32(0)
        self._writer.write_uint32(entry_count)
        self._writer.write_uint32(offset_to_keys)
        self._writer.write_bytes(b"\0" * 100)

        data_offset = offset_to_keys + RIMBinaryWriter.KEY_ELEMENT_SIZE * entry_count
        for resid, resource in enumerate(self._rim):
            self._writer.write_string(str(resource.resref), string_length=16)
            self._writer.write_uint32(resource.restype.type_id)
            self._writer.write_uint32(resid)
            self._writer.write_uint32(data_offset)
            self._writer.write_uint32(len(resource.data))
            data_offset += len(resource.data)

        for resource in self._rim:
            self._writer.write_bytes(resource.data)
