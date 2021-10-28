"""
This module holds classes relating to read and write operations.
"""
from __future__ import annotations
import io
import struct
from abc import ABC, abstractmethod
from typing import BinaryIO, Union, TextIO, List, overload, Optional
from pykotor.common.geometry import Vector3, Vector4, Vector2
from pykotor.common.language import LocalizedString


def _endian_char(big) -> str:
    """
    Returns the character that represents either big endian or small endian in struct unpack.

    Args:
        big: True if big endian.

    Returns:
        Character representing either big or small endian.
    """
    return '>' if big else '<'


class ArrayHead:
    def __init__(self, array_offset: int = 0, array_length: int = 0):
        self.length: int = array_length
        self.offset: int = array_offset


class BinaryReader:
    """
    Used for easy reading of binary files.
    """

    def __init__(self, stream: BinaryIO, offset: int = 0):
        self._stream: BinaryIO = stream
        self.offset: int = offset
        self.auto_close: bool = True
        self._stream.seek(offset)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.auto_close: self.close()

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

    @classmethod
    def from_auto(cls, source: Optional[str, bytes, BinaryReader], offset: int = 0):
        if isinstance(source, str):  # is path
            reader = BinaryReader.from_file(source, offset)
        elif isinstance(source, bytes):  # is binary data
            reader = BinaryReader.from_bytes(source, offset)
        elif isinstance(source, BinaryReader):
            reader = source
            reader.offset = offset
        else:
            raise NotImplementedError("Must specify a path, bytes object or an existing BinaryReader instance.")

        return reader

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
        return self._stream.tell() - self.offset

    def seek(self, position) -> None:
        """
        Moves the stream pointer to the byte offset.

        Args:
            position: The byte index into stream.
        """
        self._stream.seek(position + self.offset)

    def read_all(self) -> bytes:
        length = self.size() - self.offset
        self._stream.seek(self.offset)
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
        locstring = LocalizedString.from_invalid()
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

    def read_array_head(self) -> ArrayHead:
        return ArrayHead(self.read_uint32(), self.read_uint32())

    def peek(self, length: int = 1) -> bytes:
        data = self._stream.read(length)
        self._stream.seek(-length, 1)
        return data


