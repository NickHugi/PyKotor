from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.manipulate.rotate import rotate_rgb_rgba
from pykotor.resource.formats.tpc.manipulate.swizzle import deswizzle, swizzle  # noqa: F401
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCLayer, TPCMipmap, TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.resource.formats.txi.txi_data import TXI
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class TPCBinaryReader(ResourceReader):
    """Used to read TPC binary data."""

    MAX_DIMENSIONS: int = 0x8000
    IMG_DATA_START_OFFSET: Literal[0x80] = 0x80

    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int | None = None):
        super().__init__(source, offset, size)
        self._tpc: TPC = TPC()

    @autoclose
    def load(self) -> TPC:
        self._tpc = TPC()
        self._layer_count = 1
        data_size: int = self._reader.read_uint32()  # 0x0
        compressed: bool = data_size != 0
        self._reader.skip(4)  # 0x4
        width: int = self._reader.read_uint16()  # 0x8
        height: int = self._reader.read_uint16()  # 0xA

        if max(width, height) >= self.MAX_DIMENSIONS:
            raise ValueError(f"Unsupported image dimensions ({width}x{height})")

        pixel_type, self._mipmap_count = self._reader.read_uint8(), self._reader.read_uint8()
        tpc_format = TPCTextureFormat.Invalid
        if compressed:
            tpc_format = {2: TPCTextureFormat.DXT1, 4: TPCTextureFormat.DXT5}.get(pixel_type, TPCTextureFormat.Invalid)
        else:
            tpc_format = {1: TPCTextureFormat.Greyscale, 2: TPCTextureFormat.RGB, 4: TPCTextureFormat.RGBA, 12: TPCTextureFormat.BGRA}.get(pixel_type, TPCTextureFormat.Invalid)

        if tpc_format == TPCTextureFormat.Invalid:
            raise ValueError(f"Unsupported texture format (pixel_type: {pixel_type}, compressed: {compressed})")
        self._tpc._format = tpc_format  # noqa: SLF001

        total_cube_sides: Literal[6] = 6
        if not compressed:
            data_size = tpc_format.get_size(width, height)

        elif (
            height != 0  # noqa: PLR2004
            and width != 0
            and int(height / width) == total_cube_sides
        ):
            self._tpc.is_cube_map = True
            height = int(height / total_cube_sides)
            self._layer_count = total_cube_sides

        complete_data_size: int = data_size
        w, h = width, height
        for _ in range(self._mipmap_count-1):
            w = max(w >> 1, 1)
            h = max(h >> 1, 1)
            complete_data_size += tpc_format.get_size(w, h)

        complete_data_size *= self._layer_count

        self._reader.skip(0x72 + complete_data_size)
        txi_data_size: int = self._reader.size() - self._reader.position()
        if txi_data_size > 0:
            self._tpc.txi = self._reader.read_string(
                txi_data_size,
                encoding="ascii",
                errors="ignore",
            )

        txi: TXI = self._tpc._txi  # noqa: SLF001
        self._tpc.is_animated =  bool(
            self._tpc.txi
            and self._tpc.txi.strip()
            and txi.get_features().proceduretype.lower() == "cycle"  # noqa: SLF001
            and txi.get_features().numx  # noqa: PLR2004, SLF001
            and txi.get_features().numy  # noqa: SLF001
            and txi.get_features().fps  # noqa: SLF001
        )

        if self._tpc.is_animated:
            txi: TXI = self._tpc._txi  # noqa: SLF001
            self._layer_count = txi.get_features().numx * txi.get_features().numy
            width //= txi.get_features().numx
            height //= txi.get_features().numy
            data_size //= self._layer_count
            w, h = width, height
            self._mipmap_count = 0
            while w > 0 and h > 0:
                w /= 2
                h /= 2
                self._mipmap_count += 1

        if compressed and not self._tpc.is_animated:
            expected_size = (width * height) // 2 if tpc_format == TPCTextureFormat.DXT1 else width * height
            if data_size != expected_size:
                raise ValueError(f"Invalid data size for a texture of {width}x{height} pixels and format {tpc_format!r}")

        self._reader.seek(0x80)
        if width <= 0 or height <= 0 or width >= self.MAX_DIMENSIONS or height >= self.MAX_DIMENSIONS or tpc_format is TPCTextureFormat.Invalid:
            raise ValueError(f"Invalid dimensions ({width}x{height}) for format {tpc_format!r}")

        full_image_data_size = tpc_format.get_size(width, height)
        full_data_size = self._reader.size() - 0x80
        if full_data_size < (self._layer_count * full_image_data_size):
            raise ValueError(f"Insufficient data for image. Expected at least {hex(self._layer_count * full_image_data_size)} bytes, but only {hex(full_data_size)} bytes are available.")

        for _ in range(self._layer_count):
            layer = TPCLayer()
            self._tpc.layers.append(layer)
            layer_width, layer_height = width, height
            layer_size = tpc_format.get_size(layer_width, layer_height) if self._tpc.is_animated else data_size

            for _ in range(self._mipmap_count):
                mm_width, mm_height = max(1, layer_width), max(1, layer_height)
                mm_size = max(layer_size, tpc_format.min_size())
                mm = TPCMipmap(width=mm_width, height=mm_height, tpc_format=tpc_format, data=bytearray(self._reader.read_bytes(mm_size)))
                layer.mipmaps.append(mm)

                if full_data_size <= mm_size or mm_size < tpc_format.get_size(mm_width, mm_height):
                    break

                full_data_size -= mm_size
                layer_width, layer_height = layer_width >> 1, layer_height >> 1
                layer_size = tpc_format.get_size(layer_width, layer_height)

                if layer_width < 1 and layer_height < 1:
                    break

        if self._tpc.is_cube_map:
            self._tpc.convert(TPCTextureFormat.RGB if self._tpc.format() == TPCTextureFormat.DXT1 else TPCTextureFormat.RGBA)
            rotation: tuple[int, int, int, int, int, int] = (3, 1, 0, 2, 2, 0)
            for i, layer in enumerate(self._tpc.layers):
                for mipmap in layer.mipmaps:
                    rotate_rgb_rgba(mipmap.data, mipmap.width, mipmap.height, self._tpc.format().bytes_per_pixel(), rotation[i])
            self._tpc.layers[0].mipmaps, self._tpc.layers[1].mipmaps = self._tpc.layers[1].mipmaps, self._tpc.layers[0].mipmaps

        elif self._tpc.format() == TPCTextureFormat.BGRA:
            for layer in self._tpc.layers:
                for mipmap in layer.mipmaps:
                    mipmap.data = deswizzle(mipmap.data, mipmap.width, mipmap.height, self._tpc.format().bytes_per_pixel())

        return self._tpc


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
    def write(self):  # FIXME(th3w1zard1): this is a mess. Needs to be refactored since we've added cubemap/animation support.
        data = bytearray()
        compressed_size: int = 0

        width, height = self._tpc.dimensions()
        tpc_format: TPCTextureFormat = self._tpc.format()
        requires_swizzling = False
        if tpc_format is TPCTextureFormat.Greyscale:
            pixel_type = 1
        elif tpc_format is (TPCTextureFormat.RGB, TPCTextureFormat.DXT1):
            pixel_type = 2
        elif tpc_format in (TPCTextureFormat.RGBA, TPCTextureFormat.DXT5):
            pixel_type = 4
        elif tpc_format is TPCTextureFormat.BGRA:
            pixel_type = 12
            requires_swizzling = True  # noqa: F841
        else:
            msg = "Invalid TPC texture format."
            raise ValueError(msg)

        for layer in self._tpc.layers:
            for mm in layer.mipmaps:
                if requires_swizzling:
                    mm.data = swizzle(mm.data, mm.width, mm.height, 4)
                data += mm.data
                compressed_size += mm.tpc_format.get_size(mm.width, mm.height)

        if not tpc_format.is_dxt():
            compressed_size = 0

        self._writer.write_uint32(compressed_size)
        self._writer.write_single(0.0)
        self._writer.write_uint16(width)
        self._writer.write_uint16(height)
        self._writer.write_uint8(pixel_type)
        self._writer.write_uint8(len(self._tpc.layers[0].mipmaps))
        self._writer.write_bytes(b"\x00" * 114)
        self._writer.write_bytes(bytes(data))
        self._writer.write_bytes(self._tpc.txi.encode("ascii"))

