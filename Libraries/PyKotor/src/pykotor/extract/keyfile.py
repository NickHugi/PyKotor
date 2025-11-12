from __future__ import annotations

import struct

from abc import abstractmethod
from dataclasses import dataclass
from typing import BinaryIO

from pykotor.resource.bioware_archive import ArchiveResource
from pykotor.resource.type import ResourceType


@dataclass
class BIFResource:
    name: str
    type: ResourceType
    bif_index: int
    res_index: int


class KEYDataFile(ArchiveResource):
    @abstractmethod
    def get_internal_resource_count(self) -> int:
        """Return the number of internal resources (including unmerged ones)."""

    @abstractmethod
    def merge_key(
        self,
        key: KEYFile,
        data_file_index: int,
    ) -> None:
        """Merge information from the KEY into the data file.

        Without this step, this data file archive does not contain any
        resource names at all.

        Args:
            key: A KEYFile with information about this data file.
            data_file_index: The index this data file has within the KEY file.
        """


class KEYFile:
    """Reads KEY files for resource indexing.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/keyreader.cpp:26-65 (KEY reading)
        vendor/xoreos-tools/src/unkeybif.cpp (KEY/BIF extraction tool)
    """
    def __init__(
        self,
        key: BinaryIO,
    ) -> None:
        self._bifs: list[str] = []
        self._resources: list[BIFResource] = []
        self.load(key)

    def get_bifs(self) -> list[str]:
        """Return a list of all managed bifs."""
        return self._bifs

    def get_resources(self) -> list[BIFResource]:
        """Return a list of all containing resources."""
        return self._resources

    def load(
        self,
        key: BinaryIO,
    ) -> None:
        self._read_header(key)
        bif_offset: int = struct.unpack("<I", key.read(4))[0]
        self._read_bif_list(key, bif_offset)

        resource_offset: int = struct.unpack("<I", key.read(4))[0]
        self._read_res_list(key, resource_offset)

    def _read_header(
        self,
        key: BinaryIO,
    ) -> None:
        # vendor/reone/src/libs/resource/format/keyreader.cpp:26-30
        file_type: bytes = key.read(4)
        file_version: bytes = key.read(4)

        if file_type != b"KEY ":
            raise ValueError("Not a KEY file")

        if file_version not in [b"V1  ", b"V1.1"]:
            raise ValueError(f"Unsupported KEY file version: {file_version}")

        self.bif_count: int = struct.unpack("<I", key.read(4))[0]
        self.resource_count: int = struct.unpack("<I", key.read(4))[0]

    def _read_bif_list(
        self,
        key: BinaryIO,
        offset: int,
    ) -> None:
        key.seek(offset)
        for _ in range(self.bif_count):
            size: int = struct.unpack("<I", key.read(4))[0]
            data_offset: int = struct.unpack("<I", key.read(4))[0]

            current_pos: int = key.tell()
            key.seek(data_offset)
            bif_name: str = key.read(size).decode("ascii").rstrip("\0")
            self._bifs.append(bif_name)
            key.seek(current_pos)

    def _read_res_list(
        self,
        key: BinaryIO,
        offset: int,
    ) -> None:
        # vendor/reone/src/libs/resource/format/keyreader.cpp:70-86
        key.seek(offset)
        for _ in range(self.resource_count):
            name: str = key.read(16).decode("ascii").rstrip("\0")
            res_type: int = struct.unpack("<H", key.read(2))[0]
            res_id: int = struct.unpack("<I", key.read(4))[0]

            # vendor/reone/src/libs/resource/format/keyreader.cpp:73-74
            # Decompose resource_id into bif_index (upper 12 bits) and res_index (lower 20 bits)
            bif_index: int = res_id >> 20
            res_index: int = res_id & 0xFFFFF

            resource: BIFResource = BIFResource(name, ResourceType(res_type), bif_index, res_index)
            self._resources.append(resource)
