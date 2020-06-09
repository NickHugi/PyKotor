import io
import struct

from pykotor.data.color import Color
from pykotor.data.quaternion import Quaternion
from pykotor.data.uv import UV
from pykotor.data.vertex import Vertex


class BinaryReader:
    def __init__(self, stream):
        self.stream = stream

    @classmethod
    def from_path(cls, path):
        file = open(path, 'rb')
        return cls.wrap_stream(file)

    @classmethod
    def from_data(cls, data):
        stream = io.BytesIO(data)
        return BinaryReader(stream)

    @classmethod
    def from_stream(cls, stream):
        return BinaryReader(stream)

    def read_string(self, length):
        string = self.stream.read(length).decode('ascii', errors='ignore')
        if '\0' in string:
            string = string[:string.index('\0')].rstrip('\0')
            string = string.replace('\0', '')
        return string

    def read_terminated_string(self, terminator):
        string = ""
        char = ""
        while char != terminator:
            string += char
            char = self.stream.read(1).decode('ascii', errors='ignore')
        return string

    def read_uint8(self, big_endian=False):
        endian = '>' if big_endian else '<'
        return struct.unpack(endian + "B", self.stream.read(1))[0]

    def read_int8(self, big_endian=False):
        endian = '>' if big_endian else '<'
        return struct.unpack(endian + "b", self.stream.read(1))[0]

    def read_uint16(self, big_endian=False):
        endian = '>' if big_endian else '<'
        return struct.unpack(endian + "H", self.stream.read(2))[0]

    def read_int16(self, big_endian=False):
        endian = '>' if big_endian else '<'
        return struct.unpack(endian + "h", self.stream.read(2))[0]

    def read_uint32(self, big_endian=False):
        endian = '>' if big_endian else '<'
        return struct.unpack(endian + "I", self.stream.read(4))[0]

    def read_int32(self, big_endian=False):
        endian = '>' if big_endian else '<'
        return struct.unpack(endian + "i", self.stream.read(4))[0]

    def read_float32(self, big_endian=False):
        endian = '>' if big_endian else '<'
        return struct.unpack(endian + "f", self.stream.read(4))[0]

    def read_bytes(self, length):
        return self.stream.read(length)

    def read_vertex(self, big_endian=False):
        x = self.read_float32(big_endian)
        y = self.read_float32(big_endian)
        z = self.read_float32(big_endian)
        return Vertex.from_position(x, y, z)

    def read_quaternion(self, big_endian=False):
        x = self.read_float32(big_endian)
        y = self.read_float32(big_endian)
        z = self.read_float32(big_endian)
        w = self.read_float32(big_endian)
        return Quaternion.from_rotation(x, y, z, w)

    def read_uv(self, big_endian=False):
        uv = UV()
        uv.u = self.read_float32(big_endian)
        uv.v = self.read_float32(big_endian)
        return uv

    def read_color(self, big_endian=False):
        r = self.read_float32(big_endian)
        g = self.read_float32(big_endian)
        b = self.read_float32(big_endian)
        return Color.from_rgb_float(r, g, b)

    def skip(self, length):
        self.stream.read(length)

    def seek(self, position):
        self.stream.seek(position)

    def position(self):
        return self.stream.tell()

    def size(self):
        original_position = self.position()
        self.stream.seek(0, 2)
        size = self.position()
        self.stream.seek(original_position)
        return size

    def peek(self):
        byte = self.read_uint8()
        self.stream.seek(-1, 1)
        return byte
