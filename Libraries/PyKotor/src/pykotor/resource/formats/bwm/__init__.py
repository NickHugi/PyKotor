from __future__ import annotations


from pykotor.resource.formats.bwm.bwm_auto import bytes_bwm, read_bwm, write_bwm
from pykotor.resource.formats.bwm.bwm_data import (
    BWM,
    BWMAdjacency,
    BWMEdge,
    BWMFace,
    BWMType,
)
from pykotor.resource.formats.bwm.io_bwm import (
    BWMBinaryReader,
    BWMBinaryWriter,
)

__all__ = [
    "BWM",
    "BWMAdjacency",
    "BWMBinaryReader",
    "BWMBinaryWriter",
    "BWMEdge",
    "BWMFace",
    "BWMType",
    "bytes_bwm",
    "read_bwm",
    "write_bwm",
]

