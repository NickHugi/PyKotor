import struct

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.type import TARGET_TYPES, ResourceWriter, autoclose


class TPCBMPWriter(ResourceWriter):
    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tpc = tpc

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        width, height, data = self._tpc.convert(TPCTextureFormat.RGB, 0)
        assert data is not None
        file_size = 14 + 40 + (width * height * 3)

        # Header
        self._writer.write_string("BM")
        self._writer.write_uint32(file_size)
        self._writer.write_uint32(0)
        self._writer.write_uint32(54)

        # InfoHeader
        self._writer.write_uint32(40)
        self._writer.write_uint32(width)
        self._writer.write_uint32(height)
        self._writer.write_uint16(1)
        self._writer.write_uint16(24)
        self._writer.write_uint32(0)
        self._writer.write_uint32(0)
        self._writer.write_uint32(1)
        self._writer.write_uint32(1)
        self._writer.write_uint32(0)  # colors used
        self._writer.write_uint32(0)

        pixel_reader = BinaryReader.from_bytes(data)
        temp_pixels = []
        for _i in range(len(data) // 3):
            r = pixel_reader.read_uint8()
            g = pixel_reader.read_uint8()
            b = pixel_reader.read_uint8()
            temp_pixels.append([b, g, r])

        for i in range(len(temp_pixels)):
            x = i % width
            y = height - (i // width) - 1
            index = x + width * y
            self._writer.write_bytes(struct.pack("BBB", *temp_pixels[index]))
