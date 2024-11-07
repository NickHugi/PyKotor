from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.manipulate.rotate import rotate_rgb_rgba
from pykotor.resource.formats.tpc.manipulate.swizzle import deswizzle, swizzle  # noqa: F401
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCLayer, TPCMipmap, TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.formats.txi.txi_data import TXI
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class TPCBinaryReader(ResourceReader):
    """Used to read TPC binary data."""

    MAX_DIMENSIONS: Literal[0x8000] = 0x8000
    IMG_DATA_START_OFFSET: Literal[0x80] = 0x80

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
    ):
        super().__init__(source, offset, size)

    @autoclose
    def load(self) -> TPC:  # noqa: PLR0912, C901, PLR0915
        self._tpc: TPC = TPC()
        self._layer_count: int = 1
        self._mipmap_count: int = 0

        data_size: int = self._reader.read_uint32()  # 0x0
        compressed: bool = data_size != 0
        self._reader.skip(4)  # 0x4
        width: int = self._reader.read_uint16()  # 0x8
        height: int = self._reader.read_uint16()  # 0xA

        if max(width, height) >= self.MAX_DIMENSIONS:
            raise ValueError(f"Unsupported image dimensions ({width}x{height})")

        pixel_type, self._mipmap_count = (
            self._reader.read_uint8(),
            self._reader.read_uint8(),
        )
        tpc_format: TPCTextureFormat = {
            (True, 2): TPCTextureFormat.DXT1,
            (True, 4): TPCTextureFormat.DXT5,
            (False, 1): TPCTextureFormat.Greyscale,
            (False, 2): TPCTextureFormat.RGB,
            (False, 4): TPCTextureFormat.RGBA,
            (False, 12): TPCTextureFormat.BGRA,
        }.get((compressed, pixel_type), TPCTextureFormat.Invalid)
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
        for _ in range(self._mipmap_count - 1):
            w: int = max(w >> 1, 1)
            h: int = max(h >> 1, 1)
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
        self._tpc.is_animated = bool(
            self._tpc.txi
            and self._tpc.txi.strip()
            and txi.features.proceduretype
            and txi.features.proceduretype.lower() == "cycle"  # noqa: SLF001
            and txi.features.numx
            and txi.features.numy
            and txi.features.fps
        )

        if self._tpc.is_animated:
            txi: TXI = self._tpc._txi  # noqa: SLF001
            self._layer_count = (txi.features.numx or 1) * (txi.features.numy or 1)
            width //= txi.features.numx or 1
            height //= txi.features.numy or 1
            data_size //= self._layer_count
            w, h = width, height
            self._mipmap_count = 0
            while w > 0 and h > 0:
                w //= 2
                h //= 2
                self._mipmap_count += 1

        if compressed and not self._tpc.is_animated:
            expected_size: int = (width * height) // 2 if tpc_format == TPCTextureFormat.DXT1 else width * height
            if data_size != expected_size:
                raise ValueError(f"Invalid data size for a texture of {width}x{height}" f" pixels and format {tpc_format!r}")

        self._reader.seek(self.IMG_DATA_START_OFFSET)
        if width <= 0 or height <= 0 or width >= self.MAX_DIMENSIONS or height >= self.MAX_DIMENSIONS:
            raise ValueError(f"Invalid dimensions ({width}x{height}) for format {tpc_format!r}")

        full_image_data_size: int = tpc_format.get_size(
            width,
            height,
        )
        full_data_size: int = self._reader.size() - self.IMG_DATA_START_OFFSET
        if full_data_size < (self._layer_count * full_image_data_size):
            raise ValueError(
                f"Insufficient data for image. Expected at least {hex(self._layer_count * full_image_data_size)} bytes,"
                f" but only {hex(full_data_size)} bytes are available."
            )

        for _ in range(self._layer_count):
            layer = TPCLayer()
            self._tpc.layers.append(layer)
            layer_width, layer_height = width, height
            layer_size: int = tpc_format.get_size(layer_width, layer_height) if self._tpc.is_animated else data_size

            for _ in range(self._mipmap_count):
                mm_width, mm_height = (
                    max(1, layer_width),
                    max(1, layer_height),
                )
                mm_size: int = max(
                    layer_size,
                    tpc_format.min_size(),
                )
                mm = TPCMipmap(
                    width=mm_width,
                    height=mm_height,
                    tpc_format=tpc_format,
                    data=bytearray(self._reader.read_bytes(mm_size)),
                )
                layer.mipmaps.append(mm)

                if full_data_size <= mm_size or mm_size < tpc_format.get_size(mm_width, mm_height):
                    break

                full_data_size -= mm_size
                layer_width, layer_height = (
                    layer_width >> 1,
                    layer_height >> 1,
                )
                layer_size = tpc_format.get_size(
                    layer_width,
                    layer_height,
                )

                if layer_width < 1 and layer_height < 1:
                    break

        if self._tpc.format() == TPCTextureFormat.BGRA:
            for layer in self._tpc.layers:
                for mipmap in layer.mipmaps:
                    mipmap.data = deswizzle(
                        mipmap.data,
                        mipmap.width,
                        mipmap.height,
                        self._tpc.format().bytes_per_pixel(),
                    )

        return self._tpc

    def _normalize_cubemaps(self):
        self._tpc.convert(TPCTextureFormat.RGB if self._tpc.format() == TPCTextureFormat.DXT1 else TPCTextureFormat.RGBA)
        rotation: tuple[int, int, int, int, int, int] = (3, 1, 0, 2, 2, 0)
        for i, layer in enumerate(self._tpc.layers):
            for mipmap in layer.mipmaps:
                rotate_rgb_rgba(
                    mipmap.data,
                    mipmap.width,
                    mipmap.height,
                    self._tpc.format().bytes_per_pixel(),
                    rotation[i],
                )
        self._tpc.layers[0].mipmaps, self._tpc.layers[1].mipmaps = (
            self._tpc.layers[1].mipmaps,
            self._tpc.layers[0].mipmaps,
        )


