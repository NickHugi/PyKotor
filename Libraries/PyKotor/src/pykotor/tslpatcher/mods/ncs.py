"""NCS modification algorithms for TSLPatcher/HoloPatcher.

This module implements NCS bytecode modification logic for applying patches from changes.ini files.
Handles byte-level modifications for memory tokens (StrRef, 2DAMemory) in compiled scripts.

References:
----------
    vendor/TSLPatcher/TSLPatcher.pl - Original Perl NCS modification logic (HACKList)
    vendor/HoloPatcher.NET/src/TSLPatcher.Core/Mods/NCS/ - C# NCS modification implementation
    vendor/Kotor.NET/Kotor.NET.Patcher/ - Incomplete C# patcher
"""

from __future__ import annotations

from enum import Enum
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory
    from utility.common.more_collections import CaseInsensitiveDict


class NCSTokenType(Enum):
    """Token types for NCS bytecode modifications."""

    STRREF = "strref"  # 16-bit unsigned TLK string reference
    STRREF32 = "strref32"  # 32-bit signed TLK string reference (CONSTI instruction)
    MEMORY_2DA = "2damemory"  # 16-bit unsigned 2DA memory reference
    MEMORY_2DA32 = "2damemory32"  # 32-bit signed 2DA memory reference (CONSTI instruction)
    UINT32 = "uint32"  # 32-bit unsigned integer literal
    UINT16 = "uint16"  # 16-bit unsigned integer literal
    UINT8 = "uint8"  # 8-bit unsigned integer literal

    @classmethod
    def from_string(cls, value: str) -> NCSTokenType:
        """Convert a string to an NCSTokenType.

        Args:
        ----
            value: String representation of the token type

        Returns:
        -------
            NCSTokenType: The corresponding enum value

        Raises:
        ------
            ValueError: If the string doesn't match any token type
        """
        value_lower = value.lower()
        for token_type in cls:
            if token_type.value == value_lower:
                return token_type
        msg = f"Unknown token type '{value}' in HACKList patch"
        raise ValueError(msg)


