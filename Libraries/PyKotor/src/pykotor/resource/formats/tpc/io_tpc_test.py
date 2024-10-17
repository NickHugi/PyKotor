from __future__ import annotations

import math
import struct

from io import BytesIO
from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.tpc_data import TPC, TPCMipmap, TPCTextureFormat
from pykotor.resource.type import ResourceReader

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES


class TPCBinaryReader(ResourceReader):
    """Used to read TPC binary data."""

    MAX_DIMENSIONS: int = 0x8000

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._tpc: TPC = TPC()

    def load(self, tpc_data: bytes):
        tpc = BytesIO(tpc_data)
        self._read_header(tpc)
        self._read_data(tpc)
        self._fixup_cube_map()
        self.decompress()

    def _read_header(self, tpc: BytesIO):
        # Number of bytes for the pixel data in one full image
        data_size: int = struct.unpack("<I", tpc.read(4))[0]
        compressed: bool = data_size != 0

        tpc.seek(4, 1)  # Skip float

        # Image dimensions
        width, height = struct.unpack("<HH", tpc.read(4))
        if width >= self.MAX_DIMENSIONS or height >= self.MAX_DIMENSIONS:
            raise ValueError(f"Unsupported image dimensions ({width}x{height}), max is {self.MAX_DIMENSIONS}x{self.MAX_DIMENSIONS}")

        # Determine texture format
        encoding = tpc.read(1)[0]
        self._tpc._texture_format = self._get_texture_format(encoding, compressed=compressed)  # noqa: SLF001

        mipmap_count = tpc.read(1)[0]
        if compressed:
            data_size = self._tpc.format().get_size(width, height)
        else:
            self._check_cube_map(width, height)
        combined_image_and_txi_size = self._calculate_complete_data_size(data_size, width, height, mipmap_count)
        tpc.read(114)  # Skip reserved
        tpc.read(combined_image_and_txi_size)  # Skip image data
        txi_data_size = len(tpc.getvalue()) - tpc.tell()
        if txi_data_size == 0:
            return

        txi_data = bytearray(txi_data_size)
        if tpc.readinto(txi_data) != txi_data_size:
            raise OSError("Read error")
        self._tpc.txi = txi_data.decode("ascii", errors="strict").strip()

        self._tpc.is_animated = self._check_animated(width, height, data_size)

        if self._tpc.is_animated:
            w = width
            h = height
            mipmap_count = 0
            while width > 0 and height > 0:
                w //= 2
                h //= 2
                mipmap_count += 1

        if compressed:
            if self._tpc.format() == TPCTextureFormat.DXT1:  # noqa: SLF001
                if (
                    data_size != ((width * height) // 2)
                    and not self._tpc.is_animated
                ):
                    raise ValueError(f"Invalid data size for a texture of {width}x{height} pixels and format {self._tpc.format()}")  # noqa: SLF001
            elif self._tpc.format() == TPCTextureFormat.DXT5:  # noqa: SLF001, SIM102
                if (
                    data_size != (width * height)
                    and not self._tpc.is_animated
                ):
                    raise ValueError(f"Invalid data size for a texture of {width}x{height} pixels and format {self._tpc.format()}")  # noqa: SLF001

        tpc.read(128)

        if not self._has_valid_dimensions(self._tpc.format(), width, height):
            raise ValueError(f"Invalid dimensions ({width}x{height}) for format {self._tpc.format()}")


        combined_image_and_txi_size = self._tpc.format().get_size(width, height)
        complete_image_data_size = data_size - 128

        if complete_image_data_size < (self._tpc.layer_count * combined_image_and_txi_size):
            raise ValueError("Image wouldn't fit into data")
        while layer_count < self._layer_count:
            layer_width: int = width
            layer_height: int = height
            for _ in range(mipmap_count):
                width = max(1, layer_width)
                height = max(layer_height, 1)
                mm_size: int = self._tpc.format().get_size(width, height)

                # Wouldn't fit
                if full_data_size < mm_size:
                    break

                full_data_size -= mm_size
                data: bytes | None = self._stream.read(mm_size)
                if data is None:
                    raise ValueError("Failed to read mipmap data from stream of type:" f" {self._stream.__class__.__name__}")
                mipmap = TPCMipmap(
                    data=bytearray(data),
                    width=width,
                    height=height,
                )
                self._tpc.mipmaps.append(mipmap)

                layer_width >>= 1
                layer_height >>= 1
                if layer_width < 1 and layer_height < 1:
                    break

            layer_count += 1

            if len(self._tpc.mipmaps) % self._layer_count != 0:
                raise ValueError(
                    "Failed to correctly read all texture layers. Expected the number"
                    f" of mipmaps ({len(self._tpc.mipmaps)}) to be divisible by the number"
                    f" of layers ({self._layer_count}), but there is a mismatch. This"
                    " suggests an inconsistency in the texture data or an error in the"
                    " reading process."
                )

    def _check_cube_map(
        self,
        width: int,
        height: int,
    ) -> bool:
        """Check if this texture is a cube map by looking if height equals to six
        times width. This means that there are 6 sides of width * (height / 6)
        images in this texture, making it a cube map.

        The individual sides are then stored one after another, together with
        their mip maps.

        I.e.
        - Side 0, mip map 0
        - Side 0, mip map 1
        - ...
        - Side 1, mip map 0
        - Side 1, mip map 1
        - ...

        The ordering of the sides should be the usual Direct3D cube map order,
        which is the same as the OpenGL cube map order.

        Yes, that's a really hacky way to encode a cube map. But this is how
        the original game does it. It works and doesn't clash with other, normal
        textures because TPC textures always have power-of-two side lengths,
        and therefore (height / width) == 6 isn't true for non-cubemaps.
        """
        if (
            height == 0
            or width == 0
            or (height // width) != 6  # noqa: PLR2004
        ):  # noqa: PLR2004
            return False

        height //= 6
        self._tpc.layer_count = 6
        self._tpc.is_cube_map = True

        return True

    def _get_min_data_size(
        self,
        encoding: int,
        *,
        compressed: bool,
    ) -> int:
        if not compressed:
            if encoding == 0x01:  # Greyscale
                return 1
            if encoding == 0x02:  # RGB  # noqa: PLR2004
                return 3
            if encoding in (0x04, 0x0C):  # RGBA or SwizzledBGRA
                return 4
        elif encoding == 0x02:  # RGB (DXT1)  # noqa: PLR2004
            return 8
        elif encoding == 0x04:  # RGBA (DXT5)  # noqa: PLR2004
            return 16
        raise ValueError(f"Unknown TPC encoding: {encoding}")

    def _get_texture_format(
        self,
        encoding: int,
        *,
        compressed: bool,
    ) -> TPCTextureFormat:
        if compressed:
            if encoding == 0x02:  # RGB (DXT1)  # noqa: PLR2004
                return TPCTextureFormat.DXT1
            if encoding == 0x04:  # RGBA (DXT5)  # noqa: PLR2004
                return TPCTextureFormat.DXT5
        if encoding == 0x01:  # Greyscale  # noqa: PLR2004
            return TPCTextureFormat.Greyscale
        if encoding == 0x02:  # RGB  # noqa: PLR2004
            return TPCTextureFormat.RGB
        if encoding == 0x04:  # RGBA  # noqa: PLR2004
            return TPCTextureFormat.RGBA
        if encoding == 0x0C:  # SwizzledBGRA  # noqa: PLR2004
            return TPCTextureFormat.BGRA
        return TPCTextureFormat.Invalid

    def _calculate_complete_data_size(
        self,
        data_size: int,
        width: int,
        height: int,
        mip_map_count: int,
    ) -> int:
        complete_data_size = data_size
        w, h = width, height
        for _ in range(1, mip_map_count):
            w = max(w >> 1, 1)
            h = max(h >> 1, 1)
            complete_data_size += self._tpc.format().get_size(w, h)
        return complete_data_size * self._layer_count

    def _check_animated(
        self,
        width: int,
        height: int,
        data_size: int,
    ) -> bool:
        # If there is no TXI data, it cannot be animated
        if not self._tpc.txi:
            return False

        txi = TXI(self._tpc.txi)
        if (
            txi.get_features().procedure_type != "cycle"
            or txi.get_features()numx == 0
            or txi.get_features()numy == 0
            or txi.get_features().fps == 0.0
        ):
            return False

        self._layer_count = txi.get_features()numx * txi.get_features()numy

        width //= txi.get_features()numx
        height //= txi.get_features()numy

        data_size //= self._layer_count

        return True

    def _has_valid_dimensions(
        self,
        tpc_format: TPCTextureFormat,
        width: int,
        height: int,
    ) -> bool:
        return (
            width >= 0
            and width < self.MAX_DIMENSIONS
            and height >= 0
            and height < self.MAX_DIMENSIONS
            and tpc_format is not TPCTextureFormat.Invalid
        )

    def _read_mip_maps(
        self,
        tpc: BytesIO,
        width: int,
        height: int,
        mip_map_count: int,
        full_data_size: int,
    ):
        w, h = width, height
        for _layer in range(self._layer_count):
            layer_width, layer_height = width, height
            for _ in range(mip_map_count):
                mm_size: int = self._tpc.format().get_size(w, h)
                w, h = w >> 1, h >> 1
                if full_data_size < mm_size:
                    break
                full_data_size -= mm_size
                mm = TPCMipmap(
                    width=max(layer_width, 1),
                    height=max(layer_height, 1),
                    data=bytearray(tpc.read(mm_size)),
                )
                self._tpc.mipmaps.append(mm)
                w, h = mm.width, mm.height

                layer_width >>= 1
                layer_height >>= 1
                if layer_width < 1 and layer_height < 1:
                    break

        if len(self._tpc.mipmaps) % self._layer_count != 0:
            raise ValueError("Failed to correctly read all texture layers")

    def _read_data(
        self,
        tpc: BytesIO,
    ):
        for mip_map in self._tpc.mipmaps:
            width_pot = (mip_map.width & (mip_map.width - 1)) == 0
            swizzled = (
                self._tpc.format() == TPCTextureFormat.BGRA  # noqa: SLF001
                and width_pot
            )

            if swizzled:
                swiz_data = tpc.read(len(mip_map.data))
                mip_map.data = self._deswizzle(
                    swiz_data,
                    mip_map.width,
                    mip_map.height,
                )
            else:
                mip_map.data = tpc.read(len(mip_map.data))

            if self._tpc.format() == TPCTextureFormat.Greyscale:  # noqa: SLF001
                mip_map.data = self._unpack_greyscale(mip_map.data, mip_map.width, mip_map.height)

    def deswizzle(
        self,
        src: bytes,
        width: int,
        height: int,
    ) -> bytes:
        dst = bytearray(width * height * 4)
        for y in range(height):
            for x in range(width):
                offset = deswizzle_offset(x, y, width, height) * 4
                dst_offset = (y * width + x) * 4
                dst[dst_offset:dst_offset+4] = src[offset:offset+4]
        return bytes(dst)

    def deswizzle_offset(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> int:
        # This is a placeholder implementation and may not be correct
        # The actual deswizzle algorithm can be complex and depend on the specific swizzle pattern used
        block_size = 4
        block_x = x // block_size
        block_y = y // block_size
        blocks_per_row = width // block_size
        block_index = block_y * blocks_per_row + block_x
        pixel_index = (y % block_size) * block_size + (x % block_size)
        return block_index * (block_size * block_size) + pixel_index

    def _unpack_greyscale(self, data: bytes, width: int, height: int) -> bytes:
        unpacked = bytearray(width * height * 3)
        for i in range(width * height):
            unpacked[i * 3 : i * 3 + 3] = [data[i]] * 3
        return bytes(unpacked)

    def _fixup_cube_map(self):
        """Do various fixups to the cube maps. This includes rotating and swapping a
        few sides around. This is done by the original games as well.
        """
        if not self._tpc.is_cube_map:
            return

        mip_map_count = len(self._tpc.mipmaps) // self._layer_count

        for j in range(mip_map_count):
            width = self._tpc.mipmaps[j].width
            height = self._tpc.mipmaps[j].height
            size = len(self._tpc.mipmaps[j].data)

            for i in range(1, self._layer_count):
                index = i * mip_map_count + j
                if (
                    width != self._tpc.mipmaps[index].width
                    or height != self._tpc.mipmaps[index].height
                    or size != len(self._tpc.mipmaps[index].data)
                ):
                    raise ValueError("Cube map layer dimensions mismatch")

        # Since we need to rotate the individual cube sides, we need to decompress them all
        self.decompress()

        # Rotate the cube sides so that they're all oriented correctly
        rotation = [3, 1, 0, 2, 2, 0]
        for i in range(self._layer_count):
            for j in range(mip_map_count):
                index = i * mip_map_count + j
                mip_map = self._tpc.mipmaps[index]
                rotated = self._rotate90(
                    mip_map.data,
                    mip_map.width,
                    mip_map.height,
                    self._tpc.format().bytes_per_pixel(),
                    rotation[i],
                )

        # Swap the first two sides of the cube maps
        for j in range(mip_map_count):
            index0 = 0 * mip_map_count + j
            index1 = 1 * mip_map_count + j
            (
                self._tpc.mipmaps[index0].data,
                self._tpc.mipmaps[index1].data,
            ) = (
                self._tpc.mipmaps[index1].data,
                self._tpc.mipmaps[index0].data,
            )

    def _rotate90(
        self,
        data: bytearray,
        width: int,
        height: int,
        bytes_per_pixel: int,
        times: int,
    ) -> None:
        """Rotate a square image in 90° steps, clock-wise."""
        if width <= 0 or height <= 0 or bytes_per_pixel <= 0:
            return

        assert width == height, "Image must be square"

        n = width
        while times > 0:
            w = n // 2
            h = (n + 1) // 2

            for x in range(w):
                for y in range(h):
                    d0 = (y * n + x) * bytes_per_pixel
                    d1 = ((n - 1 - x) * n + y) * bytes_per_pixel
                    d2 = ((n - 1 - y) * n + (n - 1 - x)) * bytes_per_pixel
                    d3 = (x * n + (n - 1 - y)) * bytes_per_pixel

                    for p in range(bytes_per_pixel):
                        tmp = data[d0 + p]
                        data[d0 + p] = data[d1 + p]
                        data[d1 + p] = data[d2 + p]
                        data[d2 + p] = data[d3 + p]
                        data[d3 + p] = tmp

            times -= 1

    def decompress(self):
        """Decompress DXT1 and DXT5 formats to RGBA."""
        if self._tpc.format() not in {TPCTextureFormat.DXT1, TPCTextureFormat.DXT5}:
            return

        for mm in self._tpc.mipmaps:
            if self._tpc.format() == TPCTextureFormat.DXT1:
                mm.data = self.decompress_dxt1(mm.data, mm.width, mm.height)
            else:  # DXT5
                mm.data = self.decompress_dxt5(mm.data, mm.width, mm.height)

        self._tpc._texture_format = TPCTextureFormat.RGBA

    @staticmethod
    def decompress_dxt1(
        data: bytes,
        width: int,
        height: int,
    ) -> bytes:
        """Decompress DXT1 format to RGBA."""
        output = bytearray(width * height * 4)
        for y in range(0, height, 4):
            for x in range(0, width, 4):
                color_0, color_1, bits = struct.unpack("<HHI", data[:8])
                data = data[8:]

                r0, g0, b0 = (color_0 & 0xF800) >> 8, (color_0 & 0x07E0) >> 3, (color_0 & 0x001F) << 3
                r1, g1, b1 = (color_1 & 0xF800) >> 8, (color_1 & 0x07E0) >> 3, (color_1 & 0x001F) << 3

                for py in range(4):
                    for px in range(4):
                        if x + px < width and y + py < height:
                            code = (bits >> 2 * (4 * py + px)) & 0x3
                            if color_0 > color_1:
                                if code == 0:
                                    r, g, b = r0, g0, b0
                                elif code == 1:
                                    r, g, b = r1, g1, b1
                                elif code == 2:  # noqa: PLR2004
                                    r = (2 * r0 + r1) // 3
                                    g = (2 * g0 + g1) // 3
                                    b = (2 * b0 + b1) // 3
                                elif code == 3:  # noqa: PLR2004
                                    r = (r0 + 2 * r1) // 3
                                    g = (g0 + 2 * g1) // 3
                                    b = (b0 + 2 * b1) // 3
                            elif code == 0:  # noqa: PLR2004
                                r, g, b = r0, g0, b0
                            elif code == 1:  # noqa: PLR2004
                                r, g, b = r1, g1, b1
                            elif code == 2:  # noqa: PLR2004
                                r = (r0 + r1) // 2
                                g = (g0 + g1) // 2
                                b = (b0 + b1) // 2
                            elif code == 3:  # noqa: PLR2004
                                r, g, b = 0, 0, 0

                            idx = (y + py) * width + (x + px)
                            output[idx * 4 : idx * 4 + 4] = bytes([r, g, b, 255])

        return bytes(output)

    @staticmethod
    def decompress_dxt5(
        data: bytes,
        width: int,
        height: int,
    ) -> bytes:
        """Decompress DXT5 format to RGBA."""
        output = bytearray(width * height * 4)
        for y in range(0, height, 4):
            for x in range(0, width, 4):
                alpha0, alpha1 = data[0], data[1]
                alpha_bits = int.from_bytes(data[2:8], byteorder="little")
                color_0, color_1, bits = struct.unpack("<HHI", data[8:16])
                data = data[16:]

                r0, g0, b0 = (color_0 & 0xF800) >> 8, (color_0 & 0x07E0) >> 3, (color_0 & 0x001F) << 3
                r1, g1, b1 = (color_1 & 0xF800) >> 8, (color_1 & 0x07E0) >> 3, (color_1 & 0x001F) << 3

                for py in range(4):
                    for px in range(4):
                        if x + px < width and y + py < height:
                            alpha_code = (alpha_bits >> 3 * (4 * py + px)) & 0x7
                            if alpha_code == 0:
                                alpha = alpha0
                            elif alpha_code == 1:
                                alpha = alpha1
                            elif alpha0 > alpha1:
                                alpha = ((8 - alpha_code) * alpha0 + (alpha_code - 1) * alpha1) // 7
                            elif alpha_code == 6:  # noqa: PLR2004
                                alpha = 0
                            elif alpha_code == 7:  # noqa: PLR2004
                                alpha = 255
                            else:
                                alpha = ((6 - alpha_code) * alpha0 + (alpha_code - 1) * alpha1) // 5

                            color_code = (bits >> 2 * (4 * py + px)) & 0x3
                            if color_code == 0:
                                r, g, b = r0, g0, b0
                            elif color_code == 1:
                                r, g, b = r1, g1, b1
                            elif color_code == 2:  # noqa: PLR2004
                                r = (2 * r0 + r1) // 3
                                g = (2 * g0 + g1) // 3
                                b = (2 * b0 + b1) // 3
                            elif color_code == 3:  # noqa: PLR2004
                                r = (r0 + 2 * r1) // 3
                                g = (g0 + 2 * g1) // 3
                                b = (b0 + 2 * b1) // 3

                            idx = (y + py) * width + (x + px)
                            output[idx * 4 : idx * 4 + 4] = bytes([r, g, b, alpha])

        return bytes(output)


def deswizzle_offset(
    x: int,
    y: int,
    width: int,
    height: int,
) -> int:
    """Calculate the deswizzled offset for a given x, y coordinate."""
    width = int(math.log2(width))
    height = int(math.log2(height))

    offset = 0
    shift_count = 0

    while width | height:
        if width:
            offset |= (x & 0x01) << shift_count
            x >>= 1
            shift_count += 1
            width -= 1

        if height:
            offset |= (y & 0x01) << shift_count
            y >>= 1
            shift_count += 1
            height -= 1

    return offset
