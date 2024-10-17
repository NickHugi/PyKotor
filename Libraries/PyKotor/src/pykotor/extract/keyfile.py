from __future__ import annotations

import struct

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO

from pykotor.resource.type import ResourceType


class Archive(ABC):
    # This is a placeholder for the Archive class.
    # You may need to implement or import the actual Archive class.
    pass


@dataclass
class Resource:
    name: str
    type: ResourceType
    bif_index: int
    res_index: int


class KEYDataFile(Archive):
    @abstractmethod
    def get_internal_resource_count(self) -> int:
        """Return the number of internal resources (including unmerged ones)."""

    @abstractmethod
    def merge_KEY(self, key: KEYFile, data_file_index: int) -> None:
        """Merge information from the KEY into the data file.

        Without this step, this data file archive does not contain any
        resource names at all.

        Args:
            key: A KEYFile with information about this data file.
            data_file_index: The index this data file has within the KEY file.
        """


class KEYFile:
    def __init__(self, key: BinaryIO):
        self._bifs: list[str] = []
        self._resources: list[Resource] = []
        self.load(key)

    def get_bifs(self) -> list[str]:
        """Return a list of all managed bifs."""
        return self._bifs

    def get_resources(self) -> list[Resource]:
        """Return a list of all containing resources."""
        return self._resources

    def load(self, key: BinaryIO):
        self._read_header(key)
        bif_offset = struct.unpack("<I", key.read(4))[0]
        resource_offset = struct.unpack("<I", key.read(4))[0]

        self._read_bif_list(key, bif_offset)
        self._read_res_list(key, resource_offset)

    def _read_header(self, key: BinaryIO):
        file_type = key.read(4)
        file_version = key.read(4)

        if file_type != b"KEY ":
            raise ValueError("Not a KEY file")

        if file_version not in [b"V1  ", b"V1.1"]:
            raise ValueError(f"Unsupported KEY file version: {file_version}")

        self.bif_count = struct.unpack("<I", key.read(4))[0]
        self.resource_count = struct.unpack("<I", key.read(4))[0]

    def _read_bif_list(self, key: BinaryIO, offset: int):
        key.seek(offset)
        for _ in range(self.bif_count):
            size = struct.unpack("<I", key.read(4))[0]
            data_offset = struct.unpack("<I", key.read(4))[0]

            current_pos = key.tell()
            key.seek(data_offset)
            bif_name = key.read(size).decode("ascii").rstrip("\0")
            self._bifs.append(bif_name)
            key.seek(current_pos)

    def _read_res_list(self, key: BinaryIO, offset: int):
        key.seek(offset)
        for _ in range(self.resource_count):
            name = key.read(16).decode("ascii").rstrip("\0")
            res_type = struct.unpack("<H", key.read(2))[0]
            res_id = struct.unpack("<I", key.read(4))[0]

            bif_index = res_id >> 20
            res_index = res_id & 0xFFFFF

            resource = Resource(name, ResourceType(res_type), bif_index, res_index)
            self._resources.append(resource)
