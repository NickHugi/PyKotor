"""TPC binary reader/writer implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.manipulate.swizzle import deswizzle, swizzle  # noqa: F401
from pykotor.resource.formats.tpc.tpc_data import TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.formats.tpc.tpc_data import TPC, TPCMipmap
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

    # ... [TPCBinaryReader implementation remains unchanged]


class TPCBinaryWriter(ResourceWriter):
    """Used to write TPC instances as TPC binary data.

    File Structure:
    Header (128 bytes):
    - 0x00-0x03: Data size (uint32 LE) - 0 if uncompressed
    - 0x04-0x07: Alpha blend float (4 bytes)
    - 0x08-0x09: Width (uint16 LE)
    - 0x0A-0x0B: Height (uint16 LE)
    - 0x0C: Encoding (uint8)
    - 0x0D: Mipmap count (uint8)
    - 0x0E-0x7F: Reserved (114 bytes)

    Followed by:
    - Texture data
    - TXI data (optional)
    """

    MAX_DIMENSIONS: Literal[0x8000] = TPCBinaryReader.MAX_DIMENSIONS
    IMG_DATA_START_OFFSET: Literal[0x80] = TPCBinaryReader.IMG_DATA_START_OFFSET

    # Encoding values from TPCObject.cs
    ENCODING_GRAY: Literal[0x01] = 0x01
    ENCODING_RGB: Literal[0x02] = 0x02
    ENCODING_RGBA: Literal[0x04] = 0x04
    ENCODING_BGRA: Literal[0x0C] = 0x0C

    def __init__(self, tpc: TPC, target: TARGET_TYPES):
        super().__init__(target)
        self._tpc: TPC = tpc
        self._layer_count: int = len(tpc.layers) if tpc.layers else 0
        self._mipmap_count: int = len(tpc.layers[0].mipmaps) if tpc.layers and tpc.layers[0].mipmaps else 0

    def _get_pixel_encoding(self, tpc_format: TPCTextureFormat) -> int:
        """Get the pixel encoding value for the given format."""
        if tpc_format == TPCTextureFormat.Greyscale:
            return self.ENCODING_GRAY
        if tpc_format in (TPCTextureFormat.RGB, TPCTextureFormat.DXT1):
            return self.ENCODING_RGB
        if tpc_format in (TPCTextureFormat.RGBA, TPCTextureFormat.DXT5):
            return self.ENCODING_RGBA
        if tpc_format == TPCTextureFormat.BGRA:
            return self.ENCODING_BGRA
        raise ValueError(f"Invalid TPC texture format: {tpc_format}")

    def _validate_dimensions(
        self,
        width: int,
        height: int,
    ) -> None:
        """Validate the texture dimensions."""
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")
        if width >= self.MAX_DIMENSIONS or height >= self.MAX_DIMENSIONS:
            raise ValueError(f"Dimensions exceed maximum allowed: {width}x{height}")

    @autoclose
    def write(self):
        """Write the TPC data to the target."""
        if not self._tpc.layers:
            raise ValueError("TPC contains no layers")

        width, height = self._tpc.dimensions()
        tpc_format: TPCTextureFormat = self._tpc.format()

        # Validate dimensions
        self._validate_dimensions(width, height)

        # Handle animated textures and cubemaps
        layer_width: int = width
        original_height = layer_height = height

        if self._tpc.is_animated:
            # From TPCObject.cs checkAnimated()
            txi: TXI = self._tpc._txi  # noqa: SLF001
            numx: int = txi.features.numx or 1
            numy: int = txi.features.numy or 1
            layer_width: int = width // numx
            layer_height: int = height // numy
            self._layer_count = numx * numy
            if layer_width <= 0 or layer_height <= 0:
                raise ValueError(f"Invalid layer dimensions ({layer_width}x{layer_height}) for animated texture")

        elif self._tpc.is_cube_map:
            # From TPCObject.cs checkCubeMap()
            if self._layer_count != 6:  # noqa: PLR2004
                raise ValueError(f"Cubemap must have exactly 6 layers, found {self._layer_count}")
            height: int = layer_height * 6

        # Calculate data size
        data_size: int = tpc_format.get_size(layer_width, layer_height)
        if self._tpc.is_animated:
            data_size *= self._layer_count

        # Write header (128 bytes)
        pixel_encoding: int = self._get_pixel_encoding(tpc_format)
        self._writer.write_uint32(0 if not tpc_format.is_dxt() else data_size)  # 0x00-0x03: Data size
        self._writer.write_single(1.0)  # 0x04-0x07: Alpha blending (default 1.0)
        self._writer.write_uint16(width)  # 0x08-0x09: Width
        self._writer.write_uint16(height if not self._tpc.is_cube_map else original_height)  # 0x0A-0x0B: Height
        self._writer.write_uint8(pixel_encoding)  # 0x0C: Pixel encoding
        self._writer.write_uint8(self._mipmap_count)  # 0x0D: Mipmap count
        self._writer.write_bytes(bytes(0x72))  # 0x0E-0x7F: Reserved padding

        # Write texture data for each layer
        for layer in self._tpc.layers:
            curr_width, curr_height = layer_width, layer_height

            for mipmap_idx in range(self._mipmap_count):
                if mipmap_idx >= len(layer.mipmaps):
                    break

                mipmap: TPCMipmap = layer.mipmaps[mipmap_idx]
                expected_width: int = max(1, curr_width)
                expected_height: int = max(1, curr_height)

                if (
                    mipmap.width != expected_width
                    or mipmap.height != expected_height
                ):
                    raise ValueError(
                        f"Invalid mipmap dimensions at level {mipmap_idx}."  # noqa: E501
                        f" Expected {expected_width}x{expected_height},"
                        f" got {mipmap.width}x{mipmap.height}",
                    )

                mipmap_data: bytearray = mipmap.data
                if (  # From TPCObject.cs
                    tpc_format == TPCTextureFormat.BGRA  # swizzle only BGRA formats.
                    and (curr_width & (curr_width - 1)) == 0  # Is power of 2
                ):
                    mipmap_data = swizzle(mipmap_data, curr_width, curr_height, tpc_format.bytes_per_pixel())

                self._writer.write_bytes(bytes(mipmap_data))

                curr_width: int = max(curr_width >> 1, 1)
                curr_height: int = max(curr_height >> 1, 1)

                if curr_width < 1 and curr_height < 1:
                    break

        # Rest of the file format is ascii TXI data.
        if not str(self._tpc.txi).strip():
            return

        txi_data: str = self._tpc.txi.strip().replace("\r\n", "\n").replace("\n", "\r\n")
        if not txi_data.endswith("\r\n"):
            txi_data += "\r\n"
        self._writer.write_bytes(txi_data.encode("ascii"))
