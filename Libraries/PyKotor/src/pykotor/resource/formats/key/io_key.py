from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.extract.file import ResRef
from pykotor.resource.formats.key.key_data import KEY, BifEntry, KeyEntry
from pykotor.resource.type import ResourceReader, ResourceType, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import TARGET_TYPES


class KEYBinaryReader(ResourceReader):
    def __init__(self, source: str, offset: int, size: int):
        super().__init__(source, offset, size)
        self.key.bif_entries = []
        self.key: KEY = KEY()

    @autoclose
    def load(self) -> KEY:
        self._read_header()
        self._read_file_table()
        self._read_key_table()
        return self.key

    def _read_header(self):
        self.key.file_type = self._reader.read_string(4)
        self.key.file_version = self._reader.read_string(4)
        self.key.bif_count = self._reader.read_uint32()
        self.key.key_count = self._reader.read_uint32()
        self.key.offset_to_file_table = self._reader.read_uint32()
        self.key.offset_to_key_table = self._reader.read_uint32()
        self.key.build_year = self._reader.read_uint32()
        self.key.build_day = self._reader.read_uint32()

    def _read_file_table(self):
        self._reader.seek(self.key.offset_to_file_table)
        for _ in range(self.key.bif_count):
            entry = BifEntry()
            entry.filesize = self._reader.read_uint32()
            entry.filename_offset = self._reader.read_uint32()
            entry.filename_size = self._reader.read_uint16()
            entry.drives = self._reader.read_uint16()
            self.key.bif_entries.append(entry)

        for entry in self.key.bif_entries:
            self._reader.seek(entry.filename_offset)
            entry.filename = self._reader.read_string(entry.filename_size)

    def _read_key_table(self):
        self._reader.seek(self.key.offset_to_key_table)
        for _ in range(self.key.key_count):
            entry = KeyEntry()
            entry.resref = ResRef(self._reader.read_string(16).strip("\0"))
            entry.type = ResourceType(self._reader.read_uint16())
            entry.resource_id = self._reader.read_uint32()
            self.key.key_entries.append(entry)


class KEYBinaryWriter(ResourceWriter):
    def __init__(self, key: KEY, target: TARGET_TYPES):
        super().__init__(target)
        self.key_entries: list[KEY] = []
        self.key: KEY = key

    def write(self):
        self._write_header()
        self._write_file_table()
        self._write_key_table()

    def _write_header(self):
        self._writer.write_string(self.key.file_type)
        self._writer.write_string(self.key.file_version)
        self._writer.write_uint32(self.key.bif_count)
        self._writer.write_uint32(self.key.key_count)
        self._writer.write_uint32(self.key.offset_to_file_table)
        self._writer.write_uint32(self.key.offset_to_key_table)
        self._writer.write_uint32(self.key.build_year)
        self._writer.write_uint32(self.key.build_day)

    def _write_file_table(self):
        for entry in self.key.bif_entries:
            self._writer.write_uint32(entry.filesize)
            self._writer.write_uint32(entry.filename_offset)
            self._writer.write_uint16(entry.filename_size)
            self._writer.write_uint16(entry.drives)

        for entry in self.key.bif_entries:
            self._writer.write_string(entry.filename)

    def _write_key_table(self):
        for entry in self.key.key_entries:
            self._writer.write_string(str(entry.resref).ljust(16, "\0"))
            self._writer.write_uint16(entry.type.value)
            self._writer.write_uint32(entry.resource_id)