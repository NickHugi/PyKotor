from __future__ import annotations

from typing import Literal

from pykotor.common.language import Language
from pykotor.common.misc import ResRef, WrappedInt
from pykotor.common.stream import ArrayHead
from pykotor.resource.formats.tlk import TLK, TLKEntry
from pykotor.resource.type import (
    SOURCE_TYPES,
    TARGET_TYPES,
    ResourceReader,
    ResourceWriter,
    autoclose,
)

_FILE_HEADER_SIZE = 20
_ENTRY_SIZE = 40


class TLKBinaryReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._tlk: TLK | None = None
        self._texts_offset = 0
        self._text_headers = []

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> TLK:
        self._tlk = TLK()
        self._texts_offset = 0
        self._text_headers = []

        self._reader.seek(0)

        self._load_file_header()
        for stringref, _entry in self._tlk:
            self._load_entry(stringref)
        for stringref, _entry in self._tlk:
            self._load_text(stringref)

        return self._tlk

    def _load_file_header(
        self,
    ):
        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)
        language_id = self._reader.read_uint32()
        string_count = self._reader.read_uint32()
        entries_offset = self._reader.read_uint32()

        if file_version != "V3.0":
            msg = "Invalid file version."
            raise ValueError(msg)
        if file_type != "TLK ":
            msg = "Invalid file type."
            raise ValueError(msg)

        self._tlk.language = Language(language_id)
        self._tlk.resize(string_count)

        self._texts_offset = entries_offset

    def _load_entry(
        self,
        stringref: int,
    ):
        self._reader.read_uint32()  # unused - flags
        sound_resref = self._reader.read_string(16)
        self._reader.read_uint32()  # unused - volume variance
        self._reader.read_uint32()  # unused - pitch variance
        text_offset = self._reader.read_uint32()
        text_length = self._reader.read_uint32()
        self._reader.read_single()  # unused - sound length

        self._tlk.entries[stringref].voiceover = ResRef(sound_resref)

        self._text_headers.append(ArrayHead(text_offset, text_length))

    def _load_text(
        self,
        stringref: int,
    ):
        text_header = self._text_headers[stringref]

        self._reader.seek(text_header.offset + self._texts_offset)
        text = self._reader.read_string(text_header.length)

        self._tlk.entries[stringref].text = text


class TLKBinaryWriter(ResourceWriter):
    def __init__(
        self,
        tlk: TLK,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tlk = tlk

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        self._write_file_header()

        text_offset = WrappedInt(0)
        for entry in self._tlk.entries:
            self._write_entry(entry, text_offset)

        encoding = self._tlk.language.get_encoding()
        for entry in self._tlk.entries:
            self._writer.write_string(entry.text, encoding)

    def _calculate_entries_offset(
        self,
    ) -> int:
        return _FILE_HEADER_SIZE + len(self._tlk) * _ENTRY_SIZE

    def _write_file_header(
        self,
    ) -> None:
        language_id = self._tlk.language.value
        string_count: int = len(self._tlk)
        entries_offset: int = self._calculate_entries_offset()

        self._writer.write_string("TLK ", string_length=4)
        self._writer.write_string("V3.0", string_length=4)
        self._writer.write_uint32(language_id)
        self._writer.write_uint32(string_count)
        self._writer.write_uint32(entries_offset)

    def _write_entry(
        self,
        entry: TLKEntry,
        previous_offset: WrappedInt,
    ):
        sound_resref = entry.voiceover.get()
        text_offset = previous_offset.get()
        text_length = len(entry.text)
        entry_flags = 0  # Initialize entry_flags as zero

        # Check for TEXT_PRESENT: As we're writing text, let's assume it's always present
        entry_flags |= 0x0001

        # Check for SND_PRESENT: If sound_resref is defined in this entry.
        if sound_resref:
            entry_flags |= 0x0002
        entry_flags |= 0x0004  # SND_LENGTH: both vanilla dialog.tlk files have this set.

        self._writer.write_uint32(entry_flags)
        self._writer.write_string(sound_resref, string_length=16)
        self._writer.write_uint32(0)  # unused - volume variance
        self._writer.write_uint32(0)  # unused - pitch variance
        self._writer.write_uint32(text_offset)
        self._writer.write_uint32(text_length)
        self._writer.write_uint32(0)  # unused - sound length

        previous_offset += text_length
