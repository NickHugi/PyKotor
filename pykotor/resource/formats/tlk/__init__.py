from pykotor.resource.formats.tlk.tlk_data import TLK, TLKEntry  # noqa: I001,F401
from pykotor.resource.formats.tlk.io_tlk import (  # noqa: F401
    TLKBinaryReader,
    TLKBinaryWriter,
)
from pykotor.resource.formats.tlk.io_tlk_xml import (  # noqa: F401
    TLKXMLReader,
    TLKXMLWriter,
)
from pykotor.resource.formats.tlk.io_tlk_json import (  # noqa: F401
    TLKJSONReader,
    TLKJSONWriter,
)
from pykotor.resource.formats.tlk.tlk_auto import (  # noqa: F401
    detect_tlk,
    read_tlk,
    write_tlk,
)
