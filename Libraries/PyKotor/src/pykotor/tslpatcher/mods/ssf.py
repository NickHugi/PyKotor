"""SSF modification algorithms for TSLPatcher/HoloPatcher.

This module implements SSF modification logic for applying patches from changes.ini files.
Handles sound set entry modifications and memory token resolution.

References:
----------
    vendor/TSLPatcher/TSLPatcher.pl - Original Perl SSF modification logic
    vendor/HoloPatcher.NET/src/TSLPatcher.Core/Mods/SSF/ - C# SSF modification implementation
    vendor/Kotor.NET/Kotor.NET.Patcher/ - Incomplete C# patcher
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ssf import bytes_ssf
from pykotor.resource.formats.ssf.io_ssf import SSFBinaryReader
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.resource.formats.ssf import SSF, SSFSound
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory, TokenUsage


class ModifySSF:
    def __init__(self, sound: SSFSound, stringref: TokenUsage):
        self.sound: SSFSound = sound
        self.stringref: TokenUsage = stringref

    def apply(self, ssf: SSF, memory: PatcherMemory):
        ssf.set_data(self.sound, int(self.stringref.value(memory)))


class ModificationsSSF(PatcherModifications):
    def __init__(
        self,
        filename: str,
        replace: bool,  # noqa: FBT001
        modifiers: list[ModifySSF] | None = None,
    ):
        super().__init__(filename)
        self.replace_file: bool = replace
        self.no_replacefile_check = True
        self.modifiers: list[ModifySSF] = [] if modifiers is None else modifiers

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
        ssf: SSF = SSFBinaryReader(source).load()
        self.apply(ssf, memory, logger, game)
        return bytes_ssf(ssf)

    def apply(
        self,
        mutable_data: SSF,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        for modifier in self.modifiers:
            modifier.apply(mutable_data, memory)
