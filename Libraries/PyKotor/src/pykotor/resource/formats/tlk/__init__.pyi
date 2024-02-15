from pykotor.resource.formats.tlk.io_tlk import (
    TLKBinaryReader as TLKBinaryReader,
    TLKBinaryWriter as TLKBinaryWriter,
)
from pykotor.resource.formats.tlk.io_tlk_json import (
    TLKJSONReader as TLKJSONReader,
    TLKJSONWriter as TLKJSONWriter,
)
from pykotor.resource.formats.tlk.io_tlk_xml import (
    TLKXMLReader as TLKXMLReader,
    TLKXMLWriter as TLKXMLWriter,
)
from pykotor.resource.formats.tlk.tlk_auto import (
    bytes_tlk as bytes_tlk,
    detect_tlk as detect_tlk,
    read_tlk as read_tlk,
    write_tlk as write_tlk,
)
from pykotor.resource.formats.tlk.tlk_data import (
    TLK as TLK,
    TLKEntry as TLKEntry,
)
