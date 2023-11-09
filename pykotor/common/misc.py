"""This module holds various unrelated classes and methods."""

from __future__ import annotations

from copy import deepcopy
from enum import Enum, IntEnum

try:
    import chardet
except ImportError:
    chardet = None
try:
    import cchardet
except ImportError:
    cchardet = None
try:
    import charset_normalizer
except ImportError:
    charset_normalizer = None
from typing import TYPE_CHECKING, Generic, Iterable, Optional, TypeVar

from pykotor.common.geometry import Vector3
from pykotor.tools.path import PurePath

if TYPE_CHECKING:
    import os

T = TypeVar("T")
VT = TypeVar("VT")
_unique_sentinel = object()


class ResRef:
    """A string reference to a game resource. ResRefs can be a maximum of 16 characters in length."""

    class InvalidEncodingError(ValueError):
        ...

    class ExceedsMaxLengthError(ValueError):
        ...

    def __init__(
        self,
        text: str,
    ):
        self._value = ""
        self.set_data(text)

    def __len__(
        self,
    ):
        return len(self._value)

    def __eq__(
        self,
        other,
    ):
        """A ResRef can be compared to another ResRef or a str."""
        if isinstance(other, ResRef):
            other_value = other.get().lower()
        elif isinstance(other, str):
            other_value = other.lower()
        else:
            return NotImplemented
        return other_value == self._value.lower()

    def __repr__(
        self,
    ):
        return f"ResRef({self._value})"

    def __str__(
        self,
    ):
        return self._value

    @classmethod
    def from_blank(
        cls,
    ) -> ResRef:
        """Returns a blank ResRef.

        Returns
        -------
            A new ResRef instance.
        """
        return cls("")

    @classmethod
    def from_path(
        cls,
        file_path: os.PathLike | str,
    ) -> ResRef:
        """Returns a ResRef from the filename in the specified path.

        Args:
        ----
            path: The filepath.

        Returns:
        -------
            A new ResRef instance.
        """
        return cls(PurePath(file_path).name)

    def set_data(
        self,
        text: str,
        truncate: bool = True,
    ) -> None:
        """Sets the ResRef.

        Args:
        ----
            text: The reference string.
            truncate: If true, the string will be truncated to 16 characters, otherwise it will raise an error instead.

        Raises:
        ------
            ValueError:
        """
        if len(text) > 16:
            if truncate:
                text = text[:16]
            else:
                msg = "ResRef cannot exceed 16 characters."  # sourcery skip: inline-variable
                raise ResRef.ExceedsMaxLengthError(msg)
        if len(text) != len(text.encode(encoding="ascii", errors="strict")):
            msg = "ResRef must be in ASCII characters."  # sourcery skip: inline-variable
            raise ResRef.InvalidEncodingError(msg)

        self._value = text

    def get(
        self,
    ) -> str:
        return self._value


class Game(IntEnum):
    """Represents which game."""

    K1 = 1
    K2 = 2


