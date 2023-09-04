import re

from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsNSS:
    def __init__(self, filename: str, replace_file: bool):
        self.filename: str = filename
        self.destination: str = str(CaseAwarePath("Override", filename))
        self.replace_file: bool = replace_file

    def apply(self, nss: list[str], memory: PatcherMemory, logger: PatchLogger) -> None:
        source = nss[0]

        print("Looking for #2DAMEMORY# entries...")
        while match := re.search(r"#2DAMEMORY\d+#", source):
            token_id = int(source[match.start() + 10 : match.end() - 1])
            value_str: str = memory.memory_2da[token_id]
            source = (
                source[0 : match.start()]
                + value_str
                + source[match.end() : len(source)]
            )

        print("Looking for #StrRef# entries...")
        while match := re.search(r"#StrRef\d+#", source):
            token_id = int(source[match.start() + 7 : match.end() - 1])
            value: int = memory.memory_str[token_id]
            source = (
                source[0 : match.start()]
                + str(value)
                + source[match.end() : len(source)]
            )

        nss[0] = source
