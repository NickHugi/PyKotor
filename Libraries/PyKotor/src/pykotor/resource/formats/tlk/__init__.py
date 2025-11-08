from __future__ import annotations
from pykotor.resource.formats.tlk.tlk_data import TLK, TLKEntry
from pykotor.resource.formats.tlk.io_tlk import (
    TLKBinaryReader,
    TLKBinaryWriter,
)
from pykotor.resource.formats.tlk.io_tlk_xml import (
    TLKXMLReader,
    TLKXMLWriter,
)
from pykotor.resource.formats.tlk.io_tlk_json import (
    TLKJSONReader,
    TLKJSONWriter,
)
from pykotor.resource.formats.tlk.tlk_auto import (
    detect_tlk,
    read_tlk,
    write_tlk,
    bytes_tlk,
)

__all__ = [
    "TLK",
    "TLKBinaryReader",
    "TLKBinaryWriter",
    "TLKEntry",
    "TLKJSONReader",
    "TLKJSONWriter",
    "TLKXMLReader",
    "TLKXMLWriter",
    "bytes_tlk",
    "detect_tlk",
    "read_tlk",
    "write_tlk",
]
