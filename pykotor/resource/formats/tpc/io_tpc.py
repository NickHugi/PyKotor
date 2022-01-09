from __future__ import annotations

from typing import Optional

from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceWriter, ResourceReader


class TPCBinaryReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._tpc: Optional[TPC] = None

    def load(self, auto_close: bool = True) -> TPC:
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
            mm_size = self._get_size(mm_width, mm_height, tpc_format)
            mipmaps.append(self._reader.read_bytes(mm_size))

            mm_width >>= 1
            mm_height >>= 1
            mm_width = max(mm_width, 1)
            mm_height = max(mm_height, 1)

        file_size = self._reader.size()
        txi = self._reader.read_string(file_size - self._reader.position())

        self._tpc.txi_str = txi
        self._tpc.set(width, height, mipmaps, tpc_format)

        if auto_close:
            self._reader.close()

        return self._tpc

    def _get_size(self, width: int, height: int, tpc_format: TPCTextureFormat) -> int:
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


class TPCBinaryWriter(ResourceWriter):
    def __init__(self, tpc: TPC, target: TARGET_TYPES):
        super().__init__(target)
        self._tpc = tpc

    def write(self, auto_close: bool = True) -> None:
        # TODO

        if auto_close:
            self._writer.close()

        raise NotImplementedError
