from __future__ import annotations

import struct
from enum import IntEnum

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.type import (
    SOURCE_TYPES,
    TARGET_TYPES,
    ResourceReader,
    ResourceWriter,
    autoclose,
)


class _DataTypes(IntEnum):
    NO_IMAGE_DATA = 0
    UNCOMPRESSED_COLOR_MAPPED = 1
    UNCOMPRESSED_RGB = 2
    UNCOMPRESSED_BLACK_WHITE = 3
    RLE_COLOR_MAPPED = 9
    RLE_RGB = 10
    COMPRESSED_BLACK_WHITE = 11
    COMPRESSED_COLOR_MAPPED_A = 32
    COMPRESSED_COLOR_MAPPED_B = 33


class TPCTGAReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._tpc: TPC | None = None

    # @autoclose  # TODO:?
    def load(
        self,
        auto_close: bool = True,
    ) -> TPC:
        """Loads image data from the reader into a TPC texture
        Args:
            self: The loader object
            auto_close: Whether to close the reader after loading
        Returns:
            TPC: The loaded TPC texture
        Processing Logic:
            - Read header values from the reader
            - Check for uncompressed or RLE encoded RGB data
            - Load pixel data into rows or run lengths
            - Assemble pixel data into a single bytearray
            - Set the loaded data on the TPC texture.
        """
        self._tpc = TPC()

        id_length = self._reader.read_uint8()
        colormap_type = self._reader.read_uint8()  # noqa: F841
        datatype_code = self._reader.read_uint8()
        colormap_origin = self._reader.read_uint16()  # noqa: F841
        colormap_length = self._reader.read_uint16()
        colormap_depth = self._reader.read_uint8()
        x_origin = self._reader.read_uint16()  # noqa: F841
        y_origin = self._reader.read_uint16()  # noqa: F841
        width = self._reader.read_uint16()
        height = self._reader.read_uint16()
        bits_per_pixel = self._reader.read_uint8()
        image_descriptor = self._reader.read_uint8()
        self._reader.skip(id_length)

        y_flipped = bool(image_descriptor & 0b00100000)
        interleaving_id = (image_descriptor & 0b11000000) >> 6
        if interleaving_id:
            ValueError("The image data must not be interleaved.")

        if datatype_code == _DataTypes.UNCOMPRESSED_RGB:
            self._reader.skip(colormap_length * colormap_depth // 8)
            data = bytearray()

            if bits_per_pixel not in [24, 32]:
                ValueError("The image must store 24 or 32 bits per pixel.")

            pixel_rows = []
            for y in range(height):
                pixel_rows.append(bytearray())
                for _ in range(width):
                    b, g, r = (
                        self._reader.read_uint8(),
                        self._reader.read_uint8(),
                        self._reader.read_uint8(),
                    )
                    if bits_per_pixel == 32:
                        pixel_rows[y].extend([r, g, b, self._reader.read_uint8()])
                    else:
                        pixel_rows[y].extend([r, g, b])

            if y_flipped:
                for pixels in reversed(pixel_rows):
                    data.extend(pixels)
            else:
                for pixels in pixel_rows:
                    data.extend(pixels)
        elif datatype_code == _DataTypes.RLE_RGB:
            data = bytearray()
            pixels = []
            n = 0

            while self._reader.remaining():
                packet = self._reader.read_uint8()

                raw = (packet >> 7) == 0
                count = (packet & 0b01111111) + 1
                n += count

                if raw:
                    for _ in range(count):
                        b, g, r = (
                            self._reader.read_uint8(),
                            self._reader.read_uint8(),
                            self._reader.read_uint8(),
                        )
                        if bits_per_pixel == 32:
                            pixels.extend([r, g, b, self._reader.read_uint8()])
                        else:
                            pixels.extend([r, g, b, 255])
                else:
                    b, g, r = (
                        self._reader.read_uint8(),
                        self._reader.read_uint8(),
                        self._reader.read_uint8(),
                    )
                    pixel = [r, g, b]
                    if bits_per_pixel == 32:
                        pixel.append(self._reader.read_uint8())
                    else:
                        pixel.append(255)
                    for _ in range(count):
                        pixels.extend(pixel)

                if n == width * height:
                    break
            data.extend(pixels)
        else:
            msg = "The image data must be RGB and not color-mapped."
            raise ValueError(msg)

        self._tpc.set_data(width, height, [bytes(data)], TPCTextureFormat.RGBA)

        return self._tpc


class TPCTGAWriter(ResourceWriter):
    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tpc = tpc

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        """Writes the TPC texture to a BMP file
        Args:
            self: The TPCWriter instance
            auto_close: Whether to close the underlying file stream (default True).

        Returns
        -------
            None: No value is returned
        Processing Logic:
            - Get width and height of texture from TPC instance
            - Write BMP file header
            - Write pixel data in RGB or RGBA format depending on TPC format.
        """
        width, height = self._tpc.dimensions()

        self._writer.write_uint8(0)  # id length
        self._writer.write_uint8(0)  # colormap_type
        self._writer.write_uint8(2)  # datatype_code
        self._writer.write_bytes(bytes(5))  # colormap_origin
        self._writer.write_uint16(0)  # colormap_length, colormap_depth
        self._writer.write_uint16(0)  # x,y origin
        self._writer.write_uint16(width)
        self._writer.write_uint16(height)

        if self._tpc.format() in [TPCTextureFormat.RGB or TPCTextureFormat.DXT1]:
            self._writer.write_uint8(32)  # bits_per_pixel, image_descriptor
            self._writer.write_uint8(0)
            data = self._tpc.convert(TPCTextureFormat.RGB, 0).data
            pixel_reader = BinaryReader.from_bytes(data)
            for _ in range(len(data) // 3):
                r = pixel_reader.read_uint8()
                g = pixel_reader.read_uint8()
                b = pixel_reader.read_uint8()
                self._writer.write_bytes(struct.pack("BBBB", b, g, r, 255))
        else:
            self._writer.write_uint8(32)
            self._writer.write_uint8(0)
            width, height, data = self._tpc.convert(TPCTextureFormat.RGBA, 0)
            pixel_reader = BinaryReader.from_bytes(data)
            for _ in range(len(data) // 4):
                r = pixel_reader.read_uint8()
                g = pixel_reader.read_uint8()
                b = pixel_reader.read_uint8()
                a = pixel_reader.read_uint8()
                self._writer.write_bytes(struct.pack("BBBB", b, g, r, a))
