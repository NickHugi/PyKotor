from __future__ import annotations

import struct

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCTextureFormat
from pykotor.resource.type import TARGET_TYPES, ResourceWriter, autoclose


class TPCBMPWriter(ResourceWriter):
    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tpc: TPC = tpc

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ):
        """Writes the texture to a bitmap file.

        Args:
        ----
            self: The Texture object
            auto_close: Whether to close the file after writing (default True).

        Processing Logic:
        ----------------
            - Convert texture to RGB format and get width, height, data
            - Write bitmap header and info header
            - Read pixels from data and write to file in BGR format line by line.
        """
        width, height, data = self._tpc.convert(TPCTextureFormat.RGB, 0)
        file_size = 14 + 40 + (width * height * 3)

        # Header
        self._writer.write_string("BM")
        self._writer.write_uint32(file_size)
        self._writer.write_uint32(0)
        self._writer.write_uint32(54)

        # InfoHeader
        self._writer.write_uint32(40)
        self._writer.write_uint32(width)
        self._writer.write_uint32(height)
        self._writer.write_uint16(1)
        self._writer.write_uint16(24)
        self._writer.write_uint32(0)
        self._writer.write_uint32(0)
        self._writer.write_uint32(1)
        self._writer.write_uint32(1)
        self._writer.write_uint32(0)  # colors used
        self._writer.write_uint32(0)

        pixel_reader: BinaryReader = BinaryReader.from_bytes(data)
        temp_pixels: list[list[int]] = []
        for _ in range(len(data) // 3):
            r = pixel_reader.read_uint8()
            g = pixel_reader.read_uint8()
            b = pixel_reader.read_uint8()
            temp_pixels.append([b, g, r])

        for i in range(len(temp_pixels)):
            x = i % width
            y = height - (i // width) - 1
            index = x + width * y
            self._writer.write_bytes(struct.pack("BBB", *temp_pixels[index]))
