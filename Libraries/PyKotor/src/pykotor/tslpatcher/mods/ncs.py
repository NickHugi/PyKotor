from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryWriter, BinaryWriterBytearray
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.path import PureWindowsPath

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory

class MutableString:
    def __init__(self, value: str):
        self.value: str = value
    def __str__(self):
        return self.value


class ModificationsNCS(PatcherModifications):
    def __init__(self, filename, replace=None, modifiers=None):
        super().__init__(filename, replace, modifiers)
        self.action: str = "Hack "
        self.hackdata: list[tuple[str, int, int]] = []

    def patch_resource(
        self,
        ncs_source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
        ncs_bytearray: bytearray
        if isinstance(ncs_source, bytes):
            ncs_bytearray = bytearray(ncs_source)
        elif isinstance(ncs_source, bytearray):
            ncs_bytearray = ncs_source
        else:
            msg = "ncs source must be bytes/bytearray due to a current bug with the read_ncs method."
            raise TypeError(msg)
        self.apply(ncs_bytearray, memory, logger, game)
        return ncs_bytearray

    def apply(
        self,
        ncs_bytes: bytearray,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        writer: BinaryWriterBytearray = BinaryWriter.to_bytearray(ncs_bytes)
        for patch in self.hackdata:
            token_type, offset, token_id_or_value = patch
            logger.add_verbose(f"HACKList {self.sourcefile}: seeking to offset {offset:#X}")
            writer.seek(offset)
            value: int = token_id_or_value
            if token_type.lower() == "strref":  # noqa: S105
                value = memory.memory_str[value]
            elif token_type.lower() == "2damemory":  # noqa: S105
                memory_val: str | PureWindowsPath = memory.memory_2da[value]
                if isinstance(memory_val, PureWindowsPath):
                    msg = f"Memory value cannot be !FieldPath, got '{memory_val!r}'"
                    raise ValueError(msg)
                value = int(memory_val)
            logger.add_verbose(f"HACKList {self.sourcefile}: writing WORD {value} at offset {offset:#X}")
            writer.write_int16(value)  # TODO: This might need to be uint16, needs testing.

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=PatcherModifications.DEFAULT_DESTINATION):
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        replace_file: bool | str = file_section_dict.pop("ReplaceFile", self.replace_file)
        self.replace_file = bool(int(replace_file))  # tslpatcher's hacklist doesn't prefix with an exclamation point.
