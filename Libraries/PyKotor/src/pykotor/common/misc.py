from __future__ import annotations

import warnings
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Iterable, TypeVar

from collections.abc import Iterable
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from utility.common.geometry import Vector3

if TYPE_CHECKING:
    import os

    from collections.abc import Iterable

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

T = TypeVar("T")
VT = TypeVar("VT")
_unique_sentinel = object()


class ResRef(str):
    """A string reference to a game resource.

    ResRefs are the names of resources without the extension (the file stem).
    They serve as identifiers for game resources stored in archives (BIF, ERF, RIM)
    or as standalone files in the Override folder.

    Used in:
    -------
        - Encapsulated Resource Files (ERF/MOD/SAV)
        - RIM/BIF archives
        - Filenames in the Override folder
        - GFF field values (ResRef field type)
        - Resource lookups and references throughout the engine
    
    References:
    ----------
        vendor/reone/include/reone/resource/resref.h:26-66 (ResRef class definition)
        vendor/reone/include/reone/resource/resref.h:26 (kMaxResRefLength constant = 16)
        vendor/reone/include/reone/resource/resref.h:32-38 (ResRef constructor with truncation and lowercasing)
        vendor/Kotor.NET/Kotor.NET/Common/Data/ResRef.cs:9-72 (ResRef class, max length 16)
        vendor/HoloPatcher.NET/src/TSLPatcher.Core/Common/ResRef.cs:12-132 (ResRef class with validation)
        vendor/HoloPatcher.NET/src/TSLPatcher.Core/Common/ResRef.cs:15 (MaxLength constant = 16)
        vendor/HoloPatcher.NET/src/TSLPatcher.Core/Common/ResRef.cs:15 (InvalidCharacters constant)
        vendor/KotOR_IO/KotOR_IO/File Formats/GFF FieldTypes/B_ResRef.cs (ResRef GFF field type)
        vendor/xoreos-tools/src/common/util.cpp (ResRef handling utilities)
        vendor/KotOR.js/src/resource/ResourceTypes.ts (Resource type definitions)
        vendor/KotOR-dotNET/AuroraFile.cs (ResRef in C#)
        vendor/kotor/kotor/resref.py (ResRef handling in Python)
        Original BioWare Odyssey Engine (ResRef format specification)
        Note: ResRef case-insensitivity is critical for cross-platform compatibility

    Restrictions:
    ------------
        - ResRefs must be in ASCII format (non-ASCII characters are invalid)
        - ResRefs cannot exceed 16 characters in length (MAX_LENGTH = 16)
        - ResRefs cannot contain Windows filename invalid characters: '<>:"/\\|?*'
        - Usable in case-insensitive applications (KOTOR was created for Windows case-insensitive filesystem)
        - (recommended) Stored as case-sensitive text for cross-platform compatibility
        - ResRefs are trimmed of whitespace (leading/trailing spaces removed)
    
    Discrepancies:
    -------------
        - reone lowercases ResRefs automatically (resref.h:37: boost::to_lower(_value))
        - PyKotor preserves case but uses casefold() for comparisons (case-insensitive equality)
        - HoloPatcher.NET preserves case but uses case-insensitive comparison (StringComparison.OrdinalIgnoreCase)
        - Kotor.NET preserves case without automatic lowercasing
        - Original engine: Windows case-insensitive filesystem, ResRefs stored as-is but matched case-insensitively
    """

    __slots__: ClassVar[tuple[str, ...]] = ("_value",)

    MAX_LENGTH: ClassVar[int] = 16
    """Maximum length of a ResRef in characters.
    
    Reference: reone/resref.h:26 (kMaxResRefLength = 16)
    Reference: HoloPatcher.NET/ResRef.cs:14 (MaxLength = 16)
    Reference: Kotor.NET/ResRef.cs:30 (Length check > 16)
    This is a hard limit enforced by the BioWare Odyssey Engine.
    """

    INVALID_CHARACTERS: ClassVar[str] = '<>:"/\\|?*'
    """Characters that are invalid in ResRefs (Windows filename restrictions).
    
    Reference: HoloPatcher.NET/ResRef.cs:15 (InvalidCharacters constant)
    These characters cannot appear in Windows filenames and are therefore
    invalid for ResRefs which are used as filenames.
    """

    class InvalidFormatError(ValueError):
        """ResRefs must conform to Windows filename requirements."""

        def __init__(self, bad_text: str):
            invalid_chars: list[tuple[str, int]] = [(char, pos) for pos, char in enumerate(bad_text) if char in ResRef.INVALID_CHARACTERS]
            details: str = ", ".join(f"'{char}' at position {pos}" for char, pos in invalid_chars)
            message: str = f"String '{bad_text}' contains invalid characters: {details}. " f"Full list of invalid characters: '{ResRef.INVALID_CHARACTERS}'"
            super().__init__(message)

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

    def __new__(cls, text: str) -> Self:
        # Create the instance
        instance: Self = super().__new__(cls, text)
        instance.set_data(text)
        return instance

    def __len__(
        self,
    ):
        return len(self._value.strip())  # should already be stripped, leave here for clarity (it is a fast operation)

    def __bool__(self):
        return bool(self._value.strip())  # should already be stripped, leave here for clarity (it is a fast operation)

    def __eq__(
        self,
        other,
    ):
        """A ResRef can be compared to another ResRef or a str."""
        if self is other:
            return True
        if not isinstance(other, str):
            return NotImplemented
        other_value: str = other.casefold().strip()
        return other_value == self._value.casefold()

    def __hash__(self):
        return hash(self._value.casefold())

    def __repr__(
        self,
    ):
        return f"ResRef({self._value})"

    def __str__(
        self,
    ):
        return str(self._value)

    @classmethod
    def from_blank(cls) -> Self:
        return cls("")

    @classmethod
    def from_path(
        cls,
        file_path: os.PathLike | str,
    ) -> Self:
        from pykotor.extract.file import ResourceIdentifier  # Prevent circular imports

        resname: str = ResourceIdentifier.from_path(file_path).resname
        return cls(resname)

    @classmethod
    def is_valid(
        cls,
        text: str,
    ) -> bool:
        if not isinstance(text, str):
            return False
        return next(
            (False for char in cls.INVALID_CHARACTERS if char in text),
            (text != "" and text.isascii() and len(text) <= cls.MAX_LENGTH and text == text.strip()),
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
        parsed_text: str = str(text).strip()
        # Check for leading or trailing whitespace. Ensure text doesn't start/end with whitespace.
        raw_text = str(text)
        text = raw_text.strip()
        if raw_text != text:
            msg = f"String '{raw_text}' starts or ends with whitespace. It will be stripped to '{text}'"
            warnings.warn(msg, stacklevel=2)

        # Check for maximum length
        if len(text) > self.MAX_LENGTH:
            if not truncate:
                raise self.ExceedsMaxLengthError(text)
            warnings.warn(f"String '{raw_text}' exceeds the maximum allowed length ({self.MAX_LENGTH}) and will be truncated to '{text}'", stacklevel=2)
            text = text[: self.MAX_LENGTH]

        if any(
            (char, pos)  # Check for invalid characters and their positions
            for pos, char in enumerate(text)
            if char in self.INVALID_CHARACTERS
        ):
            raise self.InvalidFormatError(text)

        if not text.isascii():  # Ensure text only contains ASCII characters.
            raise self.InvalidEncodingError(text)

        # Validate text length.
        if len(parsed_text) > self.MAX_LENGTH:
            if not truncate:
                raise self.ExceedsMaxLengthError(parsed_text)
            parsed_text = parsed_text[: self.MAX_LENGTH]

        # Ensure text doesn't contain any invalid ASCII characters.
        for i in range(len(parsed_text)):
            if parsed_text[i] in self.INVALID_CHARACTERS:
                msg = f"ResRef '{text}' cannot contain any invalid characters in [{self.INVALID_CHARACTERS}]"
                raise self.InvalidFormatError(msg)

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
    RED: ClassVar[Color]
    GREEN: ClassVar[Color]
    BLUE: ClassVar[Color]
    BLACK: ClassVar[Color]
    WHITE: ClassVar[Color]

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

    def __repr__(self):
        return f"Color({self})"

    def __str__(self) -> str:
        """Returns a string of each color component separated by whitespace."""
        return f"{self.r} {self.g} {self.b} {self.a}"

    def __eq__(
        self,
        other,
    ):
        """Two Color instances are equal if their color components are equal."""
        if self is other:
            return True
        if not isinstance(other, Color):
            return NotImplemented

        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.a or 1.0))

    @classmethod
    def from_rgb_integer(
        cls,
        integer: int,
    ) -> Self:
        """Returns a Color by decoding the specified integer.

        Args:
        ----
            integer: RGB integer.

        Returns:
        -------
            A new Color instance.
        """
        red: float = (0x000000FF & integer) / 255
        green: float = ((0x0000FF00 & integer) >> 8) / 255
        blue: float = ((0x00FF0000 & integer) >> 16) / 255
        return cls(red, green, blue)

    @classmethod
    def from_rgba_integer(
        cls,
        integer: int,
    ) -> Self:
        """Returns a Color by decoding the specified integer.

        Args:
        ----
            integer: RGB integer.

        Returns:
        -------
            A new Color instance.
        """
        red: float = (0x000000FF & integer) / 255
        green: float = ((0x0000FF00 & integer) >> 8) / 255
        blue: float = ((0x00FF0000 & integer) >> 16) / 255
        alpha: float = ((0xFF000000 & integer) >> 24) / 255
        return cls(red, green, blue, alpha)

    @classmethod
    def from_bgr_integer(
        cls,
        integer: int,
    ) -> Self:
        """Returns a Color by decoding the specified integer.

        Args:
        ----
            integer: BGR integer.

        Returns:
        -------
            A new Color instance.
        """
        red: float = ((0x00FF0000 & integer) >> 16) / 255
        green: float = ((0x0000FF00 & integer) >> 8) / 255
        blue: float = (0x000000FF & integer) / 255
        return cls(red, green, blue)

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
        red: float = vector3.x
        green: float = vector3.y
        blue: float = vector3.z
        return Color(red, green, blue)

    @classmethod
    def from_bgr_vector3(
        cls,
        vector3: Vector3,
    ) -> Self:
        """Returns a Color from the specified vector components.

        Args:
        ----
            vector3: A Vector3 instance.

        Returns:
        -------
            A new Color instance.
        """
        red: float = vector3.z
        green: float = vector3.y
        blue: float = vector3.x
        return cls(red, green, blue)

    @classmethod
    def from_hex_string(
        cls,
        hex_string: str,
    ) -> Self:
        # Remove '#' if present and convert to lowercase
        color_str: str = hex_string.lstrip("#").lower()
        instance: Self = cls(0, 0, 0)

        # Handle different hex color formats
        # All values are normalized to 0.0-1.0 range by dividing by 255.0
        if len(color_str) == 3:  # Short hex format (RGB)  # noqa: PLR2004
            instance.r = int(color_str[0] * 2, 16) / 255.0
            instance.g = int(color_str[1] * 2, 16) / 255.0
            instance.b = int(color_str[2] * 2, 16) / 255.0
            instance.a = 1.0
        elif len(color_str) == 4:  # Short hex format with alpha (RGBA)  # noqa: PLR2004
            instance.r = int(color_str[0] * 2, 16) / 255.0
            instance.g = int(color_str[1] * 2, 16) / 255.0
            instance.b = int(color_str[2] * 2, 16) / 255.0
            instance.a = int(color_str[3] * 2, 16) / 255.0
        elif len(color_str) == 6:  # Full hex format (RGB)  # noqa: PLR2004
            instance.r = int(color_str[0:2], 16) / 255.0
            instance.g = int(color_str[2:4], 16) / 255.0
            instance.b = int(color_str[4:6], 16) / 255.0
            instance.a = 1.0
        elif len(color_str) == 8:  # Full hex format with alpha (RGBA)  # noqa: PLR2004
            instance.r = int(color_str[0:2], 16) / 255.0
            instance.g = int(color_str[2:4], 16) / 255.0
            instance.b = int(color_str[4:6], 16) / 255.0
            instance.a = int(color_str[6:8], 16) / 255.0
        else:
            raise ValueError(f"Invalid hex color format: {color_str}")
        return instance

    def rgb_integer(self) -> int:
        """Returns a RGB integer encoded from the color components.

        Returns:
        -------
            A integer representing a color.
        """
        red: int = int(self.r * 0xFF) << 0
        green: int = int(self.g * 0xFF) << 8
        blue: int = int(self.b * 0xFF) << 16
        return red + green + blue

    def rgba_integer(self) -> int:
        """Returns a RGB integer encoded from the color components.

        Returns:
        -------
            A integer representing a color.
        """
        red: int = int(self.r * 0xFF) << 0
        green: int = int(self.g * 0xFF) << 8
        blue: int = int(self.b * 0xFF) << 16
        alpha: int = int((self.a or 1.0) * 0xFF) << 24
        return red + green + blue + alpha

    def bgr_integer(self) -> int:
        """Returns a BGR integer encoded from the color components.

        Returns:
        -------
            A integer representing a color.
        """
        red: int = int(self.r * 255) << 16
        green: int = int(self.g * 255) << 8
        blue: int = int(self.b * 255)
        return red + green + blue

    def rgb_vector3(self) -> Vector3:
        """Returns a Vector3 representing a color with its components.

        Returns:
        -------
            A new Vector3 instance.
        """
        return Vector3(self.r, self.g, self.b)

    def bgr_vector3(self) -> Vector3:
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
    def __init__(
        self,
        iterable: Iterable[T] | None = None,
    ):
        super().__init__()
        if iterable is not None:
            for item in iterable:
                self.add(item)

    def _normalize_key(self, item: T) -> str | object:
        return item.casefold() if isinstance(item, str) else item

    def add(
        self,
        item: T,
    ):
        """Add an element to a set.

        This has no effect if the element is already present.
        """
        key: str | object = self._normalize_key(item)
        if key in self:
            return
        super().add(item)

    def remove(
        self,
        item: T,
    ):
        """Remove an element from a set; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        super().remove(self._normalize_key(item))

    def discard(
        self,
        item: T,
    ):
        """Remove an element from a set if it is a member.

        Unlike set.remove(), the discard() method does not raise an exception when an element is missing from the set.
        """
        super().discard(self._normalize_key(item))

    def update(
        self,
        *others,
    ):
        """Update a set with the union of itself and others."""
        for other in others:
            for item in other:
                self.add(item)

    def __contains__(
        self,
        item,
    ):
        return super().__contains__(self._normalize_key(item))

    def __eq__(
        self,
        other,
    ):
        if self is other:
            return True
        return super().__eq__({self._normalize_key(item) for item in other})

    def __hash__(self) -> int:  # type: ignore[override]
        # Use a normalized, immutable representation for the hash
        def _sort_key(x: Any) -> str:
            return x if isinstance(x, str) else str(x)

        normalized_items = tuple(
            sorted(
                (
                    self._normalize_key(item)
                    for item in self
                ),
                key=_sort_key
            )
        )
        return hash(normalized_items)

    def __ne__(self, other):
        return super().__ne__({self._normalize_key(item) for item in other})
