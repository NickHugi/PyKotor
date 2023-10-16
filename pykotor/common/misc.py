"""This module holds various unrelated classes and methods."""


from __future__ import annotations

import contextlib
import subprocess
import time
from datetime import datetime, timedelta, timezone
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Generic, TypeVar

from pykotor.common.geometry import Vector3
from pykotor.tools.path import CaseAwarePath

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
        other: ResRef | str | object,
    ):
        """A ResRef can be compared to another ResRef or a str."""
        other_value = other.get().lower() if isinstance(other, ResRef) else other.lower() if isinstance(other, str) else None
        return other_value == self._value.lower() if other_value is not None else NotImplemented

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
        return cls(CaseAwarePath(file_path).name)

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
        if len(text) != len(text.encode()):
            msg = "ResRef must be in ASCII characters."  # sourcery skip: inline-variable
            raise ResRef.InvalidEncodingError(msg)

        self._value = text.lower()

    def get(
        self,
    ) -> str:
        return self._value


def get_local_timezone():
    # 1. Try using Python 3.9+'s zoneinfo
    with contextlib.suppress(ImportError):
        from zoneinfo import ZoneInfo

        return ZoneInfo("local")
    # 2. Try using dateutil
    with contextlib.suppress(ImportError):
        import dateutil.tz  # type: ignore[missing import]

        return dateutil.tz.tzlocal()
    # 3. Try using pytz
    with contextlib.suppress(ImportError):
        import pytz  # type: ignore[missing import]

        local_datetime = datetime.now(pytz.utc).astimezone()
        return local_datetime.tzinfo
    # 4. Fallback to OS-specific methods

    # For UNIX-like systems (using date command)
    with contextlib.suppress(Exception):
        result = subprocess.run(["date", "+%z"], stdout=subprocess.PIPE).stdout.decode().strip()
        offset_minutes = int(result[:-2]) * 60 + int(result[-2:])
        hours, remainder = divmod(abs(offset_minutes), 60)
        sign = "-" if offset_minutes < 0 else "+"
        tzname = f"{sign}{hours:02}:{remainder:02}"
        return timezone(timedelta(minutes=offset_minutes), tzname)
    # For Windows
    with contextlib.suppress(Exception):
        result = subprocess.run("tzutil /g", shell=True, stdout=subprocess.PIPE).stdout.decode().strip()
        offset_minutes = -(time.timezone / 60) if time.localtime().tm_isdst == 0 else -(time.altzone / 60)
        hours, remainder = divmod(abs(offset_minutes), 60)
        sign = "-" if offset_minutes < 0 else "+"
        tzname = f"{sign}{hours:02}:{remainder:02}"
        return timezone(timedelta(minutes=offset_minutes), tzname)
    # Ultimate fallback: Return UTC if unable to determine local timezone
    return timezone.utc


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
        other: InventoryItem,
    ):
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


class CaseInsensitiveDict(Generic[T]):
    def __init__(
        self,
        initial: dict[str, T] | None = None,
    ):
        self._dictionary: dict[str, T] = {}
        self._case_map: dict[str, str] = {}
        if initial:
            for key, value in initial.items():
                self[key] = value  # Utilize the __setitem__ method for setting items

    def __getitem__(self, key: str) -> T:
        return self._dictionary[self._case_map[key.lower()]]

    def __setitem__(self, key: str, value: T):
        lower_key = key.lower()
        self._case_map[lower_key] = key  # Store the original form
        self._dictionary[key] = value

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

    def pop(self, key: str) -> T:
        lower_key = key.lower()
        value = self._dictionary.pop(self._case_map[lower_key])
        self._case_map.pop(lower_key)
        return value

    def get(self, __key: str, __default: VT = None) -> VT | T:
        # sourcery skip: compare-via-equals
        key_lookup: str = self._case_map.get(__key.lower(), _unique_sentinel)  # type: ignore[ignore key_lookup]
        return __default if key_lookup is _unique_sentinel else self._dictionary.get(key_lookup, __default)

    def items(self):
        return self._dictionary.items()

    def values(self):
        return self._dictionary.values()

    def keys(self):
        return self._dictionary.keys()
