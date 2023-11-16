from __future__ import annotations

import json

from pykotor.common.misc import (
    ResRef,
    decode_bytes_with_fallbacks,
)
from pykotor.resource.formats.tlk import TLK
from pykotor.resource.type import (
    SOURCE_TYPES,
    TARGET_TYPES,
    ResourceReader,
    ResourceWriter,
    autoclose,
)


class TLKJSONReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._json = {}
        self._tlk: TLK | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> TLK:
        self._tlk = TLK()
        self._json = json.loads(decode_bytes_with_fallbacks(self._reader.read_bytes(self._reader.size())))

        self._tlk.resize(len(self._json["strings"]))
        for string in self._json["strings"]:
            index = int(string["_index"])
            self._tlk.entries[index].text = string["text"]
            self._tlk.entries[index].voiceover = ResRef(string["soundResRef"])

        return self._tlk


class TLKJSONWriter(ResourceWriter):
    def __init__(
        self,
        twoda: TLK,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tlk: TLK = twoda
        self._json = {"strings": []}

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        for stringref, entry in self._tlk:
            string = {}
            self._json["strings"].append(string)
            string["_index"] = str(stringref)
            string["text"] = entry.text
            string["soundResRef"] = entry.voiceover.get()

        json_dump = json.dumps(self._json, indent=4)
        self._writer.write_bytes(json_dump.encode())
