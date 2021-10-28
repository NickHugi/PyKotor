from __future__ import annotations

from collections import namedtuple
from typing import Optional, List

from pykotor.common.language import Language
from pykotor.common.misc import ResRef, WrappedInt
from pykotor.common.stream import BinaryReader, BinaryWriter, ArrayHead

import pykotor.resource.formats.tlk


class TLKBinaryReader:
    def __init__(self, reader: BinaryReader):
        self._reader = reader

        self._tlk: Optional[pykotor.resource.formats.tlk.TLK] = None
        self._texts_offset = 0
        self._text_headers = []

    def load(self) -> pykotor.resource.formats.tlk.TLK:
        self._tlk = pykotor.resource.formats.tlk.TLK()
        self._texts_offset = 0
        self._text_headers = []

        self._reader.seek(0)

        self._load_file_header()
        [self._load_entry(stringref) for stringref, entry in self._tlk]
        [self._load_text(stringref) for stringref, entry in self._tlk]

        return self._tlk

    def _load_file_header(self):
        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)
        language_id = self._reader.read_uint32()
        string_count = self._reader.read_uint32()
        entries_offset = self._reader.read_uint32()

        if file_version != "V3.0": raise IOError("Invalid file version.")
        if file_type != "TLK ": raise IOError("Invalid file type.")

        self._tlk.language = Language(language_id)
        self._tlk.resize(string_count)

        self._texts_offset = entries_offset

    def _load_entry(self, stringref: int):
        flags = self._reader.read_uint32()  # unused
        sound_resref = self._reader.read_string(16)
        volume_variance = self._reader.read_uint32()  # unused
        pitch_variance = self._reader.read_uint32()  # unused
        text_offset = self._reader.read_uint32()
        text_length = self._reader.read_uint32()
        sound_length = self._reader.read_single()  # unused

        self._tlk.entries[stringref].voiceover = ResRef(sound_resref)

        self._text_headers.append(ArrayHead(text_offset, text_length))

    def _load_text(self, stringref: int):
        text_header = self._text_headers[stringref]

        self._reader.seek(text_header.offset + self._texts_offset)
        text = self._reader.read_string(text_header.length)

        self._tlk.entries[stringref].text = text


class TLKBinaryWriter:
    FILE_HEADER_SIZE = 20
    ENTRY_SIZE = 40

    def __init__(self, writer: BinaryWriter, tlk: pykotor.resource.formats.tlk.TLK):
        self._writer = writer
        self._tlk = tlk

    def write(self) -> None:
        self._write_file_header()

        text_offset = WrappedInt(self._calculate_entries_offset())
        [self._write_entry(entry, text_offset) for entry in self._tlk.entries]
        [self._writer.write_string(entry.text) for entry in self._tlk.entries]

    def _calculate_entries_offset(self):
        return TLKBinaryWriter.FILE_HEADER_SIZE + len(self._tlk) * TLKBinaryWriter.ENTRY_SIZE

    def _write_file_header(self) -> None:
        language_id = self._tlk.language.value
        string_count = len(self._tlk)
        entries_offset = TLKBinaryWriter.FILE_HEADER_SIZE

        self._writer.write_string("TLK ", string_length=4)
        self._writer.write_string("V3.0", string_length=4)
        self._writer.write_uint32(language_id)
        self._writer.write_uint32(string_count)
        self._writer.write_uint32(entries_offset)

    def _write_entry(self, entry: pykotor.resource.formats.tlk.TLKEntry, previous_offset: WrappedInt):
        sound_resref = entry.voiceover.get()
        text_offset = previous_offset.get()
        text_length = len(entry.text)

        self._writer.write_uint32(0)  # unused - entry flags
        self._writer.write_string(sound_resref, string_length=16)
        self._writer.write_uint32(0)  # unused - volume variance
        self._writer.write_uint32(0)  # unused - pitch variance
        self._writer.write_uint32(text_offset)
        self._writer.write_uint32(text_length)
        self._writer.write_uint32(0)  # unused - sound length

        previous_offset += text_length