class BinaryWriter(ABC):
    @classmethod
    def to_file(cls, path: str) -> BinaryWriter:
        """
        Returns a new BinaryWriter with a stream established to the specified path.

        Args:
            path: Path of the file to open.

        Returns:
            A new BinaryWriter instance.
        """
        stream = open(path, 'wb')
        return BinaryWriterFile(stream)

    @classmethod
    def to_bytearray(cls, data: bytearray = None) -> BinaryWriter:
        """
        Returns a new BinaryWriter with a stream established to the specified bytes.

        Args:
            data: The bytes to write to.

        Returns:
            A new BinaryWriter instance.
        """
        if data is None:
            data = bytearray()
        return BinaryWriterBytearray(data)

    @classmethod
    def to_auto(cls, source: Union[str, bytes, BinaryWriter]) -> BinaryWriter:
        if isinstance(source, str):  # is path
            return BinaryWriter.to_file(source)
        elif isinstance(source, bytes):  # is binary data
            return BinaryWriter.to_bytes(source)
        elif isinstance(source, BinaryWriter):
            return source
        else:
            raise NotImplementedError("Must specify a path, bytes object or an existing BinaryWriter instance.")

    @staticmethod
    def dump(path: str, data: bytes) -> None:
        """
        Convenience method used to writes the specified data to the specified file.

        Args:
            path: The filepath of the file.
            data: The data to write to the file.
        """
        with open(path, 'wb') as file:
            file.write(data)

    @abstractmethod
    def close(self) -> None:
        """
        Closes the stream.
        """

    @abstractmethod
    def size(self) -> int:
        """
        Returns the total file size.

        Returns:
            The total file size.
        """

    @abstractmethod
    def data(self) -> bytes:
        """
        Returns the full file data.

        Returns:
            The full file data.
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Clears all the data in the file.
        """

    @abstractmethod
    def seek(self, position) -> None:
        """
        Moves the stream pointer to the byte offset.

        Args:
            position: The byte index into stream.
        """

    @abstractmethod
    def end(self) -> None:
        """
        Moves the pointer for the stream to the end.
        """

    @abstractmethod
    def position(self) -> int:
        """
        Returns the byte offset into the stream.

        Returns:
            The byte offset.
        """

    @abstractmethod
    def write_uint8(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 8-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_int8(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 8-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_uint16(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 16-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_int16(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 16-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_uint32(self, value: int, *, max_neg1: bool = False, big: bool = False) -> None:
        """
        Writes an unsigned 32-bit integer to the stream.

        If the max_neg1 flag is set to true and the specified value is equal to -1 then the stream will accept the value
        and write 0xFFFFFFFF to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
            max_neg1: When the value is -1 it is to be converted to the max uint32 value.
        """

    @abstractmethod
    def write_int32(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 32-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_uint64(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 64-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_int64(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 64-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_single(self, value: float, *, big: bool = False) -> None:
        """
        Writes an 32-bit floating point number to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_double(self, value: int, *, big: bool = False) -> None:
        """
        Writes a 64-bit floating point number to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_vector2(self, value: Vector2, *, big: bool = False) -> None:
        """
        Writes two 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_vector3(self, value: Vector3, *, big: bool = False) -> None:
        """
        Writes three 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_vector4(self, value: Vector4, *, big: bool = False) -> None:
        """
        Writes four 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_bytes(self, value: bytes) -> None:
        """
        Writes the specified bytes to the stream.

        Args:
            value: The bytes to be written.
        """

    @abstractmethod
    def write_string(self, value: str, *, big: bool = False, prefix_length: int = 0, string_length: int = -1,
                     padding: str = '\0') -> None:
        """
        Writes the specified string to the stream. The string can also be prefixed by an integer specifying the
        strings length.

        Args:
            value: The string to be written.
            prefix_length: The number of bytes for the string length prefix. Valid options are 0, 1, 2 and 4.
            big: Write the prefix length integer as big endian.
            string_length: Fixes the string length to this size, truncating or padding where necessary. Ignores if -1.
            padding: What character is used as padding where applicable.
        """

    @abstractmethod
    def write_line(self, indent: int, *args) -> None:
        """
        Writes a line with specified indentation and array of values that are separated by whitespace.

        Args:
            indent: Level of indentation.
            *args: Values to write.
        """

    @abstractmethod
    def write_localized_string(self, value: LocalizedString, *, big: bool = False):
        """
        Writes the specified localized string to the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Args:
            value: The localized string to be written.
            big: Write any integers as big endian.
        """


class BinaryWriterFile(BinaryWriter):
    def __init__(self, stream: BinaryIO, offset: int = 0):
        self._stream: BinaryIO = stream
        self.offset: int = offset
        self.auto_close: bool = True
        self._stream.seek(offset)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.auto_close: self.close()

    def close(self) -> None:
        """
        Closes the stream.
        """
        self._stream.close()

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

    def data(self) -> bytes:
        """
        Returns the full file data.

        Returns:
            The full file data.
        """
        pos = self._stream.tell()
        self._stream.seek(0)
        data = self._stream.read()
        self._stream.seek(pos)
        return data

    def clear(self) -> None:
        """
        Clears all the data in the file.
        """
        self._stream.seek(0)
        self._stream.truncate()

    def seek(self, position) -> None:
        """
        Moves the stream pointer to the byte offset.

        Args:
            position: The byte index into stream.
        """
        self._stream.seek(position + self.offset)

    def end(self) -> None:
        """
        Moves the pointer for the stream to the end.
        """
        self._stream.seek(0, 2)

    def position(self) -> int:
        """
        Returns the byte offset into the stream.

        Returns:
            The byte offset.
        """
        return self._stream.tell() - self.offset

    def write_uint8(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 8-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'B', value))

    def write_int8(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 8-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'b', value))

    def write_uint16(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 16-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'H', value))

    def write_int16(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 16-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'h', value))

    def write_uint32(self, value: int, *, max_neg1: bool = False, big: bool = False) -> None:
        """
        Writes an unsigned 32-bit integer to the stream.

        If the max_neg1 flag is set to true and the specified value is equal to -1 then the stream will accept the value
        and write 0xFFFFFFFF to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
            max_neg1: When the value is -1 it is to be converted to the max uint32 value.
        """
        if max_neg1 and value == -1:
            value = 4294967295

        self._stream.write(struct.pack(_endian_char(big) + 'I', value))

    def write_int32(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 32-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'i', value))

    def write_uint64(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 64-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'Q', value))

    def write_int64(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 64-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'q', value))

    def write_single(self, value: float, *, big: bool = False) -> None:
        """
        Writes an 32-bit floating point number to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'f', value))

    def write_double(self, value: int, *, big: bool = False) -> None:
        """
        Writes a 64-bit floating point number to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'd', value))

    def write_vector2(self, value: Vector2, *, big: bool = False) -> None:
        """
        Writes two 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.x))
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.y))

    def write_vector3(self, value: Vector3, *, big: bool = False) -> None:
        """
        Writes three 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.x))
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.y))
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.z))

    def write_vector4(self, value: Vector4, *, big: bool = False) -> None:
        """
        Writes four 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.x))
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.y))
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.z))
        self._stream.write(struct.pack(_endian_char(big) + 'f', value.w))

    def write_bytes(self, value: bytes) -> None:
        """
        Writes the specified bytes to the stream.

        Args:
            value: The bytes to be written.
        """
        self._stream.write(value)

    def write_string(self, value: str, *, big: bool = False, prefix_length: int = 0, string_length: int = -1,
                     padding: str = '\0') -> None:
        """
        Writes the specified string to the stream. The string can also be prefixed by an integer specifying the
        strings length.

        Args:
            value: The string to be written.
            prefix_length: The number of bytes for the string length prefix. Valid options are 0, 1, 2 and 4.
            big: Write the prefix length integer as big endian.
            string_length: Fixes the string length to this size, truncating or padding where necessary. Ignores if -1.
            padding: What character is used as padding where applicable.
        """
        if prefix_length == 1:
            if len(value) > 255:
                raise ValueError("The string length is too large for a prefix length of 1.")
            self.write_uint8(len(value), big=big)
        elif prefix_length == 2:
            if len(value) > 65535:
                raise ValueError("The string length is too large for a prefix length of 2.")
            self.write_uint16(len(value), big=big)
        elif prefix_length == 4:
            if len(value) > 4294967295:
                raise ValueError("The string length is too large for a prefix length of 4.")
            self.write_uint32(len(value), big=big)
        elif prefix_length != 0:
            raise ValueError("An invalid prefix length was provided.")

        if string_length != -1:
            while len(value) < string_length:
                value += padding
            value = value[:string_length]

        self._stream.write(value.encode('ascii'))

    def write_line(self, indent: int, *args) -> None:
        """
        Writes a line with specified indentation and array of values that are separated by whitespace.

        Args:
            indent: Level of indentation.
            *args: Values to write.
        """
        line = "  " * indent
        for arg in args:
            if isinstance(arg, float):
                line += str(round(arg, 7))
            else:
                line += str(arg)
            line += " "
        line += "\n"
        self._stream.write(line.encode())

    def write_localized_string(self, value: LocalizedString, *, big: bool = False):
        """
        Writes the specified localized string to the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Args:
            value: The localized string to be written.
            big: Write any integers as big endian.
        """
        bw = BinaryWriter.to_bytes(b'')
        bw.write_uint32(value.stringref, big=big, max_neg1=True)
        bw.write_uint32(len(value), big=big)
        for language, gender, substring in value:
            string_id = LocalizedString.substring_id(language, gender)
            bw.write_uint32(string_id, big=big)
            bw.write_string(substring, prefix_length=4)
        locstring_data = bw.data()

        self.write_uint32(len(locstring_data))
        self.write_bytes(locstring_data)


