"""TLK modification algorithms for TSLPatcher/HoloPatcher.

This module implements TLK modification logic for applying patches from changes.ini files.
Handles string additions, modifications, and memory token resolution.

References:
----------
    vendor/TSLPatcher/TSLPatcher.pl - Original Perl TLK modification logic
    vendor/HoloPatcher.NET/src/TSLPatcher.Core/Mods/TLK/ - C# TLK modification implementation
    vendor/Kotor.NET/Kotor.NET.Patcher/ - Incomplete C# patcher
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pykotor.common.misc import ResRef
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.tlk.io_tlk import TLKBinaryReader
from pykotor.resource.formats.tlk.tlk_auto import bytes_tlk
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Literal

    from pykotor.common.misc import Game
    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory
    from utility.common.more_collections import CaseInsensitiveDict


class ModificationsTLK(PatcherModifications):
    DEFAULT_DESTINATION: ClassVar[str] = "."
    DEFAULT_SOURCEFILE: ClassVar[str] = "append.tlk"
    DEFAULT_SOURCEFILE_F: ClassVar[str] = "appendf.tlk"
    DEFAULT_SAVEAS_FILE: ClassVar[str] = "dialog.tlk"
    DEFAULT_SAVEAS_FILE_F: ClassVar[str] = "dialogf.tlk"

    def __init__(
        self,
        filename: str = DEFAULT_SOURCEFILE,
        *,
        replace: bool | None = None,  # noqa: FBT001, FBT002
        modifiers: list[ModifyTLK] | None = None,
    ):
        super().__init__(filename)
        self.destination: str = self.DEFAULT_DESTINATION
        self.modifiers: list[ModifyTLK] = [] if modifiers is None else modifiers
        self.sourcefile_f: str = self.DEFAULT_SOURCEFILE_F  # Polish version of k1
        self.saveas: str = self.DEFAULT_SAVEAS_FILE

    def pop_tslpatcher_vars(
        self,
        file_section_dict: CaseInsensitiveDict[str],
        default_destination: str | None = DEFAULT_DESTINATION,
        default_sourcefolder: str = ".",
    ):
        """Populates the TSLPatcher variables from the file section dictionary.

        Args:
        ----
            file_section_dict: CaseInsensitiveDict[str] - The file section dictionary
            default_destination: str | None - The default destination
            default_sourcefolder: str - The default source folder
        """
        if "!ReplaceFile" in file_section_dict:
            msg = "!ReplaceFile is not supported in [TLKList]"
            raise ValueError(msg)
        if "!OverrideType" in file_section_dict:
            msg = "!OverrideType is not supported in [TLKList]"
            raise ValueError(msg)

        self.sourcefile_f = file_section_dict.pop("!SourceFileF", self.DEFAULT_SOURCEFILE_F)
        super().pop_tslpatcher_vars(file_section_dict, default_destination, default_sourcefolder)

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        dialog: TLK = TLKBinaryReader(source).load()
        self.apply(dialog, memory, logger, game)
        return bytes_tlk(dialog)

    def apply(
        self,
        mutable_data: TLK,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        """Applies the TLK patches to the TLK.

        Args:
        ----
            mutable_data: TLK - The TLK to apply the patches to
            memory: PatcherMemory - The memory context
            logger: PatchLogger - The logger
            game: Game - The game
        """
        for modifier in self.modifiers:
            modifier.apply(mutable_data, memory)
            logger.complete_patch()


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

    def apply(
        self,
        dialog: TLK,
        memory: PatcherMemory,
    ):
        """Applies a TLK patch to a TLK.

        Args:
        ----
            dialog: TLK - The TLK to apply the patch to
            memory: PatcherMemory - The memory context

        Processing Logic:
        ----------------
            - Loads the TLK file
            - Replaces the token ID with the text and sound
            - Stores the new stringref in the memory context for append operations only.
        """
        self.load()
        if self.is_replacement:
            dialog.replace(self.token_id, self.text, str(self.sound))
        else:
            memory.memory_str[self.token_id] = dialog.add(self.text, str(self.sound))

    def load(self):
        """Loads the TLK file."""
        if self.tlk_filepath is None:
            return
        lookup_tlk = TalkTable(self.tlk_filepath)
        self.text = self.text or lookup_tlk.string(self.mod_index)
        self.sound = self.sound or lookup_tlk.sound(self.mod_index)
