from __future__ import annotations

import io
from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.tga import read_tga
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCLayer, TPCMipmap, TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def _decode_mipmap_to_rgba(mipmap: TPCMipmap) -> bytes:
    """Return a copy of the mipmap's pixels in RGBA order."""
    working = mipmap.copy()
    if working.tpc_format != TPCTextureFormat.RGBA:
        working.convert(TPCTextureFormat.RGBA)
    return bytes(working.data)


def _has_alpha_channel(pixels: bytes) -> bool:
    """Return True when any pixel contains transparency."""
    return any(pixels[i + 3] != 0xFF for i in range(0, len(pixels), 4))


def _write_tga_rgba(writer: ResourceWriter, width: int, height: int, rgba: bytes) -> None:
    """Write a simple uncompressed RGBA TGA image."""
    writer._writer.write_uint8(0)  # ID length
    writer._writer.write_uint8(0)  # colour map type
    writer._writer.write_uint8(2)  # image type (uncompressed true colour)
    writer._writer.write_bytes(bytes(5))  # colour map specification
    writer._writer.write_uint16(0)  # x origin
    writer._writer.write_uint16(0)  # y origin
    writer._writer.write_uint16(width)
    writer._writer.write_uint16(height)
    writer._writer.write_uint8(32)
    writer._writer.write_uint8(0x20 | 0x08)  # top-left origin, 8-bit alpha

    total_pixels = width * height
    for i in range(total_pixels):
        offset = i * 4
        r, g, b, a = rgba[offset : offset + 4]
        writer._writer.write_bytes(bytes((b, g, r, a)))


class TPCTGAReader(ResourceReader):
    """Used to read TGA binary data."""
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._tpc: TPC | None = None

    def _read_color_map(
        self,
        length: int,
        depth: int,
    ) -> list[bytes]:
        color_map: list[bytes] = []
        bytes_per_entry = depth // 8

        for _ in range(length):
            entry: bytes = self._reader.read_bytes(bytes_per_entry)
            if bytes_per_entry == 3:  # RGB format, append alpha value
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
        while self._reader.remaining():  # while n < width * height:
            packet = self._reader.read_uint8()
            count = (packet & 0b01111111) + 1
            is_raw_packet: bool = (packet >> 7) == 0
            # count = (packet & 0x7f) + 1
            # is_raw_packet = packet & 0x80
            n += count

            if is_raw_packet:
                for _ in range(count):
                    if is_direct_rgb:
                        b, g, r = (
                            self._reader.read_uint8(),
                            self._reader.read_uint8(),
                            self._reader.read_uint8(),
                        )
                        pixel = [r, g, b, self._reader.read_uint8()] if bits_per_pixel == 32 else [r, g, b, 255]
                    elif color_map:
                        index = self._reader.read_uint8()
                        color = list(color_map[index])
                        if len(color) == rgb_len:  # Check the length of the color map entry
                            color.append(255)  # Append alpha value 255
                        pixel = color
                    else:
                        pixel = self._convert_grayscale_to_rgba(self._reader.read_uint8())

                    data.extend(pixel)
            else:
                if is_direct_rgb:
                    b, g, r = (
                        self._reader.read_uint8(),
                        self._reader.read_uint8(),
                        self._reader.read_uint8(),
                    )
                    pixel = [r, g, b, self._reader.read_uint8()] if bits_per_pixel == 32 else [r, g, b, 255]
                elif color_map:
                    index = self._reader.read_uint8()
                    color = list(color_map[index])
                    if len(color) == rgb_len:  # Check the length of the color map entry
                        color.append(255)  # Append alpha value 255
                    pixel = color
                else:
                    pixel = self._convert_grayscale_to_rgba(self._reader.read_uint8())
                for _ in range(count):
                    data.extend(pixel)
            if n == width * height:
                break
        return data

    def _process_non_rle_color_mapped(
        self,
        width: int,
        height: int,
        color_map: list[bytes],
    ) -> bytearray:
        """Process non-RLE color-mapped data."""
        data = bytearray()
        for _ in range(width * height):
            index = self._reader.read_uint8()
            data.extend(color_map[index])
        return data

    @autoclose
    def load(self, *, auto_close: bool = True) -> TPC:  # noqa: FBT001, FBT002, ARG002
        self._tpc = TPC()
        raw = self._reader.read_all()
        image = read_tga(io.BytesIO(raw))

        width, height = image.width, image.height
        rgba = image.data
        face_count = 1
        face_height = height

        if height and width and height % width == 0 and height // width == 6:
            face_count = 6
            face_height = height // 6
            self._tpc.is_cube_map = True
        else:
            self._tpc.is_cube_map = False

        self._tpc.layers = []
        self._tpc.is_animated = False

        has_alpha = _has_alpha_channel(rgba)

        for face in range(face_count):
            layer = TPCLayer()
            slice_rgba = bytearray(face_height * width * 4)
            for row in range(face_height):
                src_offset = ((face * face_height) + row) * width * 4
                dst_offset = row * width * 4
                slice_rgba[dst_offset : dst_offset + width * 4] = rgba[src_offset : src_offset + width * 4]
            layer.set_single(width, face_height, slice_rgba, TPCTextureFormat.RGBA)
            self._tpc.layers.append(layer)

        self._tpc._format = TPCTextureFormat.RGBA  # noqa: SLF001
        if not has_alpha:
            self._tpc.convert(TPCTextureFormat.RGB)

        return self._tpc

class TPCTGAWriter(ResourceWriter):
    """Used to write TPC instances as TGA image data."""
    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tpc: TPC = tpc

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        if self._tpc is None:
            raise ValueError("TPC instance is not set.")
        base_layer = self._tpc.layers[0].mipmaps[0]
        frame_width, frame_height = base_layer.width, base_layer.height

        if self._tpc.is_animated:
            txi = self._tpc._txi  # noqa: SLF001
            numx = max(1, txi.features.numx or 0)
            numy = max(1, txi.features.numy or 0)
            if numx * numy != len(self._tpc.layers):
                numx = len(self._tpc.layers)
                numy = 1
            width = frame_width * numx
            height = frame_height * numy
            canvas = bytearray(width * height * 4)

            for index, layer in enumerate(self._tpc.layers):
                rgba_frame = _decode_mipmap_to_rgba(layer.mipmaps[0])
                tile_x = index % numx
                tile_y = index // numx
                for row in range(frame_height):
                    src = row * frame_width * 4
                    dst_row = tile_y * frame_height + row
                    dst = (dst_row * width + tile_x * frame_width) * 4
                    canvas[dst : dst + frame_width * 4] = rgba_frame[src : src + frame_width * 4]

        elif self._tpc.is_cube_map:
            width = frame_width
            height = frame_height * len(self._tpc.layers)
            canvas = bytearray(width * height * 4)
            for index, layer in enumerate(self._tpc.layers):
                rgba_face = _decode_mipmap_to_rgba(layer.mipmaps[0])
                for row in range(frame_height):
                    src = row * width * 4
                    dst_row = index * frame_height + row
                    dst = (dst_row * width) * 4
                    canvas[dst : dst + width * 4] = rgba_face[src : src + width * 4]

        else:
            width, height = frame_width, frame_height
            canvas = bytearray(_decode_mipmap_to_rgba(self._tpc.layers[0].mipmaps[0]))

        _write_tga_rgba(self, width, height, bytes(canvas))
