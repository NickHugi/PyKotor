"""This module handles classes relating to editing TPC files."""

from __future__ import annotations

import itertools

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc.bgra_conversions import bgra_to_grey, bgra_to_rgb, bgra_to_rgba, rgba_to_bgra  # noqa: F401
from pykotor.resource.formats.tpc.dxt_conversions import dxt1_to_rgb, dxt5_to_rgba, rgb_to_dxt1, rgba_to_dxt5  # noqa: F401
from pykotor.resource.formats.tpc.greyscale_conversions import grey_to_rgb, grey_to_rgba, rgb_to_grey, rgba_to_grey  # noqa: F401
from pykotor.resource.formats.tpc.rgb_conversions import rgb_to_rgba, rgba_to_rgb  # noqa: F401
from pykotor.resource.formats.txi.txi_data import TXI
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from PIL import Image
    from qtpy.QtGui import QIcon, QImage, QPixmap
    from typing_extensions import Literal


@dataclass
class TPCMipmap:
    data: bytearray
    width: int
    height: int

    @property
    def size(self) -> int:
        return len(self.data)


class TPCGetResult(NamedTuple):
    width: int
    height: int
    texture_format: TPCTextureFormat
    data: bytearray

    def to_qicon(self) -> QIcon:
        from qtpy.QtGui import QIcon, QImage, QPixmap, QTransform

        width, height, tpc_format, img_bytes = self
        image = QImage(bytes(img_bytes), width, height, tpc_format.to_qimage_format())
        pixmap: QPixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
        return QIcon(pixmap)

    def to_qimage(self) -> QImage:
        from qtpy.QtGui import QImage

        width, height, tpc_format, img_bytes = self
        return QImage(bytes(img_bytes), width, height, tpc_format.to_qimage_format())

    def to_pil_image(self) -> Image.Image:
        from PIL import Image

        width, height, tpc_format, img_bytes = self
        return Image.frombytes(tpc_format.to_pil_mode(), (width, height), img_bytes)


class TPCConvertResult(NamedTuple):
    width: int
    height: int
    data: bytearray