class ModifyNCS:
    """Represents a single NCS bytecode modification operation."""

    def __init__(
        self,
        token_type: NCSTokenType,
        offset: int,
        token_id_or_value: int,
    ):
        """Initialize an NCS modification.

        Args:
        ----
            token_type: Type of modification (NCSTokenType enum)
            offset: Byte offset in the NCS file to write to
            token_id_or_value: Token ID for memory lookup or direct value to write
        """
        self.token_type: NCSTokenType = token_type
        self.offset: int = offset
        self.token_id_or_value: int = token_id_or_value

    def apply(
        self,
        writer: BinaryWriter,
        memory: PatcherMemory,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Apply the NCS modification to the bytecode.

        Args:
        ----
            writer: BinaryWriter positioned in the NCS bytearray
            memory: PatcherMemory object for token lookups
            logger: PatchLogger for logging operations
            sourcefile: Name of the source file being modified (for logging)
        """
        logger.add_verbose(f"HACKList {sourcefile}: seeking to offset {self.offset:#X}")
        writer.seek(self.offset)

        if self.token_type is NCSTokenType.STRREF:
            self._write_strref(writer, memory, logger, sourcefile)
        elif self.token_type is NCSTokenType.STRREF32:
            self._write_strref32(writer, memory, logger, sourcefile)
        elif self.token_type is NCSTokenType.MEMORY_2DA:
            self._write_2damemory(writer, memory, logger, sourcefile)
        elif self.token_type is NCSTokenType.MEMORY_2DA32:
            self._write_2damemory32(writer, memory, logger, sourcefile)
        elif self.token_type is NCSTokenType.UINT32:
            self._write_uint32(writer, logger, sourcefile)
        elif self.token_type is NCSTokenType.UINT16:
            self._write_uint16(writer, logger, sourcefile)
        elif self.token_type is NCSTokenType.UINT8:
            self._write_uint8(writer, logger, sourcefile)
        else:
            msg = f"Unknown token type '{self.token_type}' in HACKList patch"
            raise ValueError(msg)

    def _write_strref(
        self,
        writer: BinaryWriter,
        memory: PatcherMemory,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Write a 16-bit unsigned TLK string reference."""
        memory_strval: int | None = memory.memory_str.get(self.token_id_or_value, None)
        if memory_strval is None:
            msg = f"StrRef{self.token_id_or_value} was not defined before use"
            raise KeyError(msg)
        value = memory.memory_str[self.token_id_or_value]
        logger.add_verbose(f"HACKList {sourcefile}: writing unsigned WORD (16-bit) {value} at offset {self.offset:#X}")
        writer.write_uint16(value, big=True)

    def _write_strref32(
        self,
        writer: BinaryWriter,
        memory: PatcherMemory,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Write a 32-bit signed TLK string reference (CONSTI instruction)."""
        memory_strval: int | None = memory.memory_str.get(self.token_id_or_value, None)
        if memory_strval is None:
            msg = f"StrRef{self.token_id_or_value} was not defined before use"
            raise KeyError(msg)
        value = memory.memory_str[self.token_id_or_value]
        logger.add_verbose(f"HACKList {sourcefile}: writing signed DWORD (32-bit) {value} at offset {self.offset:#X}")
        writer.write_int32(value, big=True)

    def _write_2damemory(
        self,
        writer: BinaryWriter,
        memory: PatcherMemory,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Write a 16-bit unsigned 2DA memory reference."""
        memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id_or_value, None)
        if memory_val is None:
            msg = f"2DAMEMORY{self.token_id_or_value} was not defined before use"
            raise KeyError(msg)
        if isinstance(memory_val, PureWindowsPath):
            msg = f"Memory value cannot be !FieldPath in [HACKList] patches, got '{memory_val!r}'"
            raise TypeError(msg)
        value = int(memory_val)
        logger.add_verbose(f"HACKList {sourcefile}: writing unsigned WORD (16-bit) {value} at offset {self.offset:#X}")
        writer.write_uint16(value, big=True)

    def _write_2damemory32(
        self,
        writer: BinaryWriter,
        memory: PatcherMemory,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Write a 32-bit signed 2DA memory reference (CONSTI instruction)."""
        memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id_or_value, None)
        if memory_val is None:
            msg = f"2DAMEMORY{self.token_id_or_value} was not defined before use"
            raise KeyError(msg)
        if isinstance(memory_val, PureWindowsPath):
            msg = f"Memory value cannot be !FieldPath in [HACKList] patches, got '{memory_val!r}'"
            raise TypeError(msg)
        value = int(memory_val)
        logger.add_verbose(f"HACKList {sourcefile}: writing signed DWORD (32-bit) {value} at offset {self.offset:#X}")
        writer.write_int32(value, big=True)

    def _write_uint32(
        self,
        writer: BinaryWriter,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Write a 32-bit unsigned integer literal."""
        value = self.token_id_or_value
        logger.add_verbose(f"HACKList {sourcefile}: writing unsigned DWORD (32-bit) {value} at offset {self.offset:#X}")
        writer.write_uint32(value, big=True)

    def _write_uint16(
        self,
        writer: BinaryWriter,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Write a 16-bit unsigned integer literal."""
        value = self.token_id_or_value
        logger.add_verbose(f"HACKList {sourcefile}: writing unsigned WORD (16-bit) {value} at offset {self.offset:#X}")
        writer.write_uint16(value, big=True)

    def _write_uint8(
        self,
        writer: BinaryWriter,
        logger: PatchLogger,
        sourcefile: str,
    ):
        """Write an 8-bit unsigned integer literal."""
        value = self.token_id_or_value
        logger.add_verbose(f"HACKList {sourcefile}: writing unsigned BYTE (8-bit) {value} at offset {self.offset:#X}")
        writer.write_uint8(value)


class ModificationsNCS(PatcherModifications):
    def __init__(
        self,
        filename: str,
        replace: bool | None = None,  # noqa: FBT001
        modifiers: list[ModifyNCS] | None = None,
    ):
        super().__init__(filename, replace, modifiers)
        self.action: str = "Hack "
        self.modifiers: list[ModifyNCS] = [] if modifiers is None else modifiers

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        with BinaryReader.from_auto(source) as reader:
            ncs_bytearray: bytearray = bytearray(reader.read_all())
        self.apply(ncs_bytearray, memory, logger, game)
        return bytes(ncs_bytearray)

    def apply(
        self,
        mutable_data: bytearray,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        """Apply all NCS modifications to the bytecode.

        Args:
        ----
            mutable_data: bytearray - The NCS bytecode to modify in-place
            memory: PatcherMemory - Memory context for token lookups
            logger: PatchLogger - Logger for recording operations
            game: Game - The game being patched (unused but required by interface)
        """
        with BinaryWriter.to_bytearray(mutable_data) as writer:
            for modifier in self.modifiers:
                modifier.apply(writer, memory, logger, self.sourcefile)

    def pop_tslpatcher_vars(
        self,
        file_section_dict: CaseInsensitiveDict[str],
        default_destination: str | None = PatcherModifications.DEFAULT_DESTINATION,
        default_sourcefolder: str = ".",
    ):
        super().pop_tslpatcher_vars(file_section_dict, default_destination, default_sourcefolder)
        replace_file: bool | str = file_section_dict.pop("ReplaceFile", self.replace_file)
        self.replace_file = bool(int(replace_file))  # NOTE: tslpatcher's hacklist does NOT prefix with an exclamation point.
