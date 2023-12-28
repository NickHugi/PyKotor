from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ssf import bytes_ssf
from pykotor.resource.formats.ssf.io_ssf import SSFBinaryReader
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.formats.ssf import SSF, SSFSound
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory, TokenUsage


class ModifySSF:
    def __init__(self, sound: SSFSound, stringref: TokenUsage):
        self.sound: SSFSound = sound
        self.stringref: TokenUsage = stringref

    def apply(self, ssf: SSF, memory: PatcherMemory) -> None:
        ssf.set_data(self.sound, int(self.stringref.value(memory)))


class ModificationsSSF(PatcherModifications):
    def __init__(
        self,
        filename: str,
        replace_file: bool,
        modifiers: list[ModifySSF] | None = None,
    ):
        super().__init__(filename)
        self.replace_file: bool = replace_file
        self.no_replacefile_check = True
        self.modifiers: list[ModifySSF] = modifiers if modifiers is not None else []

    def patch_resource(
        self,
        source_ssf: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
        ssf: SSF = SSFBinaryReader(source_ssf).load()
        self.apply(ssf, memory, logger, game)
        return bytes_ssf(ssf)

    def apply(
        self,
        ssf: SSF,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> None:
        for modifier in self.modifiers:
            modifier.apply(ssf, memory)
