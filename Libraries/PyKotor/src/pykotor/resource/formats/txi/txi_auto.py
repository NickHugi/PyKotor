from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.txi.io_txi import TXIBinaryReader, TXIBinaryWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.txi.txi_data import TXI
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def read_txi(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> TXI:
    """Returns a TXI instance from the source."""
    return TXIBinaryReader(source, offset, size or 0).load()


def write_txi(
    txi: TXI,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.TXI,
):
    """Writes the TXI data to the target location with the specified format."""
    if file_format is ResourceType.TXI:
        TXIBinaryWriter(txi, target).write()
    else:
        msg = "Unsupported format specified; use TXI."
        raise ValueError(msg)


def bytes_txi(
    txi: TXI,
    file_format: ResourceType = ResourceType.TXI,
) -> bytes:
    """Returns the TXI data in the specified format as a bytes object."""
    data = bytearray()
    write_txi(txi, data, file_format)
    return bytes(data)
