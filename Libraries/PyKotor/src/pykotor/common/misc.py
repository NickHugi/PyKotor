"""This module holds various unrelated classes and methods."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, ClassVar, Generic, ItemsView, Iterable, Iterator, TypeVar, overload

from pykotor.common.geometry import Vector3

if TYPE_CHECKING:
    import os

    from collections.abc import ItemsView, Iterable, Iterator

T = TypeVar("T")
VT = TypeVar("VT")
_unique_sentinel = object()


class ResRef:
    """A string reference to a game resource.

    ResRefs are the names of resources without the extension (the file stem).

    Used in:
    -------
        - Encapsulated Resource Files (ERF/MOD/SAV)
        - RIM/BIF archives
        - Filenames in the Override folder

    Restrictions:
    ------------
        - ResRefs must be in ASCII format
        - ResRefs cannot exceed 16 characters in length.
        - Usable in case-insensitive applications. This is because KOTOR was created for Windows, which uses a case-insensitive filesystem.
        - (recommended) Stored as case-sensitive text.
    """

    MAX_LENGTH: ClassVar[int] = 16

    INVALID_CHARACTERS: ClassVar[str] = '<>:"/\\|?*'

    class InvalidFormatError(ValueError):
        """ResRefs must conform to Windows filename requirements."""

    class InvalidEncodingError(ValueError):
        """ResRefs must only contain ASCII characters."""

        def __init__(self, text: str):
            message = f"'{text}' must only contain ASCII characters."
            super().__init__(message)

    class ExceedsMaxLengthError(ValueError):
        """ResRefs cannot exceed the maximum of 16 characters in length."""

        def __init__(self, text: str):
            message = f"Length of '{text}' ({len(text)} characters) exceeds the maximum allowed length ({ResRef.MAX_LENGTH})"
            super().__init__(message)

    class CaseSensitivityError(ValueError):
        """ResRefs cannot be converted to a different case."""

        def __init__(self, resref: ResRef, func_name: str, *args, **kwargs):
            super().__init__(f"ResRef's must be case-insensitive, attempted {resref!r}.{func_name}({args, kwargs})")

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

    def __bool__(self):
        return bool(self._value)

    def __eq__(
        self,
        other,
    ):
        """A ResRef can be compared to another ResRef or a str."""
        if self is other:
            return True
        if isinstance(other, ResRef):
            other_value = str(other).lower()
        elif isinstance(other, str):
            other_value = other.lower().strip()
        else:
            return NotImplemented
        return other_value == self._value.lower()

    def __hash__(self):
        return hash(self._value.lower())

    def __repr__(
        self,
    ):
        return f"ResRef({self._value})"

    def __str__(
        self,
    ):
        return self._value

    @classmethod
    def from_blank(cls) -> ResRef:
        """Returns a blank ResRef.

        Returns:
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
            file_path (os.PathLike | str): The path to the file.

        Returns:
        -------
            A new ResRef instance.
        """
        from pykotor.extract.file import ResourceIdentifier  # Prevent circular imports

        resname = ResourceIdentifier.from_path(file_path).resname
        return cls(resname)

    @classmethod
    def is_valid(cls, text: str) -> bool:
        if not isinstance(text, str):
            return False
        return next(
            (False for char in cls.INVALID_CHARACTERS if char in text),
            (
                text != ""
                and text.isascii()
                and len(text) <= cls.MAX_LENGTH
                and text == text.strip()
            ),
        )

    def set_data(
        self,
        text: str,
        *,
        truncate: bool = False,
    ):  # sourcery skip: remove-unnecessary-cast
        """Sets the ResRef.

        Args:
        ----
            text - str: The reference string.
            truncate - bool: Whether to truncate the text to 16 characters. Default is False.

        Raises:
        ------
            InvalidEncodingError - text was not in ascii format
            ExceedsMaxLengthError - text exceeded 16 characters
            InvalidFormatError - text starts/ends with a space or contains windows invalid filename characters.
            All of the above exceptions inherit ValueError.
        """
        parsed_text: str = str(text)

        # Ensure text only contains ASCII characters.
        if not text.isascii():
            raise self.InvalidEncodingError(text)

        # Validate text length.
        if len(parsed_text) > self.MAX_LENGTH:
            if not truncate:
                ...
                # raise self.ExceedsMaxLengthError(parsed_text)  # FIXME: pykotor isn't stable enough to enforce this yet.
            parsed_text = parsed_text[: self.MAX_LENGTH]

        # Ensure text doesn't start/end with whitespace.
        if parsed_text != parsed_text.strip():
            msg = f"ResRef '{text}' cannot start or end with a space."
            # raise self.InvalidFormatError(msg)  # FIXME: pykotor isn't stable enough to enforce this yet.

        # Ensure text doesn't contain any invalid ASCII characters.
        for i in range(len(parsed_text)):
            if parsed_text[i] in self.INVALID_CHARACTERS:
                msg = f"ResRef '{text}' cannot contain any invalid characters in [{self.INVALID_CHARACTERS}]"
                # raise self.InvalidFormatError(msg)  # FIXME: pykotor isn't stable enough to enforce this yet.

        self._value = parsed_text.strip()

    def get(self) -> str:
        """Returns a case-insensitive wrapped string."""
        return str(self._value)


class Game(IntEnum):
    """Represents which KOTOR game."""

    K1 = 1
    K2 = 2
    K1_XBOX = 3
    K2_XBOX = 4
    K1_IOS = 5
    K2_IOS = 6
    K1_ANDROID = 7
    K2_ANDROID = 8

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def is_xbox(self) -> bool:
        return self in {Game.K1_XBOX, Game.K2_XBOX}

    def is_pc(self) -> bool:
        return self in {Game.K1, Game.K2}

    def is_mobile(self) -> bool:
        return self in {Game.K1_IOS, Game.K1_ANDROID, Game.K2_IOS, Game.K2_ANDROID}

    def is_android(self) -> bool:
        return self in {Game.K1_ANDROID, Game.K2_ANDROID}

    def is_ios(self) -> bool:
        return self in {Game.K1_IOS, Game.K2_IOS}

    def is_k1(self) -> bool:
        return self.value % 2 != 0

    def is_k2(self) -> bool:
        return self.value % 2 == 0


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
        self.r: float = r
        self.g: float = g
        self.b: float = b
        self.a: float = a

    def __repr__(
        self,
    ):
        return f"Color({self})"

    def __str__(
        self,
    ) -> str:
        """Returns a string of each color component separated by whitespace."""
        return f"{self.r} {self.g} {self.b} {self.a}"

    def __eq__(
        self,
        other: Color,
    ):
        """Two Color instances are equal if their color components are equal."""
        if self is other:
            return True
        if not isinstance(other, Color):
            return NotImplemented

        return hash(self) == hash(other)

    def __hash__(
        self,
    ):
        return hash((self.r, self.g, self.b, self.a))

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

        Returns:
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

        Returns:
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

        Returns:
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

        Returns:
        -------
            A new Vector3 instance.
        """
        return Vector3(self.r, self.g, self.b)

    def bgr_vector3(
        self,
    ) -> Vector3:
        """Returns a Vector3 representing a color with its components.

        Returns:
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

    def __hash__(self):
        return hash(self._value)

    def __eq__(
        self,
        other: WrappedInt | int | object,
    ):
        if self is other:
            return True
        if isinstance(other, WrappedInt):
            return self.get() == other.get()
        if isinstance(other, int):  # sourcery skip: assign-if-exp
            return self.get() == other
        return hash(self) == hash(other)

    def set(
        self,
        value: int,
    ):
        self._value = value

    def get(
        self,
    ) -> int:
        return self._value


class InventoryItem:
    def __init__(
        self,
        resref: ResRef,
        droppable: bool = False,  # noqa: FBT001, FBT002
        infinite: bool = False,  # noqa: FBT001, FBT002
    ):
        self.resref: ResRef = resref
        self.droppable: bool = droppable
        self.infinite: bool = infinite

    def __str__(
        self,
    ) -> str:
        return str(self.resref)

    def __eq__(
        self,
        other: object,
    ):
        if self is other:
            return True
        if isinstance(other, InventoryItem):
            return self.resref == other.resref and self.droppable == other.droppable  # and self.infinite == other.infinite
        return NotImplemented

    def __hash__(
        self,
    ):
        return hash(self.resref)


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


class CaseInsensitiveHashSet(set, Generic[T]):
    def __init__(self, iterable: Iterable[T] | None = None):
        super().__init__()
        if iterable is not None:
            for item in iterable:
                self.add(item)

    def _normalize_key(self, item: T):
        return item.casefold() if isinstance(item, str) else item

    def add(self, item: T):
        """Add an element to a set.

        This has no effect if the element is already present.
        """
        key: str | object = self._normalize_key(item)
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

    def __contains__(self, item):
        return super().__contains__(self._normalize_key(item))

    def __eq__(self, other):
        if self is other:
            return True
        return super().__eq__({self._normalize_key(item) for item in other})

    def __ne__(self, other):
        return super().__ne__({self._normalize_key(item) for item in other})


class CaseInsensitiveDict(Generic[T]):
    """A class exactly like the builtin dict[str, Any], but provides case-insensitive key lookups.

    The case-sensitivity of the keys themselves are always preserved.
    """

    def __init__(
        self,
        initial: Mapping[str, T] | Iterable[tuple[str, T]] | ItemsView[str, T] | None = None,
    ):
        self._dictionary: dict[str, T] = {}
        self._case_map: dict[str, T] = {}

        if initial:
            # If initial is a mapping, use its items method.
            items: Iterable[tuple[str, T]] | ItemsView[str, T] | ItemsView[tuple[str, T], T] = (
                initial.items()
                if isinstance(initial, Mapping)
                else initial
            )

            # Iterate over initial items directly, avoiding the creation of an interim dict
            for key, value in items:
                assert not isinstance(key, tuple), f"key '{key!r}' and value '{value!r}' are not expected types."
                if isinstance(key, tuple):
                    # Unpack key-value tuple
                    k, v = key
                    self[k] = v
                else:
                    self[key] = value

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

    #    @classmethod
    #    def __class_getitem__(cls, item: Any) -> GenericAlias:
    #        return GenericAlias(cls, item)

    def __eq__(self, other: object) -> bool:
        # Quick checks.
        if self is other:
            return True
        is_casedict = isinstance(other, CaseInsensitiveDict)
        is_dict = isinstance(other, dict) and not is_casedict  # for future implementation when we make CaseInsensitiveDict subclass dict.
        if not is_dict and not is_casedict:
            return NotImplemented
        # it's a dict of some sort, do some more quick checks.
        if is_casedict and other._case_map != self._case_map:
            return False
        other_dict: dict[str, T] = other._dictionary if isinstance(other, CaseInsensitiveDict) else other
        if len(self._dictionary) != len(other_dict):
            return False

        # unfortunately we must now iterate over each and compare (slow)
        for key, value in self._dictionary.items():
            other_value: T | None = other_dict.get(key.lower())
            if other_value != value:
                return False

        return True

    def __iter__(self) -> Iterator[str]:
        yield from self._dictionary

    def __getitem__(self, key: str) -> T:
        if not isinstance(key, str):
            msg = f"Keys must be strings in CaseInsensitiveDict-inherited classes, got {key!r}"
            raise KeyError(msg)
        return self._dictionary[self._case_map[key.lower()]]

    def __setitem__(self, key: str, value: T):
        if not isinstance(key, str):
            msg = f"Keys must be strings in CaseInsensitiveDict-inherited classes, got {key!r}"
            raise KeyError(msg)
        if key in self:
            self.__delitem__(key)
        self._case_map[key.lower()] = key
        self._dictionary[key] = value

    def __delitem__(self, key: str):
        if not isinstance(key, str):
            msg = f"Keys must be strings in CaseInsensitiveDict-inherited classes, got {key!r}"
            raise KeyError(msg)
        lower_key = key.lower()
        del self._dictionary[self._case_map[lower_key]]
        del self._case_map[lower_key]

    def __contains__(self, key: str) -> bool:
        return key.lower() in self._case_map

    def __len__(self) -> int:
        return len(self._dictionary)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.from_dict({self._dictionary!r})"

    def __or__(self, other):
        if not isinstance(other, (dict, CaseInsensitiveDict)):
            return NotImplemented
        new_dict: CaseInsensitiveDict[T] = self.copy()
        new_dict.update(other)
        return new_dict

    def __ror__(self, other):
        if not isinstance(other, (dict, CaseInsensitiveDict)):
            return NotImplemented
        other_dict: CaseInsensitiveDict[T] = other if isinstance(other, CaseInsensitiveDict) else CaseInsensitiveDict.from_dict(other)
        new_dict: CaseInsensitiveDict[T] = other_dict.copy()
        new_dict.update(self)
        return new_dict

    def __ior__(self, other):
        self.update(other)
        return self

    def __reversed__(self) -> Iterator[str]:
        return reversed(list(self._dictionary.keys()))

    @overload
    def pop(self, __key: str) -> T: ...
    @overload
    def pop(self, __key: str, __default: VT = None) -> VT | T: ...

    def pop(self, __key: str, __default: VT = _unique_sentinel) -> VT | T:  # type: ignore[assignment]
        lower_key: str = __key.lower()
        try:
            # Attempt to pop the value using the case-insensitive key.
            value: T = self._dictionary.pop(self._case_map.pop(lower_key))
        except KeyError:
            if __default is _unique_sentinel:
                raise
            # Return the default value if lower_key is not found in the case map.
            return __default
        return value

    def update(self, other):
        """Extend the dictionary with the key/value pairs from other, overwriting existing keys.

        This method acts like the `update` method in a regular dictionary, but is case-insensitive.

        Args:
        ----
            other (Iterable[tuple[str, T]] | dict[str, T]):
                Key/value pairs to add to the dictionary. Can be another dictionary or an iterable of key/value pairs.
        """
        if isinstance(other, (dict, CaseInsensitiveDict)):
            for key, value in other.items():
                if not isinstance(key, str):
                    msg = f"{key} must be a str, got type {key.__class__}"
                    raise TypeError(msg)
                self[key] = value
        else:
            for key, value in other:
                if not isinstance(key, str):
                    msg = f"{key} must be a str, got type {key.__class__}"
                    raise TypeError(msg)
                self[key] = value

    @overload
    def get(self, __key: str) -> T: ...
    @overload
    def get(self, __key: str, __default: VT = None) -> VT | T: ...

    def get(self, __key: str, __default: VT = None) -> VT | T:  # type: ignore[assignment]
        key_lookup: str = self._case_map.get(__key.lower(), _unique_sentinel)  # type: ignore[arg-type]
        return (
            __default
            if key_lookup is _unique_sentinel
            else self._dictionary.get(key_lookup, __default)
        )

    def items(self):
        return self._dictionary.items()

    def values(self):
        return self._dictionary.values()

    def keys(self):
        return self._dictionary.keys()

    def copy(self) -> CaseInsensitiveDict[T]:
        return self.from_dict(self._dictionary)
