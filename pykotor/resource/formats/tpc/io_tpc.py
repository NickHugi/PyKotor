from __future__ import annotations

from typing import Optional

from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceWriter, ResourceReader, autoclose


def _get_size(
        width: int,
        height: int,
        tpc_format: TPCTextureFormat
) -> int:
    if tpc_format is TPCTextureFormat.Greyscale:
        return width * height * 1
    elif tpc_format is TPCTextureFormat.RGB:
        return width * height * 3
    elif tpc_format is TPCTextureFormat.RGBA:
        return width * height * 4
    elif tpc_format is TPCTextureFormat.DXT1:
        return max(8, ((width + 3) // 4) * ((height + 3) // 4) * 8)
    elif tpc_format is TPCTextureFormat.DXT5:
        return max(16, ((width + 3) // 4) * ((height + 3) // 4) * 16)


class TPCBinaryReader(ResourceReader):
    def __init__(
            self,
            source: SOURCE_TYPES,
            offset: int = 0,
            size: int = 0
    ):
        super().__init__(source, offset, size)
        self._tpc: Optional[TPC] = None

    @autoclose
    def load(
            self,
            auto_close: bool = True
    ) -> TPC:
        self._tpc = TPC()

        size = self._reader.read_uint32()
        min_size = -1
        compressed = size != 0

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
        else:
            if color_depth == 1:
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

        mipmaps = []
        mm_width, mm_height = width, height
        for i in range(mipmap_count):
            mm_size = _get_size(mm_width, mm_height, tpc_format)
            mm_data = self._reader.read_bytes(mm_size)
            mipmaps.append(mm_data)

            mm_width >>= 1
            mm_height >>= 1
            mm_width = max(mm_width, 1)
            mm_height = max(mm_height, 1)

        file_size = self._reader.size()
        txi = self._reader.read_string(file_size - self._reader.position())

        self._tpc.txi = txi
        self._tpc.set(width, height, mipmaps, tpc_format)

        return self._tpc


class TPCBinaryWriter(ResourceWriter):
    def __init__(
            self,
            tpc: TPC,
            target: TARGET_TYPES
    ):
        super().__init__(target)
        self._tpc = tpc

    @autoclose
    def write(
            self,
            auto_close: bool = True
    ) -> None:

        data = bytearray()
        size = 0

        for i in range(self._tpc.mipmap_count()):
            width, height, texture_format, mm_data = self._tpc.get(i)
            data += mm_data
            size += _get_size(width, height, texture_format)

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
            raise ValueError("Invalid TPC texture format.")

        width, height = self._tpc.dimensions()

        self._writer.write_uint32(size)
        self._writer.write_single(0.0)
        self._writer.write_uint16(width)
        self._writer.write_uint16(height)
        self._writer.write_uint8(encoding)
        self._writer.write_uint8(self._tpc.mipmap_count())
        self._writer.write_bytes(b'\x00' * 114)
        self._writer.write_bytes(data)
        self._writer.write_bytes(self._tpc.txi.encode('ascii'))
