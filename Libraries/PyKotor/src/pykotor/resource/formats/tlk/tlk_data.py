"""This module handles classes relating to working with TLK files."""
from __future__ import annotations

from itertools import zip_longest
from typing import Callable

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType
from utility.string import compare_and_format, format_text


class TLK:
    BINARY_TYPE = ResourceType.TLK

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

    def compare(self, other: TLK, log_func: Callable = print) -> bool:
        if len(self) != len(other):
            log_func(f"TLK row count mismatch. Old: {len(self)}, New: {len(other)}")

        mismatch_count, extra_old, extra_new = 0, 0, 0

        for (old_stringref, old_entry), (new_stringref, new_entry) in zip_longest(self, other, fillvalue=(None, None)):
            # Both TLKs have the entry but with different content
            if old_stringref is None or old_entry is None:
                if new_stringref is not None and new_entry is not None:
                    extra_new += 1
                    continue
                continue
            if new_stringref is None or new_entry is None:
                extra_old += 1
                continue
            if old_entry != new_entry:
                text_mismatch: bool = old_entry.text.lower() != new_entry.text.lower()
                vo_mismatch: bool = old_entry.voiceover != new_entry.voiceover
                if not text_mismatch and not vo_mismatch:
                    log_func("TLK entries are not equal, but no differences could be found?")
                    continue

                log_func(f"Entry mismatch at stringref: {old_stringref}")
                if text_mismatch:
                    log_func(format_text(compare_and_format(old_entry.text, new_entry.text)))
                mismatch_count += 1
                if vo_mismatch:
                    log_func(format_text(compare_and_format(old_entry.voiceover, new_entry.voiceover)))

        # Provide a summary of discrepancies
        if mismatch_count:
            log_func(f"{mismatch_count} entries have mismatches.")
        if extra_old:
            log_func(f"Old TLK has {extra_old} stringrefs that are missing in the new TLK.")
        if extra_new:
            log_func(f"New TLK has {extra_new} extra stringrefs that are not in the old TLK.")

        return not (mismatch_count or extra_old or extra_new)


class TLKEntry:
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

    def __eq__(
        self,
        other: TLKEntry,
    ):
        """Returns True if the text and voiceover match."""
        if not isinstance(other, TLKEntry):
            return NotImplemented
        return other.text == self.text and other.voiceover == self.voiceover

    @property
    def text_length(self) -> int:
        return len(self.text)
