"""This module holds classes relating to string localization."""
from __future__ import annotations

from enum import IntEnum
from typing import Any


class Language(IntEnum):
    """Language IDs recognized by both the games."""

    ENGLISH = 0
    FRENCH = 1
    GERMAN = 2
    ITALIAN = 3
    SPANISH = 4

    # Polish might require a different KOTOR executable. It is believed the games are hardcoded to the encoding 'cp-1252', but polish requires 'cp-1250'.
    # The TSL Aspyr patch did not support the Polish language which further supports this theory.
    POLISH = 5

    # The following languages are not used in any official KOTOR releases, however are supported in the TLK/GFF file formats.
    KOREAN = 128
    CHINESE_TRADITIONAL = 129
    CHINESE_SIMPLIFIED = 130
    JAPANESE = 131


    @staticmethod
    def _missing_(value) -> IntEnum:
        if not isinstance(value, int):
            return NotImplemented

        if value != 0x7FFFFFFF:  # unused? TODO: figure out what scenarios this'll happen in as it's happened on multiple occasions.
            print(f"Language integer not found: {value}")
        return Language.ENGLISH

    def get_encoding(self):
        """Get the encoding for the specified language."""
        if self in (Language.ENGLISH, Language.FRENCH, Language.GERMAN, Language.ITALIAN, Language.SPANISH):
            return "windows-1252"

        if self == Language.POLISH:
            return "windows-1250"

        if self == Language.KOREAN:
            return "euc_kr"
        if self == Language.CHINESE_TRADITIONAL:
            return "big5"
        if self == Language.CHINESE_SIMPLIFIED:
            return "gb2312"  # This encoding might not be accurate. The TLK/GFF formats could easily support "gb18030" or "GBK" but would need testing. "gb2312" is the safest option when unknown.
        if self == Language.JAPANESE:
            return "shift_jis"
        msg = f"No encoding defined for language: {self.name}"
        raise ValueError(msg)


class Gender(IntEnum):
    """Gender IDs recognized by both the games in regards to string localization."""

    MALE = 0  # or neutral
    FEMALE = 1


class LocalizedString:
    """Localized strings are a way of the game handling strings that need to be catered to a specific language or gender.

    This is achieved through either referencing a entry in the 'dialog.tlk' or by directly providing strings for each
    language.

    Attributes
    ----------
        stringref: An index into the 'dialog.tlk' file. If this value is -1 the game will use the stored substrings.
    """

    def __init__(self, stringref: int):
        self.stringref: int = stringref
        self._substrings: dict[int, str] = {}

    def __iter__(self):
        """Iterates through the list of substrings. Yields a tuple containing [language, gender, text]."""
        for substring_id, text in self._substrings.items():
            language, gender = LocalizedString.substring_pair(substring_id)
            yield language, gender, text

    def __len__(self):
        """Returns the number of substrings."""
        return len(self._substrings)

    def __str__(self):
        """If the stringref is valid, it will return it as a string. Otherwise it will return one of the substrings,
        prioritizing the english substring if it exists. If no substring exists and the stringref is invalid, "-1" is
        returned.
        """
        if self.stringref >= 0:
            return str(self.stringref)
        if self.exists(Language.ENGLISH, Gender.MALE):
            return str(self.get(Language.ENGLISH, Gender.MALE))
        for _language, _gender, text in self:
            return text
        return "-1"

    def __eq__(self, other: str | Any) -> bool:
        if not isinstance(other, LocalizedString):
            return False
        if other.stringref != self.stringref:
            return False
        return other._substrings == self._substrings

    def __hash__(self):
        return hash(self.stringref)

    @classmethod
    def from_invalid(cls):
        return cls(-1)

    @classmethod
    def from_english(cls, text: str):
        """Returns a new localizedstring object with a english substring.

        Args:
        ----
            text: the text for the english substring.

        Returns:
        -------
            a new localizedstring object.
        """
        locstring = cls(-1)
        locstring.set_data(Language.ENGLISH, Gender.MALE, text)
        return locstring

    @staticmethod
    def substring_id(language: Language, gender: Gender) -> int:
        """Returns the ID for the language gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            The substring ID.
        """
        return (language * 2) + gender

    @staticmethod
    def substring_pair(substring_id: int) -> tuple[Language, Gender]:
        """Returns the language gender pair from a substring ID.

        Args:
        ----
            substring_id: The substring ID.

        Returns:
        -------
            A tuple organized as (language, gender).
        """
        language = Language(substring_id // 2)
        gender = Gender(substring_id % 2)
        return language, gender

    def set_data(self, language: Language, gender: Gender, string: str) -> None:
        """Sets the text of the substring with the corresponding language/gender pair. The substring is created if it does
        not exist.

        Args:
        ----
            language: The language.
            gender: The gender.
            string: The new text for the new substring.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        self._substrings[substring_id] = string

    def get(self, language: Language, gender: Gender) -> str | None:
        """Gets the substring text with the corresponding language/gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            The text of the substring if a matching pair is found, otherwise returns None.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        return self._substrings[substring_id] if substring_id in self._substrings else None

    def remove(self, language: Language, gender: Gender) -> None:
        """Removes the existing substring with the respective language/gender pair if it exists. No error is thrown if it
        does not find a corresponding pair.

        Args:
        ----
            language: The language.
            gender: The gender.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        self._substrings.pop(substring_id)

    def exists(self, language: Language, gender: Gender) -> bool:
        """Returns whether or not a substring exists with the respective language/gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            True if the corresponding substring exists.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        return substring_id in self._substrings
