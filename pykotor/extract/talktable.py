from typing import List, Tuple, Dict, NamedTuple

from pykotor.common.language import Language, Gender

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
    def __init__(self, path: str):
        self._path: str = path

    def string(self, stringref: int) -> str:
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

        reader.close()

        return string

    def sound(self, stringref: int) -> ResRef:
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
            reader.seek(20 + 40 * stringref)
            flags = reader.read_uint32()
            sound_resref = reader.read_string(16)
            volume_variance = reader.read_uint32()
            pitch_variance = reader.read_uint32()
            text_offset = reader.read_uint32()
            text_length = reader.read_uint32()
            sound_length = reader.read_single()

        reader.close()

        return ResRef(sound_resref)

    def batch(self, stringrefs: List[int]) -> Dict[int, StringResult]:
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

    def size(self) -> int:
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

    def language(self) -> Language:
        reader = BinaryReader.from_file(self._path)
        reader.seek(8)
        language_id = reader.read_uint32()
        reader.close()
        return Language(language_id)
