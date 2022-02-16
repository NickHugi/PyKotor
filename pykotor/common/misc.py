"""
This module holds various unrelated classes.
"""
from __future__ import annotations
import os
from enum import IntEnum, Enum
from typing import Tuple

from pykotor.resource.type import ResourceType

from pykotor.common.geometry import Vector3


class ResRef:
    class InvalidEncodingError(ValueError):
        ...

    class ExceedsMaxLengthError(ValueError):
        ...

    """
    A string reference to a game resource. ResRefs can be a maximum of 16 characters in length.
    """

    def __init__(self, text: str):
        self._value = ""
        self.set(text)

    def __len__(self):
        return len(self._value)

    def __eq__(self, other):
        """
        A ResRef can be compared to another ResRef or a str.
        """
        if isinstance(other, ResRef):
            return other.get().lower() == self.get().lower()
        elif isinstance(other, str):
            return other.lower() == self.get().lower()
        else:
            return NotImplemented

    def __repr__(self):
        return "ResRef({})".format(self._value)

    def __str__(self):
        return self._value

    @classmethod
    def from_blank(cls) -> ResRef:
        """
        Returns a blank ResRef.

        Returns:
            A new ResRef instance.
        """
        return ResRef("")

    @classmethod
    def from_path(cls, path: str) -> ResRef:
        """
        Returns a ResRef from the filename in the specified path.

        Args:
            path: The filepath.

        Returns:
            A new ResRef instance.
        """
        return ResRef(os.path.splitext(path)[0].replace('\\', '/').split('/')[-1])

    def set(self, text: str) -> None:
        """
        Sets the ResRef.

        Args:
            text: The reference string.

        Raises:
            ValueError:
        """
        if len(text) > 16:
            raise ResRef.ExceedsMaxLengthError("ResRef cannot exceed 16 characters.")
        if len(text) != len(text.encode()):
            raise ResRef.InvalidEncodingError("ResRef must be in ASCII characters.")

        self._value = text

    def get(self) -> str:
        return self._value


class Game(IntEnum):
    """
    Represents which game.
    """
    K1 = 1
    K2 = 2


class Color:
    # Listed here for hinting purposes
    RED: Color
    GREEN: Color
    BLUE: Color
    BLACK: Color
    WHITE: Color

    def __init__(self, r: float, g: float, b: float, a: float = 1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __repr__(self):
        return "Color({}, {}, {}, {})".format(self.r, self.g, self.b, self.g)

    def __str__(self):
        """
        Returns a string of each color component separated by whitespace.
        """
        return "{} {} {} {}".format(self.r, self.g, self.b, self.a)

    def __eq__(self, other):
        """
        Two Color instances are equal if their color components are equal.
        """
        if not isinstance(other, Color):
            return NotImplemented

        return other.r == self.r and other.g == self.g and other.b == self.b and other.a == self.a

    @classmethod
    def from_rgb_integer(cls, integer: int) -> Color:
        """
        Returns a Color by decoding the specified integer.

        Args:
            integer: RGB integer.

        Returns:
            A new Color instance.
        """
        red = ((0x000000FF & integer) >> 16) / 255
        green = ((0x0000FF00 & integer) >> 8) / 255
        blue = (0x00FF0000 & integer) / 255
        return Color(red, green, blue)

    @classmethod
    def from_bgr_integer(cls, integer: int) -> Color:
        """
        Returns a Color by decoding the specified integer.

        Args:
            integer: BGR integer.

        Returns:
            A new Color instance.
        """
        red = ((0x00FF0000 & integer) >> 16) / 255
        green = ((0x0000FF00 & integer) >> 8) / 255
        blue = (0x000000FF & integer) / 255
        return Color(red, green, blue)

    @classmethod
    def from_rgb_vector3(cls, vector3: Vector3) -> Color:
        """
        Returns a Color from the specified vector components.

        Args:
            vector3: A Vector3 instance.

        Returns:
            A new Color instance.
        """
        red = vector3.x
        green = vector3.y
        blue = vector3.z
        return Color(red, green, blue)

    @classmethod
    def from_bgr_vector3(cls, vector3: Vector3) -> Color:
        """
        Returns a Color from the specified vector components.

        Args:
            vector3: A Vector3 instance.

        Returns:
            A new Color instance.
        """
        red = vector3.z
        green = vector3.y
        blue = vector3.x
        return Color(red, green, blue)

    def rgb_integer(self) -> int:
        """
        Returns a RGB integer encoded from the color components.

        Returns:
            A integer representing a color.
        """
        red = int(self.r * 255) >> 0
        green = int(self.g * 255) >> 8
        blue = int(self.b * 255) >> 16
        return red + green + blue

    def bgr_integer(self) -> int:
        """
        Returns a BGR integer encoded from the color components.

        Returns:
            A integer representing a color.
        """
        red = int(self.r * 255) << 16
        green = int(self.g * 255) << 8
        blue = int(self.b * 255)
        return red + green + blue

    def rgb_vector3(self) -> Vector3:
        """
        Returns a Vector3 representing a color with its components.

        Returns:
            A new Vector3 instance.
        """
        return Vector3(self.r, self.g, self.b)

    def bgr_vector3(self) -> Vector3:
        """
        Returns a Vector3 representing a color with its components.

        Returns:
            A new Vector3 instance.
        """
        return Vector3(self.b, self.g, self.r)


Color.RED = Color(1.0, 0.0, 0.0)
Color.GREEN = Color(0.0, 1.0, 0.0)
Color.BLUE = Color(0.0, 0.0, 1.0)
Color.BLACK = Color(0.0, 0.0, 0.0)
Color.WHITE = Color(1.0, 1.0, 1.0)


class WrappedInt:
    def __init__(self, value: int = 0):
        self._value: int = value

    def __add__(self, other):
        if isinstance(other, WrappedInt):
            self._value += other.get()
        elif isinstance(other, int):
            self._value += other
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, WrappedInt):
            return self.get() == other.get()
        elif isinstance(other, int):
            return self.get() == other
        else:
            return NotImplemented

    def set(self, value: int) -> None:
        self._value = value

    def get(self) -> int:
        return self._value


class InventoryItem:
    def __init__(self, resref: ResRef, droppable: bool = False, infinite: bool = False):
        self.resref: ResRef = resref
        self.droppable: bool = droppable
        self.infinite: bool = infinite

    def __str__(self):
        return self.resref.get()

    def __eq__(self, other: InventoryItem):
        return self.resref == other.resref and self.droppable == other.droppable


class EquipmentSlot(Enum):
    HEAD        = 1
    ARMOR       = 2
    GAUNTLET    = 8
    RIGHT_HAND  = 16
    LEFT_HAND   = 32
    RIGHT_ARM   = 128
    LEFT_ARM    = 256
    IMPLANT     = 512
    BELT        = 1024
    CLAW1       = 16384
    CLAW2       = 32768
    CLAW3       = 65536
    HIDE        = 131072
