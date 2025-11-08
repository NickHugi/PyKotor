from __future__ import annotations
from pykotor.resource.formats.tpc.tpc_data import (
    TPC,
    TPCTextureFormat,
    TPCMipmap,
    TPCLayer,
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
    bytes_tpc,
)

__all__ = [
    "TPC",
    "TPCBMPWriter",
    "TPCBinaryReader",
    "TPCBinaryWriter",
    "TPCLayer",
    "TPCMipmap",
    "TPCTGAReader",
    "TPCTGAWriter",
    "TPCTextureFormat",
    "bytes_tpc",
    "read_tpc",
    "write_tpc",
]
