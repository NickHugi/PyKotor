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
    from typing_extensions import Literal
    from utility.system.path import Path


class ModificationsTLK(PatcherModifications):
    DEFAULT_DESTINATION   = "."
    DEFAULT_SOURCEFILE    = "append.tlk"
    DEFAULT_SOURCEFILE_F  = "appendf.tlk"
    DEFAULT_SAVEAS_FILE   = "dialog.tlk"
    DEFAULT_SAVEAS_FILE_F = "dialogf.tlk"
    def __init__(
        self,
        filename: str=DEFAULT_SOURCEFILE,
        replace: bool | None =None,
        modifiers=None,
    ):
        super().__init__(filename)
        self.destination = self.DEFAULT_DESTINATION
        self.modifiers: list[ModifyTLK] = modifiers if modifiers is not None else []
        self.sourcefile_f: str = self.DEFAULT_SOURCEFILE_F  # Polish version of k1
        self.saveas = self.DEFAULT_SAVEAS_FILE

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=DEFAULT_DESTINATION):
        if "!ReplaceFile" in file_section_dict:
            msg = "!ReplaceFile is not supported in [TLKList]"
            raise ValueError(msg)
        if "!OverrideType" in file_section_dict:
            msg = "!OverrideType is not supported in [TLKList]"
            raise ValueError(msg)

        self.sourcefile_f = file_section_dict.pop("!SourceFileF", self.DEFAULT_SOURCEFILE_F)
        super().pop_tslpatcher_vars(file_section_dict, default_destination)

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        log: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        dialog: TLK = TLKBinaryReader(source).load()
        self.apply(dialog, memory, log, game)
        return bytes_tlk(dialog)

    def apply(
        self,
        dialog: TLK,
        memory: PatcherMemory,
        log: PatchLogger,
        game: Game,
    ):
        for modifier in self.modifiers:
            modifier.apply(dialog, memory)
            log.complete_patch()


class ModifyTLK:
    def __init__(
        self,
        token_id: int,
        is_replacement: bool = False,  # noqa: FBT001, FBT002
    ):
        self.tlk_filepath: Path | None = None
        self.text: str = ""
        self.sound: ResRef = ResRef.from_blank()

        self.mod_index: int = token_id
        self.token_id: int = token_id
        self.is_replacement: bool = is_replacement

    def apply(self, dialog: TLK, memory: PatcherMemory):
        self.load()
        if self.is_replacement:
            dialog.replace(self.token_id, self.text, str(self.sound))
            memory.memory_str[self.token_id] = self.token_id
        else:
            memory.memory_str[self.token_id] = dialog.add(self.text, str(self.sound))

    def load(self):
        if self.tlk_filepath is None:
            return
        lookup_tlk = TalkTable(self.tlk_filepath)
        self.text = self.text or lookup_tlk.string(self.mod_index)
        self.sound = self.sound or lookup_tlk.sound(self.mod_index)
