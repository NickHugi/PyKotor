from __future__ import annotations

import io
import struct

from enum import IntEnum
from typing import TYPE_CHECKING, Sequence

from pykotor.common.stream import BinaryWriter, BinaryWriterBytearray
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.common.stream import BinaryWriterFile
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


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
    """Used to read TGA binary data."""

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
    ):
        super().__init__(source, offset, size, use_binary_reader=False)
        self._tpc: TPC = TPC()

    def _read_color_map(
        self,
        length: int,
        depth: int,
    ) -> list[bytes]:
        color_map: list[bytes] = []
        bytes_per_entry: int = depth // 8

        for _ in range(length):
            entry: bytes = self._stream.read(bytes_per_entry)
            if bytes_per_entry == 3:  # RGB format, append alpha value  # noqa: PLR2004
                entry += b"\xff"  # Append alpha value of 255
            color_map.append(entry)

        return color_map

    @staticmethod
    def _convert_grayscale_to_rgba(grayscale_value: int) -> list[int]:
        """Convert a grayscale value to RGBA."""
        return [grayscale_value, grayscale_value, grayscale_value, 255]

    def _process_rle_data(
        self,
        width: int,
        height: int,
        bits_per_pixel: int,
        color_map: list[bytes] | None = None,
        *,
        is_direct_rgb: bool = False,
    ) -> bytearray:
        """Process RLE compressed data."""
        data = bytearray()
        n = 0
        pixel: list[int]
        rgb_len = 3
        while self._stream.tell() < len(self._stream.getbuffer()):  # while n < width * height:
            packet = int.from_bytes(self._stream.read(1), byteorder="little")
            count = (packet & 0b01111111) + 1
            is_raw_packet: bool = (packet >> 7) == 0
            # count = (packet & 0x7f) + 1
            # is_raw_packet = packet & 0x80
            n += count

            if is_raw_packet:
                for _ in range(count):
                    if is_direct_rgb:
                        b, g, r = struct.unpack("BBB", self._stream.read(3))
                        pixel = (
                            [r, g, b, int.from_bytes(self._stream.read(1), byteorder="little")]
                            if bits_per_pixel == 32  # noqa: PLR2004
                            else [r, g, b, 255]
                        )
                    elif color_map:
                        index = int.from_bytes(self._stream.read(1), byteorder="little")
                        color = list(color_map[index])
                        if len(color) == rgb_len:  # Check the length of the color map entry
                            color.append(255)  # Append alpha value 255
                        pixel = color
                    else:
                        pixel = self._convert_grayscale_to_rgba(int.from_bytes(self._stream.read(1), byteorder="little"))

                    data.extend(pixel)
            else:
                if is_direct_rgb:
                    b, g, r = struct.unpack("BBB", self._stream.read(3))
                    pixel = (
                        [r, g, b, int.from_bytes(self._stream.read(1), byteorder="little")]
                        if bits_per_pixel == 32  # noqa: PLR2004
                        else [r, g, b, 255]
                    )
                elif color_map:
                    index: int = int.from_bytes(self._stream.read(1), byteorder="little")
                    color = list(color_map[index])
                    if len(color) == rgb_len:  # Check the length of the color map entry
                        color.append(255)  # Append alpha value 255
                    pixel = color
                else:
                    pixel = self._convert_grayscale_to_rgba(int.from_bytes(self._stream.read(1), byteorder="little"))
                for _ in range(count):
                    data.extend(pixel)
            if n == width * height:
                break
        return data

    def _process_non_rle_color_mapped(
        self,
        width: int,
        height: int,
        color_map: Sequence[bytes],
    ) -> bytearray:
        """Process non-RLE color-mapped data."""
        data = bytearray()
        for _ in range(width * height):
            index = int.from_bytes(self._stream.read(1), byteorder="little")
            data.extend(color_map[index])
        return data

    @autoclose
    def load(self) -> TPC:
        """Loads image data from the reader into a TPC texture.

        Args:
        ----
            self: The loader object
            auto_close: Whether to close the reader after loading

        Returns:
        -------
            TPC: The loaded TPC texture

        Processing Logic:
        ----------------
            - Check if Pillow is available and use it to load the image if so.
            - If Pillow is not available, do the following:
                - Read header values from the reader
                - Check for uncompressed or RLE encoded RGB data
                - Load pixel data into rows or run lengths
                - Assemble pixel data into a single bytearray
                - Set the loaded data on the TPC texture.
        """
        self._tpc = TPC()
        with open(self._source, "rb") as f:  # noqa: PTH123
            self._stream = io.BytesIO(f.read())
            id_length: int = int.from_bytes(self._stream.read(1), byteorder="little")
            colormap_type: int = int.from_bytes(self._stream.read(1), byteorder="little")
            datatype_code: int = int.from_bytes(self._stream.read(1), byteorder="little")
            _colormap_origin: int = struct.unpack("<H", self._stream.read(2))[0]
            colormap_length: int = struct.unpack("<H", self._stream.read(2))[0]
            colormap_depth: int = int.from_bytes(self._stream.read(1), byteorder="little")
            _x_origin: int = struct.unpack("<H", self._stream.read(2))[0]
            _y_origin: int = struct.unpack("<H", self._stream.read(2))[0]
            width: int = struct.unpack("<H", self._stream.read(2))[0]
            height: int = struct.unpack("<H", self._stream.read(2))[0]
            bits_per_pixel: int = int.from_bytes(self._stream.read(1), byteorder="little")
            image_descriptor: int = int.from_bytes(self._stream.read(1), byteorder="little")
            self._stream.seek(id_length, 1)

            # Read the color map if necessary
            color_map: list[bytes] | None = None
            if colormap_type and colormap_length:
                color_map = self._read_color_map(colormap_length, colormap_depth)

            y_flipped = bool(image_descriptor & 0b00100000)
            interleaving_id: int = (image_descriptor & 0b11000000) >> 6
            if interleaving_id:
                raise ValueError("The tga image data cannot be interleaved.")

            data: bytearray = bytearray()
            if datatype_code == _DataTypes.UNCOMPRESSED_COLOR_MAPPED:
                if color_map is None:
                    msg = "Expected color map not found for uncompressed color-mapped data"
                    raise ValueError(msg)
                data = self._process_non_rle_color_mapped(width, height, color_map)
            elif datatype_code == _DataTypes.UNCOMPRESSED_RGB:
                self._stream.seek(colormap_length * colormap_depth // 8, 1)

                if bits_per_pixel not in {24, 32}:
                    raise ValueError("The image must store 24 or 32 bits per pixel.")

                pixel_rows: list[bytearray] = []
                for y in range(height):
                    pixel_rows.append(bytearray())
                    for _ in range(width):
                        b, g, r = struct.unpack("BBB", self._stream.read(3))
                        if bits_per_pixel == 32:  # noqa: PLR2004
                            pixel_rows[y].extend([r, g, b, int.from_bytes(self._stream.read(1), byteorder="little")])
                        else:
                            pixel_rows[y].extend([r, g, b])

                if y_flipped:
                    for pixels in reversed(pixel_rows):
                        data.extend(pixels)
                else:
                    for pixels in pixel_rows:
                        data.extend(pixels)
            elif datatype_code == _DataTypes.UNCOMPRESSED_BLACK_WHITE:
                data = bytearray()
                for _ in range(width * height):
                    gray_value: int = int.from_bytes(self._stream.read(1), byteorder="little")
                    data.extend([gray_value, gray_value, gray_value])
            elif datatype_code == _DataTypes.RLE_COLOR_MAPPED:
                if color_map is None:
                    msg = "Expected color map not found for RLE color-mapped data"
                    raise ValueError(msg)
                data = self._process_rle_data(width, height, bits_per_pixel, color_map=color_map)
            elif datatype_code == _DataTypes.RLE_RGB:
                data = self._process_rle_data(width, height, bits_per_pixel, is_direct_rgb=True)
            elif datatype_code == _DataTypes.COMPRESSED_BLACK_WHITE:
                data = self._process_rle_data(width, height, bits_per_pixel)
            elif datatype_code in {_DataTypes.COMPRESSED_COLOR_MAPPED_A, _DataTypes.COMPRESSED_COLOR_MAPPED_B}:
                if color_map is None:
                    msg = "Expected compressed color-mapped data not found for tga image reader"
                    raise ValueError(msg)
                data = self._process_rle_data(width, height, bits_per_pixel, color_map=color_map)
            else:
                msg = f"The tga datacode '{datatype_code}' is not currently supported."
                raise ValueError(msg)

            # Set the texture format based on the bits per pixel
            datacode_name: str = next((c.name for c in _DataTypes if c.value == datatype_code), _DataTypes.NO_IMAGE_DATA.name)
            self._tpc.original_datatype_code = _DataTypes.__members__[datacode_name]
            texture_format: Literal[TPCTextureFormat.RGBA, TPCTextureFormat.RGB] = (
                TPCTextureFormat.RGBA
                if bits_per_pixel == 32  # noqa: PLR2004
                else TPCTextureFormat.RGB
            )
            self._tpc.set_data([data], texture_format, width, height)
            return self._tpc


class TPCTGAWriter(ResourceWriter):
    """Used to write TPC instances as TGA image data."""

    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        self._tpc: TPC = tpc
        self._target: TARGET_TYPES = target
        self._writer: BinaryWriterBytearray | BinaryWriterFile = BinaryWriter.to_auto(target)  # type: ignore[assignment]
        self._stream: io.BytesIO | io.BufferedIOBase | io.RawIOBase = io.BytesIO(self._writer._ba) if isinstance(self._writer, BinaryWriterBytearray) else self._writer._stream  # noqa: SLF001


    @autoclose
    def write(self):
        """Writes the TPC texture to a TGA file.

        Args:
        ----
            self: The TPCTGAWriter instance

        Processing Logic:
        ----------------
            - Get width and height of texture from TPC instance
            - Write TGA file header
            - Write pixel data in RGB or RGBA format depending on TPC format.
        """
        if self._tpc is None:
            raise ValueError("TPC instance is not set.")
        width, height = self._tpc.dimensions()

        self._stream.write(
            struct.pack(
                "<BBBHHHHHHBB",
                0,  # id length
                0,  # colormap_type
                2,  # datatype_code
                0,  # colormap_origin
                0,  # colormap_length
                0,  # colormap_depth
                0,  # x_origin
                0,  # y_origin
                width,
                height,
                32,  # bits_per_pixel
                0,  # image_descriptor
            )
        )

        if self._tpc.format() in {TPCTextureFormat.RGB, TPCTextureFormat.DXT1}:
            data: bytearray = self._tpc.convert(TPCTextureFormat.RGB).data
            for i in range(0, len(data), 3):
                r, g, b = data[i:i+3]
                self._stream.write(struct.pack("BBBB", b, g, r, 255))
        else:
            width, height, data = self._tpc.convert(TPCTextureFormat.RGBA)
            for i in range(0, len(data), 4):
                r, g, b, a = data[i:i+4]
                self._stream.write(struct.pack("BBBB", b, g, r, a))
