from __future__ import annotations

import itertools
import math

from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.tpc_data import TPC, TPCMipmap, TPCTextureFormat
from pykotor.resource.formats.txi.txi_data import TXI
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class TPCBinaryReader(ResourceReader):
    """Used to read TPC binary data."""

    MAX_DIMENSIONS: int = 0x8000
    IMG_DATA_START_OFFSET: int = 0x80

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
    ):
        super().__init__(source, offset, size)
        # data: bytearray = self._source[self._offset : self._size]
        # self._stream: io.BytesIO = io.BytesIO(data)
        self._tpc: TPC = TPC()

    @autoclose
    def load(self) -> TPC:
        self._tpc = TPC()
        self._layer_count: int = 1
        data_size: int = self._reader.read_uint32()  # 0x0
        entire_file_size: int = self._reader.size()
        self._reader.skip(4)  # 0x4
        width: int = self._reader.read_uint16()  # 0x8
        height: int = self._reader.read_uint16()  # 0xA
        color_depth: int = self._reader.read_uint8()  # 0xC
        mipmap_count: int = self._reader.read_uint8()  # 0xD

        if width >= self.MAX_DIMENSIONS or height >= self.MAX_DIMENSIONS:
            raise ValueError(f"Unsupported image dimensions ({width}x{height})")

        compressed: bool = data_size != 0
        tpc_format: TPCTextureFormat = self._get_texture_format(color_depth, compressed=compressed)
        self._tpc._texture_format = tpc_format  # noqa: SLF001
        sides_on_a_cube: int = 6
        if not compressed:
            data_size = tpc_format.get_size(width, height)

        elif (
            height != 0  # noqa: PLR2004
            and width != 0
            and (height // width) == sides_on_a_cube
        ):
            self._tpc.is_cube_map = True
            height //= sides_on_a_cube
            self._layer_count = sides_on_a_cube

        combined_image_data_size: int = self._calculate_total_data_size(width, height, mipmap_count, tpc_format)
        combined_image_data_size *= self._layer_count
        self._reader.skip(0x72)  # 0xE (Skip reserved)
        self._reader.seek(self.IMG_DATA_START_OFFSET + combined_image_data_size)
        txi_data_size: int = entire_file_size - self._reader.position()
        if txi_data_size > 0:
            self._tpc.txi = self._reader.read_string(
                txi_data_size,
                encoding="ascii",
                errors="ignore",
            )

        self._tpc.is_animated = self._check_animated(width, height, data_size)
        if self._tpc.is_animated:
            mipmap_count = self._calculate_mip_map_count(width, height)

        if compressed:
            self._validate_compressed_data_size(width, height, data_size, color_depth, tpc_format)

        self._reader.seek(self.IMG_DATA_START_OFFSET)  # Skip to start of image data (0x80)
        if not self._has_valid_dimensions(tpc_format, width, height):
            raise ValueError(f"Invalid dimensions ({width}x{height}) for format {tpc_format!r}")

        full_image_data_size: int = tpc_format.get_size(width, height)
        full_data_size: int = entire_file_size - self.IMG_DATA_START_OFFSET

        if full_data_size < (self._layer_count * full_image_data_size):
            raise ValueError(
                f"Insufficient data for image. Expected at least {hex(self._layer_count * full_image_data_size)} bytes,"
                f" but only {hex(full_data_size)} bytes are available."
            )

        self._read_mipmaps(width, height, mipmap_count, tpc_format)

        if tpc_format is TPCTextureFormat.BGRA:
            self._deswizzle_bgra()
        elif tpc_format is TPCTextureFormat.Greyscale:
            self._convert_greyscale_to_rgb()

        if self._tpc.is_cube_map:
            self._fixup_cube_map()

        return self._tpc

    def _calculate_total_data_size(self, width: int, height: int, mipmap_count: int, tpc_format: TPCTextureFormat) -> int:
        total_size = 0
        for _ in range(mipmap_count):
            total_size += tpc_format.get_size(width, height)
            width = max(width >> 1, 1)
            height = max(height >> 1, 1)
        return total_size

    def _validate_compressed_data_size(self, width: int, height: int, data_size: int, color_depth: int, tpc_format: TPCTextureFormat):
        if color_depth == 2:  # RGB
            expected_size = (width * height) // 2
        elif color_depth == 4:  # RGBA
            expected_size = width * height
        else:
            raise ValueError(f"Unknown TPC encoding: {color_depth} for texture of format {tpc_format!r}")

        if data_size != expected_size and not self._tpc.is_animated:
            raise ValueError(f"Invalid data size for a texture of {width}x{height} pixels and format {tpc_format!r} color depth {color_depth}")

    def _read_mipmaps(self, width: int, height: int, mipmap_count: int, tpc_format: TPCTextureFormat):
        for layer in range(self._layer_count):
            layer_width, layer_height = width, height
            for _ in range(mipmap_count):
                mm_width = max(1, layer_width)
                mm_height = max(1, layer_height)
                mm_size: int = tpc_format.get_size(mm_width, mm_height)

                data: bytes | None = self._reader.read(mm_size)
                if data is None or len(data) != mm_size:
                    raise ValueError(f"Failed to read mipmap data. Expected {mm_size} bytes, got {len(data) if data else 0}")

                mm = TPCMipmap(
                    data=bytearray(data),
                    width=mm_width,
                    height=mm_height,
                )
                self._tpc.mipmaps.append(mm)

                layer_width >>= 1
                layer_height >>= 1
                if layer_width < 1 and layer_height < 1:
                    break

    def _deswizzle_bgra(self):
        for mm in self._tpc.mipmaps:
            if mm.width & (mm.width - 1) == 0:  # Check if width is a power of 2
                mm.data = bytearray(self.deswizzle(bytes(mm.data), mm.width, mm.height))

    def _convert_greyscale_to_rgb(self):
        for mm in self._tpc.mipmaps:
            data_gray: bytearray = mm.data
            mm.data = bytearray(mm.width * mm.height * 3)
            for j in range(mm.width * mm.height):
                mm.data[j * 3 : (j + 1) * 3] = [data_gray[j]] * 3

        return self._tpc

    def _has_valid_dimensions(
        self,
        tpc_format: TPCTextureFormat,
        width: int,
        height: int,
    ) -> bool:
        return (
            width > 0  #   # noqa: PLR2044
            and width < self.MAX_DIMENSIONS
            and height > 0
            and height < self.MAX_DIMENSIONS
            and tpc_format is not TPCTextureFormat.Invalid
        )

    def deswizzle(self, src: bytes, width: int, height: int) -> bytes:
        dst = bytearray(width * height * 4)

        for y, x in itertools.product(range(height), range(width)):
            offset: int = self.deswizzle_offset(x, y, width, height) * 4

            dst[4 * (y * width + x) + 0] = src[offset + 0]
            dst[4 * (y * width + x) + 1] = src[offset + 1]
            dst[4 * (y * width + x) + 2] = src[offset + 2]
            dst[4 * (y * width + x) + 3] = src[offset + 3]

        return bytes(dst)

    def deswizzle_offset(
        self,
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

    def _calculate_mip_map_count(
        self,
        width: int,
        height: int,
    ) -> int:
        count = 0
        while width > 0 and height > 0:
            width >>= 1
            height >>= 1
            count += 1
        return count

    def _check_animated(
        self,
        width: int,
        height: int,
        data_size: int,
    ) -> bool:
        if not self._tpc.txi:
            return False

        txi = TXI(self._tpc.txi)
        if (
            txi.get_features().proceduretype.lower() != "cycle"
            or not txi.get_features().numx  # noqa: PLR2004
            or not txi.get_features().numy
            or not txi.get_features().fps
        ):
            return False

        self._layer_count = txi.get_features().numx * txi.get_features().numy
        width //= txi.get_features().numx
        height //= txi.get_features().numy
        data_size //= self._layer_count

        return True

    def _fixup_cube_map(self):
        """Do various fixups to the cube maps. This includes rotating and swapping a
        few sides around. This is done by the original games as well.
        """
        if not self._tpc.is_cube_map:
            return

        mm_count: int = len(self._tpc.mipmaps) // self._layer_count
        for j in range(mm_count):
            width: int = self._tpc.mipmaps[j].width
            height: int = self._tpc.mipmaps[j].height
            size: int = len(self._tpc.mipmaps[j].data)

            for i in range(1, self._layer_count):
                index = i * mm_count + j
                if (
                    width != self._tpc.mipmaps[index].width
                    or height != self._tpc.mipmaps[index].height
                    or size != len(self._tpc.mipmaps[index].data)
                ):
                    raise ValueError("Cube map layer dimensions mismatch detected.")

        tpc_format: TPCTextureFormat = self._tpc.format()
        if tpc_format in (TPCTextureFormat.DXT1, TPCTextureFormat.DXT5):

            # Since we need to rotate the individual cube sides, we need to decompress them all
            self._tpc.convert(
                TPCTextureFormat.RGBA
                if tpc_format == TPCTextureFormat.DXT5
                else TPCTextureFormat.RGB
            )
        else:
            raise ValueError(f"Unsupported cube map format: {tpc_format!r}. Cubemaps must be DXT1 or DXT5")

        # Rotate the cube sides so that they're all oriented correctly
        rotation: tuple[int, int, int, int, int, int] = (3, 1, 0, 2, 2, 0)
        for i in range(self._layer_count):
            for j in range(mm_count):
                index: int = i * mm_count + j
                mm: TPCMipmap = self._tpc.mipmaps[index]
                self._rotate90(
                    mm.data,
                    mm.width,
                    mm.height,
                    tpc_format.bytes_per_pixel(),
                    rotation[i],
                )

        # Swap the first two sides of the cube maps
        for j in range(mm_count):
            index0: int = 0 * mm_count + j
            index1: int = 1 * mm_count + j
            self._tpc.mipmaps[index0].data, self._tpc.mipmaps[index1].data = (
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

        assert width == height, f"Image must be square. Current dimensions: width={width}, height={height}."

        n: int = width
        while times > 0:
            w: int = n // 2
            h: int = (n + 1) // 2

            for x in range(w):
                for y in range(h):
                    d0: int = (y * n + x) * bytes_per_pixel
                    d1: int = ((n - 1 - x) * n + y) * bytes_per_pixel
                    d2: int = ((n - 1 - y) * n + (n - 1 - x)) * bytes_per_pixel
                    d3: int = (x * n + (n - 1 - y)) * bytes_per_pixel

                    for p in range(bytes_per_pixel):
                        tmp: int = data[d0 + p]
                        data[d0 + p] = data[d1 + p]
                        data[d1 + p] = data[d2 + p]
                        data[d2 + p] = data[d3 + p]
                        data[d3 + p] = tmp

            times -= 1

    def _get_texture_format(  # noqa: PLR0911
        self,
        color_depth: int,
        *,
        compressed: bool,
    ) -> TPCTextureFormat:
        if compressed:
            if color_depth == 2:  # RGB (DXT1)  # noqa: PLR2004
                return TPCTextureFormat.DXT1
            if color_depth == 4:  # RGBA (DXT5)  # noqa: PLR2004
                return TPCTextureFormat.DXT5
        if color_depth == 1:  # Greyscale  # noqa: PLR2004
            return TPCTextureFormat.Greyscale
        if color_depth == 2:  # RGB  # noqa: PLR2004
            return TPCTextureFormat.RGB
        if color_depth == 4:  # RGBA  # noqa: PLR2004
            return TPCTextureFormat.RGBA
        if color_depth == 12:  # SwizzledBGRA  # noqa: PLR2004
            return TPCTextureFormat.BGRA
        return TPCTextureFormat.Invalid


class TPCBinaryWriter(ResourceWriter):
    """Used to write TPC instances as TPC binary data."""

    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tpc: TPC = tpc

    @autoclose
    def write(self):
        data = bytearray()
        size: int = 0

        for i in range(self._tpc.mipmap_count()):
            width, height, texture_format, mm_data = self._tpc.get(i)
            assert mm_data is not None
            data += mm_data
            detsize: int = texture_format.get_size(width, height)
            assert detsize is not None
            size += detsize

        tpc_fmt: TPCTextureFormat = self._tpc.format()
        if tpc_fmt in (TPCTextureFormat.RGBA, TPCTextureFormat.BGRA):
            color_depth = 4
            size = 0
        elif tpc_fmt is TPCTextureFormat.RGB:
            color_depth = 2
            size = 0
        elif tpc_fmt is TPCTextureFormat.Greyscale:
            color_depth = 1
            size = 0
        elif tpc_fmt is TPCTextureFormat.DXT1:
            color_depth = 2
        elif tpc_fmt is TPCTextureFormat.DXT5:
            color_depth = 4
        else:
            msg = "Invalid TPC texture format."
            raise ValueError(msg)

        width, height = self._tpc.dimensions()

        self._writer.write_uint32(size)
        self._writer.write_single(0.0)
        self._writer.write_uint16(width)
        self._writer.write_uint16(height)
        self._writer.write_uint8(color_depth)
        self._writer.write_uint8(self._tpc.mipmap_count())
        self._writer.write_bytes(b"\x00" * 114)
        self._writer.write_bytes(bytes(data))
        self._writer.write_bytes(self._tpc.txi.encode("ascii"))
