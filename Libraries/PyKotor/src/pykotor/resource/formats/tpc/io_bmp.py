from __future__ import annotations

import struct

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc.tpc_data import TPCTextureFormat
from pykotor.resource.type import ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc.tpc_data import TPC, TPCMipmap
    from pykotor.resource.type import TARGET_TYPES


class TPCBMPWriter(ResourceWriter):
    """Writes TPC textures as BMP (Windows Bitmap) image files.
    
    Converts TPC textures to standard BMP format. Currently only writes the first
    mipmap layer as RGB24 format.
    
    References:
    ----------
        Standard BMP file format specification (Windows Bitmap)
        Note: BMP is a standard format, no specific vendor implementation needed
    
    Missing Features:
    ----------------
        - Only writes first layer/mipmap (TODO: Other layers)
        - No alpha channel support (BMP format limitation)
    """
    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tpc: TPC = tpc

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # TODO(th3w1zard1): Other layers???  # pyright: ignore[reportUnusedParameters]
        self._tpc.convert(TPCTextureFormat.RGB)
        mm: TPCMipmap = self._tpc.get(0, 0)
        file_size = 14 + 40 + (mm.width * mm.height * 3)

        # Header
        self._writer.write_string("BM")
        self._writer.write_uint32(file_size)
        self._writer.write_uint32(0)
        self._writer.write_uint32(54)

        # InfoHeader
        self._writer.write_uint32(40)
        self._writer.write_uint32(mm.width)
        self._writer.write_uint32(mm.height)
        self._writer.write_uint16(1)
        self._writer.write_uint16(24)
        self._writer.write_uint32(0)
        self._writer.write_uint32(0)
        self._writer.write_uint32(1)
        self._writer.write_uint32(1)
        self._writer.write_uint32(0)  # colors used
        self._writer.write_uint32(0)

        pixel_reader: BinaryReader = BinaryReader.from_bytes(mm.data)
        temp_pixels: list[list[int]] = []
        for _ in range(len(mm.data) // 3):
            r = pixel_reader.read_uint8()
            g = pixel_reader.read_uint8()
            b = pixel_reader.read_uint8()
            temp_pixels.append([b, g, r])

        for i in range(len(temp_pixels)):
            x = i % mm.width
            y = mm.height - (i // mm.width) - 1
            index = x + mm.width * y
            self._writer.write_bytes(struct.pack("BBB", *temp_pixels[index]))
