from pykotor.resource.formats.tpc.tpc_data import (  # noqa: I001,F401
    TPC,
    TPCTextureFormat,
)
from pykotor.resource.formats.tpc.io_tpc import (  # noqa: F401
    TPCBinaryReader,
    TPCBinaryWriter,
)
from pykotor.resource.formats.tpc.io_tga import TPCTGAWriter, TPCTGAReader  # noqa: F401
from pykotor.resource.formats.tpc.io_bmp import TPCBMPWriter  # noqa: F401
from pykotor.resource.formats.tpc.tpc_auto import (  # noqa: F401
    read_tpc,
    write_tpc,
    detect_tpc,
)
