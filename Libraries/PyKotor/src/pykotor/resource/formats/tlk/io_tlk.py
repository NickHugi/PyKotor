from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import Language
from pykotor.common.misc import ResRef, WrappedInt
from pykotor.common.stream import ArrayHead
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.formats.tlk.tlk_data import TLKEntry
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

_FILE_HEADER_SIZE = 20
_ENTRY_SIZE = 40


class TLKBinaryReader(ResourceReader):
    """Reads TLK (Talk Table) files.
    
    TLK files store localized strings used throughout the game for dialog, item descriptions,
    and other text content. Each entry can have text, sound references, and flags.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/tlkreader.cpp:26-65 (TLK reading)
        vendor/reone/src/libs/resource/format/tlkwriter.cpp (TLK writing)
    
    Missing Features:
    ----------------
        - ResRef lowercasing (reone lowercases sound resrefs)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
        language: Language | None = None,
    ):
        super().__init__(source, offset, size)
        self._tlk: TLK
        self._texts_offset = 0
        self._text_headers: list[ArrayHead] = []
        self._language: Language | None = language

    @autoclose
    def load(self, *, auto_close: bool = True) -> TLK:  # noqa: FBT001, FBT002, ARG002
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

    def _load_file_header(self):
        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)
        language_id = self._reader.read_uint32()
        string_count = self._reader.read_uint32()
        entries_offset = self._reader.read_uint32()

        if file_type != "TLK ":
            msg = "Invalid file type."
            raise ValueError(msg)
        if file_version != "V3.0":
            msg = "Invalid file version."
            raise ValueError(msg)

        self._tlk.language = Language(language_id) if self._language is None else self._language
        self._tlk.resize(string_count)

        self._texts_offset = entries_offset

    def _load_entry(
        self,
        stringref: int,
    ):
        # vendor/reone/src/libs/resource/format/tlkreader.cpp:40-60
        entry: TLKEntry = self._tlk.entries[stringref]

        entry_flags = self._reader.read_uint32()
        # vendor/reone/src/libs/resource/format/tlkreader.cpp:45-46
        # NOTE: reone lowercases sound_resref, PyKotor does not
        sound_resref = self._reader.read_string(16)
        _volume_variance = self._reader.read_uint32()  # unused
        _pitch_variance = self._reader.read_uint32()  # unused
        text_offset = self._reader.read_uint32()
        text_length = self._reader.read_uint32()
        entry.sound_length = self._reader.read_single()  # unused
        # vendor/reone/src/libs/resource/format/tlkreader.cpp:50-52
        entry.text_present = (entry_flags & 0x0001) != 0  # Check if the TEXT_PRESENT flag is set
        entry.sound_present = (entry_flags & 0x0002) != 0  # Check if the SND_PRESENT flag is set
        entry.soundlength_present = (entry_flags & 0x0004) != 0  # Check if the SND_LENGTH flag is set
        entry.voiceover = ResRef(sound_resref)
        self._text_headers.append(ArrayHead(text_offset, text_length))

    def _load_text(
        self,
        stringref: int,
    ):
        text_header: ArrayHead = self._text_headers[stringref]

        self._reader.seek(text_header.offset + self._texts_offset)
        text: str = self._reader.read_string(text_header.length, encoding=self._tlk.language.get_encoding())

        self._tlk.entries[stringref].text = text


class TLKBinaryWriter(ResourceWriter):
    def __init__(
        self,
        tlk: TLK,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tlk: TLK = tlk

    @autoclose
    def write(self, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002
        self._write_file_header()

        text_offset = WrappedInt(0)
        encoding: str | None = self._tlk.language.get_encoding()
        for entry in self._tlk.entries:
            self._write_entry(entry, text_offset)

        for entry in self._tlk.entries:
            self._writer.write_string(entry.text, encoding or "cp1252", errors="replace")

    def _calculate_entries_offset(self) -> int:
        return _FILE_HEADER_SIZE + len(self._tlk) * _ENTRY_SIZE

    def _write_file_header(self):
        language_id: int = self._tlk.language.value
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
        sound_resref = str(entry.voiceover)
        text_offset = previous_offset.get()
        text_length = len(entry.text)

        entry_flags = 0  # Initialize entry_flags as zero
        if entry.text_present:
            entry_flags |= 0x0001  # TEXT_PRESENT: As we're writing text, let's assume it's always present
        if entry.sound_present:
            entry_flags |= 0x0002  # SND_PRESENT: If sound_resref is defined in this entry.
        if entry.soundlength_present:
            entry_flags |= 0x0004  # SND_LENGTH: Unused by KOTOR1 and 2. Determines whether the sound length field is utilized.

        self._writer.write_uint32(entry_flags)
        self._writer.write_string(sound_resref, string_length=16)
        self._writer.write_uint32(0)  # unused - volume variance
        self._writer.write_uint32(0)  # unused - pitch variance
        self._writer.write_uint32(text_offset)
        self._writer.write_uint32(text_length)
        self._writer.write_uint32(0)  # unused - sound length

        previous_offset += text_length
