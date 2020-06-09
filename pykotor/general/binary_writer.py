import io
import struct


class BinaryWriter:
    @classmethod
    def from_path(cls, path):
        stream = open(path, 'wb')
        return BinaryWriter(stream)

    @classmethod
    def from_data(cls, data=None):
        if data is None:
            data = bytearray()
        stream = io.BytesIO(data)
        return BinaryWriter(stream)

    def get_data(self):
        self.stream.seek(0)
        return self.stream.read()

    def __init__(self, stream):
        self.stream = stream

    def write_string(self, string, padding_length=0, padding=b'\0'):
        if padding_length != 0:
            string = string[:padding_length]
            string.rjust(padding_length, padding)
        self.stream.write(string.encode())

    def write_uint8(self, value, big_endian=False):
        endian = '>' if big_endian else '<'
        self.stream.write(struct.pack(endian + 'B', value))

    def write_int8(self, value, big_endian=False):
        endian = '>' if big_endian else '<'
        self.stream.write(struct.pack(endian + 'b', value))

    def write_uint16(self, value, big_endian=False):
        endian = '>' if big_endian else '<'
        self.stream.write(struct.pack(endian + 'H', value))

    def write_int16(self, value, big_endian=False):
        endian = '>' if big_endian else '<'
        self.stream.write(struct.pack(endian + 'h', value))

    def write_uint32(self, value, big_endian=False):
        endian = '>' if big_endian else '<'
        self.stream.write(struct.pack(endian + 'I', value))

    def write_int32(self, value, big_endian=False):
        endian = '>' if big_endian else '<'
        self.stream.write(struct.pack(endian + 'i', value))

    def write_float32(self, value, big_endian=False):
        endian = '>' if big_endian else '<'
        self.stream.write(struct.pack(endian + 'f', value))

    def write_bytes(self, value):
        self.stream.write(value)

    def write_padding(self, byte, length):
        for i in range(length):
            self.stream.write(byte)

    def write_vertex(self, value, big_endian=False):
        self.write_float32(value.x, big_endian)
        self.write_float32(value.y, big_endian)
        self.write_float32(value.z, big_endian)

    def skip(self, length):
        self.stream.read(length)

    def seek(self, position):
        self.stream.seek(position)

    def size(self):
        original_position = self.position()
        self.stream.seek(0, 2)
        size = self.position()
        self.stream.seek(original_position)
        return size

    def close(self):
        self.stream.close()

    def position(self):
        return self.stream.tell()