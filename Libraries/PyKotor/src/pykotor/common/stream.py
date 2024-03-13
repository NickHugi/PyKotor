"""This module holds classes relating to read and write operations."""
from __future__ import annotations

import io
import mmap
import os
import struct

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.system.path import Path

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Literal

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
        buffer_size: int | None = None,
    ):
        self.auto_close: bool = True

        # Safe to change outside constructor.
        self.buffer_size: int = 4096 if buffer_size is None else buffer_size  # Size of the buffer for chunked reading

        # Definitions don't change after construction.
        self._stream: io.RawIOBase | io.BufferedIOBase | mmap.mmap = stream
        self._offset: int = offset

        # Definitions are updated internally.
        self._stream_pos: int = offset
        self._buffer: bytearray = bytearray()
        self._buffer_pos: int = 0

        # Setup
        self._stream.seek(offset)

        # Setup the size, ensure it's nonzero.
        total_size = self.true_size()
        if offset > total_size - (size or 0):
            msg = "Specified offset/size is greater than the number of available bytes."
            raise OSError(msg)
        if size is not None and size <= 0:
            msg = f"Size must be greater than zero, got {size}"
            raise ValueError(msg)

        self._size: int = total_size - offset if size is None else size
        self._stream_pos: int = offset # Initialize the stream position to the offset.

    def __repr__(
        self,
    ):
        return (
            f"{self.__class__.__name__}(stream={self._stream}, offset={self._offset}, size={self._size}, buffer_size={self.buffer_size})"
            f"(extra attrs: self._buffer_pos={self._buffer_pos} self._stream_pos={self._stream_pos} )"
        )

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

    def _fill_buffer(self):
        # Calculate the remaining size that can be read from the stream, respecting the initial offset and total size.
        read_size = min(self.buffer_size, self.remaining())
        self._buffer = bytearray(self._stream.read(read_size) or b"")
        self._buffer_pos = 0
        # Do not adjust _stream_pos here; it will be updated on read.

    def read(self, size: int) -> bytes:
        if size <= 0:
            return b""

        result = bytearray()
        while size > 0:
            # If the buffer is exhausted, attempt to refill it.
            if self._buffer_pos >= len(self._buffer):
                prev_buffer_len = len(self._buffer)  # Capture the buffer length before refill
                self._fill_buffer()
                if not self._buffer:  # If buffer is still empty after refill, end of file/stream.
                    raise OSError("This operation would exceed the bounds of the stream.")
                # Adjust stream position only after actual refill.
                self._stream_pos += (prev_buffer_len - self._buffer_pos)

            # Calculate how much to read from the buffer.
            available_to_read = min(size, len(self._buffer) - self._buffer_pos)
            result.extend(self._buffer[self._buffer_pos:self._buffer_pos + available_to_read])
            self._buffer_pos += available_to_read
            size -= available_to_read

        # Ensure stream position reflects the total bytes read from the buffer after all operations.
        if self._buffer_pos == len(self._buffer):  # If buffer was completely consumed,
            self._stream_pos += len(result)  # adjust stream position accordingly.

        return bytes(result)

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

        # return cls(stream, offset, size) here to test issues with mmap

        try:
            mmap_stream = mmap.mmap(stream.fileno(), length=0, access=mmap.ACCESS_READ)
        except (ValueError, OSError):  # ValueError means mmap cannot map to empty files
            return cls(stream, offset, size)
        else:
            return cls(mmap_stream, offset, size)

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
        instance = cls.from_stream(stream, offset, size)
        if instance._stream is not stream:  # Close the old stream if needed. # noqa: SLF001
            stream.close()
        return instance

    @classmethod
    def from_bytes(
        cls,
        data: bytes | memoryview | bytearray,
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
        return cls(stream, offset, size)

    @classmethod
    def from_auto(
        cls,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
    ) -> BinaryReader:
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
            reader = cls(source._stream, source._offset, source._size)  # noqa: SLF001

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
            if offset != 0:  # seek is an expensive call.
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
        if isinstance(self._stream, mmap.mmap):  # Faster than seeking around but only supported for mmap.
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
        return self._size - self.position()

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
        self.read(length)

    def position(self) -> int:
        # Reflects the abstraction of reading from the stream, including buffer reads.
        return self._stream_pos + self._buffer_pos - self._offset

    def seek(self, position: int):
        """Moves the internal pointer to the specified position, efficiently handling buffering."""
        absolute_position = position + self._offset
        # For positions outside the current buffer or when the buffer is empty,
        # Seek the underlying stream and refill the buffer.
        self._stream.seek(absolute_position)
        self._stream_pos = absolute_position  # Update the stream position accordingly.
        self._buffer = bytearray()  # Clear the current buffer.
        self._fill_buffer()  # Refill the buffer from the current stream position.
        self._buffer_pos = 0  # Reset buffer position for the new buffer.

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
        return self.read(self.remaining()) or b""

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
        return struct.unpack(f"{_endian_char(big)}B", self.read(1) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}b", self.read(1))[0]

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
        return struct.unpack(f"{_endian_char(big)}H", self.read(2) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}h", self.read(2) or b"")[0]

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
        unpacked = struct.unpack(f"{_endian_char(big)}I", self.read(4) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}i", self.read(4) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}Q", self.read(8) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}q", self.read(8) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}f", self.read(4) or b"")[0]

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
        return struct.unpack(f"{_endian_char(big)}d", self.read(8) or b"")[0]

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
        return self.read(length) or b""

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
        string_byte_data = self.read(length) or b""
        string = decode_bytes_with_fallbacks(string_byte_data, encoding=encoding, errors=errors)
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

    def peek(self, length: int = 1) -> bytes:
        # Peeks ahead in the stream the specified number of bytes without advancing the position.
        current_pos = self.position()
        data = self.read(length)
        self.seek(current_pos)
        return data

    def exceed_check(self, num: int):
        if num < self.remaining():
            raise OSError("This operation would exceed the stream's boundaries.")


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

    def data(  # FIXME:
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

    def clear(  # FIXME:
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
            bw.write_string(substring, prefix_length=4, encoding=language.get_encoding())

        locstring_data: bytes = bw.data()
        self.write_uint32(len(locstring_data))
        self.write_bytes(locstring_data)
