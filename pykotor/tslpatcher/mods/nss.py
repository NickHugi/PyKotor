from __future__ import annotations

import re
from typing import TYPE_CHECKING

import chardet

from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.tools.path import PurePath

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsNSS:
    def __init__(self, filename: str, replace_file: bool):
        self.filename: str = filename
        self.destination: str = "Override"
        self.action: str = "Compile"
        self.replace_file: bool = replace_file

    def apply(self, nss_bytes: bytes, memory: PatcherMemory, logger: PatchLogger, game: Game) -> bytes:
        encoding: str = (chardet and chardet.detect(nss_bytes) or {}).get("encoding") or "utf8"
        source = nss_bytes.decode(encoding=encoding, errors="replace")

        match = re.search(r"#2DAMEMORY\d+#", source)
        while match:
            token_id = int(source[match.start() + 10 : match.end() - 1])
            value = memory.memory_2da[token_id]
            source = source[: match.start()] + str(value) + source[match.end() :]
            match = re.search(r"#2DAMEMORY\d+#", source)

        match = re.search(r"#StrRef\d+#", source)
        while match:
            token_id = int(source[match.start() + 7 : match.end() - 1])
            value = memory.memory_str[token_id]
            source = source[: match.start()] + str(value) + source[match.end() :]
            match = re.search(r"#StrRef\d+#", source)

        self.filename = str(PurePath(self.filename).with_suffix(".ncs"))
        return bytes_ncs(compile_nss(source, game))