class BinaryWriterBytearray(BinaryWriter):
    def __init__(self, ba: bytearray, offset: int = 0):
        self._ba = ba
        self._offset: int = offset
        self._position = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    def close(self) -> None:
        """
        Closes the stream.
        """

    def size(self) -> int:
        """
        Returns the total file size.

        Returns:
            The total file size.
        """
        return len(self._ba)

    def data(self) -> bytes:
        """
        Returns the full file data.

        Returns:
            The full file data.
        """
        return bytes(self._ba)

    def clear(self) -> None:
        """
        Clears all the data in the file.
        """
        self._ba.clear()

    def seek(self, position) -> None:
        """
        Moves the stream pointer to the byte offset.

        Args:
            position: The byte index into stream.
        """
        self._position = position

    def end(self) -> None:
        """
        Moves the pointer for the stream to the end.
        """
        self._position = len(self._ba) - 1

    def position(self) -> int:
        """
        Returns the byte offset into the stream.

        Returns:
            The byte offset.
        """
        return self._position - self._offset

    def write_uint8(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 8-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'B', value))

    def write_int8(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 8-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'b', value))

    def write_uint16(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 16-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'H', value))

    def write_int16(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 16-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'h', value))

    def write_uint32(self, value: int, *, max_neg1: bool = False, big: bool = False) -> None:
        """
        Writes an unsigned 32-bit integer to the stream.

        If the max_neg1 flag is set to true and the specified value is equal to -1 then the stream will accept the value
        and write 0xFFFFFFFF to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
            max_neg1: When the value is -1 it is to be converted to the max uint32 value.
        """
        if max_neg1 and value == -1:
            value = 4294967295

        self._ba.extend(struct.pack(_endian_char(big) + 'I', value))

    def write_int32(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 32-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'i', value))

    def write_uint64(self, value: int, *, big: bool = False) -> None:
        """
        Writes an unsigned 64-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'Q', value))

    def write_int64(self, value: int, *, big: bool = False) -> None:
        """
        Writes a signed 64-bit integer to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'q', value))

    def write_single(self, value: float, *, big: bool = False) -> None:
        """
        Writes an 32-bit floating point number to the stream.

        Args:
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value))

    def write_double(self, value: int, *, big: bool = False) -> None:
        """
        Writes a 64-bit floating point number to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'd', value))

    def write_vector2(self, value: Vector2, *, big: bool = False) -> None:
        """
        Writes two 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.x))
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.y))

    def write_vector3(self, value: Vector3, *, big: bool = False) -> None:
        """
        Writes three 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.x))
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.y))
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.z))

    def write_vector4(self, value: Vector4, *, big: bool = False) -> None:
        """
        Writes four 32-bit floating point numbers to the stream.

        Args:
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.x))
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.y))
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.z))
        self._ba.extend(struct.pack(_endian_char(big) + 'f', value.w))

    def write_bytes(self, value: bytes) -> None:
        """
        Writes the specified bytes to the stream.

        Args:
            value: The bytes to be written.
        """
        self._ba.extend(value)

    def write_string(self, value: str, *, big: bool = False, prefix_length: int = 0, string_length: int = -1,
                     padding: str = '\0') -> None:
        """
        Writes the specified string to the stream. The string can also be prefixed by an integer specifying the
        strings length.

        Args:
            value: The string to be written.
            prefix_length: The number of bytes for the string length prefix. Valid options are 0, 1, 2 and 4.
            big: Write the prefix length integer as big endian.
            string_length: Fixes the string length to this size, truncating or padding where necessary. Ignores if -1.
            padding: What character is used as padding where applicable.
        """
        if prefix_length == 1:
            if len(value) > 255:
                raise ValueError("The string length is too large for a prefix length of 1.")
            self.write_uint8(len(value), big=big)
        elif prefix_length == 2:
            if len(value) > 65535:
                raise ValueError("The string length is too large for a prefix length of 2.")
            self.write_uint16(len(value), big=big)
        elif prefix_length == 4:
            if len(value) > 4294967295:
                raise ValueError("The string length is too large for a prefix length of 4.")
            self.write_uint32(len(value), big=big)
        elif prefix_length != 0:
            raise ValueError("An invalid prefix length was provided.")

        if string_length != -1:
            while len(value) < string_length:
                value += padding
            value = value[:string_length]

        self._ba.extend(value.encode('ascii'))

    def write_line(self, indent: int, *args) -> None:
        """
        Writes a line with specified indentation and array of values that are separated by whitespace.

        Args:
            indent: Level of indentation.
            *args: Values to write.
        """
        line = "  " * indent
        for arg in args:
            if isinstance(arg, float):
                line += str(round(arg, 7))
            else:
                line += str(arg)
            line += " "
        line += "\n"
        self._ba.extend(line.encode())

    def write_localized_string(self, value: LocalizedString, *, big: bool = False):
        """
        Writes the specified localized string to the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Args:
            value: The localized string to be written.
            big: Write any integers as big endian.
        """
        bw = BinaryWriter.to_bytearray(b'')
        bw.write_uint32(value.stringref, big=big, max_neg1=True)
        bw.write_uint32(len(value), big=big)
        for language, gender, substring in value:
            string_id = LocalizedString.substring_id(language, gender)
            bw.write_uint32(string_id, big=big)
            bw.write_string(substring, prefix_length=4)
        locstring_data = bw.data()

        self.write_uint32(len(locstring_data))
        self.write_bytes(locstring_data)

