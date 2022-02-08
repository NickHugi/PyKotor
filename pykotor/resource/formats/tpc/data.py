"""
This module handles classes relating to editing TPC files.
"""
from __future__ import annotations

import struct
from enum import IntEnum
from typing import List, Tuple, Optional, NamedTuple

from pykotor.resource.type import ResourceType

from pykotor.common.stream import BinaryReader, BinaryWriter


class TPCGetResult(NamedTuple):
    width: int
    height: int
    format: TPCTextureFormat
    data: Optional[bytes]


class TPCConvertResult(NamedTuple):
    width: int
    height: int
    data: Optional[bytes]


class TPC:
    """
    Represents a TPC file.

    Attributes:
        txi: Stores additional information regarding the texture.
    """

    BINARY_TYPE = ResourceType.TPC

    def __init__(self):
        self._texture_format: TPCTextureFormat = TPCTextureFormat.Invalid
        self._mipmaps: List[bytes] = []
        self._width: int = 0
        self._height: int = 0
        self.txi: str = ""

        # TODO: cube maps

    def mipmap_count(self) -> int:
        """
        Returns the number of mipmaps.

        Returns:
            The number of mipmaps.
        """
        return len(self._mipmaps)

    def format(self) -> TPCTextureFormat:
        """
        Returns the format of the stored texture.

        Returns:
            The format of the stored texture.
        """
        return self._texture_format

    def dimensions(self) -> Tuple[int, int]:
        """
        Returns the width and height of the largest mipmap.

        Returns:
            A tuple containing [width, height].
        """
        return self._width, self._height

    def get(self, mipmap: int = 0) -> TPCGetResult:
        """
        Returns a tuple containing the width, height, texture format, and data of the specified mipmap.

        Args:
            mipmap: The index of the mipmap.

        Returns:
            A tuple equal to (width, height, texture format, data).
        """
        width, height = self._mipmap_size(mipmap)
        return TPCGetResult(width, height, self._texture_format, self._mipmaps[mipmap])

    def convert(self, texture_format: TPCTextureFormat, mipmap: int = 0) -> TPCConvertResult:
        """
        Returns a tuple containing the width, height and data of the specified mipmap where the data returned is in
        the texture format specified.

        Args:
            texture_format: The format the texture data should be converted to.
            mipmap: The index of the mipmap.

        Returns:
            A tuple equal to (width, height, data)
        """
        width, height = self._mipmap_size(mipmap)
        raw_data = self._mipmaps[mipmap]
        data = bytes()

        if texture_format == TPCTextureFormat.DXT1 or texture_format == TPCTextureFormat.DXT5:
            raise NotImplementedError()

        if texture_format == TPCTextureFormat.Greyscale:
            raise NotImplementedError()

        if texture_format == TPCTextureFormat.RGBA:
            if self._texture_format is TPCTextureFormat.DXT5:
                data = TPC._dxt5_to_rgba(raw_data, width, height)
            elif self._texture_format is TPCTextureFormat.DXT1:
                data = TPC._dxt1_to_rgba(raw_data, width, height)
            elif self._texture_format is TPCTextureFormat.RGBA:
                data = raw_data
            elif self._texture_format is TPCTextureFormat.RGB:
                data = TPC._rgb_to_rgba(raw_data, width, height)
            elif self._texture_format is TPCTextureFormat.Greyscale:
                data = TPC._grey_to_rgba(raw_data, width, height)

        if texture_format == TPCTextureFormat.RGB:
            if self._texture_format is TPCTextureFormat.DXT5:
                data = TPC._dxt5_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_rgb(data, width, height)
            elif self._texture_format is TPCTextureFormat.DXT1:
                data = TPC._dxt1_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_rgb(data, width, height)
            elif self._texture_format is TPCTextureFormat.RGBA:
                data = TPC._rgba_to_rgb(raw_data, width, height)
            elif self._texture_format is TPCTextureFormat.RGB:
                data = raw_data
            elif self._texture_format is TPCTextureFormat.Greyscale:
                data = TPC._grey_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_rgb(data, width, height)

        return TPCConvertResult(width, height, data)

    def set_single(self, width: int, height: int, data: bytes, texture_format: TPCTextureFormat) -> None:
        """
        Sets the texture data but only for a single mipmap.

        Args:
            width: The new width.
            height: The new height.
            data: The new texture data.
            texture_format: The texture format.
        """
        self.set(width, height, [data], texture_format)

    def set(self, width: int, height: int, mipmaps: List[bytes], texture_format: TPCTextureFormat) -> None:
        """
        Sets the new texture data.

        Args:
            width: The new width.
            height: The new height.
            mipmaps: The new mipmaps data.
            texture_format: The texture format.
        """
        # TODO: Some sort of simple sanity check on the data; make sure the mipmaps' data have the appropriate size
        #       according to their texture format.

        self._texture_format = texture_format
        self._mipmaps = mipmaps
        self._width = width
        self._height = height

    def _mipmap_size(self, mipmap: int) -> Tuple[int, int]:
        """
        Returns the size of the specified mipmap.

        Args:
            mipmap: The index of the mipmap.

        Raises:
            IndexError: The index for the mipmap is out of range.

        Returns:
            A tuple equal to (width, height).
        """
        if 0 > mipmap >= len(self._mipmaps):
            raise IndexError("The index for the mipmap is out of range.")

        width = self._width
        height = self._height
        for i in range(mipmap):
            width >>= 1
            height >>= 1
        return width, height

    @staticmethod
    def _dxt5_to_rgba(data: bytes, width: int, height: int) -> bytearray:
        dxt_reader = BinaryReader.from_bytes(data)
        pixels = [0] * width * height

        for ty in range(height, 0, -4):
            for tx in range(0, width, 4):
                alpha0 = dxt_reader.read_uint8()
                alpha1 = dxt_reader.read_uint8()
                dxt_alpha = TPC._integer48(dxt_reader.read_bytes(6))
                color0 = TPC._rgba565_to_rgb888(dxt_reader.read_int16())
                color1 = TPC._rgba565_to_rgb888(dxt_reader.read_int16())
                dxt_pixels = dxt_reader.read_uint32(big=True)

                color_code = []
                color_code.extend([color0, color1])
                if color0 > color1:
                    color_code.append(TPC._interpolate(0.3333333, color0, color1))
                    color_code.append(TPC._interpolate(0.6666666, color0, color1))
                else:
                    color_code.append(TPC._interpolate(0.5555555, color0, color1))
                    color_code.append(0xFF000000)

                alpha_code = [alpha0, alpha1]
                if alpha0 > alpha1:
                    alpha_code.append(int((6.0 * alpha0 + 1.0 * alpha1 + 3) / 7))
                    alpha_code.append(int((5.0 * alpha0 + 2.0 * alpha1 + 3) / 7))
                    alpha_code.append(int((4.0 * alpha0 + 3.0 * alpha1 + 3) / 7))
                    alpha_code.append(int((3.0 * alpha0 + 4.0 * alpha1 + 3) / 7))
                    alpha_code.append(int((2.0 * alpha0 + 5.0 * alpha1 + 3) / 7))
                    alpha_code.append(int((1.0 * alpha0 + 6.0 * alpha1 + 3) / 7))
                else:
                    alpha_code.append(int((4.0 * alpha0 + 1.0 * alpha1 + 1) / 5))
                    alpha_code.append(int((3.0 * alpha0 + 2.0 * alpha1 + 2) / 5))
                    alpha_code.append(int((2.0 * alpha0 + 3.0 * alpha1 + 2) / 5))
                    alpha_code.append(int((1.0 * alpha0 + 4.0 * alpha1 + 2) / 5))
                    alpha_code.append(0)
                    alpha_code.append(255)

                for y in range(4):
                    for x in range(4):
                        pixelc_code = dxt_pixels & 3
                        dxt_pixels >>= 2
                        a = alpha_code[(dxt_alpha >> (3 * (4 * (3 - y) + x))) & 7]
                        pixel = color_code[pixelc_code] | (a << 24)
                        pixels[(ty - 4 + y) * width + (tx + x)] = pixel

        new_data = bytearray()
        for pixel in pixels:
            new_data.append((pixel & 0x00FF0000) >> 16)
            new_data.append((pixel & 0x0000FF00) >> 8)
            new_data.append((pixel & 0x000000FF))
            new_data.append((pixel & 0xFF000000) >> 24)

        return new_data

    @staticmethod
    def _dxt1_to_rgba(data: bytes, width: int, height: int) -> bytearray:
        dxt_reader = BinaryReader.from_bytes(data)
        pixels = [0] * width * height

        for ty in range(height, 0, -4):
            for tx in range(0, width, 4):
                color0 = TPC._rgba565_to_rgb888(dxt_reader.read_int16())
                color1 = TPC._rgba565_to_rgb888(dxt_reader.read_int16())
                dxt_pixels = dxt_reader.read_uint32(big=True)

                color_code = []
                color_code.extend([color0, color1])
                if color0 > color1:
                    color_code.append(TPC._interpolate(0.3333333, color0, color1))
                    color_code.append(TPC._interpolate(0.6666666, color0, color1))
                else:
                    color_code.append(TPC._interpolate(0.5555555, color0, color1))
                    color_code.append(0xFF000000)

                for y in range(4):
                    for x in range(4):
                        pixel_code = dxt_pixels & 3
                        dxt_pixels >>= 2
                        pixels[(ty - 4 + y) * width + (tx + x)] = color_code[pixel_code] + 0xFF000000

        new_data = bytearray()
        for pixel in pixels:
            new_data.append((pixel & 0x00FF0000) >> 16)
            new_data.append((pixel & 0x0000FF00) >> 8)
            new_data.append((pixel & 0x000000FF))
            new_data.append(255)

        return new_data

    @staticmethod
    def _rgb_to_rgba(data: bytes, width: int, height: int) -> bytearray:
        new_data = bytearray()
        rgb_reader = BinaryReader.from_bytes(data)

        for y in range(height):
            for x in range(width):
                new_data.extend([rgb_reader.read_uint8(), rgb_reader.read_uint8(), rgb_reader.read_uint8(), 255])

        return new_data

    @staticmethod
    def _grey_to_rgba(data: bytes, width: int, height: int) -> bytearray:
        new_data = bytearray()
        rgb_reader = BinaryReader.from_bytes(data)

        for y in range(height):
            for x in range(width):
                brightness = rgb_reader.read_uint8()
                new_data.extend([brightness, brightness, brightness, 255])

        return new_data

    @staticmethod
    def _rgba_to_rgb(data: bytes, width: int, height: int) -> bytearray:
        new_data = bytearray()
        rgb_reader = BinaryReader.from_bytes(data)

        for y in range(height):
            for x in range(width):
                new_data.extend([rgb_reader.read_uint8(), rgb_reader.read_uint8(), rgb_reader.read_uint8()])
                rgb_reader.skip(1)

        return new_data

    @staticmethod
    def _rgba_to_grey(data: bytes, width: int, height: int) -> bytearray:
        new_data = bytearray()
        rgb_reader = BinaryReader.from_bytes(data)

        for y in range(height):
            for x in range(width):
                r = rgb_reader.read_uint8()
                g = rgb_reader.read_uint8()
                b = rgb_reader.read_uint8()
                a = rgb_reader.read_uint8()
                highest = r
                if g > highest:
                    highest = g
                if b > highest:
                    highest = b
                new_data.extend([highest])

        return new_data

    @staticmethod
    def _rgba565_to_rgb888(color: int) -> int:
        blue = (color & 0x1F)
        green = (color >> 5) & 0x3F
        red = (color >> 11) & 0x1F
        return (blue << 3) + (green << 10) + (red << 19)

    @staticmethod
    def _interpolate(weight: float, color0: int, color1: int) -> int:
        color0_blue = color0 & 255
        color0_greed = (color0 >> 8) & 255
        color0_red = (color0 >> 16) & 255

        color1_blue = color1 & 255
        color1_greed = (color1 >> 8) & 255
        color1_red = (color1 >> 16) & 255

        blue = int(((1.0 - weight) * color0_blue) + (weight * color1_blue))
        green = int(((1.0 - weight) * color0_greed) + (weight * color1_greed))
        red = int(((1.0 - weight) * color0_red) + (weight * color1_red))

        return (blue) + (green << 8) + (red << 16)

    @staticmethod
    def _integer48(bytes48: bytes) -> int:
        return bytes48[0] + (bytes48[1] << 8) + (bytes48[2] << 16) + (bytes48[3] << 24) + (bytes48[4] << 32) + (
                bytes48[5] << 40)


class TPCTextureFormat(IntEnum):
    Invalid = -1
    Greyscale = 0
    RGB = 1
    RGBA = 2
    DXT1 = 3
    DXT5 = 4
