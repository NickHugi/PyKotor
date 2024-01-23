"""This module handles classes relating to editing TPC files."""

from __future__ import annotations

import itertools
from enum import IntEnum
from typing import NamedTuple

from pykotor.common.stream import BinaryReader
from pykotor.resource.type import ResourceType


class TPCGetResult(NamedTuple):
    width: int
    height: int
    texture_format: TPCTextureFormat
    data: bytes | None


class TPCConvertResult(NamedTuple):
    width: int
    height: int
    data: bytes | None

class TPC:
    """Represents a TPC file.

    Attributes
    ----------
        txi: Stores additional information regarding the texture.
    """

    BINARY_TYPE = ResourceType.TPC

    def __init__(
        self,
    ):
        self._texture_format: TPCTextureFormat = TPCTextureFormat.RGB
        self._mipmaps: list[bytes] = [bytes(0 for _ in range(4 * 4 * 3))]
        self._width: int = 4
        self._height: int = 4
        self.txi: str = ""

        # TODO: cube maps

    def mipmap_count(
        self,
    ) -> int:
        """Returns the number of mipmaps.

        Returns
        -------
            The number of mipmaps.
        """
        return len(self._mipmaps)

    def format(
        self,
    ) -> TPCTextureFormat:
        """Returns the format of the stored texture.

        Returns
        -------
            The format of the stored texture.
        """
        return self._texture_format

    def dimensions(
        self,
    ) -> tuple[int, int]:
        """Returns the width and height of the largest mipmap.

        Returns
        -------
            A tuple containing [width, height].
        """
        return self._width, self._height

    def get(
        self,
        mipmap: int = 0,
    ) -> TPCGetResult:
        """Returns a tuple containing the width, height, texture format, and data of the specified mipmap.

        Args:
        ----
            mipmap: The index of the mipmap.

        Returns:
        -------
            A tuple equal to (width, height, texture format, data).
        """
        width, height = self._mipmap_size(mipmap)
        return TPCGetResult(width, height, self._texture_format, self._mipmaps[mipmap])

    def convert(
        self,
        convert_format: TPCTextureFormat,
        mipmap: int = 0,
    ) -> TPCConvertResult:
        """Returns a tuple containing the width, height and data of the specified mipmap where the data returned is in the texture format specified.

        Args:
        ----
            convert_format: The format the texture data should be converted to.
            mipmap: The index of the mipmap.

        Returns:
        -------
            A tuple equal to (width, height, data)
        """
        width, height = self._mipmap_size(mipmap)
        raw_data: bytes = self._mipmaps[mipmap]
        data = bytearray()

        if convert_format in [TPCTextureFormat.DXT1, TPCTextureFormat.DXT5]:
            raise NotImplementedError

        if convert_format == TPCTextureFormat.Greyscale:
            raise NotImplementedError

        data: bytearray
        if convert_format == TPCTextureFormat.RGBA:
            if self._texture_format == TPCTextureFormat.DXT5:
                data = TPC._dxt5_to_rgba(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.DXT1:
                data = TPC._dxt1_to_rgba(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.RGBA:
                data = bytearray(raw_data)
            elif self._texture_format == TPCTextureFormat.RGB:
                data = TPC._rgb_to_rgba(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.Greyscale:
                data = TPC._grey_to_rgba(raw_data, width, height)

        if convert_format == TPCTextureFormat.RGB:
            if self._texture_format == TPCTextureFormat.DXT5:
                data = TPC._dxt5_to_rgb(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.DXT1:
                data = TPC._dxt1_to_rgb(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.RGBA:
                data = TPC._rgba_to_rgb(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.RGB:
                data = bytearray(raw_data)
            elif self._texture_format == TPCTextureFormat.Greyscale:
                data = TPC._grey_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_rgb(data, width, height)

        return TPCConvertResult(width, height, data)

    def set_single(
        self,
        width: int,
        height: int,
        data: bytes,
        texture_format: TPCTextureFormat,
    ):
        """Sets the texture data but only for a single mipmap.

        Args:
        ----
            width: The new width.
            height: The new height.
            data: The new texture data.
            texture_format: The texture format.
        """
        self.set_data(width, height, [data], texture_format)

    def set_data(
        self,
        width: int,
        height: int,
        mipmaps: list[bytes],
        texture_format: TPCTextureFormat,
    ):
        """Sets the new texture data.

        Args:
        ----
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

    def is_compressed(
        self,
    ) -> bool:
        return self._texture_format in [TPCTextureFormat.DXT1, TPCTextureFormat.DXT5]

    def _mipmap_size(
        self,
        mipmap: int,
    ) -> tuple[int, int]:
        """Returns the size of the specified mipmap.

        Args:
        ----
            mipmap: The index of the mipmap.

        Raises:
        ------
            IndexError: The index for the mipmap is out of range.

        Returns:
        -------
            A tuple equal to (width, height).
        """
        if 0 > mipmap >= len(self._mipmaps):
            msg = "The index for the mipmap is out of range."
            raise IndexError(msg)

        width = self._width
        height = self._height
        for _ in range(mipmap):
            width >>= 1
            height >>= 1
        return width, height

    # region Convert to RGBA
    @staticmethod
    def _dxt5_to_rgba(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        """Converts DXT5 compressed texture data to RGBA bytes.

        Args:
        ----
            data: bytes - The compressed DXT5 texture data
            width: int - Width of the texture
            height: int - Height of the texture

        Returns:
        -------
            bytearray - Uncompressed RGBA pixel data

        Processing Logic:
        ----------------
            - Reads the compressed DXT5 data using a BinaryReader
            - Loops through each 4x4 block
                - Decodes the alpha and color data
                - Decompresses the pixel colors and alphas
                - Writes the RGBA values to the output byte array
            - Returns the uncompressed pixel data.
        """
        dxt_reader: BinaryReader = BinaryReader.from_bytes(data)
        new_data = bytearray(width * height * 4)

        for ty, tx in itertools.product(range(4, height + 4, 4), range(0, width, 4)):
            alpha0 = dxt_reader.read_uint8()
            alpha1 = dxt_reader.read_uint8()
            dxt_alpha = TPC._integer48(dxt_reader.read_bytes(6))

            x = dxt_reader.read_int16()
            y = dxt_reader.read_int16()
            c0 = TPC._rgba565_to_rgb(x)
            c1 = TPC._rgba565_to_rgb(y)
            dxt_pixels = dxt_reader.read_uint32(big=True)

            cc = [c0, c1]
            if TPC._rgba565_to_rgb888(x) > TPC._rgba565_to_rgb888(y):
                cc.extend(
                    [
                        TPC._interpolate_rgb(0.3333333, c0, c1),
                        TPC._interpolate_rgb(0.6666666, c0, c1),
                    ],
                )
            else:
                cc.extend([TPC._interpolate_rgb(0.5555555, c0, c1), (0, 0, 0)])

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
                alpha_code.extend(
                    (int((1.0 * alpha0 + 4.0 * alpha1 + 2) / 5), 0, 255),
                )
            for y in [3, 2, 1, 0]:
                for x in [0, 1, 2, 3]:
                    pixelc_code = dxt_pixels & 3
                    dxt_pixels >>= 2

                    a = alpha_code[(dxt_alpha >> (3 * (4 * y + x))) & 7]

                    index = ((ty - 4 + y) * width + (tx + x)) * 4
                    new_data[index + 0] = cc[pixelc_code][0]
                    new_data[index + 1] = cc[pixelc_code][1]
                    new_data[index + 2] = cc[pixelc_code][2]
                    new_data[index + 3] = a

        return new_data

    @staticmethod
    def _dxt1_to_rgba(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        """Converts DXT1 compressed texture data to RGBA format.

        Args:
        ----
            data: bytes - The compressed DXT1 texture data
            width: int - Width of the texture
            height: int - Height of the texture

        Returns:
        -------
            bytearray - Uncompressed RGBA texture data

        Processing Logic:
        ----------------
            - Parse the DXT1 data using a BinaryReader
            - Iterate over 4x4 pixel blocks
            - Decode the color values and interpolation data
            - Extract and interpolate the RGBA values for each pixel
            - Write the uncompressed RGBA values to a bytearray.
        """
        dxt_reader: BinaryReader = BinaryReader.from_bytes(data)
        new_data = bytearray(width * height * 4)

        for ty, tx in itertools.product(range(4, height + 4, 4), range(0, width, 4)):
            x = dxt_reader.read_int16()
            y = dxt_reader.read_int16()
            c0: tuple[int, int, int] = TPC._rgba565_to_rgb(x)
            c1: tuple[int, int, int] = TPC._rgba565_to_rgb(y)
            dxt_pixels = dxt_reader.read_uint32(big=True)

            cc: list[tuple[int, int, int]] = [c0, c1]
            if TPC._rgba565_to_rgb888(x) > TPC._rgba565_to_rgb888(y):
                cc.extend(
                    [
                        TPC._interpolate_rgb(0.3333333, c0, c1),
                        TPC._interpolate_rgb(0.6666666, c0, c1),
                    ],
                )
            else:
                cc.extend([TPC._interpolate_rgb(0.5555555, c0, c1), (0, 0, 0)])

            for y in [3, 2, 1, 0]:
                for x in [0, 1, 2, 3]:
                    pixelc_code = dxt_pixels & 3
                    dxt_pixels >>= 2

                    index = ((ty - 4 + y) * width + (tx + x)) * 4
                    new_data[index + 0] = cc[pixelc_code][0]
                    new_data[index + 1] = cc[pixelc_code][1]
                    new_data[index + 2] = cc[pixelc_code][2]
                    new_data[index + 3] = 255

        return new_data

    @staticmethod
    def _rgb_to_rgba(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        new_data = bytearray()
        rgb_reader = BinaryReader.from_bytes(data)

        for _ty, _x in itertools.product(range(4, height + 4, 4), range(width)):
            new_data.extend(
                [
                    rgb_reader.read_uint8(),
                    rgb_reader.read_uint8(),
                    rgb_reader.read_uint8(),
                    255,
                ],
            )

        return new_data

    @staticmethod
    def _grey_to_rgba(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        new_data = bytearray()
        rgb_reader = BinaryReader.from_bytes(data)

        for _y, _x in itertools.product(range(height), range(width)):
            brightness = rgb_reader.read_uint8()
            new_data.extend([brightness, brightness, brightness, 255])

        return new_data

    # endregion

    # region Convert to Grey
    @staticmethod
    def _rgba_to_grey(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        new_data = bytearray()
        rgb_reader = BinaryReader.from_bytes(data)

        for _y, _x in itertools.product(range(height), range(width)):
            r = rgb_reader.read_uint8()
            g = rgb_reader.read_uint8()
            b = rgb_reader.read_uint8()
            rgb_reader.read_uint8()
            highest = r
            if g > highest:
                highest = g
            if b > highest:
                highest = b
            new_data.extend([highest])

        return new_data

    # endregion

    # region Convert to RGB
    @staticmethod
    def _dxt5_to_rgb(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        dxt_reader = BinaryReader.from_bytes(data)
        new_data = bytearray(width * height * 3)

        for ty, tx in itertools.product(range(4, height + 4, 4), range(0, width, 4)):
            dxt_reader.skip(8)

            x = dxt_reader.read_int16()
            y = dxt_reader.read_int16()
            c0: tuple[int, int, int] = TPC._rgba565_to_rgb(x)
            c1: tuple[int, int, int] = TPC._rgba565_to_rgb(y)
            dxt_pixels = dxt_reader.read_uint32(big=True)

            cc: list[tuple[int, int, int]] = [c0, c1]
            if TPC._rgba565_to_rgb888(x) > TPC._rgba565_to_rgb888(y):
                cc.extend(
                    [
                        TPC._interpolate_rgb(0.3333333, c0, c1),
                        TPC._interpolate_rgb(0.6666666, c0, c1),
                    ],
                )
            else:
                cc.extend([TPC._interpolate_rgb(0.5555555, c0, c1), (0, 0, 0)])

            for y in [3, 2, 1, 0]:
                for x in [0, 1, 2, 3]:
                    pixelc_code = dxt_pixels & 3
                    dxt_pixels >>= 2

                    index = ((ty - 4 + y) * width + (tx + x)) * 3
                    new_data[index + 0] = cc[pixelc_code][0]
                    new_data[index + 1] = cc[pixelc_code][1]
                    new_data[index + 2] = cc[pixelc_code][2]

        return new_data

    @staticmethod
    def _dxt1_to_rgb(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        dxt_reader = BinaryReader.from_bytes(data)
        new_data = bytearray(width * height * 3)

        for ty, tx in itertools.product(range(4, height + 4, 4), range(0, width, 4)):
            x = dxt_reader.read_int16()
            y = dxt_reader.read_int16()
            c0: tuple[int, int, int] = TPC._rgba565_to_rgb(x)
            c1: tuple[int, int, int] = TPC._rgba565_to_rgb(y)
            dxt_pixels = dxt_reader.read_uint32(big=True)

            cc: list[tuple[int, int, int]] = [c0, c1]
            if TPC._rgba565_to_rgb888(x) > TPC._rgba565_to_rgb888(y):
                cc.extend(
                    [
                        TPC._interpolate_rgb(0.3333333, c0, c1),
                        TPC._interpolate_rgb(0.6666666, c0, c1),
                    ],
                )
            else:
                cc.extend([TPC._interpolate_rgb(0.5555555, c0, c1), (0, 0, 0)])

            for y in [3, 2, 1, 0]:
                for x in [0, 1, 2, 3]:
                    pixelc_code = dxt_pixels & 3
                    dxt_pixels >>= 2

                    index = ((ty - 4 + y) * width + (tx + x)) * 3
                    new_data[index + 0] = cc[pixelc_code][0]
                    new_data[index + 1] = cc[pixelc_code][1]
                    new_data[index + 2] = cc[pixelc_code][2]

        return new_data

    @staticmethod
    def _rgba_to_rgb(
        data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        new_data = bytearray()
        rgb_reader: BinaryReader = BinaryReader.from_bytes(data)

        for _y, _x in itertools.product(range(height), range(width)):
            new_data.extend(
                [
                    rgb_reader.read_uint8(),
                    rgb_reader.read_uint8(),
                    rgb_reader.read_uint8(),
                ],
            )
            rgb_reader.skip(1)

        return new_data

    # endregion

    @staticmethod
    def _rgba565_to_rgb888(
        color: int,
    ) -> int:
        blue = color & 0x1F
        green = (color >> 5) & 0x3F
        red = (color >> 11) & 0x1F
        return (blue << 3) + (green << 10) + (red << 19)

    @staticmethod
    def _interpolate(
        weight: float,
        color0: int,
        color1: int,
    ) -> int:
        """Interpolates between two colors.

        Args:
        ----
            weight: float - Blend factor between 0-1
            color0: int - First color
            color1: int - Second color

        Returns:
        -------
            int - Interpolated color

        Processing Logic:
        ----------------
            - Extract blue, green, red channels from each color
            - Interpolate each channel value based on weight
            - Reassemble and return new color.
        """
        color0_blue = color0 & 255
        color0_greed = (color0 >> 8) & 255
        color0_red = (color0 >> 16) & 255

        color1_blue = color1 & 255
        color1_greed = (color1 >> 8) & 255
        color1_red = (color1 >> 16) & 255

        blue = int(((1.0 - weight) * color0_blue) + (weight * color1_blue))
        green = int(((1.0 - weight) * color0_greed) + (weight * color1_greed))
        red = int(((1.0 - weight) * color0_red) + (weight * color1_red))

        return blue + (green << 8) + (red << 16)

    @staticmethod
    def _rgba565_to_rgb(
        color: int,
    ):
        """Converts a 16-bit 565 RGB color to a tuple of 8-bit RGB values.

        Args:
        ----
            color: 16-bit 565 RGB color value

        Returns:
        -------
            tuple: tuple of (red, green, blue) color component values

        Processing Logic:
        ----------------
            - Extracts the blue component from the lowest 5 bits
            - Extracts the green component from bits 5-10
            - Extracts the red component from bits 11-15
            - Left shifts the components to scale from 5 or 6 bits to 8 bits.
        """
        blue = color & 0x1F
        green = (color >> 5) & 0x3F
        red = (color >> 11) & 0x1F
        return red << 3, green << 2, blue << 3

    @staticmethod
    def _interpolate_rgb(
        weight: float,
        color0,
        color1,
    ):
        color0_blue = color0[2]
        color0_greed = color0[1]
        color0_red = color0[0]

        color1_blue = color1[2]
        color1_greed = color1[1]
        color1_red = color1[0]

        blue = int(((1.0 - weight) * color0_blue) + (weight * color1_blue))
        green = int(((1.0 - weight) * color0_greed) + (weight * color1_greed))
        red = int(((1.0 - weight) * color0_red) + (weight * color1_red))

        return red, green, blue

    @staticmethod
    def _integer48(
        bytes48: bytes,
    ) -> int:
        return bytes48[0] + (bytes48[1] << 8) + (bytes48[2] << 16) + (bytes48[3] << 24) + (bytes48[4] << 32) + (bytes48[5] << 40)


class TPCTextureFormat(IntEnum):
    Invalid = -1
    Greyscale = 0
    RGB = 1
    RGBA = 2
    DXT1 = 3
    DXT5 = 4
