from __future__ import annotations

import os
import struct
import time

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO

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
    def add(
        self,
        data: BinaryIO,
        restype: ResourceType,
    ) -> None:
        """Add a stream of the specified type to the data writer.

        Args:
            data: the data to write
            type: the type of this data
        """


class KEYWriter:
    """Writes KEY (Keyfile) files.
    
    KEY files index BIF/BZF archives and provide resource lookup tables. This writer
    creates KEY files by collecting BIF entries and their contained resources.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/keyreader.cpp (KEY reading structure)
        vendor/reone/include/reone/resource/format/keyreader.h (KEY structure)
        vendor/xoreos-tools/src/xml/keydumper.cpp (KEY to XML conversion)
        vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEY.cs (KEY structure)
        vendor/KotOR.js/src/resource/KEYObject.ts (KEY loading)
        Note: KEY writing is uncommon in vendor implementations; most tools only read KEY files.
        PyKotor's KEYWriter is primarily for modding and tooling purposes.
    
    Missing Features:
    ----------------
        - ResRef lowercasing (vendor implementations lowercase ResRefs)
        - Resource ID decomposition (vendor implementations decompose resource IDs)
        - BZF compression support (vendor implementations handle compressed BIFs)
    """
    def __init__(self):
        self._entries: list[Entry] = []

    def add_bif(
        self,
        file_name: str,
        files: list[str],
        size: int,
    ) -> None:
        """Add a reference to a specific BIF/BZF file to this KEY file.

        Args:
            file_name: the filename of the specific BIF/BZF file
            files: the files contained in this BIF/BZF file
            size: total size of the bif file
        """
        self._entries.append(Entry(file_name, files, size))

    def write(
        self,
        write_stream: BinaryIO,
    ) -> None:
        """Write the collected information as KEY file to the specified WriteStream.

        Args:
            write_stream: The stream to write to
        
        References:
        ----------
            vendor/reone/src/libs/resource/format/keyreader.cpp:26-40 (KEY header structure)
            vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYReader.cs (KEY reading)
            KEY file format: 8-byte signature, BIF count, resource count, offsets, timestamps
        """
        # Write header
        # vendor/reone/src/libs/resource/format/keyreader.cpp:26-28 (signature reading)
        write_stream.write(struct.pack(">4s4s", b"KEY ", b"V1  "))

        # Number of BIF/BZF files
        write_stream.write(struct.pack("<I", len(self._entries)))

        total_count: int = sum(len(entry.files) for entry in self._entries)
        total_filename_size: int = sum(len(entry.file_name) for entry in self._entries)

        # Number of resources in all BIF/BZF files
        write_stream.write(struct.pack("<I", total_count))

        # Constant offset to the file table
        write_stream.write(struct.pack("<I", 64))

        # Calculate the key table offset
        key_table_offset: int = 64 + len(self._entries) * 12 + total_filename_size

        # Offset to the keytable
        write_stream.write(struct.pack("<I", key_table_offset))

        # Write the creation time of the file
        now: time.struct_time = time.localtime()
        write_stream.write(struct.pack("<II", now.tm_year, now.tm_yday))

        # Reserved padding
        write_stream.write(b"\0" * 32)

        # Write file table
        filename_offset: int = 64 + len(self._entries) * 12
        for entry in self._entries:
            write_stream.write(struct.pack("<III", entry.file_size, filename_offset, len(entry.file_name)))
            filename_offset += len(entry.file_name)

        # Write file name table
        for entry in self._entries:
            write_stream.write(entry.file_name.encode("ascii"))

        # Write Key table
        for x, entry in enumerate(self._entries):
            for y, file in enumerate(entry.files):
                write_stream.write(os.path.basename(file).encode("ascii"))  # noqa: PTH119
                write_stream.write(struct.pack("<HI", ResourceType.from_extension(file.split(".")[-1]).type_id, (x << 20) + y))
