from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pykotor.common.misc import decode_bytes_with_fallbacks
from pykotor.resource.formats.ncs import bytes_ncs, compile_nss
from pykotor.tools.path import PurePath
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsNSS(PatcherModifications):
    def __init__(self, filename: str, replace_file: bool, destination: str | None = None) -> None:
        super().__init__(filename, destination, saveas=str(PurePath(filename).with_suffix(".ncs")))
        self.replace_file: bool = replace_file
        self.action: str = "Compile"

    def apply(self, nss_bytes: bytes, memory: PatcherMemory, logger: PatchLogger, game: Game) -> bytes:
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
