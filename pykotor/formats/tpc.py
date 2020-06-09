from __future__ import annotations

from enum import IntEnum
from typing import List, Tuple

from pykotor.general.binary_reader import BinaryReader


class TextureType(IntEnum):
    Invalid = -1
    Greyscale = 0
    RGB = 1
    RGBA = 2
    DXT1 = 3
    DXT5 = 4


class TPC:
    @staticmethod
    def load(data: bytes) -> TPC:
        return _TPCReader.load(data)

    def build(self):
        return _TPCWriter.build(self)

    def __init__(self):
        self.txi: str = ""
        self._texture_type: TextureType = TextureType.Invalid
        self._mipmaps: List[bytes] = []
        self._width: int = 0
        self._height: int = 0

    def set_image(self, width: int, height: int, data: bytearray, texture_type: TextureType) -> None:
        self._width = width
        self._height = height
        self._mipmaps = [data]
        self._texture_type = texture_type

    def set_mipmaps(self, width: int, height: int, mipmaps: List[bytearray], texture_type: TextureType) -> None:
        self._width = width
        self._height = height
        self._mipmaps = mipmaps
        self._texture_type = texture_type

    def get_mipmap_size(self, mipmap: int = 0) -> Tuple[int, int]:
        width = self.width
        height = self.height
        for i in range(mipmap):
            width >>= 1
            height >>= 1
        return width, height

    def get_rgba_bytes(self, mipmap: int = 0) -> List[bytearray]:
        if self.texture_type == TextureType.Greyscale:
            return self._rgba_bytes_from_gray(mipmap)
        elif self.texture_type == TextureType.RGB:
            return self._rgba_bytes_from_rgb(mipmap)
        elif self.texture_type == TextureType.RGBA:
            return self._rgba_bytes_from_rgba(mipmap)
        elif self.texture_type == TextureType.DXT1:
            return self._rgba_bytes_from_dxt1(mipmap)
        elif self.texture_type == TextureType.DXT5:
            return self._rgba_bytes_from_dxt5(mipmap)

    def _rgba_bytes_from_gray(self, mipmap: int = 0) -> List[bytearray]:
        data = bytearray()

        for gray in self.mipmaps[mipmap]:
            data.append(gray)
            data.append(gray)
            data.append(gray)
            data.append(255)

        return data

    def _rgba_bytes_from_rgba(self, mipmap: int = 0) -> List[bytearray]:
        data = bytearray()

        pixels = zip(*[iter(self.mipmaps[mipmap])] * 4)
        for r, g, b, a in pixels:
            data.append(r)
            data.append(g)
            data.append(b)
            data.append(a)

        return data

    def _rgba_bytes_from_rgb(self, mipmap: int = 0) -> List[bytearray]:
        data = bytearray()

        pixels = zip(*[iter(self.mipmaps[mipmap])]*3)
        for r, g, b in pixels:
            data.append(r)
            data.append(g)
            data.append(b)
            data.append(255)

        return data

    def _rgba_bytes_from_dxt1(self, mipmap: int = 0) -> List[bytearray]:
        dxt_reader = BinaryReader.from_data(self.mipmaps[mipmap])
        width, height = self.get_mipmap_size(mipmap)
        pixels = [0] * width * height

        for ty in range(height, 0, -4):
            for tx in range(0, width, 4):
                color0 = self._rgba565_to_rgb888(dxt_reader.read_int16())
                color1 = self._rgba565_to_rgb888(dxt_reader.read_int16())
                dxt_pixels = dxt_reader.read_uint32(True)

                color_code = []
                color_code.extend([color0, color1])
                if color0 > color1:
                    color_code.append(self._interpolate(0.3333333, color0, color1))
                    color_code.append(self._interpolate(0.6666666, color0, color1))
                else:
                    color_code.append(self._interpolate(0.5555555, color0, color1))
                    color_code.append(0xFF000000)

                for y in range(4):
                    for x in range(4):
                        pixel_code = dxt_pixels & 3
                        dxt_pixels >>= 2
                        pixels[(ty - 4 + y) * self.width + (tx + x)] = color_code[pixel_code] + 0xFF000000

        data = bytearray()
        for pixel in pixels:

            data.append((pixel & 0x00FF0000) >> 16)
            data.append((pixel & 0x0000FF00) >> 8)
            data.append((pixel & 0x000000FF))
            data.append(255)

        return data

    def _rgba_bytes_from_dxt5(self, mipmap: int = 0) -> List[bytearray]:
        dxt_reader = BinaryReader.from_data(self.mipmaps[mipmap])
        width, height = self.get_mipmap_size(mipmap)
        pixels = [0] * width * height

        for ty in range(height, 0, -4):
            for tx in range(0, width, 4):
                alpha0 = dxt_reader.read_uint8()
                alpha1 = dxt_reader.read_uint8()
                dxt_alpha = self._integer48(dxt_reader.read_bytes(6))
                color0 = self._rgba565_to_rgb888(dxt_reader.read_int16())
                color1 = self._rgba565_to_rgb888(dxt_reader.read_int16())
                dxt_pixels = dxt_reader.read_uint32(True)

                color_code = []
                color_code.extend([color0, color1])
                if color0 > color1:
                    color_code.append(self._interpolate(0.3333333, color0, color1))
                    color_code.append(self._interpolate(0.6666666, color0, color1))
                else:
                    color_code.append(self._interpolate(0.5555555, color0, color1))
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
                        pixels[(ty - 4 + y) * self.width + (tx + x)] = pixel

        data = bytearray()
        for pixel in pixels:

            data.append((pixel & 0x00FF0000) >> 16)
            data.append((pixel & 0x0000FF00) >> 8)
            data.append((pixel & 0x000000FF))
            data.append((pixel & 0xFF000000) >> 24)

        return data

    def _rgba565_to_rgb888(self, color: int) -> int:
        blue = (color & 0x1F)
        green = (color >> 5) & 0x3F
        red = (color >> 11) & 0x1F
        return (blue << 3) + (green << 10) + (red << 19)

    def _interpolate(self, weight: float, color0: int, color1: int) -> int:
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

    def _integer48(self, bytes48: int) -> int:
        return bytes48[0] + (bytes48[1] << 8) + (bytes48[2] << 16) + (bytes48[3] << 24) + (bytes48[4] << 32) + (
                    bytes48[5] << 40)


class _TPCReader:
    @staticmethod
    def load(data: bytes) -> TPC:
        pass
        # TODO


class _TPCWriter:
    @staticmethod
    def build(tpc: TPC) -> bytes:
        pass
        # TODO


class _TGAWriter:
    @staticmethod
    def build(rgba: bytes) -> bytes:
        pass
        # TODO
