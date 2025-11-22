"""This module handles reading and writing KEY files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.resource.formats.key.key_data import KEY, BifEntry, KeyEntry
from pykotor.resource.type import ResourceReader, ResourceType, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class KEYBinaryReader(ResourceReader):
    """Reads KEY files.
    
    KEY files index game resources stored in BIF files. They contain references to BIF files
    and resource entries that map ResRefs to locations within those BIF files.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/keyreader.cpp:26-65 (KEY reading)
        vendor/xoreos-tools/src/unkeybif.cpp (KEY/BIF extraction tool)
    
    Missing Features:
    ----------------
        - ResRef lowercasing (reone lowercases resrefs)
        - Resource ID decomposition (reone decomposes resource_id into bif_index/resource_index)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self.key: KEY = KEY()

    @autoclose
    def load(self, *, auto_close: bool = True) -> KEY:  # noqa: FBT001, FBT002, ARG002
        """Load KEY data from source."""
        # vendor/reone/src/libs/resource/format/keyreader.cpp:26-65
        # Read signature
        self.key.file_type = self._reader.read_string(4)
        self.key.file_version = self._reader.read_string(4)

        if self.key.file_type != KEY.FILE_TYPE:
            msg = f"Invalid KEY file type: {self.key.file_type}"
            raise ValueError(msg)

        if self.key.file_version != KEY.FILE_VERSION:
            msg = f"Unsupported KEY version: {self.key.file_version}"
            raise ValueError(msg)

        # Read counts and offsets
        bif_count: int = self._reader.read_uint32()
        key_count: int = self._reader.read_uint32()
        file_table_offset: int = self._reader.read_uint32()
        key_table_offset: int = self._reader.read_uint32()

        # Read build info
        self.key.build_year = self._reader.read_uint32()
        self.key.build_day = self._reader.read_uint32()

        # there's 32 bytes of reserved bytes here.

        # Read file table
        self._reader.seek(file_table_offset)
        for _ in range(bif_count):
            bif: BifEntry = BifEntry()
            bif.filesize = self._reader.read_uint32()
            filename_offset: int = self._reader.read_uint32()
            filename_size: int = self._reader.read_uint16()
            bif.drives = self._reader.read_uint16()

            # Save current position
            current_pos: int = self._reader.position()

            # Read filename
            self._reader.seek(filename_offset)
            bif.filename = self._reader.read_string(filename_size).rstrip("\0").replace("\\", "/").lstrip("/")

            # Restore position
            self._reader.seek(current_pos)
            self.key.bif_entries.append(bif)

        # Read key table
        self._reader.seek(key_table_offset)
        for _ in range(key_count):
            entry: KeyEntry = KeyEntry()
            # vendor/reone/src/libs/resource/format/keyreader.cpp:45-50
            # reone lowercases resref at line 46
            resref_str = self._reader.read_string(16).rstrip("\0").lower()
            entry.resref = ResRef(resref_str)
            entry.restype = ResourceType.from_id(self._reader.read_uint16())
            # vendor/reone/src/libs/resource/format/keyreader.cpp:51-52
            # NOTE: reone decomposes resource_id into bif_index/resource_index, PyKotor stores as-is
            entry.resource_id = self._reader.read_uint32()
            self.key.key_entries.append(entry)

        self.key.build_lookup_tables()

        return self.key


class KEYBinaryWriter(ResourceWriter):
    """Writes KEY files."""

    def __init__(
        self,
        key: KEY,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.key: KEY = key

    @autoclose
    def write(self, *, auto_close: bool = True) -> None:  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Write KEY data to target."""
        self._write_header()
        self._write_file_table()
        self._write_key_table()

    def _write_header(self) -> None:
        """Write KEY file header."""
        # Write signature
        self._writer.write_string(self.key.file_type)
        self._writer.write_string(self.key.file_version)

        # Write counts
        self._writer.write_uint32(len(self.key.bif_entries))
        self._writer.write_uint32(len(self.key.key_entries))

        # Write table offsets
        self._writer.write_uint32(self.key.calculate_file_table_offset())
        self._writer.write_uint32(self.key.calculate_key_table_offset())

        # Write build info
        self._writer.write_uint32(self.key.build_year)
        self._writer.write_uint32(self.key.build_day)

        # Write reserved bytes
        self._writer.write_bytes(b"\0" * 32)

    def _write_file_table(self) -> None:
        """Write BIF file table."""
        # Write file entries
        for i, bif in enumerate(self.key.bif_entries):
            self._writer.write_uint32(bif.filesize)
            self._writer.write_uint32(self.key.calculate_filename_offset(i))
            self._writer.write_uint16(len(bif.filename) + 1)  # +1 for null terminator
            self._writer.write_uint16(bif.drives)

        # Write filenames
        for bif in self.key.bif_entries:
            self._writer.write_string(bif.filename)
            self._writer.write_uint8(0)  # Null terminator

    def _write_key_table(self) -> None:
        """Write resource key table."""
        for entry in self.key.key_entries:
            # Write ResRef (padded with nulls to 16 bytes)
            resref: str = str(entry.resref)
            self._writer.write_string(resref)
            self._writer.write_bytes(b"\0" * (16 - len(resref)))

            # Write type and ID
            self._writer.write_uint16(entry.restype.type_id)
            self._writer.write_uint32(entry.resource_id)
