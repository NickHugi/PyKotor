from __future__ import annotations

import io
import struct

from typing import TYPE_CHECKING

try:
    from PIL import Image

    pillow_available = True
except ImportError:
    pillow_available = False


from pykotor.common.stream import BinaryReader, BinaryWriterFile
from pykotor.resource.formats.tpc.tpc_data import TPCTextureFormat
from pykotor.resource.type import ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc.tpc_data import TPC
    from pykotor.resource.type import TARGET_TYPES


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
        if pillow_available:
            self._write_with_pillow()
        else:
            self._write_with_custom_logic()

    def _write_with_pillow(
        self,
    ):
        if self._tpc is None:
            raise ValueError("TPC instance is not set.")

        if self._tpc.format() is TPCTextureFormat.RGBA:
            width, height, _format, data = self._tpc.get()
            mode = "RGBA"
        else:
            width, height, data = self._tpc.convert(TPCTextureFormat.RGB)
            mode = "RGB"
        img = Image.frombytes(mode, (width, height), data)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(self._writer._stream if isinstance(self._writer, BinaryWriterFile) else io.BytesIO(self._writer._ba), format="BMP")

    def _write_with_custom_logic(
        self,
    ):
        if self._tpc is None:
            raise ValueError("TPC instance is not set.")
        width, height, data = self._tpc.convert(TPCTextureFormat.RGB)
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