class Color:
    # Listed here for hinting purposes
    RED: Color
    GREEN: Color
    BLUE: Color
    BLACK: Color
    WHITE: Color

    def __init__(
        self,
        r: float,
        g: float,
        b: float,
        a: float = 1.0,
    ):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __repr__(
        self,
    ):
        return f"Color({self.r}, {self.g}, {self.b}, {self.g})"

    def __str__(
        self,
    ):
        """Returns a string of each color component separated by whitespace."""
        return f"{self.r} {self.g} {self.b} {self.a}"

    def __eq__(
        self,
        other: Color | object,
    ):
        """Two Color instances are equal if their color components are equal."""
        if not isinstance(other, Color):
            return NotImplemented

        return other.r == self.r and other.g == self.g and other.b == self.b and other.a == self.a

    @classmethod
    def from_rgb_integer(
        cls,
        integer: int,
    ) -> Color:
        """Returns a Color by decoding the specified integer.

        Args:
        ----
            integer: RGB integer.

        Returns:
        -------
            A new Color instance.
        """
        red = (0x000000FF & integer) / 255
        green = ((0x0000FF00 & integer) >> 8) / 255
        blue = ((0x00FF0000 & integer) >> 16) / 255
        return Color(red, green, blue)

    @classmethod
    def from_rgba_integer(
        cls,
        integer: int,
    ) -> Color:
        """Returns a Color by decoding the specified integer.

        Args:
        ----
            integer: RGB integer.

        Returns:
        -------
            A new Color instance.
        """
        red = (0x000000FF & integer) / 255
        green = ((0x0000FF00 & integer) >> 8) / 255
        blue = ((0x00FF0000 & integer) >> 16) / 255
        alpha = ((0xFF000000 & integer) >> 24) / 255
        return Color(red, green, blue, alpha)

    @classmethod
    def from_bgr_integer(
        cls,
        integer: int,
    ) -> Color:
        """Returns a Color by decoding the specified integer.

        Args:
        ----
            integer: BGR integer.

        Returns:
        -------
            A new Color instance.
        """
        red = ((0x00FF0000 & integer) >> 16) / 255
        green = ((0x0000FF00 & integer) >> 8) / 255
        blue = (0x000000FF & integer) / 255
        return Color(red, green, blue)

    @classmethod
    def from_rgb_vector3(
        cls,
        vector3: Vector3,
    ) -> Color:
        """Returns a Color from the specified vector components.

        Args:
        ----
            vector3: A Vector3 instance.

        Returns:
        -------
            A new Color instance.
        """
        red = vector3.x
        green = vector3.y
        blue = vector3.z
        return Color(red, green, blue)

    @classmethod
    def from_bgr_vector3(
        cls,
        vector3: Vector3,
    ) -> Color:
        """Returns a Color from the specified vector components.

        Args:
        ----
            vector3: A Vector3 instance.

        Returns:
        -------
            A new Color instance.
        """
        red = vector3.z
        green = vector3.y
        blue = vector3.x
        return Color(red, green, blue)

    def rgb_integer(
        self,
    ) -> int:
        """Returns a RGB integer encoded from the color components.

        Returns
        -------
            A integer representing a color.
        """
        red = int(self.r * 0xFF) << 0
        green = int(self.g * 0xFF) << 8
        blue = int(self.b * 0xFF) << 16
        return red + green + blue

    def rgba_integer(
        self,
    ) -> int:
        """Returns a RGB integer encoded from the color components.

        Returns
        -------
            A integer representing a color.
        """
        red = int(self.r * 0xFF) << 0
        green = int(self.g * 0xFF) << 8
        blue = int(self.b * 0xFF) << 16
        alpha = int(self.a * 0xFF) << 24
        return red + green + blue + alpha

    def bgr_integer(
        self,
    ) -> int:
        """Returns a BGR integer encoded from the color components.

        Returns
        -------
            A integer representing a color.
        """
        red = int(self.r * 255) << 16
        green = int(self.g * 255) << 8
        blue = int(self.b * 255)
        return red + green + blue

    def rgb_vector3(
        self,
    ) -> Vector3:
        """Returns a Vector3 representing a color with its components.

        Returns
        -------
            A new Vector3 instance.
        """
        return Vector3(self.r, self.g, self.b)

    def bgr_vector3(
        self,
    ) -> Vector3:
        """Returns a Vector3 representing a color with its components.

        Returns
        -------
            A new Vector3 instance.
        """
        return Vector3(self.b, self.g, self.r)


Color.RED = Color(1.0, 0.0, 0.0)
Color.GREEN = Color(0.0, 1.0, 0.0)
Color.BLUE = Color(0.0, 0.0, 1.0)
Color.BLACK = Color(0.0, 0.0, 0.0)
Color.WHITE = Color(1.0, 1.0, 1.0)


class WrappedInt:
    def __init__(
        self,
        value: int = 0,
    ):
        self._value: int = value

    def __add__(
        self,
        other: WrappedInt | int | object,
    ):
        if isinstance(other, WrappedInt):
            self._value += other.get()
            return None
        if isinstance(other, int):
            self._value += other
            return None
        return NotImplemented

    def __eq__(
        self,
        other: WrappedInt | int | object,
    ):
        if isinstance(other, WrappedInt):
            return self.get() == other.get()
        if isinstance(other, int):
            return self.get() == other
        return NotImplemented

    def set(
        self,
        value: int,
    ) -> None:
        self._value = value

    def get(
        self,
    ) -> int:
        return self._value


