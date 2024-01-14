from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.tlk.io_tlk import TLKBinaryReader
from pykotor.resource.formats.tlk.tlk_auto import bytes_tlk
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from pykotor.common.misc import Game, ResRef
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsTLK(PatcherModifications):
    DEFAULT_DESTINATION = "."
    DEFAULT_SOURCEFILE  = "append.tlk"
    DEFAULT_SOURCEFILE_F = "appendf.tlk"
    DEFAULT_SAVEAS_FILE = "dialog.tlk"
    def __init__(self, filename=DEFAULT_SOURCEFILE, replace=None, modifiers=None) -> None:
        super().__init__(filename)
        self.destination = self.DEFAULT_DESTINATION
        self.modifiers: list[ModifyTLK] = modifiers if modifiers is not None else []
        self.sourcefile_f: str = self.DEFAULT_SOURCEFILE_F  # Polish version of k1

    def apply(
        self,
        dialog: TLK,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> None:
        for modifier in self.modifiers:
            if modifier.is_replacement:
                modifier.replace(dialog, memory)
            else:
                modifier.insert(dialog, memory)
            logger.complete_patch()

    def patch_resource(
        self,
        source_tlk: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
        dialog: TLK | SOURCE_TYPES = source_tlk
        if not isinstance(source_tlk, TLK):
            dialog = TLKBinaryReader(source_tlk).load()
        assert isinstance(dialog, TLK)
        self.apply(dialog, memory, logger, game)
        return bytes_tlk(dialog)

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=DEFAULT_DESTINATION):
        if "!ReplaceFile" in file_section_dict:
            msg = "!ReplaceFile is not supported in [TLKList]"
            raise ValueError(msg)
        if "!OverrideType" in file_section_dict:
            msg = "!OverrideType is not supported in [TLKList]"
            raise ValueError(msg)

        self.sourcefile_f = file_section_dict.pop("!SourceFileF", self.DEFAULT_SOURCEFILE_F)  # Polish only?
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        self.saveas = self.saveas if self.saveas != self.sourcefile else self.DEFAULT_SAVEAS_FILE


class ModifyTLK:
    def __init__(
        self,
        token_id: int,
        text: str,
        sound: ResRef,
        is_replacement: bool = False,
    ):
        self.token_id: int = token_id
        self.text: str = text
        self.sound: ResRef = sound
        self.is_replacement: bool = is_replacement

    def insert(self, dialog: TLK, memory: PatcherMemory) -> None:
        dialog.add(self.text, self.sound.get())
        memory.memory_str[self.token_id] = len(dialog.entries) - 1

    def replace(self, dialog: TLK, memory: PatcherMemory) -> None:
        dialog.replace(self.token_id, self.text, self.sound.get())
        memory.memory_str[self.token_id] = self.token_id
