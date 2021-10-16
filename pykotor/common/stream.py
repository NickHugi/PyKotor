"""
This module holds classes relating to read and write operations.
"""
from __future__ import annotations
import io
import struct
from typing import BinaryIO, Union, TextIO, List, overload
from pykotor.common.geometry import Vector3, Vector4, Vector2
from pykotor.common.language import LocalizedString
from multipledispatch import dispatch


def _endian_char(big) -> str:
    """
    Returns the character that represents either big endian or small endian in struct unpack.

    Args:
        big: True if big endian.

    Returns:
        Character representing either big or small endian.
    """
    return '>' if big else '<'


class BinaryReader:
    """
    Used for easy reading of binary files.
    """

    def __init__(self, stream: BinaryIO, offset: int = 0):
        self._stream = stream
        self._offset = offset
        #self._stream.seek(offset)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def from_file(cls, path: str, offset: int = 0) -> BinaryReader:
        """
        Returns a new BinaryReader with a stream established to the specified path.

        Args:
            path: Path of the file to open.
            offset: Number of bytes into the stream to consider as position 0.

        Returns:
            A new BinaryReader instance.
        """
        stream = open(path, 'rb')
        return BinaryReader(stream, offset)

    @classmethod
    def from_bytes(cls, data: bytes, offset: int = 0) -> BinaryReader:
        """
        Returns a new BinaryReader with a stream established to the bytes stored in memory.

        Args:
            data: The bytes of data.
            offset: Number of bytes into the stream to consider as position 0.

        Returns:
            A new BinaryReader instance.
        """
        stream = io.BytesIO(data)
        return BinaryReader(stream, offset)

    @staticmethod
    def load_file(path: str) -> bytes:
        """
        Returns bytes of a file at from specified path.

        Args:
            path: The path of the file.

        Returns:
            The bytes of the file.
        """
        with open(path, 'rb') as file:
            return file.read()

    def size(self) -> int:
        """
        Returns the total file size.

        Returns:
            The total file size.
        """
        pos = self._stream.tell()
        self._stream.seek(0, 2)
        size = self._stream.tell()
        self._stream.seek(pos)
        return size

    def close(self) -> None:
        """
        Closes the stream.
        """
        self._stream.close()

    def skip(self, length) -> None:
        """
        Skips ahead in the stream the specified number of bytes.

        Args:
            length: How many bytes to skip.
        """
        self._stream.read(length)

    def position(self) -> int:
        """
        Returns the byte offset into the stream.

        Returns:
            The byte offset.
        """
        return self._stream.tell() - self._offset

    def seek(self, position) -> None:
        """
        Moves the stream pointer to the byte offset.

        Args:
            position: The byte index into stream.
        """
        self._stream.seek(position + self._offset)

    def read_all(self) -> bytes:
        length = self.size() - self._offset
        self._stream.seek(self._offset)
        return self._stream.read(length)

    def read_uint8(self, *, big: bool = False) -> int:
        """
        Reads an unsigned 8-bit integer from the stream.

        Args:
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        return struct.unpack(_endian_char(big) + 'B', self._stream.read(1))[0]

    def read_int8(self, *, big: bool = False) -> int:
        """
        Reads an signed 8-bit integer from the stream.

        Args:
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        return struct.unpack(_endian_char(big) + 'b', self._stream.read(1))[0]

    def read_uint16(self, *, big: bool = False) -> int:
        """
        Reads an unsigned 16-bit integer from the stream.

        Args:
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        return struct.unpack(_endian_char(big) + 'H', self._stream.read(2))[0]

    def read_int16(self, *, big: bool = False) -> int:
        """
        Reads an signed 16-bit integer from the stream.

        Args:
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        return struct.unpack(_endian_char(big) + 'h', self._stream.read(2))[0]

    def read_uint32(self, *, max_neg1: bool = False, big: bool = False) -> int:
        """
        Reads an unsigned 32-bit integer from the stream.

        If max_is_neg1 flag is set to true and the bytes read off the stream are equal to 0xFFFFFFFF then the method
        will return a value of -1 instead of 4294967295.

        Args:
            max_neg1: Return -1 when the value of the stream equals 0xFFFFFFFF.
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        unpacked = struct.unpack(_endian_char(big) + "I", self._stream.read(4))[0]

        if unpacked == 4294967295 and max_neg1:
            unpacked = -1

        return unpacked

    def read_int32(self, *, big: bool = False) -> int:
        """
        Reads an signed 32-bit integer from the stream.

        Args:
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        return struct.unpack(_endian_char(big) + 'i', self._stream.read(4))[0]

    def read_uint64(self, *, big: bool = False) -> int:
        """
        Reads an unsigned 64-bit integer from the stream.

        Args:
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        return struct.unpack(_endian_char(big) + 'Q', self._stream.read(8))[0]

    def read_int64(self, *, big: bool = False) -> int:
        """
        Reads an signed 64-bit integer from the stream.

        Args:
            big: Read int bytes as big endian.

        Returns:
            An integer from the stream.
        """
        return struct.unpack(_endian_char(big) + 'q', self._stream.read(8))[0]

    def read_single(self, *, big: bool = False) -> int:
        """
        Reads an 32-bit floating point number from the stream.

        Args:
            big: Read float bytes as big endian.

        Returns:
            An float from the stream.
        """
        return struct.unpack(_endian_char(big) + 'f', self._stream.read(4))[0]

    def read_double(self, *, big: bool = False) -> int:
        """
        Reads an 64-bit floating point number from the stream.

        Args:
            big: Read float bytes as big endian.

        Returns:
            An float from the stream.
        """
        return struct.unpack(_endian_char(big) + 'd', self._stream.read(8))[0]

    def read_vector2(self, *, big: bool = False) -> Vector2:
        """
        Reads a two 32-bit floating point numbers from the stream.

        Args:
            big: Read bytes as big endian.

        Returns:
            A new Vector2 instance using floats read from the stream.
        """
        x, y = self.read_single(big=big), self.read_single(big=big)
        return Vector2(x, y)

    def read_vector3(self, *, big: bool = False) -> Vector3:
        """
        Reads a three 32-bit floating point numbers from the stream.

        Args:
            big: Read bytes as big endian.

        Returns:
            A new Vector3 instance using floats read from the stream.
        """
        x, y, z = self.read_single(big=big), self.read_single(big=big), self.read_single(big=big)
        return Vector3(x, y, z)

    def read_vector4(self, *, big: bool = False) -> Vector4:
        """
        Reads a four 32-bit floating point numbers from the stream.

        Args:
            big: Read bytes as big endian.

        Returns:
            A new Vector4 instance using floats read from the stream.
        """
        x, y, z, w = self.read_single(big=big), self.read_single(big=big), self.read_single(big=big), \
                     self.read_single(big=big)
        return Vector4(x, y, z, w)

    def read_bytes(self, length: int) -> bytes:
        """
        Reads a specified number of bytes from the stream.

        Args:
            length: Number of bytes to read.

        Returns:
            A bytes object containing the read bytes.
        """
        return self._stream.read(length)

    def read_string(self, length: int) -> str:
        """
        Reads a string from the stream with the specified length. Any null bytes and characters proceeding a null byte
        are trimmed from the final value and any unknown characters are ignored.

        Args:
            length: Amount of character to read.

        Returns:
            A string read from the stream.
        """
        string = self._stream.read(length).decode('ascii', errors='ignore')
        if '\0' in string:
            string = string[:string.index('\0')].rstrip('\0')
            string = string.replace('\0', '')
        return string

    def read_terminated_string(self, terminator: str) -> str:
        """
        Reads a string continuously from the stream until it hits the terminator string specified. Any unknown
        characters are ignored.

        Args:
            terminator: The terminator string.

        Returns:
            A string read from the stream.
        """
        string = ""
        char = ""
        while char != terminator:
            string += char
            char = self.read_bytes(1).decode('ascii', errors='ignore')
        return string

    def read_localized_string(self) -> LocalizedString:
        """
        Reads the localized string data structure from the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Returns:
            A LocalizedString read from the stream.
        """
        locstring = LocalizedString()
        self.skip(4)  # total number of bytes of the localized string
        locstring.stringref = self.read_uint32(max_neg1=True)
        string_count = self.read_uint32()
        for i in range(string_count):
            string_id = self.read_uint32()
            length = self.read_uint32()
            string = self.read_string(length)
            language, gender = LocalizedString.substring_pair(string_id)
            locstring.set(language, gender, string)
        return locstring

    def peek(self, length: int = 1) -> bytes:
        data = self._stream.read(length)
        self._stream.seek(-length, 1)
        return data
