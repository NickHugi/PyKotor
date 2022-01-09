import struct

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.type import ResourceWriter, TARGET_TYPES


class TPCTGAWriter(ResourceWriter):
    def __init__(self, tpc: TPC, target: TARGET_TYPES):
        super().__init__(target)
        self._tpc = tpc

    def write(self, auto_close: bool = True) -> None:
        width, height = self._tpc.dimensions()

        self._writer.write_uint8(0)
        self._writer.write_uint8(0)
        self._writer.write_uint8(2)
        self._writer.write_bytes(bytes(5))
        self._writer.write_uint16(0)
        self._writer.write_uint16(0)
        self._writer.write_uint16(width)
        self._writer.write_uint16(height)
        self._writer.write_uint8(32)
        self._writer.write_uint8(40)

        width, height, data = self._tpc.convert(TPCTextureFormat.RGBA, 0)
        pixel_reader = BinaryReader.from_bytes(data)
        for i in range(len(data) // 4):
            r = pixel_reader.read_uint8()
            g = pixel_reader.read_uint8()
            b = pixel_reader.read_uint8()
            a = pixel_reader.read_uint8()
            self._writer.write_bytes(struct.pack('BBBB', b, g, r, a))
        
        if auto_close:
            self._writer.close()
