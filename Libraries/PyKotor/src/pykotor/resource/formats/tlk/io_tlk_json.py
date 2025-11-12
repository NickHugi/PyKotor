from __future__ import annotations

import json

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose
from pykotor.tools.encoding import decode_bytes_with_fallbacks

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

    class TLKStringEntry(TypedDict):
        _index: str
        text: str
        soundResRef: str

    class TLKJSONDict(TypedDict):
        strings: list[TLKStringEntry]


class TLKJSONReader(ResourceReader):
    """Reads TLK files from JSON format.
    
    JSON is a PyKotor-specific convenience format for easier editing of talk tables.
    
    References:
    ----------
        Note: JSON format is PyKotor-specific, not a standard game format
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._json: dict = {}
        self._tlk: TLK | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> TLK:  # noqa: FBT001, FBT002, ARG002
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
        self._json: TLKJSONDict = {"strings": []}

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        for stringref, entry in self._tlk:
            string: TLKStringEntry = {
                "_index": str(stringref),
                "text": entry.text,
                "soundResRef": str(entry.voiceover)
            }
            self._json["strings"].append(string)

        json_dump = json.dumps(self._json, indent=4)
        self._writer.write_bytes(json_dump.encode())
