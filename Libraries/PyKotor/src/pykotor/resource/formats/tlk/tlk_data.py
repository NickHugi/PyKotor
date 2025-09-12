"""This module handles classes relating to working with TLK files."""

from __future__ import annotations

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType


class TLK(ComparableMixin):
    BINARY_TYPE = ResourceType.TLK
    COMPARABLE_FIELDS = ("language",)
    COMPARABLE_SEQUENCE_FIELDS = ("entries",)

    def __init__(
        self,
        language: Language = Language.ENGLISH,
    ):
        self.entries: list[TLKEntry] = []
        self.language: Language = language  # game does not use this field

    def __len__(
        self,
    ) -> int:
        """Returns the number of stored entries."""
        return len(self.entries)

    def __iter__(
        self,
    ):
        """Iterates through the stored entry with each iteration yielding a stringref and the corresponding entry data."""
        yield from enumerate(self.entries)

    def __getitem__(
        self,
        item,
    ):
        """Returns an entry for the specified stringref.

        Args:
        ----
            item: The stringref.

        Raises:
        ------
            IndexError: If the stringref does not exist.

        Returns:
        -------
            The corresponding TLKEntry.
        """
        return self.entries[item] if isinstance(item, int) else NotImplemented

    def get(
        self,
        stringref: int,
    ) -> TLKEntry | None:
        """Returns an entry for the specified stringref if it exists, otherwise returns None.

        Args:
        ----
            stringref: The stringref.

        Returns:
        -------
            The corresponding TLKEntry or None.
        """
        return self.entries[stringref] if 0 <= stringref < len(self) else None

    def add(
        self,
        text: str,
        sound_resref: str = "",
    ) -> int:
        entry = TLKEntry(text, ResRef(sound_resref))
        self.entries.append(entry)
        return len(self.entries) - 1

    def replace(self, stringref: int, text: str, sound_resref: str = ""):
        """Replaces an entry at the specified stringref with the provided text and sound resref.

        Args:
        ----
            stringref: The stringref of the entry to be replaced.
            text: The new text for the entry.
            sound_resref: The new sound resref for the entry.
        """
        if not 0 <= stringref < len(self.entries):
            msg = f"Cannot replace nonexistent stringref in dialog.tlk: '{stringref}'"
            raise IndexError(msg)
        old_text: str = self.entries[stringref].text
        old_sound: ResRef = self.entries[stringref].voiceover
        self.entries[stringref] = TLKEntry(text or old_text, ResRef(sound_resref) if sound_resref else old_sound)

    def resize(
        self,
        size: int,
    ):
        """Resizes the number of entries to the specified size.

        Args:
        ----
            size: The new number of entries.
        """
        if len(self) > size:
            self.entries = self.entries[:size]
        else:
            self.entries.extend([TLKEntry("", ResRef.from_blank()) for _ in range(len(self), size)])

    # compare is provided by ComparableMixin


class TLKEntry(ComparableMixin):
    COMPARABLE_FIELDS = ("text", "voiceover")
    def __init__(
        self,
        text: str,
        voiceover: ResRef,
    ):
        self.text: str = text
        self.voiceover: ResRef = voiceover

        # The following fields exist in TLK format, but do not perform any function in KOTOR. The game ignores these.
        # entry flags. These are set in both game's TLKs
        self.text_present: bool = True
        self.sound_present: bool = True
        self.soundlength_present: bool = True
        self.sound_length: int = 0

    def __eq__(self, other: object):
        """Returns True if the text and voiceover match."""
        if self is other:
            return True
        if not isinstance(other, TLKEntry):
            return NotImplemented
        return other.text == self.text and other.voiceover == self.voiceover

    @property
    def text_length(self) -> int:
        return len(self.text)
