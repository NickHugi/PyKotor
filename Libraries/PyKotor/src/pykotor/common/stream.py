"""This module holds classes relating to read and write operations."""

from __future__ import annotations

import io
import mmap
import os
import struct

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.system.path import Path

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Literal, Self

    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def _endian_char(
    big: bool,  # noqa: FBT001
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
    """Provides easier reading of binary objects that abstracts uniformly to all different stream/data types."""

    def __init__(
        self,
        stream: io.RawIOBase | io.BufferedIOBase | mmap.mmap,
        offset: int = 0,
        size: int | None = None,
    ):
        self.auto_close: bool = True

        self._stream: io.RawIOBase | io.BufferedIOBase | mmap.mmap = stream
        self._offset: int = offset
        self._stream.seek(offset)

        total_size = self.true_size()
        if self._offset > total_size - (size or 0):
            msg = "Specified offset/size is greater than the number of available bytes."
            raise OSError(msg)
        if size and size < 0:
            msg = f"Size must be greater than zero, got {size}"
            raise ValueError(msg)

        self._size: int = total_size - self._offset if size is None else size

    @property
    def _true_stream_position(self) -> int:
        """Private property to access the current position of the stream for debugging purposes.

        Returns:
        -------
            int: The current absolute position of the stream pointer.
        """
        return self._stream.tell()

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        self.close()

    def read(self, size: int) -> bytes | None:
        return self._stream.read(size)

    @classmethod
    def from_stream(
        cls,
        stream: io.RawIOBase | io.BufferedIOBase,
        offset: int = 0,
        size: int | None = None,
    ):
        if not stream.seekable():
            msg = "Stream must be seekable"
            raise ValueError(msg)
        try:
            mmap_stream = mmap.mmap(stream.fileno(), length=0, access=mmap.ACCESS_READ)
        except (ValueError, OSError):  # ValueError means mmap cannot map to empty files
            if isinstance(stream, io.RawIOBase):
                return cls(io.BufferedReader(stream), offset, size)
            return cls(stream, offset, size)
        else:
            return cls(mmap_stream, offset, size)

    @classmethod
    def from_file(
        cls,
        path: os.PathLike | str,
        offset: int = 0,
        size: int | None = None,
    ) -> Self:
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
        instance = cls.from_stream(stream, offset, size)
        if instance._stream is not stream:
            stream.close()
        return instance

    @classmethod
    def from_bytes(
        cls,
        data: bytes | memoryview | bytearray,
        offset: int = 0,
        size: int | None = None,
    ) -> Self:
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
        return cls(stream, offset, size)

    @classmethod
    def from_auto(
        cls,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
    ) -> Self:
        if isinstance(source, (os.PathLike, str)):  # is path
            reader = cls.from_file(source, offset, size)

        elif isinstance(source, (memoryview, bytes, bytearray)):  # is binary data
            reader = cls.from_bytes(source, offset, size)

        elif isinstance(source, (io.IOBase, mmap.mmap)):
            if isinstance(source, (io.RawIOBase, io.BufferedIOBase)):  # only seekable streams are supported.
                reader = cls.from_stream(source, offset, size)
            else:
                msg = f"Stream of type '{source.__class__}' is not supported by this {cls.__name__} class."
                raise TypeError(msg)

        elif isinstance(source, BinaryReader):  # is already a BinaryReader instance
            reader = cls(source._stream, source.offset(), source.size())

        else:
            msg = f"Must specify a path, bytes-like object, stream, io. or an existing BinaryReader instance, got type ({source.__class__})."
            raise TypeError(msg)

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
        """Returns the total number of bytes remaining in the stream.

        Returns:
        -------
            The number of accessible bytes.
        """
        return self._size

    def true_size(
        self,
    ) -> int:
        """Returns the total number of bytes in the stream.

        Returns:
        -------
            The total file size.
        """
        if isinstance(self._stream, mmap.mmap):
            return self._stream.size()

        current = self._stream.tell()
        self._stream.seek(0, os.SEEK_END)
        size = self._stream.tell()
        self._stream.seek(current)
        return size

    def remaining(
        self,
    ) -> int:
        """Returns the remaining number of bytes in the stream.

        Returns:
        -------
            The total file size.
        """
        return self.size() - self.position()

    def close(
        self,
    ):
        """Closes the underlying stream and releases any resources."""
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

        Returns:
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
        """
        return self._stream.read(self.remaining()) or b""

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
        return struct.unpack(f"{_endian_char(big)}B", self._stream.read(1) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}b", self._stream.read(1) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}H", self._stream.read(2) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}h", self._stream.read(2) or b"")[0]

    def read_uint32(
        self,
        *,
        max_neg1: bool = False,
        big: bool = False,
    ) -> int:
        """Reads an unsigned 32-bit integer from the stream.

        If max_is_neg1 flag is set to true and the bytes read off the stream are equal to 0xFFFFFFFF then the method
        will return a value of -1 instead of 4294967295 (hex 0xFFFFFFFF).

        Args:
        ----
            max_neg1: Return -1 when the value of the stream equals 0xFFFFFFFF (dec 4294967295).
            big: Read int bytes as big endian.

        Returns:
        -------
            An integer from the stream.
        """
        self.exceed_check(4)
        unpacked = struct.unpack(f"{_endian_char(big)}I", self._stream.read(4) or b"")[0]

        if unpacked == 0xFFFFFFFF and max_neg1:  # noqa: PLR2004
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
        return struct.unpack(f"{_endian_char(big)}i", self._stream.read(4) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}Q", self._stream.read(8) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}q", self._stream.read(8) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}f", self._stream.read(4) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}d", self._stream.read(8) or b"")[0]

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
        return self._stream.read(length) or b""

    def read_string(
        self,
        length: int,
        encoding: str | None = "windows-1252",
        errors: Literal["ignore", "strict", "replace"] = "ignore",
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
        string_byte_data = self._stream.read(length) or b""
        if encoding is None:
            string = decode_bytes_with_fallbacks(string_byte_data, encoding=encoding, errors=errors)
            RobustLogger().warning(f"decode_bytes_with_fallbacks called and returned '{string}'")
        else:
            string = string_byte_data.decode(encoding=encoding, errors=errors)
        if "\0" in string:
            string = string[: string.index("\0")].rstrip("\0")
            string = string.replace("\0", "")
        return string

    def read_terminated_string(
        self,
        terminator: str,
        length: int = -1,
        encoding: str = "ascii",
        *,
        strict: bool = True,
    ) -> str:
        """Reads a string continuously from the stream up to a specified length or until it hits the terminator character, whichever comes first.
        If length is -1, reads until the terminator is encountered without a length constraint.

        Args:
        ----
            terminator: The terminator character.
            length: The maximum length to read from the stream, or -1 for no length constraint.
                If a terminator is found before length is reached, skip the remaining.
            encoding: the encoding to use, in most cases this should be "ascii" (default)
            strict: Whether to stop appending the final string if a character could not be decoded by the encoding.

        Returns:
        -------
            A string read from the stream.
        """
        string: str = ""
        char: str = ""
        bytes_read: int = 0

        while char != terminator and (length == -1 or bytes_read < length):
            string += char
            self.exceed_check(1)
            char = self.read_bytes(1).decode(encoding=encoding, errors="ignore")
            bytes_read += 1
            if not char and strict:
                break

        if length == -1:
            return string

        # If a length is specified and not all bytes were read, skip the remaining bytes
        remaining_length = length - bytes_read
        if remaining_length > 0:
            self.skip(remaining_length)
        return string

    def read_locstring(
        self,
    ) -> LocalizedString:
        """Reads the localized string data structure from the stream.

        The binary data structure that is read follows the structure found in the GFF format specification.

        Returns:
        -------
            A LocalizedString read from the stream.
        """
        locstring: LocalizedString = LocalizedString.from_invalid()
        self.skip(4)  # total number of bytes of the localized string
        locstring.stringref = self.read_uint32(max_neg1=True)
        string_count = self.read_uint32()
        for _ in range(string_count):
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
        data = self._stream.read(length)
        self._stream.seek(-length, 1)
        return b"" if data is None else data

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
            OSError: When the attempted read operation exceeds the number of remaining bytes.
        """
        attempted_seek = self.position() + num
        if attempted_seek < 0:
            msg = f"Cannot seek to a negative value {attempted_seek}, abstracted seek value: {num}"
            raise OSError(msg)
        if attempted_seek > self.size():
            msg = "This operation would exceed the streams boundaries."
            raise OSError(msg)


class BinaryWriter(ABC):
    @abstractmethod
    def __enter__(self): ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb): ...

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
            return cls.to_file(source)
        if isinstance(source, bytearray):  # is mutable binary data
            return cls.to_bytearray(source)
        if isinstance(source, (bytes, memoryview)):  # is immutable binary data
            return cls.to_bytearray(bytearray(source))
        if isinstance(source, BinaryWriterFile):
            return BinaryWriterFile(source._stream, source.offset)  # noqa: SLF001
        if isinstance(source, BinaryWriterBytearray):
            return BinaryWriterBytearray(source._ba, source._offset)  # noqa: SLF001
        msg = "Must specify a path, bytes object or an existing BinaryWriter instance."
        raise NotImplementedError(msg)

    @staticmethod
    def dump(
        path: os.PathLike | str,
        data: bytes | bytearray | memoryview | mmap.mmap,
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

        Returns:
        -------
            The total file size.
        """

    @abstractmethod
    def data(
        self,
    ) -> bytes:
        """Returns the full file data.

        Returns:
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

        Returns:
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
        errors: str = "strict",
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
        stream: io.BufferedIOBase | io.RawIOBase,
        offset: int = 0,
    ):
        self._stream: io.BufferedIOBase | io.RawIOBase = stream
        self.offset: int = offset  # FIXME: rename to _offset like all the other classes in this file.
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

        Returns:
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

        Returns:
        -------
            The full file data.
        """
        pos: int = self._stream.tell()
        self._stream.seek(0)
        data: bytes | None = self._stream.read()
        self._stream.seek(pos)
        return b"" if data is None else data

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

        Returns:
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
        self._stream.write(value.encode(encoding or "windows-1252", errors=errors))

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
    ): ...

    def close(
        self,
    ):
        """Closes the stream."""

    def size(
        self,
    ) -> int:
        """Returns the total file size.

        Returns:
        -------
            The total file size.
        """
        return len(self._ba)

    def data(
        self,
    ) -> bytes:
        """Returns the full file data.

        Returns:
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

        Returns:
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
            bw.write_string(substring, prefix_length=4, encoding=language.get_encoding(), errors="replace")

        locstring_data: bytes = bw.data()
        self.write_uint32(len(locstring_data))
        self.write_bytes(locstring_data)