class InventoryItem:
    def __init__(
        self,
        resref: ResRef,
        droppable: bool = False,
        infinite: bool = False,
    ):
        self.resref: ResRef = resref
        self.droppable: bool = droppable
        self.infinite: bool = infinite

    def __str__(
        self,
    ):
        return self.resref.get()

    def __eq__(
        self,
        other: object,
    ):
        if not isinstance(other, InventoryItem):
            return NotImplemented
        return self.resref == other.resref and self.droppable == other.droppable


class EquipmentSlot(Enum):
    INVALID = 0
    HEAD = 1**0
    ARMOR = 2**1
    GAUNTLET = 2**3
    RIGHT_HAND = 2**4
    LEFT_HAND = 2**5
    RIGHT_ARM = 2**7
    LEFT_ARM = 2**8
    IMPLANT = 2**9
    BELT = 2**10
    CLAW1 = 2**14
    CLAW2 = 2**15
    CLAW3 = 2**16
    HIDE = 2**17
    # TSL Only:
    RIGHT_HAND_2 = 2**18
    LEFT_HAND_2 = 2**19


FALLBACK_ENCODINGS = [
    # "ascii",        # python's encode() and decode() defaults to utf-8 so we should match the behavior.  # noqa: ERA001
    "utf_8",        # UTF-8: Extremely popular, variable-width, and likely to throw errors on invalid data.
    "windows-1252", # Windows-1252: Common in Western languages, superset of ISO-8859-1, with well-defined error behavior.
    "iso8859_15",   # ISO-8859-15: Similar to ISO-8859-1 but includes the euro sign and other characters.
    "shift_jis",    # Shift_JIS: Popular in Japanese text, likely to throw errors on non-Japanese data.
    "gbk",          # GBK: Superset of GB2312, popular for Simplified Chinese, distinct error behavior.
    "euc_kr",       # EUC-KR: Common for Korean text, good error signaling.
    "iso8859_2",    # ISO-8859-2: Latin alphabet for Central European languages, more specific than ISO-8859-1.
    "iso8859_5",    # ISO-8859-5: Used for Cyrillic scripts, less common and likely to signal errors for non-Cyrillic text.
    "iso8859_6",    # ISO-8859-6: Used for Arabic, strict error handling for non-Arabic text.
    "iso8859_7",    # ISO-8859-7: Designed for Modern Greek, likely to produce errors for non-Greek text.
    "iso8859_9",    # ISO-8859-9: Latin alphabet for Turkish, similar error behavior to other single-byte encodings.
    "utf_16",       # UTF-16: Can encode all Unicode characters, with potential errors from improper surrogate handling.
    "latin_1",      # ISO-8859-1: As a semi-last resort, can decode any byte stream to some character representation.
    "utf_32",       # UTF-32: Can encode everything but is less common and has a clear error behavior for incorrect data.
]


def decode_bytes_with_fallbacks(byte_content: bytes, errors="strict", encoding: str | None = None) -> str:
    if len(byte_content) == 0:
        return ""
    decoded_text: str | None = None
    encodings_to_try = deepcopy(FALLBACK_ENCODINGS)
    detected_encoding: str | None = None

    # If a specific encoding is provided, try that first
    if isinstance(encoding, str):
        encodings_to_try.insert(0, encoding)  # user choice, insert after utf-8

    # Detect encoding if one of our encoding detection libraries are available
    if charset_normalizer is not None:
        matches = charset_normalizer.from_bytes(byte_content).best()
        if matches and matches.encoding:
            detected_encoding = matches.encoding
        if detected_encoding:
            encodings_to_try.insert(1 if isinstance(encoding, str) else 2, detected_encoding)  # chardet_normalizer's best guess, insert after utf-8
    if not detected_encoding and chardet is not None:
        detected_encoding = (chardet.detect(byte_content) or {}).get("encoding")
        if detected_encoding:
            encodings_to_try.insert(1 if isinstance(encoding, str) else 2, detected_encoding)  # chardet's best guess, insert after utf-8
    if not detected_encoding and cchardet is not None:
        detected_encoding = (cchardet.detect(byte_content) or {}).get("encoding")
        if detected_encoding:
            encodings_to_try.insert(1 if isinstance(encoding, str) else 2, detected_encoding)  # cchardet's best guess, insert after utf-8

    for enc in encodings_to_try:
        try:
            decoded_text = byte_content.decode(enc, errors="strict")
            break  # Stop at the first successful decoding
        except UnicodeDecodeError:
            continue

    return decoded_text or byte_content.decode("iso-8859-1", errors=errors)