class TPC:
    """Represents a TPC file.

    Attributes:
    ----------
        txi (str): Stores additional information regarding the texture.
    """

    BINARY_TYPE = ResourceType.TPC

    def __init__(
        self,
    ):
        self._txi: TXI = TXI()
        self._texture_format: TPCTextureFormat = TPCTextureFormat.RGB
        self.mipmaps: list[TPCMipmap] = []
        self.is_animated: bool = False
        self.layer_count: int = 1
        self.is_cube_map: bool = False

        from pykotor.resource.formats.tpc.io_tga import _DataTypes

        self.original_datatype_code: _DataTypes = _DataTypes.NO_IMAGE_DATA

    @property
    def txi(self) -> str:
        return str(self._txi)

    @txi.setter
    def txi(self, value: str):
        self._txi = TXI(value)

    def set_single(
        self,
        width: int,
        height: int,
        data: bytes,
        texture_format: TPCTextureFormat,
    ):
        self.set_data([data], texture_format, width, height)

    def set_data(
        self,
        mipmaps: list[bytes | bytearray],
        texture_format: TPCTextureFormat | None = None,
        width: int | None = None,
        height: int | None = None,
    ):
        # Perform sanity check on mipmap data sizes
        if not mipmaps:
            self.mipmaps.clear()
            return
        texture_format = self._texture_format if texture_format is None else texture_format

        mm_size: int = len(mipmaps[0]) // 4
        mm_width: int = mm_size if width is None else width
        mm_height: int = mm_size if height is None else height
        for i, mipmap in enumerate(mipmaps):
            mm_data: bytes | bytearray = mipmap if isinstance(mipmap, bytearray) else bytearray(mipmap)
            expected_size: int = texture_format.get_size(mm_width, mm_height)
            if len(mm_data) != expected_size:
                raise ValueError(f"Mipmap {i} has incorrect size (out of {len(mipmaps)} mipmaps total)." f" Expected {expected_size} bytes, got {len(mm_data)} bytes.")
            mm = TPCMipmap(mm_data, mm_width, mm_height)
            if len(self.mipmaps) <= i:
                self.mipmaps.append(mm)
            else:
                self.mipmaps[i] = mm
            if mm_width <= 1 or mm_height <= 1:
                break
            mm_width = max(1, mm_width // 2)
            mm_height = max(1, mm_height // 2)

    def mipmap_count(
        self,
    ) -> int:
        """Returns the number of mipmaps.

        Returns:
        -------
            The number of mipmaps.
        """
        return len(self.mipmaps)

    def format(
        self,
    ) -> TPCTextureFormat:
        """Returns the format of the stored texture.

        Returns:
        -------
            The format of the stored texture.
        """
        return self._texture_format

    def dimensions(
        self,
    ) -> tuple[int, int]:
        """Returns the width and height of the largest mipmap.

        Returns:
        -------
            A tuple containing [width, height].
        """
        return self.mipmaps[0].width, self.mipmaps[0].height

    def mipmap_size(self, mipmap: int) -> tuple[int, int]:
        if not 0 <= mipmap < len(self.mipmaps):
            raise IndexError("Mipmap index out of range")
        return self.mipmaps[mipmap].width, self.mipmaps[mipmap].height

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
        width, height = self.mipmap_size(mipmap)
        return TPCGetResult(width, height, self._texture_format, self.mipmaps[mipmap].data)

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
        raw_data: bytes = bytes(self.mipmaps[mipmap].data)
        if self._texture_format == convert_format and not y_flip:  # Is conversion needed?
            return TPCConvertResult(width, height, bytearray(raw_data))

        data: bytearray = bytearray(raw_data)
        if convert_format == TPCTextureFormat.Greyscale:
            if self._texture_format == TPCTextureFormat.DXT5:
                rgba_data = TPC._dxt5_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_grey(rgba_data, width, height)
            elif self._texture_format == TPCTextureFormat.DXT1:
                rgba_data = TPC._dxt1_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_grey(rgba_data, width, height)
            elif self._texture_format == TPCTextureFormat.RGBA:
                data = TPC._rgba_to_grey(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.RGB:
                rgba_data = TPC._rgb_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_grey(rgba_data, width, height)

        if convert_format == TPCTextureFormat.RGBA:
            if self._texture_format == TPCTextureFormat.DXT5:
                data = TPC._dxt5_to_rgba(raw_data, width, height)
            elif self._texture_format == TPCTextureFormat.DXT1:
                data = TPC._dxt1_to_rgba(raw_data, width, height)
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
            elif self._texture_format == TPCTextureFormat.Greyscale:
                rgba_data = TPC._grey_to_rgba(raw_data, width, height)
                data = TPC._rgba_to_rgb(rgba_data, width, height)

        return TPCConvertResult(width, height, data)

    def get_bytes_per_pixel(self):
        bytes_per_pixel = 0
        if self._texture_format == TPCTextureFormat.Greyscale:
            bytes_per_pixel = 1
        elif self._texture_format in {TPCTextureFormat.RGB, TPCTextureFormat.RGBA}:
            bytes_per_pixel = 4 if self._texture_format == TPCTextureFormat.RGBA else 3
        return bytes_per_pixel

    @staticmethod
    def flip_image_data(data: bytes | bytearray, width: int, height: int, bytes_per_pixel: int) -> bytes:
        """Flip the image data vertically."""
        flipped_data = bytearray(len(data))
        row_length = width * bytes_per_pixel

        for row in range(height):
            source_start = row * row_length
            source_end = source_start + row_length
            dest_start = (height - 1 - row) * row_length
            flipped_data[dest_start : dest_start + row_length] = data[source_start:source_end]

        return bytes(flipped_data)

    def is_compressed(
        self,
    ) -> bool:
        return self._texture_format in {TPCTextureFormat.DXT1, TPCTextureFormat.DXT5}

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
        if not self.mipmaps or 0 > mipmap >= len(self.mipmaps):
            msg = "The index for the mipmap is out of range."
            raise IndexError(msg)
        mm = self.mipmaps[mipmap]
        return mm.width, mm.height

    @staticmethod
    def _calculate_color_indices(
        rgba_block: list[tuple[int, int, int, int]],
        c0: tuple[int, int, int],
        c1: tuple[int, int, int],
    ) -> int:
        """Calculate 2-bit indices for each pixel in a 4x4 block."""
        indices: int = 0
        for i, pixel in enumerate(rgba_block):
            r, g, b, _a = pixel
            dr0, dg0, db0 = r - c0[0], g - c0[1], b - c0[2]
            dr1, dg1, db1 = r - c1[0], g - c1[1], b - c1[2]
            distance0 = dr0**2 + dg0**2 + db0**2
            distance1 = dr1**2 + dg1**2 + db1**2
            index = 0 if distance0 < distance1 else 1
            indices |= index << (i * 2)
        return indices

    @staticmethod
    def _select_representative_colors(rgba_block: list[tuple[int, int, int, int]]) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        """Select representative colors for DXT1 compression."""
        colors = sorted(rgba_block, key=lambda x: (x[0] << 16) + (x[1] << 8) + x[2])
        return colors[0][:3], colors[-1][:3]

    @staticmethod
    def rgba_to_dxt1(
        rgba_data: bytes,
        width: int,
        height: int,
    ) -> bytearray:
        """Convert RGBA data to DXT1 compressed format."""
        compressed_data = bytearray()
        for y, x in itertools.product(range(0, height, 4), range(0, width, 4)):
            rgba_block: list[tuple[int, int, int, int]] = [
                cast(Tuple[int, int, int, int], tuple(rgba_data[i : i + 4]))
                for dy in range(4)
                for dx in range(4)
                for i in range((y * width + x + dy * width + dx) * 4, (y * width + x + dy * width + dx) * 4 + 4, 4)
            ]
            c0, c1 = TPC._select_representative_colors(rgba_block)
            c0_565 = TPC._rgb_to_rgba565(c0)
            c1_565 = TPC._rgb_to_rgba565(c1)
            indices = TPC._calculate_color_indices(rgba_block, c0, c1)
            compressed_data += c0_565.to_bytes(2, byteorder="little")
            compressed_data += c1_565.to_bytes(2, byteorder="little")
            compressed_data += indices.to_bytes(4, byteorder="little")
        return compressed_data

    # region Convert to RGBA
    @staticmethod
    def _dxt5_to_rgba(
        data: bytes | bytearray,
        width: int,
        height: int,
    ) -> bytearray:  # sourcery skip: merge-list-appends-into-extend
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
                cc.extend(
                    [
                        TPC._interpolate_rgb(0.5555555, c0, c1),
                        (0, 0, 0),
                    ]
                )

            alpha_code = [alpha0, alpha1]
            if alpha0 > alpha1:
                alpha_code.extend(
                    (
                        int((6.0 * alpha0 + 1.0 * alpha1 + 3) / 7),
                        int((5.0 * alpha0 + 2.0 * alpha1 + 3) / 7),
                        int((4.0 * alpha0 + 3.0 * alpha1 + 3) / 7),
                        int((3.0 * alpha0 + 4.0 * alpha1 + 3) / 7),
                        int((2.0 * alpha0 + 5.0 * alpha1 + 3) / 7),
                        int((1.0 * alpha0 + 6.0 * alpha1 + 3) / 7),
                    )
                )
            else:
                alpha_code.extend(
                    (
                        int((4.0 * alpha0 + 1.0 * alpha1 + 1) / 5),
                        int((3.0 * alpha0 + 2.0 * alpha1 + 2) / 5),
                        int((2.0 * alpha0 + 3.0 * alpha1 + 2) / 5),
                        int((1.0 * alpha0 + 4.0 * alpha1 + 2) / 5),
                        0,
                        255,
                    )
                )
            for y in (3, 2, 1, 0):
                for x in (0, 1, 2, 3):
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
        data: bytes | bytearray,
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

            for y in (3, 2, 1, 0):
                for x in (0, 1, 2, 3):
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
        data: bytes | bytearray,
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
        data: bytes | bytearray,
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
        data: bytes | bytearray,
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
            highest = max(g, highest)
            highest = max(b, highest)
            new_data.extend([highest])

        return new_data

    # endregion

    # region Convert to RGB
    @staticmethod
    def _dxt5_to_rgb(
        data: bytes | bytearray,
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

            for y in (3, 2, 1, 0):
                for x in (0, 1, 2, 3):
                    pixelc_code = dxt_pixels & 3
                    dxt_pixels >>= 2

                    index = ((ty - 4 + y) * width + (tx + x)) * 3
                    new_data[index + 0] = cc[pixelc_code][0]
                    new_data[index + 1] = cc[pixelc_code][1]
                    new_data[index + 2] = cc[pixelc_code][2]

        return new_data

    @staticmethod
    def _dxt1_to_rgb(
        data: bytes | bytearray,
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

            for y in (3, 2, 1, 0):
                for x in (0, 1, 2, 3):
                    pixelc_code = dxt_pixels & 3
                    dxt_pixels >>= 2

                    index = ((ty - 4 + y) * width + (tx + x)) * 3
                    new_data[index + 0] = cc[pixelc_code][0]
                    new_data[index + 1] = cc[pixelc_code][1]
                    new_data[index + 2] = cc[pixelc_code][2]

        return new_data

    @staticmethod
    def _rgba_to_rgb(
        data: bytes | bytearray,
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
    def _rgb_to_rgba565(rgb: tuple[int, int, int]) -> int:
        """Convert an RGB tuple to 5:6:5 bit RGB format."""
        r, g, b = rgb
        return (r >> 3) << 11 | (g >> 2) << 5 | b >> 3

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
    ) -> tuple[int, int, int]:
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
        color0: tuple[int, int, int],
        color1: tuple[int, int, int],
    ) -> tuple[int, int, int]:
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

    def rotate90(  # noqa: C901
        self,
        times: int,
    ) -> None:
        """Rotate all mipmaps in 90° steps, clock-wise for positive times, counter-clockwise for negative times."""
        times = times % 4  # Normalize to -3 to 3 range
        if times == 0:
            return  # No rotation needed

        bytes_per_pixel: Literal[1, 4, 3, 0] = self._texture_format.bytes_per_pixel()
        if bytes_per_pixel <= 0 or not self.mipmaps or self._texture_format is TPCTextureFormat.Invalid:
            return

        for mipmap in self.mipmaps:
            width, height = mipmap.width, mipmap.height
            if width <= 0 or height <= 0:
                continue

            data: bytearray = mipmap.data
            new_data = bytearray(len(data))

            dst_idx: int = 0
            for y in range(height):
                for x in range(width):
                    src_idx: int = (y * width + x) * bytes_per_pixel
                    if times in {1, -3}:
                        dst_idx = ((width - 1 - x) * height + y) * bytes_per_pixel
                    elif times in {2, -2}:
                        dst_idx = ((height - 1 - y) * width + (width - 1 - x)) * bytes_per_pixel
                    elif times in {3, -1}:
                        dst_idx = (x * height + (height - 1 - y)) * bytes_per_pixel

                    for i in range(bytes_per_pixel):
                        new_data[dst_idx + i] = data[src_idx + i]

            mipmap.data = new_data
            if abs(times) % 2 != 0:
                mipmap.width, mipmap.height = mipmap.height, mipmap.width

    def flip_vertically(self) -> None:
        """Flip all mipmaps vertically."""
        bytes_per_pixel: Literal[1, 4, 3, 0] = self._texture_format.bytes_per_pixel()
        if bytes_per_pixel <= 0 or not self.mipmaps or self._texture_format is TPCTextureFormat.Invalid:
            return

        for mipmap in self.mipmaps:
            mm_width, mm_height = mipmap.width, mipmap.height
            if mm_width <= 0 or mm_height <= 0:
                continue

            pitch: int = bytes_per_pixel * mm_width
            data: bytearray = mipmap.data

            for y in range(mm_height // 2):
                top_row: int = y * pitch
                bottom_row: int = (mm_height - 1 - y) * pitch

                # Swap rows
                data[top_row : top_row + pitch], data[bottom_row : bottom_row + pitch] = (
                    data[bottom_row : bottom_row + pitch],
                    data[top_row : top_row + pitch],
                )

    def flip_horizontally(self) -> None:
        """Flip all mipmaps horizontally."""
        bytes_per_pixel: Literal[1, 4, 3, 0] = self._texture_format.bytes_per_pixel()
        if bytes_per_pixel <= 0 or not self.mipmaps or self._texture_format is TPCTextureFormat.Invalid:
            return

        for mipmap in self.mipmaps:
            mm_width, mm_height = mipmap.width, mipmap.height
            if mm_width <= 0 or mm_height <= 0:
                continue

            data: bytearray = mipmap.data

            for y in range(mm_height):
                row_start = y * mm_width * bytes_per_pixel
                for x in range(mm_width // 2):
                    left_pixel: int = row_start + x * bytes_per_pixel
                    right_pixel: int = row_start + (mm_width - 1 - x) * bytes_per_pixel

                    # Swap pixels
                    for i in range(bytes_per_pixel):
                        data[left_pixel + i], data[right_pixel + i] = (
                            data[right_pixel + i],
                            data[left_pixel + i],
                        )


class TPCTextureFormat(IntEnum):
    Invalid = -1
    Greyscale = 0
    DXT1 = 1
    DXT3 = 2
    DXT5 = 3
    RGB = 4
    RGBA = 5
    BGRA = 6
    BGR = 7

    def bytes_per_pixel(self) -> Literal[1, 4, 3, 0]:
        bytes_per_pixel = 0
        if self is TPCTextureFormat.Greyscale:
            bytes_per_pixel = 1
        elif self in (TPCTextureFormat.RGB, TPCTextureFormat.BGR):
            bytes_per_pixel = 3
        elif self in (TPCTextureFormat.RGBA, TPCTextureFormat.BGRA):
            bytes_per_pixel = 4
        return bytes_per_pixel

    def is_dxt(self) -> bool:
        return self in (
            TPCTextureFormat.DXT1,
            TPCTextureFormat.DXT3,
            TPCTextureFormat.DXT5,
        )

    def min_size(self) -> Literal[1, 3, 4, 8, 16, 0]:
        if self is TPCTextureFormat.Greyscale:
            return 1
        if self in (TPCTextureFormat.RGB, TPCTextureFormat.BGR):
            return 3
        if self in (TPCTextureFormat.RGBA, TPCTextureFormat.BGRA):
            return 4
        if self is TPCTextureFormat.DXT1:
            return 8
        if self is TPCTextureFormat.DXT5:
            return 16
        return 0

    def to_qimage_format(self) -> QImage.Format:
        """Convert this texture format to a QImage format."""
        from qtpy.QtGui import QImage

        if self is TPCTextureFormat.Greyscale:
            return QImage.Format.Format_Grayscale8
        if self is TPCTextureFormat.RGB:
            return QImage.Format.Format_RGB888
        if self is TPCTextureFormat.RGBA:
            return QImage.Format.Format_RGBA8888
        if self is TPCTextureFormat.BGRA:
            return QImage.Format.Format_ARGB32
        return QImage.Format.Format_Invalid

    def to_pil_mode(self) -> str:
        """Convert this texture format to a PIL mode string."""
        if self is TPCTextureFormat.Greyscale:
            return "L"
        if self is TPCTextureFormat.RGB or self is TPCTextureFormat.BGR:
            return "RGB"
        if self is TPCTextureFormat.RGBA or self is TPCTextureFormat.BGRA:
            return "RGBA"
        raise ValueError(f"Invalid texture format: {self!r}")

    def get_size(
        self,
        width: int,
        height: int,
    ) -> int:
        if self is TPCTextureFormat.Greyscale:
            return width * height * 1
        if self is TPCTextureFormat.RGB or self is TPCTextureFormat.BGR:
            return width * height * 3
        if self is TPCTextureFormat.RGBA or self is TPCTextureFormat.BGRA:
            return width * height * 4
        if self is TPCTextureFormat.DXT1:
            return max(8, ((width + 3) // 4) * ((height + 3) // 4) * 8)
        if self is TPCTextureFormat.DXT5:
            return max(16, ((width + 3) // 4) * ((height + 3) // 4) * 16)
        return 0
