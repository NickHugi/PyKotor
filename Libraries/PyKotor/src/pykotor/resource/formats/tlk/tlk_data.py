"""This module handles classes relating to working with TLK files.

Talk Table (TLK) files contain all text strings used in the game, both written and spoken.
They enable easy localization by providing a lookup table from string reference numbers (StrRef)
to localized text and associated voice-over audio files.

References:
----------
    vendor/TSLPatcher/lib/site/Bioware/TLK.pm:1-533 - Complete TLK implementation
    vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:11-132 - Binary format
    vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:10-227 - C# TLK reader/writer
    vendor/KotOR-Bioware-Libs/TLK.pm - Perl TLK library
    vendor/reone/src/libs/resource/format/tlkreader.cpp:31-84 - TLK parsing
    vendor/xoreos/src/aurora/talktable.cpp:42-176 - Talk table implementation
    vendor/KotOR.js/src/resource/TalkTable.ts:13-195 - TypeScript implementation
    vendor/sotor/core/src/formats/tlk/read.rs:11-89 - Rust TLK reader

Binary Format:
-------------
    Header (20 bytes):
        - 4 bytes: File Type ("TLK ")
        - 4 bytes: File Version ("V3.0" for KotOR, "V4.0" for Jade Empire)
        - 4 bytes: Language ID (int32)
        - 4 bytes: String Count (int32)
        - 4 bytes: String Entries Offset (int32)
    
    String Data Table (40 bytes per entry):
        - 4 bytes: Flags (bit 0=text present, bit 1=sound present, bit 2=sound length present)
        - 16 bytes: Sound ResRef (null-terminated ASCII, max 16 chars)
        - 4 bytes: Volume Variance (unused in KotOR)
        - 4 bytes: Pitch Variance (unused in KotOR)
        - 4 bytes: Offset to String (from String Entries Offset)
        - 4 bytes: String Size (length in bytes)
        - 4 bytes: Sound Length (float, seconds)
    
    String Entries:
        - Variable length null-terminated strings
        
    Reference: TSLPatcher/TLK.pm:42-79, Kotor.NET:57-90, KotOR_IO:46-76
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType
from utility.common.misc_string.util import compare_and_format, format_text

if TYPE_CHECKING:
    from typing import Any


class TLK(ComparableMixin):
    """Talk Table containing localized strings and voice-over references.
    
    The TLK file is the central localization mechanism for KotOR, mapping string reference
    numbers (StrRef) to localized text and optional voice-over audio files. The game loads
    dialog.tlk at startup and references strings throughout the game using StrRef numbers.
    
    References:
    ----------
        vendor/TSLPatcher/lib/site/Bioware/TLK.pm:31-123 - string_from_resref() lookup function
        vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:13-55 - FileRoot class
        vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:19-93 - TLK class with indexer
        vendor/reone/src/libs/resource/format/tlkreader.cpp:31-46 - TalkTable loading
        
    Attributes:
    ----------
        entries: List of TLKEntry objects indexed by StrRef
            Reference: TSLPatcher/TLK.pm:63-79 (string lookup by index)
            Reference: Kotor.NET/TLKBinaryStructure.cs:16 (StringData list)
            Reference: KotOR_IO/TLK.cs:93 (String_Data_Table)
            StrRef numbers are array indices (0-based)
            Game uses StrRef -1 to indicate no string reference
            
        language: Language identifier for this talk table
            Reference: Kotor.NET/TLKBinaryStructure.cs:63 (LanguageID field)
            Reference: KotOR_IO/TLK.cs:84 (LanguageID property)
            Reference: TSLPatcher/TLK.pm:42-44 (version check for V4.0)
            NOTE: Game ignores this field in KotOR, always uses dialog.tlk
            Used primarily for modding tools to identify language
    """
    
    BINARY_TYPE = ResourceType.TLK
    COMPARABLE_FIELDS = ("language",)
    COMPARABLE_SEQUENCE_FIELDS = ("entries",)

    def __init__(
        self,
        language: Language = Language.ENGLISH,
    ):
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:16
        # vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:93
        # List of string entries indexed by StrRef (0-based array index)
        self.entries: list[TLKEntry] = []
        
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:63
        # vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:84
        # Language ID field - unused by game but present in file format
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

    def compare(self, other: object, log_func: Callable[[str], Any] = print) -> bool:  # noqa: C901, PLR0912, PLR0915
        """Smart TLK comparison that detects insertions/deletions and shows meaningful diffs.

        Args:
        ----
            other: The other TLK to compare against
            log_func: Function to call with comparison output messages

        Returns:
        -------
            True if TLKs are identical, False otherwise
        """
        if not isinstance(other, TLK):
            log_func(f"Type mismatch: 'TLK' vs '{other.__class__.__name__ if isinstance(other, object) else type(other)}'")
            return False

        # Build content-based lookup to detect moved/reordered entries
        def entry_key(entry: TLKEntry) -> tuple[str, str]:
            """Create a hashable key for an entry."""
            return (entry.text, str(entry.voiceover))

        # Build maps of content to indices
        entries1_map: dict[tuple[str, str], list[int]] = {}  # content -> list of indices
        entries2_map: dict[tuple[str, str], list[int]] = {}  # content -> list of indices

        for idx, entry in enumerate(self.entries):
            key = entry_key(entry)
            if key not in entries1_map:
                entries1_map[key] = []
            entries1_map[key].append(idx)

        for idx, entry in enumerate(other.entries):
            key = entry_key(entry)
            if key not in entries2_map:
                entries2_map[key] = []
            entries2_map[key].append(idx)

        # Find entries that exist in both (at any index)
        added_keys = set(entries2_map.keys()) - set(entries1_map.keys())
        removed_keys = set(entries1_map.keys()) - set(entries2_map.keys())

        # Track which entries we've reported
        reported_indices1: set[int] = set()
        reported_indices2: set[int] = set()

        # Report size difference
        len1 = len(self.entries)
        len2 = len(other.entries)

        if len1 != len2:
            log_func(f"TLK size mismatch: Old has {len1} entries, New has {len2} entries (diff: {len2 - len1:+d})")

        # Report added entries (in new file only)
        if added_keys:
            log_func(f"\n{len(added_keys)} entries added in new TLK:")
            for key in sorted(added_keys):
                indices = entries2_map[key]
                for idx in indices:
                    entry = other.entries[idx]
                    log_func(f"  [New:{idx}] {entry}")
                    reported_indices2.add(idx)

        # Report removed entries (in old file only)
        if removed_keys:
            log_func(f"\n{len(removed_keys)} entries removed from old TLK:")
            for key in sorted(removed_keys):
                indices = entries1_map[key]
                for idx in indices:
                    entry = self.entries[idx]
                    log_func(f"  [Old:{idx}] {entry}")
                    reported_indices1.add(idx)

        # Check for entries at same index that have different content
        modified_count = 0
        max_index = min(len1, len2)
        for idx in range(max_index):
            if idx in reported_indices1 or idx in reported_indices2:
                continue
            entry1 = self.entries[idx]
            entry2 = other.entries[idx]

            if entry1 != entry2:
                # This is a genuine content change at the same index
                if modified_count == 0:
                    log_func("\nEntries modified at same index:")
                modified_count += 1
                log_func(f"  [{idx}] Old: {entry1}")
                log_func(f"  [{idx}] New: {entry2}")
                reported_indices1.add(idx)
                reported_indices2.add(idx)

        # Summary
        has_differences = bool(added_keys or removed_keys or modified_count)

        if has_differences:
            log_func(f"\nTLK Summary: {len(added_keys)} added, {len(removed_keys)} removed, {modified_count} modified")

        return not has_differences


class TLKEntry(ComparableMixin):
    """A single string entry in a Talk Table.
    
    Each entry represents one localized string that can be referenced by its StrRef (array index).
    Entries contain the text content and an optional reference to a voice-over audio file.
    
    References:
    ----------
        vendor/TSLPatcher/lib/site/Bioware/TLK.pm:76-79 - String reading from offset
        vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:92-130 - StringData class
        vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:165-227 - String_Data class
        vendor/reone/src/libs/resource/format/tlkreader.cpp:48-82 - Entry parsing
        
    Binary Format (40 bytes):
    ------------------------
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | uint32 | Flags (bit 0=text, bit 1=sound, bit 2=sound length)
        0x04   | 16   | char[] | Sound ResRef (null-terminated, max 16 chars)
        0x14   | 4    | uint32 | Volume Variance (unused in KotOR)
        0x18   | 4    | uint32 | Pitch Variance (unused in KotOR)
        0x1C   | 4    | int32  | Offset to String (from String Entries Offset)
        0x20   | 4    | int32  | String Size (length in bytes)
        0x24   | 4    | float  | Sound Length (seconds)
        
        Reference: Kotor.NET/TLKBinaryStructure.cs:92-130, KotOR_IO/TLK.cs:194-200
    
    Attributes:
    ----------
        text: The localized text string
            Reference: TSLPatcher/TLK.pm:76-79 (string reading from offset)
            Reference: Kotor.NET/TLKBinaryStructure.cs:36-37 (StringEntries list)
            Reference: KotOR_IO/TLK.cs:191 (StringText property)
            Reference: reone/tlkreader.cpp:78-79 (text reading)
            Encoding: ASCII for English, language-specific for others
            Can contain special tokens like <CUSTOM0>, <FullName>, etc.
            
        voiceover: Reference to voice-over WAV file (ResRef)
            Reference: Kotor.NET/TLKBinaryStructure.cs:97 (SoundResRef property)
            Reference: KotOR_IO/TLK.cs:197 (SoundResRef field, 16 chars)
            Reference: reone/tlkreader.cpp:68-69 (soundResRef reading)
            Max 16 characters, stored as null-terminated string in binary
            If empty/blank, no voice-over is associated with this entry
            Game looks for WAV files in StreamVoice/ or StreamWaves/ folders
            
        sound_length: Duration of voice-over audio in seconds
            Reference: Kotor.NET/TLKBinaryStructure.cs:102 (Length property, float)
            Reference: KotOR_IO/TLK.cs:206 (SoundLength field)
            Reference: reone/tlkreader.cpp:80-81 (soundLength reading)
            NOTE: Unused by KotOR game engine, but present in file format
            Primarily used by modding tools for audio synchronization
    """
    
    COMPARABLE_FIELDS = ("text", "voiceover")
    def __init__(
        self,
        text: str,
        voiceover: ResRef,
    ):
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:36-37
        # vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:191
        # vendor/TSLPatcher/lib/site/Bioware/TLK.pm:76-79
        # Localized text string (encoding depends on language)
        self.text: str = text
        
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:97
        # vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:197
        # vendor/reone/src/libs/resource/format/tlkreader.cpp:68-69
        # Voice-over WAV file reference (max 16 chars)
        self.voiceover: ResRef = voiceover

        # vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:102
        # vendor/KotOR_IO/KotOR_IO/File Formats/TLK.cs:206
        # Duration of voice-over in seconds (unused by game, but present in format)
        self.sound_length: int = 0  # This remains a regular attribute

    # The following fields exist in TLK format, but do not perform any function in KOTOR. The game ignores these.
    # entry flags. These are set in both game's TLKs
    @property
    def text_present(self) -> bool:
        """Always True; present for compatibility (TLK field)."""
        return True
    @text_present.setter
    def text_present(self, value: bool):
        self._text_present = value

    @property
    def sound_present(self) -> bool:
        """Always True; present for compatibility (TLK field)."""
        return True
    @sound_present.setter
    def sound_present(self, value: bool):
        self._sound_present = value

    @property
    def soundlength_present(self) -> bool:
        """Always True; present for compatibility (TLK field)."""
        return True
    @soundlength_present.setter
    def soundlength_present(self, value: bool):
        self._soundlength_present = value

    def __eq__(self, other: object):
        """Returns True if the text and voiceover match."""
        if self is other:
            return True
        if not isinstance(other, TLKEntry):
            return NotImplemented
        return other.text == self.text and other.voiceover == self.voiceover

    def __hash__(self) -> int:
        """Returns a hash of the TLKEntry."""
        return hash((self.text, self.voiceover))

    def __repr__(self) -> str:
        """Returns a string representation of the TLKEntry."""
        max_repr_length = 50
        text_preview = self.text[:max_repr_length] + "..." if len(self.text) > max_repr_length else self.text
        text_preview = text_preview.replace("\n", "\\n").replace("\r", "\\r")
        return f"TLKEntry(text={text_preview!r}, voiceover={self.voiceover!r})"

    def __str__(self) -> str:
        """Returns a human-readable string representation of the TLKEntry."""
        return f"text: {self.text}, voiceover: {self.voiceover!r}"

    @property
    def text_length(self) -> int:
        return len(self.text)
    @text_length.setter
    def text_length(self, value: int):
        self._text_length = value
