"""This module holds classes relating to string localization."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


# BCP 47 language code
class Language(IntEnum):
    """Language IDs recognized by both the games.

    Found in the TalkTable header, and CExoLocStrings (LocalizedStrings) within GFFs.
    """

    # UNSET = 0x7FFFFFFF  # noqa: ERA001
    UNKNOWN = 0x7FFFFFFE

    # The following languages have official releases
    # cp-1252
    ENGLISH = 0
    FRENCH = 1
    GERMAN = 2
    ITALIAN = 3
    SPANISH = 4
    POLISH = 5  # cp-1250, only released for K1.
    # The following custom languages have been added for additional localization support within PyKotor.
    # cp-1252
    AFRIKAANS = 6
    BASQUE = 7
    BRETON = 9
    CATALAN = 10
    CHAMORRO = 11
    CHICHEWA = 12
    CORSICAN = 13
    DANISH = 14
    DUTCH = 15
    FAROESE = 16
    FILIPINO = 18
    FINNISH = 19
    FLEMISH = 20
    FRISIAN = 21
    GALICIAN = 22
    GANDA = 23
    HAITIAN_CREOLE = 24
    HAUSA_LATIN = 25
    HAWAIIAN = 26
    ICELANDIC = 27
    IDO = 28
    INDONESIAN = 29
    IGBO = 30
    IRISH = 31
    INTERLINGUA = 32
    JAVANESE_LATIN = 33
    LATIN = 34
    LUXEMBOURGISH = 35
    MALTESE = 36
    NORWEGIAN = 37
    OCCITAN = 38
    PORTUGUESE = 39
    SCOTS = 40
    SCOTTISH_GAELIC = 41
    SHONA = 42
    SOTO = 43
    SUNDANESE_LATIN = 44
    SWAHILI = 45
    SWEDISH = 46
    TAGALOG = 47
    TAHITIAN = 48
    TONGAN = 49
    UZBEK_LATIN = 50
    WALLOON = 51
    XHOSA = 52
    YORUBA = 53
    WELSH = 54
    ZULU = 55
    # cp-1251
    BULGARIAN = 58
    BELARISIAN = 59
    MACEDONIAN = 60
    RUSSIAN = 61
    SERBIAN_CYRILLIC = 62
    TAJIK = 63
    TATAR_CYRILLIC = 64
    UKRAINIAN = 66
    UZBEK = 67
    # cp-1250
    ALBANIAN = 68
    BOSNIAN_LATIN = 69
    CZECH = 70
    SLOVAK = 71
    SLOVENE = 72
    CROATIAN = 73
    HUNGARIAN = 75
    ROMANIAN = 76  # before 1993 reform
    # cp-1253
    GREEK = 77
    # ISO-8859-3
    ESPERANTO = 78  # loss of information if encoded to cp-1253
    # cp-1254
    AZERBAIJANI_LATIN = 79
    TURKISH = 81
    TURKMEN_LATIN = 82
    # cp-1255
    HEBREW = 83
    # cp-1256
    ARABIC = 84
    # cp-1257
    ESTONIAN = 85
    LATVIAN = 86
    LITHUANIAN = 87
    # cp-1258
    VIETNAMESE = 88
    # cp-874
    THAI = 89
    # The following languages aren't fully encodeable to 8-bit without loss of information:
    # cp-1252
    AYMARA = 90
    KINYARWANDA = 91
    KURDISH_LATIN = 92
    MALAGASY = 93
    MALAY_LATIN = 94
    MAORI = 95
    MOLDOVAN_LATIN = 96
    SAMOAN = 97
    SOMALI = 98

    # The following languages are supported in the GFF/TLK file formats, but are probably not encodable to 8-bit without significant loss of information
    # therefore are probably incompatible with KOTOR.
    KOREAN = 128
    CHINESE_TRADITIONAL = 129
    CHINESE_SIMPLIFIED = 130
    JAPANESE = 131

    @staticmethod
    def _missing_(value: Any) -> IntEnum:
        if not isinstance(value, int):
            return NotImplemented

        if value != 0x7FFFFFFF:  # 0x7FFFFFFF is unset/disabled/unused
            print(f"Language integer not known: {value}")
        return Language.ENGLISH

    def is_8bit_encoding(self) -> bool:
        return self not in {
            Language.UNKNOWN,
            Language.KOREAN,
            Language.JAPANESE,
            Language.CHINESE_SIMPLIFIED,
            Language.CHINESE_TRADITIONAL,
            Language.THAI,
        }

    def get_encoding(self) -> str | None:
        """Gets the encoding for a given language.

        Args:
        ----
            self: {Language}: The language to get the encoding for

        Returns:
        -------
            encoding (str): The encoding for the given language

        Processing Logic:
        ----------------
            - Check if language is in list of Latin-based languages and return "cp1252" encoding
            - Check if language is in list of Cyrillic-based languages and return "cp1251" encoding
            - Check if language is in list of Central European languages and return "cp1250" encoding
            - Check individual languages and return their specific encodings.
        """
        if self in {
            Language.ALBANIAN,
            Language.BOSNIAN_LATIN,
            Language.CROATIAN,
            Language.CZECH,
            Language.HUNGARIAN,
            Language.MOLDOVAN_LATIN,
            Language.POLISH,
            Language.ROMANIAN,  # before 1993 reform
            Language.SLOVAK,
            Language.SLOVENE,
        }:
            return "cp1250"
        if self in {
            Language.BULGARIAN,
            Language.BELARISIAN,
            Language.MACEDONIAN,
            Language.RUSSIAN,
            Language.SERBIAN_CYRILLIC,
            Language.TAJIK,
            Language.TATAR_CYRILLIC,
            Language.UKRAINIAN,
            Language.UZBEK,
        }:
            return "cp1251"
        if self in {
            Language.ENGLISH,
            Language.FRENCH,
            Language.GERMAN,
            Language.ITALIAN,
            Language.SPANISH,
            Language.AFRIKAANS,
            Language.BASQUE,
            Language.BRETON,
            Language.CATALAN,
            Language.CHAMORRO,
            Language.CHICHEWA,
            Language.CORSICAN,
            Language.DANISH,
            Language.DUTCH,
            Language.FAROESE,
            Language.FILIPINO,
            Language.FINNISH,
            Language.FLEMISH,
            Language.FRISIAN,
            Language.GALICIAN,
            Language.GANDA,
            Language.HAITIAN_CREOLE,
            Language.HAUSA_LATIN,
            Language.HAWAIIAN,
            Language.ICELANDIC,
            Language.IDO,
            Language.INDONESIAN,
            Language.IGBO,
            Language.IRISH,
            Language.INTERLINGUA,
            Language.JAVANESE_LATIN,
            Language.LATIN,
            Language.LUXEMBOURGISH,
            Language.MALTESE,
            Language.MAORI,
            Language.NORWEGIAN,
            Language.OCCITAN,
            Language.PORTUGUESE,
            Language.SCOTS,
            Language.SCOTTISH_GAELIC,
            Language.SHONA,
            Language.SOTO,
            Language.SUNDANESE_LATIN,
            Language.SWAHILI,
            Language.SWEDISH,
            Language.TAGALOG,
            Language.TAHITIAN,
            Language.TONGAN,
            Language.UZBEK_LATIN,
            Language.WALLOON,
            Language.XHOSA,
            Language.YORUBA,
            Language.WELSH,
            Language.ZULU,
        }:
            return "cp1252"
        if self == Language.GREEK:
            return "cp1253"
        if self in {
            Language.AZERBAIJANI_LATIN,
            Language.TURKISH,
            Language.TURKMEN_LATIN,
        }:
            return "cp1254"
        if self == Language.HEBREW:
            return "cp1255"
        if self == Language.ARABIC:
            return "cp1256"
        if self in {
            Language.ESTONIAN,
            Language.LATVIAN,
            Language.LITHUANIAN,
        }:
            return "cp1257"
        if self == Language.VIETNAMESE:
            return "cp1258"
        if self == Language.THAI:
            return "cp874"
        if self in {
            Language.MALAY_LATIN,
            Language.SAMOAN,
            Language.SOMALI,
        }:
            return "ISO-8859-1"
        if self in {
            Language.AYMARA,
            Language.ESPERANTO,
            Language.MALAGASY,
        }:
            return "ISO-8859-3"
        if self == Language.KURDISH_LATIN:
            return "ISO-8859-9"
        if self == Language.KINYARWANDA:
            return "ISO-8859-10"

        # The following languages/encodings may not be 8-bit and need additional information in order to be supported.
        if self == Language.KOREAN:
            return "cp949"
        if self == Language.CHINESE_TRADITIONAL:
            return "cp950"
        if self == Language.CHINESE_SIMPLIFIED:
            return "cp936"
        if self == Language.JAPANESE:
            return "cp932"
        if self == Language.UNKNOWN:
            return None
        msg = f"No encoding defined for language: {self.name}"
        raise ValueError(msg)

    def get_bcp47_code(self):
        lang_map = {
            Language.ENGLISH: "en",
            Language.FRENCH: "fr",
            Language.GERMAN: "de",
            Language.ITALIAN: "it",
            Language.SPANISH: "es",
            Language.POLISH: "pl",
            Language.AFRIKAANS: "af",
            Language.BASQUE: "eu",
            Language.BRETON: "br",
            Language.CATALAN: "ca",
            Language.CHAMORRO: "ch",
            Language.CHICHEWA: "ny",
            Language.CORSICAN: "co",
            Language.DANISH: "da",
            Language.DUTCH: "nl",
            Language.FAROESE: "fo",
            Language.FILIPINO: "filipino",
            Language.FINNISH: "fi",
            Language.FLEMISH: "nl-BE",
            Language.FRISIAN: "fy",
            Language.GALICIAN: "gl",
            Language.GANDA: "lg",
            Language.HAITIAN_CREOLE: "ht",
            Language.HAUSA_LATIN: "ha",
            Language.HAWAIIAN: "haw",
            Language.ICELANDIC: "is",
            Language.IDO: "io",
            Language.INDONESIAN: "id",
            Language.IGBO: "ig",
            Language.IRISH: "ga",
            Language.INTERLINGUA: "ia",
            Language.JAVANESE_LATIN: "jv",  # jv-Latn
            Language.LATIN: "la",
            Language.LUXEMBOURGISH: "lb",
            Language.MALTESE: "mt",
            Language.NORWEGIAN: "no",
            Language.OCCITAN: "oc",
            Language.PORTUGUESE: "pt",
            Language.SCOTS: "sco",
            Language.SCOTTISH_GAELIC: "gd",
            Language.SHONA: "sn",
            Language.SOTO: "st",
            Language.SUNDANESE_LATIN: "su",  # su-Latn
            Language.SWAHILI: "sw",
            Language.SWEDISH: "sv",
            Language.TAGALOG: "tl",
            Language.TAHITIAN: "ty",
            Language.TONGAN: "to",
            Language.UZBEK_LATIN: "uz",  # uz-Latn
            Language.WALLOON: "wa",
            Language.XHOSA: "xh",
            Language.YORUBA: "yo",
            Language.WELSH: "cy",
            Language.ZULU: "zu",
            Language.BULGARIAN: "bg",
            Language.BELARISIAN: "be",
            Language.MACEDONIAN: "mk",
            Language.RUSSIAN: "ru",
            Language.SERBIAN_CYRILLIC: "sr",  # sr-Cyrl
            Language.TAJIK: "tg",
            Language.TATAR_CYRILLIC: "tt",  # tt-Cyrl
            Language.UKRAINIAN: "uk",
            Language.UZBEK: "uz",  # uz-Cyrl
            Language.ALBANIAN: "sq",
            Language.BOSNIAN_LATIN: "bs",
            Language.CZECH: "cs",
            Language.SLOVAK: "sk",
            Language.SLOVENE: "sl",
            Language.CROATIAN: "hr",
            Language.HUNGARIAN: "hu",
            Language.ROMANIAN: "ro",
            Language.GREEK: "el",
            Language.ESPERANTO: "eo",
            Language.AZERBAIJANI_LATIN: "az",  # az-Latn
            Language.TURKISH: "tr",
            Language.TURKMEN_LATIN: "tk",  # tk-Latn
            Language.HEBREW: "he",
            Language.ARABIC: "ar",
            Language.ESTONIAN: "et",
            Language.LATVIAN: "lv",
            Language.LITHUANIAN: "lt",
            Language.VIETNAMESE: "vi",
            Language.THAI: "th",
            Language.AYMARA: "ay",
            Language.KINYARWANDA: "rw",
            Language.KURDISH_LATIN: "ku",  # ku-Latn
            Language.MALAGASY: "mg",
            Language.MALAY_LATIN: "ms",  # ms-Latn
            Language.MAORI: "mi",
            Language.MOLDOVAN_LATIN: "mo",  # mo-Latn
            Language.SAMOAN: "sm",
            Language.SOMALI: "so",
            Language.KOREAN: "ko",
            Language.CHINESE_TRADITIONAL: "zh-TW",  # zh-Hant
            Language.CHINESE_SIMPLIFIED: "zh-CN",  # zh-Hans
            Language.JAPANESE: "ja",
            # Add any additional languages if necessary
        }
        return lang_map.get(self)


class Gender(IntEnum):
    """Gender IDs recognized by both the games in regards to string localization."""

    MALE = 0  # or neutral
    FEMALE = 1


class LocalizedString:
    """Localized strings are a way of the game handling strings that need to be catered to a specific language or gender.

    This is achieved through either referencing a entry in the 'dialog.tlk' or by directly providing strings for each
    language.

    Attributes:
    ----------
        stringref: An index into the 'dialog.tlk' file. If this value is -1 the game will use the stored substrings.
    """

    def __init__(self, stringref: int):
        self.stringref: int = stringref
        self._substrings: dict[int, str] = {}

    def __iter__(self):
        """Iterates through the list of substrings. Yields a tuple containing (language, gender, text)."""
        for substring_id, text in self._substrings.items():
            language, gender = LocalizedString.substring_pair(substring_id)
            yield language, gender, text

    def __len__(self):
        """Returns the number of substrings."""
        return len(self._substrings)

    def __hash__(self):
        return hash(self.stringref)

    def __str__(self):
        """If the stringref is valid, it will return it as a string. Otherwise it will return one of the substrings,
        prioritizing the english substring if it exists. If no substring exists and the stringref is invalid, "-1" is
        returned.
        """
        if self.stringref >= 0:
            return str(self.stringref)
        # TODO: There's no reason we should default to english here, perhaps remove the __str__ overload and ensure relevant references call .get() with language information.
        if self.exists(Language.ENGLISH, Gender.MALE):
            return str(self.get(Language.ENGLISH, Gender.MALE))
        # language either unset or not english.
        for _language, _gender, text in self:
            return text
        return "-1"

    def __eq__(self, other) -> bool:
        if not isinstance(other, LocalizedString):
            return False
        if other.stringref != self.stringref:
            return False
        return other._substrings == self._substrings

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
        """Returns a tuple containing the Language and Gender for a given substring ID.

        Args:
        ----
            substring_id: The ID of the substring

        Returns:
        -------
            tuple: A tuple containing (Language, Gender)

        Processing Logic:
        ----------------
            - Divide the substring_id by 2 to get the Language id
            - Take the remainder of substring_id % 2 to get the Gender id
            - Return a tuple with the Language and Gender enum instances.
        """
        language = Language(substring_id // 2)
        gender = Gender(substring_id % 2)
        return language, gender

    def set_data(
        self,
        language: Language,
        gender: Gender,
        string: str,
    ):
        """Sets the text of the substring with the corresponding language/gender pair.

        Note: The substring is created if it does not exist.

        Args:
        ----
            language: The language.
            gender: The gender.
            string: The new text for the new substring.
        """
        substring_id: int = LocalizedString.substring_id(language, gender)
        self._substrings[substring_id] = string

    def get(
        self,
        language: Language,
        gender: Gender,
        *,
        use_fallback: bool = False,
    ) -> str | None:
        """Gets the substring text with the corresponding language/gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            The text of the substring if a matching pair is found, otherwise returns None.
        """
        substring_id: int = LocalizedString.substring_id(language, gender)
        return self._substrings.get(substring_id, next(iter(self._substrings.values()), None) if use_fallback else None)

    def remove(
        self,
        language: Language,
        gender: Gender,
    ):
        """Removes the existing substring with the respective language/gender pair if it exists.

        Note: No error is thrown if it does not find a corresponding pair.

        Args:
        ----
            language: The language.
            gender: The gender.
        """
        substring_id: int = LocalizedString.substring_id(language, gender)
        self._substrings.pop(substring_id)

    def exists(
        self,
        language: Language,
        gender: Gender,
    ) -> bool:
        """Returns whether or not a substring exists with the respective language/gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            True if the corresponding substring exists.
        """
        substring_id: int = LocalizedString.substring_id(language, gender)
        return substring_id in self._substrings
