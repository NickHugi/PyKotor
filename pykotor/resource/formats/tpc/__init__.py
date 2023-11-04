from pykotor.resource.formats.tpc.tpc_data import (
    TPC,
    TPCTextureFormat,
)
from pykotor.resource.formats.tpc.io_tpc import (
    TPCBinaryReader,
    TPCBinaryWriter,
)
from pykotor.resource.formats.tpc.io_tga import TPCTGAWriter, TPCTGAReader
from pykotor.resource.formats.tpc.io_bmp import TPCBMPWriter
from pykotor.resource.formats.tpc.tpc_auto import (
    read_tpc,
    write_tpc,
    detect_tpc,
)
