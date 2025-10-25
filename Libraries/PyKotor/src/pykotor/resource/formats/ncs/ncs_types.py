"""Enhanced type system for NCS format based on DeNCS implementation.

This module provides a comprehensive type system for NCS bytecode operations,
including basic types, compound types, and struct types with proper size calculations.
"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


class NCSTypeCode(IntEnum):
    """Type codes used in NCS bytecode operations."""

    # Basic types
    NONE = 0x00
    STACK = 0x01
    INTEGER = 0x03
    FLOAT = 0x04
    STRING = 0x05
    OBJECT = 0x06

    # Engine types
    EFFECT = 0x10
    EVENT = 0x11
    LOCATION = 0x12
    TALENT = 0x13

    # Compound types
    INTINT = 0x20
    FLOATFLOAT = 0x21
    OBJECTOBJECT = 0x22
    STRINGSTRING = 0x23
    STRUCTSTRUCT = 0x24
    INTFLOAT = 0x25
    FLOATINT = 0x26

    # Compound engine types
    EFFECTEFFECT = 0x30
    EVENTEVENT = 0x31
    LOCLOC = 0x32
    TALTAL = 0x33

    # Vector types
    VECTORVECTOR = 0x3A
    VECTORFLOAT = 0x3B
    FLOATVECTOR = 0x3C

    # Special types
    VECTOR = 0xF0  # -16 in signed byte
    STRUCT = 0xF1  # -15 in signed byte
    INVALID = 0xFF  # -1 in signed byte


class NCSType:
    """Represents a type in the NCS type system.

    Provides type information, size calculations, and type conversion utilities.
    Based on DeNCS Type.java implementation.
    """

    __slots__ = ("_size", "_type_code")

    def __init__(self, type_code: int | NCSTypeCode | str):
        """Initialize an NCS type.

        Args:
        ----
            type_code: Type code as integer, NCSTypeCode enum, or string name
        """
        if isinstance(type_code, str):
            self._type_code = self._decode_string(type_code)
        elif isinstance(type_code, NCSTypeCode):
            self._type_code = type_code
        else:
            self._type_code = NCSTypeCode(type_code)

        self._size = self._calculate_size()

    @staticmethod
    def _decode_string(type_str: str) -> NCSTypeCode:
        """Decode a type string to a type code.

        Args:
        ----
            type_str: String representation of type (e.g., "int", "float")

        Returns:
        -------
            NCSTypeCode: Corresponding type code

        Raises:
        ------
            ValueError: If type string is unknown
        """
        type_map = {
            "void": NCSTypeCode.NONE,
            "int": NCSTypeCode.INTEGER,
            "float": NCSTypeCode.FLOAT,
            "string": NCSTypeCode.STRING,
            "object": NCSTypeCode.OBJECT,
            "effect": NCSTypeCode.EFFECT,
            "event": NCSTypeCode.EVENT,
            "location": NCSTypeCode.LOCATION,
            "talent": NCSTypeCode.TALENT,
            "vector": NCSTypeCode.VECTOR,
            "action": NCSTypeCode.NONE,  # Actions have void type
            "struct": NCSTypeCode.STRUCT,
            "stack": NCSTypeCode.STACK,
            # Aliases
            "INT": NCSTypeCode.INTEGER,
            "OBJECT_ID": NCSTypeCode.OBJECT,
        }

        if type_str not in type_map:
            msg = f"Unknown type string: {type_str}"
            raise ValueError(msg)

        return type_map[type_str]

    def _calculate_size(self) -> int:
        """Calculate the size of this type in 4-byte words.

        Returns:
        -------
            int: Size in 4-byte words

        Raises:
        ------
            ValueError: If type size cannot be determined
        """
        size_map = {
            NCSTypeCode.NONE: 0,
            NCSTypeCode.STACK: 1,
            NCSTypeCode.INTEGER: 1,
            NCSTypeCode.FLOAT: 1,
            NCSTypeCode.STRING: 1,
            NCSTypeCode.OBJECT: 1,
            NCSTypeCode.EFFECT: 1,
            NCSTypeCode.EVENT: 1,
            NCSTypeCode.LOCATION: 1,
            NCSTypeCode.TALENT: 1,
            NCSTypeCode.VECTOR: 3,  # 12 bytes = 3 words
        }

        if self._type_code in size_map:
            return size_map[self._type_code]

        # Struct size must be determined externally
        if self._type_code == NCSTypeCode.STRUCT:
            msg = "Struct size must be determined by context"
            raise ValueError(msg)

        # Unknown type
        msg = f"Cannot determine size of type code: {self._type_code}"
        raise ValueError(msg)

    @property
    def type_code(self) -> NCSTypeCode:
        """Get the type code."""
        return self._type_code

    @property
    def size(self) -> int:
        """Get the size in 4-byte words."""
        return self._size

    @property
    def byte_size(self) -> int:
        """Get the size in bytes."""
        return self._size * 4

    def is_typed(self) -> bool:
        """Check if this is a valid typed value (not invalid/stack)."""
        return self._type_code not in {NCSTypeCode.INVALID, NCSTypeCode.STACK}

    def is_numeric(self) -> bool:
        """Check if this is a numeric type (int or float)."""
        return self._type_code in {NCSTypeCode.INTEGER, NCSTypeCode.FLOAT}

    def is_engine_type(self) -> bool:
        """Check if this is an engine-specific type."""
        return self._type_code in {
            NCSTypeCode.EFFECT,
            NCSTypeCode.EVENT,
            NCSTypeCode.LOCATION,
            NCSTypeCode.TALENT,
        }

    def to_string(self) -> str:
        """Convert type to its string representation.

        Returns:
        -------
            str: String representation (e.g., "int", "float")
        """
        type_names = {
            NCSTypeCode.NONE: "void",
            NCSTypeCode.STACK: "stack",
            NCSTypeCode.INTEGER: "int",
            NCSTypeCode.FLOAT: "float",
            NCSTypeCode.STRING: "string",
            NCSTypeCode.OBJECT: "object",
            NCSTypeCode.EFFECT: "effect",
            NCSTypeCode.EVENT: "event",
            NCSTypeCode.LOCATION: "location",
            NCSTypeCode.TALENT: "talent",
            NCSTypeCode.VECTOR: "vector",
            NCSTypeCode.STRUCT: "struct",
            NCSTypeCode.INVALID: "invalid",
            # Compound types
            NCSTypeCode.INTINT: "intint",
            NCSTypeCode.FLOATFLOAT: "floatfloat",
            NCSTypeCode.OBJECTOBJECT: "objectobject",
            NCSTypeCode.STRINGSTRING: "stringstring",
            NCSTypeCode.STRUCTSTRUCT: "structstruct",
            NCSTypeCode.INTFLOAT: "intfloat",
            NCSTypeCode.FLOATINT: "floatint",
            NCSTypeCode.EFFECTEFFECT: "effecteffect",
            NCSTypeCode.EVENTEVENT: "eventevent",
            NCSTypeCode.LOCLOC: "locloc",
            NCSTypeCode.TALTAL: "taltal",
            NCSTypeCode.VECTORVECTOR: "vectorvector",
            NCSTypeCode.VECTORFLOAT: "vectorfloat",
            NCSTypeCode.FLOATVECTOR: "floatvector",
        }

        return type_names.get(self._type_code, "unknown")

    def get_element(self, position: int) -> Self:
        """Get element at position (for struct/vector support).

        Args:
        ----
            position: Position index (1-based)

        Returns:
        -------
            NCSType: Type at position

        Raises:
        ------
            ValueError: If position is invalid for this type
        """
        if position != 1:
            msg = f"Position {position} > 1 for non-struct type"
            raise ValueError(msg)
        return self

    def __str__(self) -> str:
        """String representation of the type."""
        return self.to_string()

    def __repr__(self) -> str:
        """Developer representation of the type."""
        return f"NCSType({self._type_code.name})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another type."""
        if isinstance(other, NCSType):
            return self._type_code == other._type_code
        if isinstance(other, (int, NCSTypeCode)):
            return self._type_code == other
        return NotImplemented

    def __hash__(self) -> int:
        """Hash for use in dictionaries/sets."""
        return hash(self._type_code)


def create_type(type_input: int | NCSTypeCode | str | NCSType) -> NCSType:
    """Create an NCSType from various input types.

    Args:
    ----
        type_input: Type specification

    Returns:
    -------
        NCSType: Created type object
    """
    if isinstance(type_input, NCSType):
        return type_input
    return NCSType(type_input)
