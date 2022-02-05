"""
This module handles classes relating to editing TLK files.
"""
from __future__ import annotations

from typing import List

from pykotor.common.language import Language
from pykotor.common.misc import ResRef


class TLK:
    def __init__(self):
        self.entries: List[TLKEntry] = []
        self.language: Language = Language.ENGLISH

    def __len__(self):
        """
        Returns the number of stored entries.
        """
        return len(self.entries)

    def __iter__(self):
        """
        Iterates through the stored entry with each iteration yielding a stringref and the corresponding entry data.
        """
        for stringref, entry in enumerate(self.entries):
            yield stringref, entry

    def __getitem__(self, item):
        """
        Returns an entry for the specified stringref.

        Args:
            item: The stringref.

        Raises:
            IndexError: If the stringref does not exist.

        Returns:
            The corresponding TLKEntry.
        """
        if not isinstance(item, int):
            return NotImplemented
        return self.entries[item]

    def get(self, stringref: int) -> TLKEntry:
        """
        Returns an entry for the specified stringref if it exists, otherwise returns None.

        Args:
            stringref: The stringref.

        Returns:
            The corresponding TLKEntry or None.
        """
        return self.entries[stringref] if 0 <= stringref < len(self) else None

    def resize(self, size: int) -> None:
        """
        Resizes the number of entries to the specified size.

        Args:
            size: The new number of entries.
        """
        if len(self) > size:
            self.entries = self.entries[:size]
        else:
            self.entries = [TLKEntry("", ResRef.from_blank()) for _ in range(len(self), size)]


class TLKEntry:
    def __init__(self, text: str, voiceover: ResRef):
        self.text: str = text
        self.voiceover: ResRef = voiceover

    def __eq__(self, other):
        """
        Returns True if the text and voiceover match.
        """
        if not isinstance(other, TLKEntry):
            return NotImplemented
        return other.text == self.text and other.voiceover == self.voiceover