class CaseInsensitiveHashSet(set, Generic[T]):
    def __init__(self, iterable: Optional[Iterable[T]] = None):
        super().__init__()
        if iterable:
            for item in iterable:
                self.add(item)

    def _normalize_key(self, item: T):
        return item.lower() if isinstance(item, str) else item

    def add(self, item: T):
        """Add an element to a set.

        This has no effect if the element is already present.
        """
        key = self._normalize_key(item)
        if key not in self:
            super().add(item)

    def remove(self, item: T):
        """Remove an element from a set; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        super().remove(self._normalize_key(item))

    def discard(self, item: T):
        """Remove an element from a set if it is a member.

        Unlike set.remove(), the discard() method does not raise an exception when an element is missing from the set.
        """
        super().discard(self._normalize_key(item))

    def update(self, *others):
        """Update a set with the union of itself and others."""
        for other in others:
            for item in other:
                self.add(item)

    def __contains__(self, item) -> bool:
        return super().__contains__(self._normalize_key(item))

    def __le__(self, other) -> bool:
        return super().__le__({self._normalize_key(item) for item in other})

    def __lt__(self, other) -> bool:
        return super().__lt__({self._normalize_key(item) for item in other})

    def __eq__(self, other) -> bool:
        return super().__eq__({self._normalize_key(item) for item in other})

    def __ne__(self, other) -> bool:
        return super().__ne__({self._normalize_key(item) for item in other})

    def __gt__(self, other) -> bool:
        return super().__gt__({self._normalize_key(item) for item in other})

    def __ge__(self, other) -> bool:
        return super().__ge__({self._normalize_key(item) for item in other})


class CaseInsensitiveDict(Generic[T]):
    def __init__(
        self,
        initial: Iterable[tuple[str, T]] | None = None,
    ):
        self._dictionary: dict[str, T] = {}
        self._case_map: dict[str, str] = {}

        if initial:
            # Iterate over initial items directly, avoiding the creation of an interim dict
            for key, value in initial:
                self[key] = value  # Utilize the __setitem__ method for setting items

    @classmethod
    def from_dict(cls, initial: dict[str, T]) -> CaseInsensitiveDict[T]:
        """Class method to create a CaseInsensitiveDict instance from a dictionary.

        Args:
        ----
            initial (dict[str, T]): A dictionary from which to create the CaseInsensitiveDict.

        Returns:
        -------
            CaseInsensitiveDict[T]: A new instance of CaseInsensitiveDict.
        """
        # Create an empty instance of CaseInsensitiveDict
        case_insensitive_dict = cls()

        for key, value in initial.items():
            case_insensitive_dict[key] = value  # Utilize the __setitem__ method for setting items

        return case_insensitive_dict

    def __iter__(self):
        yield from self._dictionary

    def __getitem__(self, key: str) -> T:
        return self._dictionary[self._case_map[key.lower()]]

    def __setitem__(self, key: str, value: T):
        lower_key = key.lower()
        self._case_map[lower_key] = key
        self._dictionary[key] = value  # Store the original form

    def __delitem__(self, key: str):
        lower_key = key.lower()
        del self._dictionary[self._case_map[lower_key]]
        del self._case_map[lower_key]

    def __contains__(self, key: str) -> bool:
        return key.lower() in self._case_map

    def __len__(self) -> int:
        return len(self._dictionary)

    def __repr__(self) -> str:
        return repr(self._dictionary)

    def pop(self, key: str, __default: VT = None) -> VT | T:
        lower_key = key.lower()
        try:
            # Attempt to pop the value using the case-insensitive key.
            value = self._dictionary.pop(self._case_map.pop(lower_key))
        except KeyError:
            # Return the default value if lower_key is not found in the case map.
            return __default
        return value

    def get(self, __key: str, __default: VT = None) -> VT | T:
        # sourcery skip: compare-via-equals
        key_lookup: str = self._case_map.get(__key.lower(), _unique_sentinel)  # type: ignore[arg-type]
        return __default if key_lookup is _unique_sentinel else self._dictionary.get(key_lookup, __default)

    def items(self):
        return self._dictionary.items()

    def values(self):
        return self._dictionary.values()

    def keys(self):
        return self._dictionary.keys()
