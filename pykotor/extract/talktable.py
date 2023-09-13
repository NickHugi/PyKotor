from __future__ import annotations

from typing import NamedTuple

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.tools.path import CaseAwarePath


class StringResult(NamedTuple):
    text: str
    sound: ResRef


class TalkTable:
    """
    Talktables are for read-only loading of stringrefs stored in a dialog.tlk file. Files are only opened when accessing
    a stored string, this means that strings are always up to date at the time of access as opposed to TLK objects which
    may be out of date with its source file.
    """

    def __init__(
        self,
        path: CaseAwarePath,
    ):
        self._path: CaseAwarePath = CaseAwarePath(path)

    def string(
        self,
        stringref: int,
    ) -> str:
        """
        Access a string from the tlk file.

        Args:
        ----
            stringref: The entry id.

        Returns:
        -------
            A string.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        texts_offset = reader.read_uint32()

        if stringref == -1 or stringref >= entries_count:
            string = ""
        else:
            _, _, _, _, text_offset, text_length, _ = self._extract_common_data(
                reader,
                stringref,
            )
            reader.seek(texts_offset + text_offset)
            string = reader.read_string(text_length)
        reader.close()
        return string

    def sound(
        self,
        stringref: int,
    ) -> ResRef:
        """
        Access the sound ResRef from the tlk file.

        Args:
        ----
            stringref: The entry id.

        Returns:
        -------
            A ResRef.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        _ = reader.read_uint32()  # Unused texts_offset

        if stringref == -1 or stringref >= entries_count:
            sound_resref = ""
        else:
            _, sound_resref, _, _, _, _, _ = self._extract_common_data(
                reader,
                stringref,
            )
        reader.close()
        return ResRef(sound_resref)

    def _extract_common_data(self, reader: BinaryReader, stringref: int):
        reader.seek(20 + 40 * stringref)
        flags = reader.read_uint32()
        sound_resref = reader.read_string(16)
        volume_variance = reader.read_uint32()
        pitch_variance = reader.read_uint32()
        text_offset = reader.read_uint32()
        text_length = reader.read_uint32()
        sound_length = reader.read_single()

        return (
            flags,
            sound_resref,
            volume_variance,
            pitch_variance,
            text_offset,
            text_length,
            sound_length,
        )

    def batch(
        self,
        stringrefs: list[int],
    ) -> dict[int, StringResult]:
        """
        Loads a list of strings and sound ResRefs from the specified list. This is all performed using a single file
        handle and should be used if loading multiple strings from the tlk file.

        Args:
        ----
            stringrefs: A list of stringref ints.

        Returns:
        -------
            Dictionary with stringref keys and Tuples (string, sound) values.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        texts_offset = reader.read_uint32()

        batch: dict[int, StringResult] = {}

        for stringref in stringrefs:
            if stringref == -1 or stringref >= entries_count:
                batch[stringref] = StringResult("", ResRef.from_blank())
                continue

            (
                _,
                sound_resref,
                _,
                _,
                text_offset,
                text_length,
                _,
            ) = self._extract_common_data(reader, stringref)

            reader.seek(texts_offset + text_offset)
            string = reader.read_string(text_length)
            sound = ResRef(sound_resref)

            batch[stringref] = StringResult(string, sound)

        reader.close()

        return batch

    def size(
        self,
    ) -> int:
        """
        Returns the number of entries in the talk table.

        Returns
        -------
            The number of entries in the talk table.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        reader.close()
        return entries_count

    def language(
        self,
    ) -> Language:
        """
        Returns the matching Language of the TLK file.

        Returns
        -------
            The language of the TLK file.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(8)
        language_id = reader.read_uint32()
        reader.close()
        return Language(language_id)
