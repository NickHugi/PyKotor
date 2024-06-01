from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.tpc_data import TPC, TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def _get_size(
    width: int,
    height: int,
    tpc_format: TPCTextureFormat,
) -> int | None:
    """Calculates the size of a texture in bytes based on its format.

    Args:
    ----
        width: int - Width of the texture in pixels
        height: int - Height of the texture in pixels
        tpc_format: TPCTextureFormat - Format of the texture

    Returns:
    -------
        int - Size of the texture in bytes, or None if unknown format

    Processing Logic:
    ----------------
        - Calculate size based on format:
            - Greyscale: width * height * 1 byte per pixel
            - RGB: width * height * 3 bytes per pixel
            - RGBA: width * height * 4 bytes per pixel
            - DXT1/DXT5: Compressed formats, size calculated differently
        - Return None if invalid format.
    """
    if tpc_format is TPCTextureFormat.Greyscale:
        return width * height * 1
    if tpc_format is TPCTextureFormat.RGB:
        return width * height * 3
    if tpc_format is TPCTextureFormat.RGBA:
        return width * height * 4
    if tpc_format is TPCTextureFormat.DXT1:
        return max(8, ((width + 3) // 4) * ((height + 3) // 4) * 8)
    if tpc_format is TPCTextureFormat.DXT5:
        return max(16, ((width + 3) // 4) * ((height + 3) // 4) * 16)
    return None


class TPCBinaryReader(ResourceReader):
    """Used to read TPC binary data."""
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._tpc: TPC | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> TPC:
        """Loads a texture from the reader and returns a TPC object.

        Args:
        ----
            auto_close: Whether to close the reader after loading (default True)

        Returns:
        -------
            TPC: The loaded TPC texture object

        Processing Logic:
        ----------------
            - Reads header values like size, dimensions, format
            - Skips unnecessary data
            - Loops to read each mipmap level
            - Sets TPC data and returns the object
        """
        self._tpc = TPC()

        size: int = self._reader.read_uint32()
        min_size = -1
        compressed: bool = size != 0

        self._reader.skip(4)

        width, height = self._reader.read_uint16(), self._reader.read_uint16()
        color_depth = self._reader.read_uint8()
        mipmap_count = self._reader.read_uint8()
        self._reader.skip(114)

        tpc_format = TPCTextureFormat.Invalid
        if compressed:
            if color_depth == 2:
                tpc_format = TPCTextureFormat.DXT1
                min_size = 8
            elif color_depth == 4:
                tpc_format = TPCTextureFormat.DXT5
                min_size = 16
        elif color_depth == 1:
            tpc_format = TPCTextureFormat.Greyscale
            size = width * height
            min_size = 1
        elif color_depth == 2:
            tpc_format = TPCTextureFormat.RGB
            size = width * height * 3
            min_size = 3
        elif color_depth == 4:
            tpc_format = TPCTextureFormat.RGBA
            size = width * height * 4
            min_size = 4

        mipmaps: list[bytes] = []
        mm_width, mm_height = width, height
        for _ in range(mipmap_count):
            mm_size = _get_size(mm_width, mm_height, tpc_format) or min_size
            mm_data = self._reader.read_bytes(mm_size)
            mipmaps.append(mm_data)

            mm_width >>= 1
            mm_height >>= 1
            mm_width = max(mm_width, 1)
            mm_height = max(mm_height, 1)

        file_size = self._reader.size()
        txi = self._reader.read_string(file_size - self._reader.position(), encoding="ascii")

        self._tpc.txi = txi
        self._tpc.set_data(width, height, mipmaps, tpc_format)

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
    def write(
        self,
        auto_close: bool = True,
    ):
        """Writes the TPC texture data to the file stream.

        Args:
        ----
            auto_close: Whether to close the file stream after writing (default: True)

        Writes TPC texture data to file stream:
            - Gets texture data from TPC object
            - Writes header information like size, dimensions, encoding
            - Writes raw texture data
            - Writes TXI data
            - Optionally closes file stream..
        """
        data = bytearray()
        size: int = 0

        for i in range(self._tpc.mipmap_count()):
            width, height, texture_format, mm_data = self._tpc.get(i)
            assert mm_data is not None
            data += mm_data
            detsize = _get_size(width, height, texture_format)
            assert detsize is not None
            size += detsize

        if self._tpc.format() == TPCTextureFormat.RGBA:
            encoding = 4
            size = 0
        elif self._tpc.format() == TPCTextureFormat.RGB:
            encoding = 2
            size = 0
        elif self._tpc.format() == TPCTextureFormat.Greyscale:
            encoding = 1
            size = 0
        elif self._tpc.format() == TPCTextureFormat.DXT1:
            encoding = 2
        elif self._tpc.format() == TPCTextureFormat.DXT5:
            encoding = 4
        else:
            msg = "Invalid TPC texture format."
            raise ValueError(msg)

        width, height = self._tpc.dimensions()

        self._writer.write_uint32(size)
        self._writer.write_single(0.0)
        self._writer.write_uint16(width)
        self._writer.write_uint16(height)
        self._writer.write_uint8(encoding)
        self._writer.write_uint8(self._tpc.mipmap_count())
        self._writer.write_bytes(b"\x00" * 114)
        self._writer.write_bytes(data)
        self._writer.write_bytes(self._tpc.txi.encode("ascii"))
