from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter, BinaryWriterBytearray
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
        elif isinstance(ncs_source, (os.PathLike, str)):
            ncs_bytearray = bytearray(BinaryReader.load_file(ncs_source))
        elif isinstance(ncs_source, BinaryReader):
            ncs_bytearray = bytearray(ncs_source.read_all())
        else:
            msg = f"Unexpected source type passed to ModificationsNCS.patch_resource, got source type of {type(ncs_source)}"
            raise TypeError(msg)

        self.apply(ncs_bytearray, memory, logger, game)
        return bytes(ncs_bytearray)

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
            value: int
            if token_type.lower() == "strref":
                value = memory.memory_str[token_id_or_value]
            elif token_type.lower() == "2damemory":
                memory_val: str | PureWindowsPath = memory.memory_2da[token_id_or_value]
                if isinstance(memory_val, PureWindowsPath):
                    msg = f"Memory value cannot be !FieldPath in [HACKList] patches, got '{memory_val!r}'"
                    raise ValueError(msg)
                value = int(memory_val)
            else:
                value = token_id_or_value
            logger.add_verbose(f"HACKList {self.sourcefile}: writing WORD {value} at offset {offset:#X}")
            writer.write_int16(value)  # TODO: This might need to be uint16, needs testing.

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=PatcherModifications.DEFAULT_DESTINATION):
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        replace_file: bool | str = file_section_dict.pop("ReplaceFile", self.replace_file)
        self.replace_file = bool(int(replace_file))  # NOTE: tslpatcher's hacklist does NOT prefix with an exclamation point.
