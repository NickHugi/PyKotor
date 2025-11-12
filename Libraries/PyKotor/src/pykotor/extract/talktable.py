from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader

if TYPE_CHECKING:
    import os


class StringResult(NamedTuple):
    text: str
    sound: ResRef


class TLKData(NamedTuple):
    flags: int
    voiceover: str
    volume_variance: int
    pitch_variance: int
    text_offset: int
    text_length: int
    sound_length: float


class TalkTable:  # TODO(th3w1zard1): dialogf.tlk  # noqa: FIX002, TD003
    """Talktables are for read-only loading of stringrefs stored in a dialog.tlk file.

    Files are only opened when accessing a stored string, this means that strings are always up to date at
    the time of access as opposed to TLK objects which may be out of date with its source file.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/tlkreader.cpp:26-65 (TLK reading)
        vendor/reone/src/libs/resource/format/tlkwriter.cpp (TLK writing)
    """

    def __init__(
        self,
        path: os.PathLike | str,
    ):
        self._path: Path = Path(path)

    def path(self) -> Path:
        return self._path

    def string(
        self,
        stringref: int,
    ) -> str:
        """Access a string from the tlk file.

        Args:
        ----
            stringref: The entry id.

        Returns:
        -------
            A string.
        """
        if stringref == -1:
            return ""
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(12)
            entries_count: int = reader.read_uint32()
            texts_offset: int = reader.read_uint32()

            if stringref >= entries_count:
                return ""

            tlkdata: TLKData = self._extract_common_tlk_data(reader, stringref)
            reader.seek(texts_offset + tlkdata.text_offset)
            return reader.read_string(tlkdata.text_length)

    def sound(
        self,
        stringref: int,
    ) -> ResRef:
        """Access the sound ResRef from the tlk file.

        Args:
        ----
            stringref: The entry id.

        Returns:
        -------
            A ResRef.
        """
        if stringref == -1:
            return ResRef.from_blank()
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(12)
            entries_count = reader.read_uint32()
            reader.skip(4)

            if stringref >= entries_count:
                return ResRef.from_blank()

            tlkdata = self._extract_common_tlk_data(reader, stringref)
            return ResRef(tlkdata.voiceover)

    def _extract_common_tlk_data(
        self,
        reader: BinaryReader,
        stringref: int,
    ) -> TLKData:
        # vendor/reone/src/libs/resource/format/tlkreader.cpp:43-64
        # Entry offset calculation: header (20 bytes) + entry_size (40 bytes) * stringref
        reader.seek(20 + 40 * stringref)

        return TLKData(
            flags=reader.read_uint32(),
            voiceover=reader.read_string(16),
            volume_variance=reader.read_uint32(),
            pitch_variance=reader.read_uint32(),
            text_offset=reader.read_uint32(),
            text_length=reader.read_uint32(),
            sound_length=reader.read_single(),
        )

    def batch(
        self,
        stringrefs: list[int],
    ) -> dict[int, StringResult]:
        """Loads a list of strings and sound ResRefs from the specified list.

        This is all performed using a single file handle and should be used if loading multiple strings from the tlk file.

        Args:
        ----
            stringrefs: A list of stringref ints.

        Returns:
        -------
            Dictionary with stringref keys and Tuples (string, sound) values.
        """
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(8)
            language_id = reader.read_uint32()
            language: Language = Language(language_id)
            encoding: str | None = language.get_encoding()
            entries_count = reader.read_uint32()
            texts_offset = reader.read_uint32()

            batch: dict[int, StringResult] = {}

            for stringref in stringrefs:
                if stringref == -1 or stringref >= entries_count:
                    batch[stringref] = StringResult("", ResRef.from_blank())
                    continue

                tlkdata: TLKData = self._extract_common_tlk_data(reader, stringref)

                reader.seek(texts_offset + tlkdata.text_offset)
                string = reader.read_string(tlkdata.text_length, encoding=encoding)
                sound = ResRef(tlkdata.voiceover)

                batch[stringref] = StringResult(string, sound)

            return batch

    def size(
        self,
    ) -> int:
        """Returns the number of entries in the talk table.

        Returns:
        -------
            The number of entries in the talk table.
        """
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(12)
            return reader.read_uint32()  # entries_count

    def language(
        self,
    ) -> Language:
        """Returns the matching Language of the TLK file.

        Returns:
        -------
            The language of the TLK file.
        """
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(8)
            language_id = reader.read_uint32()
            return Language(language_id)
