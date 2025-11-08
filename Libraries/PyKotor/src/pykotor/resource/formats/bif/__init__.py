from __future__ import annotations
from pykotor.resource.formats.bif.bif_data import BIF, BIFResource, BIFType
from pykotor.resource.formats.bif.bif_auto import read_bif, write_bif, bytes_bif
from pykotor.resource.formats.bif.io_bif import BIFBinaryReader, BIFBinaryWriter

__all__ = [
    "BIF",
    "BIFBinaryReader",
    "BIFBinaryWriter",
    "BIFResource",
    "BIFType",
    "bytes_bif",
    "read_bif",
    "write_bif",
]
