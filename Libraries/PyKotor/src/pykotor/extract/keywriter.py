from __future__ import annotations

import struct
import time

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType


@dataclass
class Entry:
    file_name: str
    files: list[str]
    file_size: int


class KEYDataWriter(ABC):
    @abstractmethod
    def size(self) -> int:
        """Get the size of this data file, to write it into the KEY file.

        Returns:
            The total size of this data file
        """

    @abstractmethod
    def add(self, data: BinaryIO, type: ResourceType):
        """Add a stream of the specified type to the data writer.

        Args:
            data: the data to write
            type: the type of this data
        """


class KEYWriter:
    def __init__(self):
        self._entries: list[Entry] = []

    def add_bif(self, file_name: str, files: list[str], size: int):
        """Add a reference to a specific BIF/BZF file to this KEY file.

        Args:
            file_name: the filename of the specific BIF/BZF file
            files: the files contained in this BIF/BZF file
            size: total size of the bif file
        """
        self._entries.append(Entry(file_name, files, size))

    def write(self, write_stream: BinaryIO):
        """Write the collected information as KEY file to the specified WriteStream.

        Args:
            write_stream: The stream to write to
        """
        # Write header
        write_stream.write(struct.pack(">4s4s", b"KEY ", b"V1  "))

        # Number of BIF/BZF files
        write_stream.write(struct.pack("<I", len(self._entries)))

        total_count = sum(len(entry.files) for entry in self._entries)
        total_filename_size = sum(len(entry.file_name) for entry in self._entries)

        # Number of resources in all BIF/BZF files
        write_stream.write(struct.pack("<I", total_count))

        # Constant offset to the file table
        write_stream.write(struct.pack("<I", 64))

        # Calculate the key table offset
        key_table_offset = 64 + len(self._entries) * 12 + total_filename_size

        # Offset to the keytable
        write_stream.write(struct.pack("<I", key_table_offset))

        # Write the creation time of the file
        now = time.localtime()
        write_stream.write(struct.pack("<II", now.tm_year, now.tm_yday))

        # Reserved padding
        write_stream.write(b"\0" * 32)

        # Write file table
        filename_offset = 64 + len(self._entries) * 12
        for entry in self._entries:
            write_stream.write(struct.pack("<III", entry.file_size, filename_offset, len(entry.file_name)))
            filename_offset += len(entry.file_name)

        # Write file name table
        for entry in self._entries:
            write_stream.write(entry.file_name.encode("ascii"))

        # Write Key table
        for x, entry in enumerate(self._entries):
            for y, file in enumerate(entry.files):
                ResRef(file).write_to(write_stream)
                write_stream.write(struct.pack("<HI", ResourceType.from_extension(file.split(".")[-1]).type_id, (x << 20) + y))
