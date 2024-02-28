from __future__ import annotations
from .tpc_data import (
    TPC,
    TPCTextureFormat,
)
from .io_tpc import (
    TPCBinaryReader,
    TPCBinaryWriter,
)
from .io_tga import TPCTGAWriter, TPCTGAReader
from .io_bmp import TPCBMPWriter
from .tpc_auto import (
    read_tpc,
    write_tpc,
    detect_tpc,
    bytes_tpc,
)
