from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.tlk.io_tlk import TLKBinaryReader
from pykotor.resource.formats.tlk.tlk_auto import bytes_tlk
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory
    from utility.path import Path


class ModificationsTLK(PatcherModifications):
    DEFAULT_DESTINATION = "."
    DEFAULT_SOURCEFILE  = "append.tlk"
    DEFAULT_SAVEAS_FILE = "dialog.tlk"
    def __init__(self, filename=DEFAULT_SOURCEFILE, replace=None, modifiers=None) -> None:
        super().__init__(filename)
        self.destination = self.DEFAULT_DESTINATION
        self.modifiers: list[ModifyTLK] = modifiers if modifiers is not None else []

    def apply(
        self,
        dialog,
        memory: PatcherMemory,
        log: PatchLogger | None = None,
        game: Game | None = None,
    ) -> None:
        for modifier in self.modifiers:
            modifier.apply(dialog, memory)
            if log:
                log.complete_patch()

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        log: PatchLogger | None = None,
        game: Game | None = None,
    ) -> bytes:
        dialog: TLK = TLKBinaryReader(source).load()
        self.apply(dialog, memory, log, game)
        return bytes_tlk(dialog)

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=DEFAULT_DESTINATION):
        if "!ReplaceFile" in file_section_dict:
            msg = "!ReplaceFile is not supported in [TLKList]"
            raise ValueError(msg)
        if "!OverrideType" in file_section_dict:
            msg = "!OverrideType is not supported in [TLKList]"
            raise ValueError(msg)

        self.sourcefile_f = file_section_dict.pop("!SourceFileF", "appendf.tlk")  # Polish only?
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        self.saveas = self.saveas if self.saveas != self.sourcefile else self.DEFAULT_SAVEAS_FILE


class ModifyTLK:
    def __init__(
        self,
        token_id: int,
        is_replacement: bool = False,
    ):
        self.tlk_filepath: Path | None = None
        self.text: str = ""
        self.sound: ResRef = ResRef.from_blank()

        self.mod_index: int = token_id
        self.token_id: int = token_id
        self.is_replacement: bool = is_replacement

    def apply(self, dialog: TLK, memory: PatcherMemory) -> None:
        self.load()
        if self.is_replacement:
            memory.memory_str[self.token_id] = dialog.add(self.text, self.sound.get())
        else:
            dialog.replace(self.token_id, self.text, self.sound.get())
            memory.memory_str[self.token_id] = self.token_id

    def load(self):
        if self.tlk_filepath is not None:
            lookup_tlk = TalkTable(self.tlk_filepath)
            self.text = self.text or lookup_tlk.string(self.mod_index)
            self.sound = self.sound or lookup_tlk.sound(self.mod_index)
