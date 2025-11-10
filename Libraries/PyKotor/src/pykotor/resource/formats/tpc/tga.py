"""
Compact TGA reader/writer inspired by the vendor implementations.
"""

from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from typing import BinaryIO


TGA_TYPE_TRUE_COLOR = 2
TGA_TYPE_GRAYSCALE = 3
TGA_TYPE_RLE_TRUE_COLOR = 10


@dataclass
class TGAImage:
    width: int
    height: int
    data: bytes  # RGBA8888, row-major, origin = top-left

    @property
    def pixel_depth(self) -> int:
        return 32


def _flip_vertically(buffer: bytearray, width: int, height: int, bpp: int) -> None:
    stride = width * bpp
    for row in range(height // 2):
        a = row * stride
        b = (height - row - 1) * stride
        buffer[a : a + stride], buffer[b : b + stride] = buffer[b : b + stride], buffer[a : a + stride]


def _read_rle(stream: BinaryIO, width: int, height: int, pixel_depth: int) -> bytes:
    bytes_per_pixel = pixel_depth // 8
    total_pixels = width * height
    result = bytearray(total_pixels * bytes_per_pixel)

    dst = 0
    while dst < len(result):
        packet = stream.read(1)
        if not packet:
            raise ValueError("Unexpected end of RLE stream")

        header = packet[0]
        count = (header & 0x7F) + 1

        if header & 0x80:
            pixel = stream.read(bytes_per_pixel)
            if len(pixel) != bytes_per_pixel:
                raise ValueError("Incomplete RLE pixel data")
            for _ in range(count):
                result[dst : dst + bytes_per_pixel] = pixel
                dst += bytes_per_pixel
        else:
            raw = stream.read(count * bytes_per_pixel)
            if len(raw) != count * bytes_per_pixel:
                raise ValueError("Incomplete raw RLE span")
            result[dst : dst + len(raw)] = raw
            dst += len(raw)

    return bytes(result)


def read_tga(stream: BinaryIO) -> TGAImage:
    header = stream.read(18)
    if len(header) != 18:
        raise ValueError("Incomplete TGA header")

    (
        id_length,
        color_map_type,
        image_type,
        color_map_origin,
        color_map_length,
        color_map_depth,
        x_origin,
        y_origin,
        width,
        height,
        pixel_depth,
        descriptor,
    ) = struct.unpack("<BBBHHBHHHHBB", header)

    if color_map_type != 0:
        raise ValueError("Color-mapped TGAs are not supported")

    supported_types = {TGA_TYPE_TRUE_COLOR, TGA_TYPE_GRAYSCALE, TGA_TYPE_RLE_TRUE_COLOR}
    if image_type not in supported_types:
        raise ValueError(f"Unsupported TGA image type: {image_type}")

    stream.seek(id_length, io.SEEK_CUR)

    if image_type == TGA_TYPE_RLE_TRUE_COLOR:
        raw = _read_rle(stream, width, height, pixel_depth)
    else:
        bytes_per_pixel = pixel_depth // 8
        raw = stream.read(width * height * bytes_per_pixel)
        if len(raw) != width * height * bytes_per_pixel:
            raise ValueError("Unexpected end of TGA pixel data")

    rgba = bytearray(width * height * 4)

    if image_type == TGA_TYPE_GRAYSCALE or pixel_depth == 8:
        for i, value in enumerate(raw):
            rgba[i * 4 : i * 4 + 4] = bytes((value, value, value, 255))
    elif pixel_depth == 24:
        for i in range(width * height):
            b, g, r = raw[i * 3 : i * 3 + 3]
            rgba[i * 4 : i * 4 + 4] = bytes((r, g, b, 255))
    elif pixel_depth == 32:
        for i in range(width * height):
            b, g, r, a = raw[i * 4 : i * 4 + 4]
            rgba[i * 4 : i * 4 + 4] = bytes((r, g, b, a))
    else:
        raise ValueError(f"Unsupported pixel depth: {pixel_depth}")

    # Flip vertically if origin is bottom-left (bit 5 not set).
    if (descriptor & 0x20) == 0:
        _flip_vertically(rgba, width, height, 4)

    return TGAImage(width=width, height=height, data=bytes(rgba))


def write_tga(image: TGAImage, stream: BinaryIO, rle: bool = False) -> None:
    width, height = image.width, image.height
    pixel_depth = 32
    descriptor = 0x20 | 0x08  # origin top-left, 8 bits of alpha

    header = struct.pack(
        "<BBBHHBHHHHBB",
        0,  # ID length
        0,  # color map type
        TGA_TYPE_RLE_TRUE_COLOR if rle else TGA_TYPE_TRUE_COLOR,
        0,
        0,
        0,
        0,
        0,
        width,
        height,
        pixel_depth,
        descriptor,
    )
    stream.write(header)

    data = bytearray(image.data)
    # Ensure origin is top-left; our in-memory data already is, but the TGA
    # writer expects bottom-left order before optional flipping. We invert so
    # that the stored data matches descriptor 0x20 (top origin).
    _flip_vertically(data, width, height, 4)

    if not rle:
        for i in range(width * height):
            r, g, b, a = data[i * 4 : i * 4 + 4]
            stream.write(bytes((b, g, r, a)))
        return

    # Simple RLE encoder that operates on scanlines.
    def write_packet(packet_pixels: list[bytes], raw: bool) -> None:
        count = len(packet_pixels)
        if raw:
            stream.write(bytes([count - 1]))
            for px in packet_pixels:
                stream.write(px)
        else:
            stream.write(bytes([0x80 | (count - 1)]))
            stream.write(packet_pixels[0])

    stride = width * 4
    for row in range(height):
        start = row * stride
        scanline = data[start : start + stride]
        x = 0
        while x < width:
            # Look ahead for repeated pixels.
            current = scanline[x * 4 : (x + 1) * 4]
            repeat = 1
            while x + repeat < width and scanline[(x + repeat) * 4 : (x + repeat + 1) * 4] == current and repeat < 128:
                repeat += 1

            if repeat > 1:
                write_packet([bytes((current[2], current[1], current[0], current[3]))], raw=False)
                x += repeat
                continue

            # Gather raw run until we hit a repetition.
            raw_pixels: list[bytes] = []
            while x < width:
                pixel = scanline[x * 4 : (x + 1) * 4]
                bgr = bytes((pixel[2], pixel[1], pixel[0], pixel[3]))
                raw_pixels.append(bgr)
                x += 1
                if x == width:
                    break
                nxt = scanline[x * 4 : (x + 1) * 4]
                if nxt == pixel or len(raw_pixels) == 128:
                    break

            write_packet(raw_pixels, raw=True)

