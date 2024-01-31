from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.system.path import PureWindowsPath

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory
    from typing_extensions import Literal


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
    ) -> bytes | Literal[True]:
        with BinaryReader.from_auto(ncs_source) as reader:
            ncs_bytearray: bytearray = bytearray(reader.read_all())
        self.apply(ncs_bytearray, memory, logger, game)
        return bytes(ncs_bytearray)

    def apply(
        self,
        ncs_bytearray: bytearray,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        with BinaryWriter.to_bytearray(ncs_bytearray) as writer:
            for patch in self.hackdata:
                token_type, offset, token_id_or_value = patch
                logger.add_verbose(f"HACKList {self.sourcefile}: seeking to offset {offset:#X}")
                writer.seek(offset)
                value: int
                if token_type.lower() == "strref":
                    memory_strval: int | None = memory.memory_str.get(token_id_or_value, None)
                    if memory_strval is None:
                        msg = f"StrRef{token_id_or_value} was not defined before use"
                        raise KeyError(msg)
                    value = memory.memory_str[token_id_or_value]
                elif token_type.lower() == "2damemory":
                    memory_val: str | PureWindowsPath | None = memory.memory_2da.get(token_id_or_value, None)
                    if memory_val is None:
                        msg = f"2DAMEMORY{token_id_or_value} was not defined before use"
                        raise KeyError(msg)
                    if isinstance(memory_val, PureWindowsPath):
                        msg = f"Memory value cannot be !FieldPath in [HACKList] patches, got '{memory_val!r}'"
                        raise ValueError(msg)
                    value = int(memory_val)
                else:
                    value = token_id_or_value
                logger.add_verbose(f"HACKList {self.sourcefile}: writing unsigned WORD {value} at offset {offset:#X}")
                writer.write_uint16(value, big=True)

    def pop_tslpatcher_vars(
        self,
        file_section_dict,
        default_destination=PatcherModifications.DEFAULT_DESTINATION,
        default_sourcefolder=".",
    ):
        super().pop_tslpatcher_vars(file_section_dict, default_destination, default_sourcefolder)
        replace_file: bool | str = file_section_dict.pop("ReplaceFile", self.replace_file)
        self.replace_file = bool(int(replace_file))  # NOTE: tslpatcher's hacklist does NOT prefix with an exclamation point.
