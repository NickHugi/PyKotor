from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsNSS:
    def __init__(self, filename: str, replace_file: bool):
        self.filename: str = filename
        self.destination: str = "Override"
        self.replace_file: bool = replace_file

    def apply(self, nss: list[str], memory: PatcherMemory, logger: PatchLogger) -> None:
        source = nss[0]

        match = re.search(r"#2DAMEMORY\d+#", source)
        while match:
            token_id = int(source[match.start() + 10 : match.end() - 1])
            value = memory.memory_2da[token_id]
            source = source[0 : match.start()] + str(value) + source[match.end() : len(source)]
            match = re.search(r"#2DAMEMORY\d+#", source)

        match = re.search(r"#StrRef\d+#", source)
        while match:
            token_id = int(source[match.start() + 7 : match.end() - 1])
            value = memory.memory_str[token_id]
            source = source[0 : match.start()] + str(value) + source[match.end() : len(source)]
            match = re.search(r"#StrRef\d+#", source)

        nss[0] = source
