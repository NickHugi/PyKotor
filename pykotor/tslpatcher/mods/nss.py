from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pykotor.common.misc import decode_bytes_with_fallbacks
from pykotor.resource.formats.ncs import bytes_ncs, compile_nss
from pykotor.helpers.path import PurePath
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsNSS(PatcherModifications):
    def __init__(self, filename, replace=None, modifiers=None) -> None:
        super().__init__(filename, replace, modifiers)
        self.saveas = str(PurePath(filename).with_suffix(".ncs"))
        self.action: str = "Compile"

    def apply(self, nss_bytes: bytes, memory: PatcherMemory, logger: PatchLogger, game: Game) -> bytes:
        """Takes the source nss bytes and replaces instances of 2DAMEMORY# and StrRef# with the relevant data.

        Args:
        ----
            nss_bytes: bytes: The bytes to patch.
            memory: PatcherMemory: Memory references for patching. 
            logger: PatchLogger: Logger for logging messages.
            game: Game: The game being patched.

        Returns:
        -------
            bytes: The patched bytes.
        Processing Logic:
            1. Decodes bytes to a string
            2. Replaces #2DAMEMORY# tokens with values from PatcherMemory
            3. Replaces #StrRef# tokens with values from PatcherMemory 
            4. Compiles the patched string and encodes to bytes.
        """
        source: str = decode_bytes_with_fallbacks(nss_bytes)

        match = re.search(r"#2DAMEMORY\d+#", source)
        while match:
            token_id = int(source[match.start() + 10 : match.end() - 1])
            value_str: str = memory.memory_2da[token_id]
            source = source[: match.start()] + value_str + source[match.end() :]
            match = re.search(r"#2DAMEMORY\d+#", source)

        match = re.search(r"#StrRef\d+#", source)
        while match:
            token_id = int(source[match.start() + 7 : match.end() - 1])
            value = memory.memory_str[token_id]
            source = source[: match.start()] + str(value) + source[match.end() :]
            match = re.search(r"#StrRef\d+#", source)

        return bytes_ncs(compile_nss(source, game))

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=PatcherModifications.DEFAULT_DESTINATION):
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        # TODO: Need to handle HACKList here and in apply.