if __name__ == "__main__":
    import random
    import time

    if TYPE_CHECKING:
        from typing_extensions import Self

    # Constants
    TEST_FILE = "test_file.bin"
    NUM_OPERATIONS = 10000
    NUM_INSTANTIATIONS = 10
    FILE_SIZE = 500 * 1024 * 1024  # 500MB
    FILE_DATA: bytes | None = None

    # Function to perform the I/O operations
    def test_io_performance(stream_class: type, mode: str = "rb") -> tuple[int, int, int]:
        print(f"Testing {stream_class.__name__}, mode={mode}")
        assert FILE_DATA is not None
        instantiation_times = []
        operation_times = []

        for i in range(NUM_INSTANTIATIONS):
            try:
                instantiation_start_time = time.time()
                if stream_class is BinaryReader:
                    if mode == "file":
                        stream = BinaryReader.from_file(TEST_FILE)
                    elif mode == "bytes":
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_bytes(FILE_DATA)
                    elif mode == "mmap":
                        raw_raw_stream = open(TEST_FILE, "rb")
                        raw_stream = mmap.mmap(raw_raw_stream.fileno(), os.stat(TEST_FILE).st_size, access=mmap.ACCESS_READ)
                        instantiation_start_time = time.time()
                        stream = BinaryReader(raw_stream)
                    elif mode == "stream(io.BufferedReader)":
                        raw_raw_stream = open(TEST_FILE, "rb")
                        raw_stream = io.BufferedReader(raw_raw_stream)
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    elif mode == "stream(io.BufferedRandom)":
                        raw_raw_stream = open(TEST_FILE, "r+b")
                        raw_stream = io.BufferedRandom(raw_raw_stream)
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    elif mode == "stream(io.BytesIO)":
                        # Special handling for BytesIO
                        stream = io.BytesIO(FILE_DATA)
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(stream)
                    elif mode == "stream(io.FileIO)":
                        raw_stream = io.FileIO(TEST_FILE, "rb")
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    elif mode == "stream(raw)":
                        raw_stream = open(TEST_FILE, "rb")
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    else:
                        raise ValueError(f"cannot test mode: {mode}")
                elif stream_class is io.BytesIO:
                    # Special handling for BytesIO
                    stream = io.BytesIO(FILE_DATA)
                else:
                    raw_stream = open(TEST_FILE, mode)
                    if stream_class is io.BufferedReader:
                        stream = io.BufferedReader(raw_stream)
                    elif stream_class is io.BufferedRandom:
                        stream = io.BufferedRandom(raw_stream)
                    else:
                        stream = stream_class(TEST_FILE, mode)
                instantiation_end_time = time.time()
                instantiation_times.append(instantiation_end_time - instantiation_start_time)
            finally:
                if i != NUM_INSTANTIATIONS-1:
                    stream.close()

        try:
            operation_start_time = time.time()
            for _ in range(NUM_OPERATIONS):
                seek_position = random.randint(0, os.path.getsize(TEST_FILE) - 1)
                stream.seek(seek_position)
                stream.read(1)
            operation_end_time = time.time()
            operation_times.append(operation_end_time - operation_start_time)
        finally:
            stream.close()

        total_instantiation_time = sum(instantiation_times)
        total_operation_time = sum(operation_times)
        total_time = total_instantiation_time + total_operation_time

        return total_instantiation_time, total_operation_time, total_time

    # Main function to run the tests
    def main():
        global FILE_DATA  # noqa: PLW0603

        results = []
        # Test using different stream types
        stream_types = [
            (io.FileIO, "rb"),            # Raw access
            (io.BytesIO, "rb"),           # In-memory stream (needs special handling)
            (io.BufferedReader, "rb"),    # Buffered reading
            (io.BufferedRandom, "r+b"),   # Buffered random access
            (BinaryReader, "file"),
            (BinaryReader, "mmap"),
            (BinaryReader, "stream(io.BufferedReader)"),
            (BinaryReader, "stream(io.BufferedRandom)"),
            (BinaryReader, "stream(io.BytesIO)"),
            (BinaryReader, "stream(io.FileIO)"),
            (BinaryReader, "stream(raw)"),
        ]

        # Ensure the test file exists and is the correct size
        if not os.path.exists(TEST_FILE) or os.path.getsize(TEST_FILE) != FILE_SIZE:
            FILE_DATA = os.urandom(FILE_SIZE)
            print("Creating test file...")
            with open(TEST_FILE, "wb") as f:
                f.write(FILE_DATA)
        if FILE_DATA is None:
            with open(TEST_FILE, "rb") as f:
                FILE_DATA = f.read()

        # Run the tests
        for stream_class, mode in stream_types:
            total_instantiation_time, total_operation_time, total_time = test_io_performance(stream_class, mode)
            results.append([f"{stream_class.__name__}({mode})", total_instantiation_time, total_operation_time, total_time])

        # Sort by total performance (fastest first)
        results.sort(key=lambda x: x[3])
        fastest_total_time = results[0][3]
        fastest_instantiation_time = min(results, key=lambda x: x[1])[1]
        fastest_operation_time = min(results, key=lambda x: x[2])[2]

        for result in results:
            for i, elem in enumerate(result):
                if elem == 0:
                    result[i] = 0.0001

        # Print the results with additional statistics
        print("------------------------------------------------------\n\nInstantiation Statistics (sorted by fastest to slowest):\n")
        for result in results:
            speed_percent = (fastest_instantiation_time / result[1]) * 100
            print(f"{result[0]}: {result[1]:.4f} seconds ({speed_percent:.2f}% of fastest, {result[1] / NUM_INSTANTIATIONS:.2f}s per)")

        print("------------------------------------------------------\n\nOperation Statistics (sorted by fastest to slowest):")
        for result in results:
            speed_percent = (fastest_operation_time / result[2]) * 100
            print(f"{result[0]}: {result[2]:.4f} seconds ({speed_percent:.2f}% of fastest, {result[2] / NUM_INSTANTIATIONS:.2f}s per)")

        print("------------------------------------------------------\n\nCombined Statistics (sorted by fastest to slowest):")
        for result in results:
            speed_percent = (fastest_total_time / result[3]) * 100
            print(f"{result[0]}: {result[3]:.4f} seconds (Inst: {result[1]:.4f}s, Ops: {result[2]:.4f}s) ({speed_percent:.2f}% of fastest)")
        print("------------------------------------------------------\n")

        # Calculate average times
        avg_instantiation_time = sum(r[1] for r in results) / len(results)
        avg_operation_time = sum(r[2] for r in results) / len(results)
        avg_total_time = sum(r[3] for r in results) / len(results)

        print(f"Average Instantiation Time: {avg_instantiation_time:.4f} seconds")
        print(f"Average Operation Time: {avg_operation_time:.4f} seconds")
        print(f"Average Total Time: {avg_total_time:.4f} seconds")
        print(f"Fastest Total Time: {fastest_total_time:.4f} seconds")
        print(f"Slowest Total Time: {results[-1][3]:.4f} seconds")
        print(f"Speed Ratio (Slowest/Fastest): {results[-1][3] / fastest_total_time:.2f}\n")

    main()
