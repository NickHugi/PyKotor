from pathlib import Path
from typing import List, Dict, NamedTuple

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader


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
            path: Path
    ):
        self._path: Path = Path(path)

    def string(
            self,
            stringref: int
    ) -> str:
        """
        Access a string from the tlk file.

        Args:
            stringref: The entry id.

        Returns:
            A string.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        texts_offset = reader.read_uint32()

        if stringref == -1 or stringref >= entries_count:
            string = ""
        else:
            string = self._extracted_from_string_22(reader, stringref, texts_offset)
        reader.close()

        return string

    # TODO Rename this here and in `string`
    def _extracted_from_string_22(self, reader, stringref, texts_offset):
        reader.seek(20 + 40 * stringref)
        flags = reader.read_uint32()
        sound_resref = reader.read_string(16)
        volume_variance = reader.read_uint32()
        pitch_variance = reader.read_uint32()
        text_offset = reader.read_uint32()
        text_length = reader.read_uint32()
        sound_length = reader.read_single()

        reader.seek(texts_offset + text_offset)
        return reader.read_string(text_length)

    def sound(
            self,
            stringref: int
    ) -> ResRef:
        """
        Access the sound ResRef from the tlk file.

        Args:
            stringref: The entry id.

        Returns:
            A ResRef.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        texts_offset = reader.read_uint32()

        if stringref == -1 or stringref >= entries_count:
            sound_resref = ""
        else:
            sound_resref = self._extracted_from_sound_22(reader, stringref)
        reader.close()

        return ResRef(sound_resref)

    # TODO Rename this here and in `sound`
    def _extracted_from_sound_22(self, reader, stringref):
        reader.seek(20 + 40 * stringref)
        flags = reader.read_uint32()
        result = reader.read_string(16)
        volume_variance = reader.read_uint32()
        pitch_variance = reader.read_uint32()
        text_offset = reader.read_uint32()
        text_length = reader.read_uint32()
        sound_length = reader.read_single()

        return result

    def batch(
            self,
            stringrefs: List[int]
    ) -> Dict[int, StringResult]:
        """
        Loads a list of strings and sound ResRefs from the specified list. This is all performed using a single file
        handle and should be used if loading multiple strings from the tlk file.

        Args:
            stringrefs: A list of stringref ints.

        Returns:
            Dictionary with stringref keys and Tuples (string, sound) values.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        texts_offset = reader.read_uint32()

        batch = {}

        for stringref in stringrefs:
            if stringref == -1 or stringref >= entries_count:
                batch[stringref] = StringResult("", ResRef.from_blank())
                continue

            reader.seek(20 + 40 * stringref)
            flags = reader.read_uint32()
            sound_resref = reader.read_string(16)
            volume_variance = reader.read_uint32()
            pitch_variance = reader.read_uint32()
            text_offset = reader.read_uint32()
            text_length = reader.read_uint32()
            sound_length = reader.read_single()

            reader.seek(texts_offset + text_offset)
            string = reader.read_string(text_length)
            sound = ResRef(sound_resref)

            batch[stringref] = StringResult(string, sound)

        reader.close()

        return batch

    def size(
            self
    ) -> int:
        """
        Returns the number of entries in the talk table.

        Returns:
            The number of entries in the talk table.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(12)
        entries_count = reader.read_uint32()
        reader.close()
        return entries_count

    def language(
            self
    ) -> Language:
        """
        Returns the matching Language of the TLK file.

        Returns:
            The language of the TLK file.
        """
        reader = BinaryReader.from_file(self._path)
        reader.seek(8)
        language_id = reader.read_uint32()
        reader.close()
        return Language(language_id)
