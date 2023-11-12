"""This module holds various unrelated classes and methods."""


from __future__ import annotations

import contextlib
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Generic, Iterable, Optional, TypeVar

import charset_normalizer

from pykotor.common.geometry import Vector3
from pykotor.helpers.path import PurePath

if TYPE_CHECKING:
    import os

    from pykotor.common.language import Language

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


def decode_bytes_with_fallbacks(
    byte_content: bytes,
    errors="strict",
    encoding: str | None = None,
    lang: Language | None = None,
) -> str:
    """A well rounded decoding function used to decode byte content with provided language/encoding information. If an exact match cannot be
    determined, it will use heuristics based on what is known, to determine what encoding to use. Utilizes the charset_normalizer library internally.

    Args:
    ----
        byte_content (bytes): the bytes to decode
        errors (str): When detection fails, this determines how to decode the ultimate fallback encoding. Same variable sent to the builtin decode() function.
        lang (Language): The language of the bytes being decoded, if known.
    """
    provided_encoding = encoding or (lang.get_encoding() if lang else None)
    if provided_encoding:
        with contextlib.suppress(UnicodeDecodeError):
            return byte_content.decode(provided_encoding, errors=errors)

    detected_encoding = charset_normalizer.from_bytes(byte_content).best()
    if detected_encoding:
        return byte_content.decode(encoding=detected_encoding.encoding, errors=errors)
    return byte_content.decode(errors=errors)


def find_best_8bit_encoding(s: str) -> str | None:
    # First, we encode the string to UTF-8 bytes. Python str objects are inherently Unicode.
    utf8_encoded = s.encode("utf-8")

    # Then, we try to find the best match for this byte string
    # assuming it was originally encoded with an unknown 8-bit charset
    matches = charset_normalizer.from_bytes(utf8_encoded)

    # We filter out non 8-bit encodings and Unicode encodings
    eight_bit_encodings = [match for match in matches if match.encoding != "utf-8" and "iso" in match.encoding]

    # If we have 8-bit matches, we take the one with the highest confidence
    if eight_bit_encodings:
        best_match = max(eight_bit_encodings, key=lambda m: m.chaos)
        return best_match.encoding

    return None


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

    def pop(self, __key: str, __default: VT = _unique_sentinel) -> VT | T:  # type: ignore[assignment]
        lower_key = __key.lower()
        try:
            # Attempt to pop the value using the case-insensitive key.
            value = self._dictionary.pop(self._case_map.pop(lower_key))
        except KeyError:
            if __default is _unique_sentinel:
                raise
            # Return the default value if lower_key is not found in the case map.
            return __default
        return value

    def get(self, __key: str, __default: VT = None) -> VT | T:  # type: ignore[assignment]
        key_lookup: str = self._case_map.get(__key.lower(), _unique_sentinel)  # type: ignore[arg-type]
        return __default if key_lookup is _unique_sentinel else self._dictionary.get(key_lookup, __default)

    def items(self):
        return self._dictionary.items()

    def values(self):
        return self._dictionary.values()

    def keys(self):
        return self._dictionary.keys()