class TPCBinaryWriter(ResourceWriter):
    """Used to write TPC instances as TPC binary data."""

    MAX_DIMENSIONS: Literal[0x8000] = TPCBinaryReader.MAX_DIMENSIONS
    IMG_DATA_START_OFFSET: Literal[0x80] = TPCBinaryReader.IMG_DATA_START_OFFSET

    def __init__(self, tpc: TPC, target: TARGET_TYPES):
        super().__init__(target)
        self._tpc: TPC = tpc
        self._layer_count: int = len(tpc.layers) if tpc.layers else 0
        self._mipmap_count: int = len(tpc.layers[0].mipmaps) if tpc.layers and tpc.layers[0].mipmaps else 0

    def _get_pixel_type(self, tpc_format: TPCTextureFormat) -> int:
        """Get the pixel type value for the given format."""
        if tpc_format == TPCTextureFormat.Greyscale:
            return 1
        if tpc_format in (TPCTextureFormat.RGB, TPCTextureFormat.DXT1):
            return 2
        if tpc_format in (TPCTextureFormat.RGBA, TPCTextureFormat.DXT5):
            return 4
        if tpc_format == TPCTextureFormat.BGRA:
            return 12
        raise ValueError(f"Invalid TPC texture format: {tpc_format}")

    def _validate_dimensions(self, width: int, height: int) -> None:
        """Validate the texture dimensions."""
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")
        if width >= self.MAX_DIMENSIONS or height >= self.MAX_DIMENSIONS:
            raise ValueError(f"Dimensions exceed maximum allowed: {width}x{height}")

    def _calculate_data_size(self, width: int, height: int, tpc_format: TPCTextureFormat) -> int:
        """Calculate the complete data size for all layers and mipmaps."""
        if not tpc_format.is_dxt():
            return tpc_format.get_size(width, height)

        if tpc_format == TPCTextureFormat.DXT1:
            return max(8, (width * height) // 2)
        if tpc_format in (TPCTextureFormat.DXT3, TPCTextureFormat.DXT5):
            return max(16, width * height)
        return 0

    @autoclose
    def write(self):  # noqa: C901, PLR0912, PLR0915
        """Write the TPC data to the target."""
        if not self._tpc.layers:
            raise ValueError("TPC contains no layers")

        width, height = self._tpc.dimensions()
        tpc_format: TPCTextureFormat = self._tpc.format()

        # Validate dimensions
        self._validate_dimensions(width, height)

        # Handle animated textures and cubemaps
        layer_width, layer_height = width, height

        if self._tpc.is_animated:
            txi: TXI = self._tpc._txi  # noqa: SLF001
            numx: int = txi.features.numx or 1
            numy: int = txi.features.numy or 1
            layer_width: int = width // numx
            layer_height: int = height // numy
            self._layer_count = numx * numy
            if layer_width <= 0 or layer_height <= 0:
                raise ValueError(f"Invalid layer dimensions ({layer_width}x{layer_height}) for animated texture")

        elif self._tpc.is_cube_map:
            if self._layer_count != 6:  # noqa: PLR2004
                raise ValueError(f"Cubemap must have exactly 6 layers, found {self._layer_count}")
            layer_height = height // 6

        # Calculate data size
        data_size = self._calculate_data_size(layer_width, layer_height, tpc_format)
        if self._tpc.is_animated:
            data_size *= self._layer_count

        # Write header
        pixel_type: int = self._get_pixel_type(tpc_format)
        self._writer.write_uint32(data_size)  # Data size
        self._writer.write_single(0.0)  # Alpha blending
        self._writer.write_uint16(width)  # Width
        self._writer.write_uint16(height)  # Height
        self._writer.write_uint8(pixel_type)  # Pixel format
        self._writer.write_uint8(self._mipmap_count)  # Mipmap count
        self._writer.write_bytes(bytes(0x72))  # Padding

        # Write texture data for each layer
        for layer in self._tpc.layers:
            curr_width, curr_height = layer_width, layer_height

            for mipmap_idx in range(self._mipmap_count):
                if mipmap_idx >= len(layer.mipmaps):
                    break

                mipmap: TPCMipmap = layer.mipmaps[mipmap_idx]
                expected_width: int = max(1, curr_width)
                expected_height: int = max(1, curr_height)

                if mipmap.width != expected_width or mipmap.height != expected_height:
                    raise ValueError(
                        f"Invalid mipmap dimensions at level {mipmap_idx}. " f"Expected {expected_width}x{expected_height}, " f"got {mipmap.width}x{mipmap.height}"
                    )  # noqa: E501

                mipmap_data: bytearray = mipmap.data
                if tpc_format == TPCTextureFormat.BGRA:
                    mipmap_data = swizzle(mipmap_data, curr_width, curr_height, tpc_format.bytes_per_pixel())

                self._writer.write_bytes(bytes(mipmap_data))

                curr_width: int = max(curr_width >> 1, 1)
                curr_height: int = max(curr_height >> 1, 1)

                if curr_width < 1 and curr_height < 1:
                    break

        # Write TXI data if present
        if self._tpc.txi:
            txi_data: str = self._tpc.txi.strip().replace("\r\n", "\n").replace("\n", "\r\n")
            if not txi_data.endswith("\r\n"):
                txi_data += "\r\n"
            self._writer.write_bytes(txi_data.encode("ascii"))
