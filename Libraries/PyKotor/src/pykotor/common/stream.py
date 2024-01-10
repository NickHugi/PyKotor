"""This module holds classes relating to read and write operations."""
from __future__ import annotations

import io
import os
import struct
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, BinaryIO

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.path import Path

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def _endian_char(
    big: bool,
) -> str:
    """Returns the character that represents either big endian or small endian in struct unpack.

    Args:
    ----
        big: True if big endian.

    Returns:
    -------
        Character representing either big or small endian.
    """
    return ">" if big else "<"


class ArrayHead:
    def __init__(
        self,
        array_offset: int = 0,
        array_length: int = 0,
    ):
        self.length: int = array_length
        self.offset: int = array_offset


class BinaryReader:
    """Used for easy reading of binary files."""

    def __init__(
        self,
        stream: BinaryIO,
        offset: int = 0,
        size: int | None = None,
    ):
        self._stream: BinaryIO = stream
        self._offset: int = offset
        self.auto_close: bool = True
        self._stream.seek(offset)

        available = self.true_size() - offset
        self._size: int = available if size is None else size
        if available > self.true_size():
            msg = "Specified size is greater than the number of available bytes."
            raise OSError(msg)

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        if self.auto_close:
            self.close()

    @classmethod
    def from_file(
        cls,
        path: os.PathLike | str,
        offset: int = 0,
        size: int | None = None,
    ) -> BinaryReader:
        """Returns a new BinaryReader with a stream established to the specified path.

        Args:
        ----
            path: str or pathlike object of the file to open.
            offset: Number of bytes into the stream to consider as position 0.
            size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

        Returns:
        -------
            A new BinaryReader instance.
        """
        stream = Path.pathify(path).open("rb")
        return BinaryReader(stream, offset, size)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        offset: int = 0,
        size: int | None = None,
    ) -> BinaryReader:
        """Returns a new BinaryReader with a stream established to the bytes stored in memory.

        Args:
        ----
            data: The bytes of data.
            offset: Number of bytes into the stream to consider as position 0.
            size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

        Returns:
        -------
            A new BinaryReader instance.
        """
        stream = io.BytesIO(data)
        return BinaryReader(stream, offset, size)

    @classmethod
    def from_auto(
        cls,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
    ):
        if isinstance(source, (os.PathLike, str)):  # is path
            reader = BinaryReader.from_file(source, offset, size)
        elif isinstance(source, (bytes, bytearray, memoryview)):  # is binary data
            reader = BinaryReader.from_bytes(source, offset, size)
        elif isinstance(source, BinaryReader):
            reader = BinaryReader(source._stream, source._offset, source._size)
        else:
            msg = "Must specify a path, bytes-like object or an existing BinaryReader instance."
            raise NotImplementedError(msg)

        return reader

    @staticmethod
    def load_file(
        path: os.PathLike | str,
        offset: int = 0,
        size: int = -1,
    ) -> bytes:
        """Returns bytes of a file at from specified path.

        Args:
        ----
            path: The str or path-like path of the file.
            offset: The offset into the file.
            size: The amount of bytes to load, if size equals -1 loads the whole file.

        Returns:
        -------
            The bytes of the file.
        """
        with Path.pathify(path).open("rb") as reader:
            reader.seek(offset)
            return reader.read() if size == -1 else reader.read(size)

    def offset(
        self,
    ) -> int:
        """Returns the offset value.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            int: The offset value
        Retrieves and returns the internally stored offset value.
        """
        return self._offset

    def set_offset(
        self,
        offset: int,
    ):
        self.seek(self.position() + offset)
        self._offset = offset

    def size(
        self,
    ) -> int:
        """Returns the total number of bytes accessible.

        Returns
        -------
            The number of accessible bytes.
        """
        return self._size

    def true_size(
        self,
    ) -> int:
        """Returns the total number of bytes in the stream.

        Returns
        -------
            The total file size.
        """
        pos: int = self._stream.tell()
        self._stream.seek(0, 2)
        size: int = self._stream.tell()
        self._stream.seek(pos)
        return size

    def remaining(
        self,
    ) -> int:
        """Returns the remaining number of bytes in the stream.

        Returns
        -------
            The total file size.
        """
        return self.size() - self.position()

    def close(
        self,
    ):
        """Closes the stream."""
        self._stream.close()

    def skip(
        self,
        length: int,
    ):
        """Skips ahead in the stream the specified number of bytes.

        Args:
        ----
            length: How many bytes to skip.
        """
        self.exceed_check(length)
        self._stream.read(length)

    def position(
        self,
    ) -> int:
        """Returns the byte offset into the stream.

        Returns
        -------
            The byte offset.
        """
        return self._stream.tell() - self._offset

    def seek(
        self,
        position: int,
    ):
        """Moves the stream pointer to the byte offset.

        Args:
        ----
            position: The byte index into stream.
        """
        self.exceed_check(position - self.position())
        self._stream.seek(position + self._offset)

    def read_all(
        self,
    ) -> bytes:
        """Read all remaining bytes from the stream.

        Args:
        ----
            self: The stream object

        Returns:
        -------
            bytes: The bytes read from the stream

        Processing Logic:
        ----------------
            - Get the length of bytes remaining from current offset to end of stream
            - Seek the stream to the current offset
            - Read the bytes of the given length from the stream
            - Return the bytes read.
        """
        length = self.size() - self._offset
        self._stream.seek(self._offset)
        return self._stream.read(length)

    def read_uint8(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads an unsigned 8-bit integer from the stream.

        Args:
        ----
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(1)
        return struct.unpack(f"{_endian_char(big)}B", self._stream.read(1))[0]

    def read_int8(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads an signed 8-bit integer from the stream.

        Args:
        ----
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(1)
        return struct.unpack(f"{_endian_char(big)}b", self._stream.read(1))[0]

    def read_uint16(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads an unsigned 16-bit integer from the stream.

        Args:
        ----
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(2)
        return struct.unpack(f"{_endian_char(big)}H", self._stream.read(2))[0]

    def read_int16(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads an signed 16-bit integer from the stream.

        Args:
        ----
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(2)
        return struct.unpack(f"{_endian_char(big)}h", self._stream.read(2))[0]

    def read_uint32(
        self,
        *,
        max_neg1: bool = False,
        big: bool = False,
    ) -> int:
        """Reads an unsigned 32-bit integer from the stream.

        If max_is_neg1 flag is set to true and the bytes read off the stream are equal to 0xFFFFFFFF then the method
        will return a value of -1 instead of 4294967295.

        Args:
        ----
            max_neg1: Return -1 when the value of the stream equals 0xFFFFFFFF.
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(4)
        unpacked = struct.unpack(f"{_endian_char(big)}I", self._stream.read(4))[0]

        if unpacked == 0xFFFFFFFF and max_neg1:
            unpacked = -1

        return unpacked

    def read_int32(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads a signed 32-bit integer from the stream.

        Args:
        ----
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(4)
        return struct.unpack(f"{_endian_char(big)}i", self._stream.read(4))[0]

    def read_uint64(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads an unsigned 64-bit integer from the stream.

        Args:
        ----
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(8)
        return struct.unpack(f"{_endian_char(big)}Q", self._stream.read(8))[0]

    def read_int64(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads a signed 64-bit integer from the stream.

        Args:
        ----
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(8)
        return struct.unpack(f"{_endian_char(big)}q", self._stream.read(8))[0]

    def read_single(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads a 32-bit floating point number from the stream.

        Args:
        ----
            big: Read float bytes as big endian.

        Returns:
        -------
            An float from the stream.
        """
        self.exceed_check(4)
        return struct.unpack(f"{_endian_char(big)}f", self._stream.read(4))[0]

    def read_double(
        self,
        *,
        big: bool = False,
    ) -> int:
        """Reads a 64-bit floating point number from the stream.

        Args:
        ----
            big: Read float bytes as big endian.

        Returns:
        -------
            An float from the stream.
        """
        self.exceed_check(8)
        return struct.unpack(f"{_endian_char(big)}d", self._stream.read(8))[0]

    def read_vector2(
        self,
        *,
        big: bool = False,
    ) -> Vector2:
        """Reads two 32-bit floating point numbers from the stream.

        Args:
        ----
            big: Read bytes as big endian.

        Returns:
        -------
            A new Vector2 instance using floats read from the stream.
        """
        self.exceed_check(8)
        x, y = self.read_single(big=big), self.read_single(big=big)
        return Vector2(x, y)

    def read_vector3(
        self,
        *,
        big: bool = False,
    ) -> Vector3:
        """Reads three 32-bit floating point numbers from the stream.

        Args:
        ----
            big: Read bytes as big endian.

        Returns:
        -------
            A new Vector3 instance using floats read from the stream.
        """
        self.exceed_check(12)
        x, y, z = (
            self.read_single(big=big),
            self.read_single(big=big),
            self.read_single(big=big),
        )
        return Vector3(x, y, z)

    def read_vector4(
        self,
        *,
        big: bool = False,
    ) -> Vector4:
        """Reads four 32-bit floating point numbers from the stream.

        Args:
        ----
            big: Read bytes as big endian.

        Returns:
        -------
            A new Vector4 instance using floats read from the stream.
        """
        self.exceed_check(16)
        x, y, z, w = (
            self.read_single(big=big),
            self.read_single(big=big),
            self.read_single(big=big),
            self.read_single(big=big),
        )
        return Vector4(x, y, z, w)

    def read_bytes(
        self,
        length: int,
    ) -> bytes:
        """Reads a specified number of bytes from the stream.

        Args:
        ----
            length: Number of bytes to read.

        Returns:
        -------
            A bytes object containing the read bytes.
        """
        self.exceed_check(length)
        return self._stream.read(length)

    def read_string(
        self,
        length: int,
        encoding: str | None = "windows-1252",
    ) -> str:
        """Reads a string from the stream with the specified length.

        Any null bytes and characters proceeding a null byte are trimmed from the
        final value and any unknown characters are ignored.

        Args:
        ----
            length: Amount of character to read.
            encoding: Encoding of string to read.  If not specified, will default to 'windows-1252'. If set to None, will autodetect using charset_normalizer.

        Returns:
        -------
            A string read from the stream.
        """
        self.exceed_check(length)
        string_byte_data = self._stream.read(length)
        string = decode_bytes_with_fallbacks(string_byte_data, encoding=encoding, errors="ignore")
        if "\0" in string:
            string = string[: string.index("\0")].rstrip("\0")
            string = string.replace("\0", "")
        return string

    def read_terminated_string(
        self,
        terminator: str,
    ) -> str:
        """Reads a string continuously from the stream until it hits the terminator string specified.

        Any unknown characters are ignored.

        Args:
        ----
            terminator: The terminator string.

        Returns:
        -------
            A string read from the stream.
        """
        string = ""
        char = ""
        while char != terminator:
            string += char
            self.exceed_check(1)
            char = self.read_bytes(1).decode("ascii", errors="ignore")
        return string

    def read_locstring(
        self,
    ) -> LocalizedString:
        """Reads the localized string data structure from the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Returns
        -------
            A LocalizedString read from the stream.
        """
        locstring: LocalizedString = LocalizedString.from_invalid()
        self.skip(4)  # total number of bytes of the localized string
        locstring.stringref = self.read_uint32(max_neg1=True)
        string_count = self.read_uint32()
        for _i in range(string_count):
            string_id = self.read_uint32()
            language, gender = LocalizedString.substring_pair(string_id)
            length = self.read_uint32()
            string = self.read_string(length, encoding=language.get_encoding())
            locstring.set_data(language, gender, string)
        return locstring

    def read_array_head(
        self,
    ) -> ArrayHead:
        return ArrayHead(self.read_uint32(), self.read_uint32())

    def peek(
        self,
        length: int = 1,
    ) -> bytes:
        data: bytes = self._stream.read(length)
        self._stream.seek(-length, 1)
        return data

    def exceed_check(
        self,
        num: int,
    ):
        """Raises an error if the specified number exceeds the number of remaining bytes.

        Args:
        ----
            num: Number of bytes.

        Raises:
        ------
            OSError: Iset_datahe given number sex exceeds the number of remaining bytes.
        """
        if self.position() + num > self.size():
            msg = "This operation would exceed the streams boundaries."
            raise OSError(msg)


class BinaryWriter(ABC):
    @abstractmethod
    def __enter__(self):
        ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    @classmethod
    def to_file(
        cls,
        path: os.PathLike | str,
    ) -> BinaryWriterFile:
        """Returns a new BinaryWriter with a stream established to the specified path.

        Args:
        ----
            path: str or PathLike object of the file to open.

        Returns:
        -------
            A new BinaryWriter instance.
        """
        return BinaryWriterFile(Path.pathify(path).open("wb"))

    @classmethod
    def to_bytearray(
        cls,
        data: bytearray | None = None,
    ) -> BinaryWriterBytearray:
        """Returns a new BinaryWriter with a stream established to the specified bytes.

        Args:
        ----
            data: The bytes to write to.

        Returns:
        -------
            A new BinaryWriter instance.
        """
        if isinstance(data, (bytes, memoryview)):
            msg = "Must be bytearray, not bytes or memoryview."
            raise TypeError(msg)
        if data is None:
            data = bytearray()
        return BinaryWriterBytearray(data)

    @classmethod
    def to_auto(
        cls,
        source: TARGET_TYPES,
    ) -> BinaryWriter:
        if isinstance(source, (os.PathLike, str)):  # is path
            return BinaryWriter.to_file(source)
        if isinstance(source, bytearray):  # is mutable binary data
            return BinaryWriter.to_bytearray(source)
        if isinstance(source, (bytes, memoryview)):  # is immutable binary data
            return BinaryWriter.to_bytearray(bytearray(source))
        if isinstance(source, BinaryWriter):
            return source
        msg = "Must specify a path, bytes object or an existing BinaryWriter instance."
        raise NotImplementedError(msg)

    @staticmethod
    def dump(
        path: os.PathLike | str,
        data: bytes,
    ):
        """Convenience method used to write the specified data to the specified file.

        Args:
        ----
            path: The filepath of the file.
            data: The data to write to the file.
        """
        with Path.pathify(path).open("wb") as file:
            file.write(data)

    @abstractmethod
    def close(
        self,
    ):
        """Closes the stream."""

    @abstractmethod
    def size(
        self,
    ) -> int:
        """Returns the total file size.

        Returns
        -------
            The total file size.
        """

    @abstractmethod
    def data(
        self,
    ) -> bytes:
        """Returns the full file data.

        Returns
        -------
            The full file data.
        """

    @abstractmethod
    def clear(
        self,
    ):
        """Clears all the data in the file."""

    @abstractmethod
    def seek(
        self,
        position: int,
    ):
        """Moves the stream pointer to the byte offset.

        Args:
        ----
            position: The byte index into stream.
        """

    @abstractmethod
    def end(
        self,
    ):
        """Moves the pointer for the stream to the end."""

    @abstractmethod
    def position(
        self,
    ) -> int:
        """Returns the byte offset into the stream.

        Returns
        -------
            The byte offset.
        """

    @abstractmethod
    def write_uint8(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 8-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_int8(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 8-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_uint16(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 16-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_int16(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 16-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_uint32(
        self,
        value: int,
        *,
        max_neg1: bool = False,
        big: bool = False,
    ):
        """Writes an unsigned 32-bit integer to the stream.

        If the max_neg1 flag is set to true and the specified value is equal to -1 then the stream will accept the value
        and write 0xFFFFFFFF to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
            max_neg1: When the value is -1 it is to be converted to the max uint32 value.
        """

    @abstractmethod
    def write_int32(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 32-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_uint64(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 64-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_int64(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 64-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_single(
        self,
        value: float,
        *,
        big: bool = False,
    ):
        """Writes an 32-bit floating point number to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """

    @abstractmethod
    def write_double(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a 64-bit floating point number to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_vector2(
        self,
        value: Vector2,
        *,
        big: bool = False,
    ):
        """Writes two 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_vector3(
        self,
        value: Vector3,
        *,
        big: bool = False,
    ):
        """Writes three 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_vector4(
        self,
        value: Vector4,
        *,
        big: bool = False,
    ):
        """Writes four 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """

    @abstractmethod
    def write_bytes(
        self,
        value: bytes,
    ):
        """Writes the specified bytes to the stream.

        Args:
        ----
            value: The bytes to be written.
        """

    @abstractmethod
    def write_string(
        self,
        value: str,
        encoding: str | None = "windows-1252",
        errors: str = "errors",
        *,
        big: bool = False,
        prefix_length: int = 0,
        string_length: int = -1,
        padding: str = "\0",
    ):
        """Writes the specified string to the stream.

        The string can also be prefixed by an integer specifying the strings length.

        Args:
        ----
            value: The string to be written.
            encoding: The string encoding. If not set, will use the default "windows-1252". If set to None, will autodetect using charset_normalizer.
            prefix_length: The number of bytes for the string length prefix. Valid options are 0, 1, 2 and 4.
            big: Write the prefix length integer as big endian.
            string_length: Fixes the string length to this size, truncating or padding where necessary. Ignores if -1.
            padding: What character is used as padding where applicable.
        """

    @abstractmethod
    def write_line(
        self,
        indent: int,
        *args,
    ):
        """Writes a line with specified indentation and array of values that are separated by whitespace.

        Args:
        ----
            indent: Level of indentation.
            *args: Values to write.
        """

    @abstractmethod
    def write_locstring(
        self,
        value: LocalizedString,
        *,
        big: bool = False,
    ):
        """Writes the specified localized string to the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Args:
        ----
            value: The localized string to be written.
            big: Write any integers as big endian.
        """


class BinaryWriterFile(BinaryWriter):
    def __init__(
        self,
        stream: BinaryIO,
        offset: int = 0,
    ):
        self._stream: BinaryIO = stream
        self.offset: int = offset
        self.auto_close: bool = True

        self._stream.seek(offset)

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        if self.auto_close:
            self.close()

    def close(
        self,
    ):
        """Closes the stream."""
        self._stream.close()

    def size(
        self,
    ) -> int:
        """Returns the total file size.

        Returns
        -------
            The total file size.
        """
        pos: int = self._stream.tell()
        self._stream.seek(0, 2)
        size: int = self._stream.tell()
        self._stream.seek(pos)
        return size

    def data(
        self,
    ) -> bytes:
        """Returns the full file data.

        Returns
        -------
            The full file data.
        """
        pos: int = self._stream.tell()
        self._stream.seek(0)
        data: bytes = self._stream.read()
        self._stream.seek(pos)
        return data

    def clear(
        self,
    ):
        """Clears all the data in the file."""
        self._stream.seek(0)
        self._stream.truncate()

    def seek(
        self,
        position: int,
    ):
        """Moves the stream pointer to the byte offset.

        Args:
        ----
            position: The byte index into stream.
        """
        self._stream.seek(position + self.offset)

    def end(
        self,
    ):
        """Moves the pointer for the stream to the end."""
        self._stream.seek(0, 2)

    def position(
        self,
    ) -> int:
        """Returns the byte offset into the stream.

        Returns
        -------
            The byte offset.
        """
        return self._stream.tell() - self.offset

    def write_uint8(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 8-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}B", value))

    def write_int8(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 8-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}b", value))

    def write_uint16(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 16-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}H", value))

    def write_int16(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 16-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}h", value))

    def write_uint32(
        self,
        value: int,
        *,
        max_neg1: bool = False,
        big: bool = False,
    ):
        """Writes an unsigned 32-bit integer to the stream.

        If the max_neg1 flag is set to true and the specified value is equal to -1 then the stream will accept the value
        and write 0xFFFFFFFF to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
            max_neg1: When the value is -1 it is to be converted to the max uint32 value.
        """
        if max_neg1 and value == -1:
            value = 0xFFFFFFFF

        self._stream.write(struct.pack(f"{_endian_char(big)}I", value))

    def write_int32(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 32-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}i", value))

    def write_uint64(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 64-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}Q", value))

    def write_int64(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 64-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}q", value))

    def write_single(
        self,
        value: float,
        *,
        big: bool = False,
    ):
        """Writes an 32-bit floating point number to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value))

    def write_double(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a 64-bit floating point number to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}d", value))

    def write_vector2(
        self,
        value: Vector2,
        *,
        big: bool = False,
    ):
        """Writes two 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.x))
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.y))

    def write_vector3(
        self,
        value: Vector3,
        *,
        big: bool = False,
    ):  # sourcery skip: class-extract-method
        """Writes three 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.x))
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.y))
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.z))

    def write_vector4(
        self,
        value: Vector4,
        *,
        big: bool = False,
    ):
        """Writes four 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.x))
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.y))
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.z))
        self._stream.write(struct.pack(f"{_endian_char(big)}f", value.w))

    def write_bytes(
        self,
        value: bytes,
    ):
        """Writes the specified bytes to the stream.

        Args:
        ----
            value: The bytes to be written.
        """
        self._stream.write(value)

    def write_string(
        self,
        value: str,
        encoding: str | None = "windows-1252",
        errors: str = "strict",
        *,
        big: bool = False,
        prefix_length: int = 0,
        string_length: int = -1,
        padding: str = "\0",
    ):  # sourcery skip: inline-variable, switch
        """Writes the specified string to the stream.

        The string can also be prefixed by an integer specifying the strings length.

        Args:
        ----
            value: The string to be written.
            encoding: The encoding of the string to be written. If not set, will default to "windows-1252".
            prefix_length: The number of bytes for the string length prefix. Valid options are 0, 1, 2 and 4.
            big: Write the prefix length integer as big endian.
            string_length: Fixes the string length to this size, truncating or padding where necessary. Ignores if -1.
            padding: What character is used as padding where applicable.
        """
        if prefix_length == 0:
            pass
        elif prefix_length == 1:
            if len(value) > 0xFF:
                msg = "The string length is too large for a prefix length of 1."
                raise ValueError(msg)
            self.write_uint8(len(value), big=big)
        elif prefix_length == 2:
            if len(value) > 0xFFFF:
                msg = "The string length is too large for a prefix length of 2."
                raise ValueError(msg)
            self.write_uint16(len(value), big=big)
        elif prefix_length == 4:
            if len(value) > 0xFFFFFFFF:
                msg = "The string length is too large for a prefix length of 4."
                raise ValueError(msg)
            self.write_uint32(len(value), big=big)
        else:
            msg = f"An invalid prefix length '{prefix_length}' was provided."
            raise ValueError(msg)

        if string_length != -1:
            while len(value) < string_length:
                value += padding
            value = value[:string_length]
        if encoding is None:
            self._stream.write(value.encode("windows-1252", errors=errors))
        else:
            self._stream.write(value.encode(encoding, errors=errors))

    def write_line(
        self,
        indent: int,
        *args: float | str,
    ):
        """Writes a line with specified indentation and array of values that are separated by whitespace.

        The data will be written with utf-8 encoding.

        Args:
        ----
            indent: Level of indentation.
            *args: Values to write.
        """
        line: str = "  " * indent
        for arg in args:
            line += str(round(arg, 7)) if isinstance(arg, float) else str(arg)
            line += " "
        line += "\n"
        self._stream.write(line.encode())

    def write_locstring(
        self,
        value: LocalizedString,
        *,
        big: bool = False,
    ):
        """Writes the specified localized string to the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Args:
        ----
            value: The localized string to be written.
            big: Write any integers as big endian.
        """
        bw: BinaryWriterBytearray = BinaryWriter.to_bytearray()
        bw.write_uint32(value.stringref, big=big, max_neg1=True)
        bw.write_uint32(len(value), big=big)
        for language, gender, substring in value:
            string_id: int = LocalizedString.substring_id(language, gender)
            bw.write_uint32(string_id, big=big)
            bw.write_string(substring, prefix_length=4, encoding=language.get_encoding())
        locstring_data: bytes = bw.data()

        self.write_uint32(len(locstring_data))
        self.write_bytes(locstring_data)


class BinaryWriterBytearray(BinaryWriter):
    def __init__(
        self,
        ba: bytearray,
        offset: int = 0,
    ):
        self._ba: bytearray = ba
        self._offset: int = offset
        self._position: int = 0

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        ...

    def close(
        self,
    ):
        """Closes the stream."""

    def size(
        self,
    ) -> int:
        """Returns the total file size.

        Returns
        -------
            The total file size.
        """
        return len(self._ba)

    def data(
        self,
    ) -> bytes:
        """Returns the full file data.

        Returns
        -------
            The full file data.
        """
        return bytes(self._ba)

    def clear(
        self,
    ):
        """Clears all the data in the file."""
        self._ba.clear()

    def seek(
        self,
        position: int,
    ):
        """Moves the stream pointer to the byte offset.

        Args:
        ----
            position: The byte index into stream.
        """
        self._position = position

    def end(
        self,
    ):
        """Moves the pointer for the stream to the end."""
        self._position = len(self._ba)

    def position(
        self,
    ) -> int:
        """Returns the byte offset into the stream.

        Returns
        -------
            The byte offset.
        """
        return self._position - self._offset

    def write_uint8(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 8-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 1] = struct.pack(
            f"{_endian_char(big)}B",
            value,
        )
        self._position += 1

    def write_int8(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 8-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 1] = struct.pack(
            f"{_endian_char(big)}b",
            value,
        )
        self._position += 1

    def write_uint16(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 16-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 2] = struct.pack(
            f"{_endian_char(big)}H",
            value,
        )
        self._position += 2

    def write_int16(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 16-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 2] = struct.pack(
            f"{_endian_char(big)}h",
            value,
        )
        self._position += 2

    def write_uint32(
        self,
        value: int,
        *,
        max_neg1: bool = False,
        big: bool = False,
    ):
        """Writes an unsigned 32-bit integer to the stream.

        If the max_neg1 flag is set to true and the specified value is equal to -1 then the stream will accept the value
        and write 0xFFFFFFFF to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
            max_neg1: When the value is -1 it is to be converted to the max uint32 value.
        """
        if max_neg1 and value == -1:
            value = 0xFFFFFFFF
        self._ba[self._position : self._position + 4] = struct.pack(
            f"{_endian_char(big)}I",
            value,
        )
        self._position += 4

    def write_int32(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 32-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 4] = struct.pack(
            f"{_endian_char(big)}i",
            value,
        )
        self._position += 4

    def write_uint64(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes an unsigned 64-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 8] = struct.pack(
            f"{_endian_char(big)}Q",
            value,
        )
        self._position += 8

    def write_int64(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a signed 64-bit integer to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 8] = struct.pack(
            f"{_endian_char(big)}q",
            value,
        )
        self._position += 8

    def write_single(
        self,
        value: float,
        *,
        big: bool = False,
    ):
        """Writes an 32-bit floating point number to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write int bytes as big endian.
        """
        self._ba[self._position : self._position + 4] = struct.pack(
            f"{_endian_char(big)}f",
            value,
        )
        self._position += 4

    def write_double(
        self,
        value: int,
        *,
        big: bool = False,
    ):
        """Writes a 64-bit floating point number to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba[self._position : self._position + 8] = struct.pack(
            f"{_endian_char(big)}d",
            value,
        )
        self._position += 8

    def write_vector2(
        self,
        value: Vector2,
        *,
        big: bool = False,
    ):
        """Writes two 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba[self._position : self._position + 4] = struct.pack(
            f"{_endian_char(big)}f",
            value.x,
        )
        self._ba[self._position + 4 : self._position + 8] = struct.pack(
            f"{_endian_char(big)}f",
            value.y,
        )
        self._position += 8

    def write_vector3(
        self,
        value: Vector3,
        *,
        big: bool = False,
    ):  # sourcery skip: class-extract-method
        """Writes three 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba[self._position : self._position + 4] = struct.pack(
            f"{_endian_char(big)}f",
            value.x,
        )
        self._ba[self._position + 4 : self._position + 8] = struct.pack(
            f"{_endian_char(big)}f",
            value.y,
        )
        self._ba[self._position + 8 : self._position + 12] = struct.pack(
            f"{_endian_char(big)}f",
            value.z,
        )
        self._position += 12

    def write_vector4(
        self,
        value: Vector4,
        *,
        big: bool = False,
    ):
        """Writes four 32-bit floating point numbers to the stream.

        Args:
        ----
            value: The value to be written.
            big: Write bytes as big endian.
        """
        self._ba[self._position : self._position + 4] = struct.pack(
            f"{_endian_char(big)}f",
            value.x,
        )
        self._ba[self._position + 4 : self._position + 8] = struct.pack(
            f"{_endian_char(big)}f",
            value.y,
        )
        self._ba[self._position + 8 : self._position + 12] = struct.pack(
            f"{_endian_char(big)}f",
            value.z,
        )
        self._ba[self._position + 12 : self._position + 16] = struct.pack(
            f"{_endian_char(big)}f",
            value.w,
        )
        self._position += 16

    def write_bytes(
        self,
        value: bytes,
    ):
        """Writes the specified bytes to the stream.

        Args:
        ----
            value: The bytes to be written.
        """
        self._ba[self._position : self._position + len(value)] = value
        self._position += len(value)

    def write_string(
        self,
        value: str,
        encoding: str | None = "windows-1252",
        errors: str = "strict",
        *,
        big: bool = False,
        prefix_length: int = 0,
        string_length: int = -1,
        padding: str = "\0",
    ):  # sourcery skip: inline-variable, switch
        """Writes the specified string to the stream.

        The string can also be prefixed by an integer specifying the strings length.

        Args:
        ----
            value: The string to be written.
            encoding: The encoding to convert to bytes. Defaults to "windows-1252".
            prefix_length: The number of bytes for the string length prefix. Valid options are 0, 1, 2 and 4.
            big: Write the prefix length integer as big endian.
            string_length: Fixes the string length to this size, truncating or padding where necessary. Ignores if -1.
            padding: What character is used as padding where applicable.
        """
        if prefix_length == 0:
            pass
        elif prefix_length == 1:
            if len(value) > 0xFF:
                msg = "The string length is too large for a prefix length of 1."
                raise ValueError(msg)
            self.write_uint8(len(value), big=big)
        elif prefix_length == 2:
            if len(value) > 0xFFFF:
                msg = "The string length is too large for a prefix length of 2."
                raise ValueError(msg)
            self.write_uint16(len(value), big=big)
        elif prefix_length == 4:
            if len(value) > 0xFFFFFFFF:
                msg = "The string length is too large for a prefix length of 4."
                raise ValueError(msg)
            self.write_uint32(len(value), big=big)
        else:
            msg = "An invalid prefix length was provided."
            raise ValueError(msg)

        if string_length != -1:
            while len(value) < string_length:
                value += padding
            value = value[:string_length]

        self._encode_val_and_update_position(value, encoding, errors)

    def write_line(
        self,
        indent: int,
        *args: list[float] | list[str],
    ):
        """Writes a line with specified indentation and array of values that are separated by whitespace.

        Args:
        ----
            indent: Level of indentation.
            *args: Values to write.
        """
        line: str = "  " * indent
        for arg in args:
            line += str(round(arg, 7)) if isinstance(arg, float) else str(arg)
            line += " "
        line += "\n"

        self._encode_val_and_update_position(line, "ascii")

    def _encode_val_and_update_position(
        self,
        value: str,
        encoding: str | None,
        errors: str = "strict",
    ):
        encoded: bytes = value.encode(encoding or "windows-1252", errors=errors)
        self._ba[self._position : self._position + len(encoded)] = encoded
        self._position += len(encoded)

    def write_locstring(
        self,
        value: LocalizedString,
        *,
        big: bool = False,
    ):
        """Writes the specified localized string to the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Args:
        ----
            value: The localized string to be written.
            big: Write any integers as big endian.
        """
        bw: BinaryWriterBytearray = BinaryWriter.to_bytearray()
        bw.write_uint32(value.stringref, big=big, max_neg1=True)
        bw.write_uint32(len(value), big=big)

        for language, gender, substring in value:
            string_id: int = LocalizedString.substring_id(language, gender)
            bw.write_uint32(string_id, big=big)
            bw.write_string(substring, prefix_length=4, encoding=language.get_encoding())

        locstring_data: bytes = bw.data()
        self.write_uint32(len(locstring_data))
        self.write_bytes(locstring_data)
