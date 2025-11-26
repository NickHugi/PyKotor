"""This module holds classes relating to read and write operations."""

from __future__ import annotations

import io
import mmap
import os

from types import TracebackType
from typing import Any, IO

from pathlib import Path
from typing_extensions import Self

from pykotor.common.language import LocalizedString
from utility.common.stream import ArrayHead as _ArrayHead, RawBinaryReader, RawBinaryWriter, RawBinaryWriterBytearray, RawBinaryWriterFile

ArrayHead = _ArrayHead  # backwards compatibility


class BinaryReader(RawBinaryReader):
    """Provides easier reading of binary objects that abstracts uniformly to all different stream/data types."""

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
        string_count: int = self.read_uint32()
        for _ in range(string_count):
            string_id: int = self.read_uint32()
            language, gender = LocalizedString.substring_pair(string_id)
            length: int = self.read_uint32()
            string: str = self.read_string(length, encoding=language.get_encoding())
            locstring.set_data(language, gender, string)
        return locstring


class BinaryWriter(RawBinaryWriter):
    def __enter__(
        self,
    ) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def write_locstring(
        self,
        value: LocalizedString,
        *,
        big: bool = False,
    ): ...

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
    def to_file(
        cls,
        path: str | os.PathLike,
    ) -> BinaryWriterFile:
        return BinaryWriterFile(Path(path).open("wb"))


class BinaryWriterFile(RawBinaryWriterFile):
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
        bw: RawBinaryWriterBytearray = RawBinaryWriter.to_bytearray()
        bw.write_uint32(value.stringref, big=big, max_neg1=True)
        bw.write_uint32(len(value), big=big)

        for language, gender, substring in value:
            string_id: int = LocalizedString.substring_id(language, gender)
            bw.write_uint32(string_id, big=big)
            bw.write_string(substring, prefix_length=4, encoding=language.get_encoding())

        locstring_data: bytes = bw.data()
        self.write_uint32(len(locstring_data))
        self.write_bytes(locstring_data)


class BinaryWriterBytearray(RawBinaryWriterBytearray):
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

    # Constants
    TEST_FILE = "test_file.bin"
    NUM_OPERATIONS = 10000
    NUM_INSTANTIATIONS = 10
    FILE_SIZE = 500 * 1024 * 1024  # 500MB
    FILE_DATA: bytes | None = None

    # Function to perform the I/O operations
    def test_io_performance(  # noqa: C901, PLR0912, PLR0915
        stream_class: type,
        mode: str = "rb",
    ) -> tuple[float, float, float]:
        print(f"Testing {stream_class.__name__}, mode={mode}")
        assert FILE_DATA is not None
        instantiation_times: list[float] = []
        operation_times: list[float] = []
        stream: BinaryReader | io.BytesIO | io.FileIO | io.BufferedReader | io.BufferedRandom | None = None
        raw_raw_stream: io.RawIOBase | io.BufferedIOBase | mmap.mmap | None = None
        raw_stream: IO[Any] | mmap.mmap | None = None

        for i in range(NUM_INSTANTIATIONS):
            try:
                instantiation_start_time: float = time.time()
                if stream_class is BinaryReader:
                    if mode == "file":
                        stream = BinaryReader.from_file(TEST_FILE)
                    elif mode == "bytes":
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_bytes(FILE_DATA)
                    elif mode == "mmap":
                        raw_raw_stream = open(TEST_FILE, "rb")  # noqa: PTH123, SIM115
                        raw_stream = mmap.mmap(raw_raw_stream.fileno(), os.stat(TEST_FILE).st_size, access=mmap.ACCESS_READ)  # noqa: PTH116
                        instantiation_start_time = time.time()
                        stream = BinaryReader(raw_stream)
                    elif mode == "stream(io.BufferedReader)":
                        raw_raw_stream = open(TEST_FILE, "rb")  # noqa: PTH123, SIM115
                        raw_stream = io.BufferedReader(raw_raw_stream)
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    elif mode == "stream(io.BufferedRandom)":
                        raw_raw_stream = open(TEST_FILE, "r+b")  # noqa: PTH123, SIM115
                        assert isinstance(raw_raw_stream, io.RawIOBase), "raw_raw_stream must be a RawIOBase"
                        raw_stream = io.BufferedRandom(raw_raw_stream)
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    elif mode == "stream(io.BytesIO)":
                        # Special handling for BytesIO
                        raw_stream = io.BytesIO(FILE_DATA)
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    elif mode == "stream(io.FileIO)":
                        raw_stream = io.FileIO(TEST_FILE, "rb")
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    elif mode == "stream(raw)":
                        raw_stream = open(TEST_FILE, "rb")  # noqa: PTH123, SIM115
                        instantiation_start_time = time.time()
                        stream = BinaryReader.from_stream(raw_stream)
                    else:
                        raise ValueError(f"cannot test mode: {mode}")
                elif stream_class is io.BytesIO:
                    # Special handling for BytesIO
                    raw_stream = io.BytesIO(FILE_DATA)
                    instantiation_start_time = time.time()
                    stream = BinaryReader.from_stream(raw_stream)
                else:
                    raw_stream = open(TEST_FILE, mode)  # noqa: PTH123, SIM115
                    if stream_class is io.BufferedReader:
                        assert isinstance(raw_stream, io.RawIOBase), "raw_stream must be a RawIOBase"
                        stream = io.BufferedReader(raw_stream)
                    elif stream_class is io.BufferedRandom:
                        assert isinstance(raw_stream, io.RawIOBase), "raw_stream must be a RawIOBase"
                        stream = io.BufferedRandom(raw_stream)
                    else:
                        stream = stream_class(TEST_FILE, mode)  # pyright: ignore[reportArgumentType, reportCallIssue]
                instantiation_end_time: float = time.time()
                instantiation_times.append(instantiation_end_time - instantiation_start_time)
            finally:
                if i != NUM_INSTANTIATIONS - 1:
                    assert stream is not None, "stream is None"
                    stream.close()

        try:
            operation_start_time: float = time.time()
            for _ in range(NUM_OPERATIONS):
                seek_position: int = random.randint(0, os.path.getsize(TEST_FILE) - 1)  # noqa: S311, PTH202
                assert stream is not None, "stream is None"
                stream.seek(seek_position)
                stream.read(1)
            operation_end_time: float = time.time()
            operation_times.append(operation_end_time - operation_start_time)
        finally:
            assert stream is not None, "stream is None"
            stream.close()

        total_instantiation_time: float = sum(instantiation_times)
        total_operation_time: float = sum(operation_times)
        total_time: float = total_instantiation_time + total_operation_time

        return total_instantiation_time, total_operation_time, total_time

    # Main function to run the tests
    def main():
        global FILE_DATA  # noqa: PLW0603

        results: list[list[int | float]] = []
        # Test using different stream types
        stream_types: list[tuple[type, str]] = [
            (io.FileIO, "rb"),  # Raw access
            (io.BytesIO, "rb"),  # In-memory stream (needs special handling)
            (io.BufferedReader, "rb"),  # Buffered reading
            (io.BufferedRandom, "r+b"),  # Buffered random access
            (BinaryReader, "file"),
            (BinaryReader, "mmap"),
            (BinaryReader, "stream(io.BufferedReader)"),
            (BinaryReader, "stream(io.BufferedRandom)"),
            (BinaryReader, "stream(io.BytesIO)"),
            (BinaryReader, "stream(io.FileIO)"),
            (BinaryReader, "stream(raw)"),
        ]

        # Ensure the test file exists and is the correct size
        if not os.path.exists(TEST_FILE) or os.path.getsize(TEST_FILE) != FILE_SIZE:  # noqa: PTH110, PTH202
            FILE_DATA = os.urandom(FILE_SIZE)
            print("Creating test file...")
            with open(TEST_FILE, "wb") as f:  # noqa: PTH123
                f.write(FILE_DATA)
        if FILE_DATA is None:
            with open(TEST_FILE, "rb") as f:  # noqa: PTH123
                FILE_DATA = f.read()

        # Run the tests
        for stream_class, mode in stream_types:
            print(f"Testing {stream_class.__name__}, mode={mode}")
            total_instantiation_time, total_operation_time, total_time = test_io_performance(stream_class, mode)
            results.append(
                [
                    f"{stream_class.__name__}({mode})",  # pyright: ignore[reportArgumentType]
                    total_instantiation_time,
                    total_operation_time,
                    total_time,
                ]
            )

        # Sort by total performance (fastest first)
        results.sort(key=lambda x: x[3])
        fastest_total_time: float = results[0][3]
        fastest_instantiation_time: float = min(results, key=lambda x: x[1])[1]
        fastest_operation_time: float = min(results, key=lambda x: x[2])[2]

        for result in results:
            for i, elem in enumerate(result):
                if elem != 0:
                    continue
                result[i] = 0.0001

        # Print the results with additional statistics
        print("------------------------------------------------------\n\nInstantiation Statistics (sorted by fastest to slowest):\n")
        for result in results:
            speed_percent: float = (fastest_instantiation_time / result[1]) * 100
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
        avg_instantiation_time: float = sum(r[1] for r in results) / len(results)
        avg_operation_time: float = sum(r[2] for r in results) / len(results)
        avg_total_time: float = sum(r[3] for r in results) / len(results)

        print(f"Average Instantiation Time: {avg_instantiation_time:.4f} seconds")
        print(f"Average Operation Time: {avg_operation_time:.4f} seconds")
        print(f"Average Total Time: {avg_total_time:.4f} seconds")
        print(f"Fastest Total Time: {fastest_total_time:.4f} seconds")
        print(f"Slowest Total Time: {results[-1][3]:.4f} seconds")
        print(f"Speed Ratio (Slowest/Fastest): {results[-1][3] / fastest_total_time:.2f}\n")

    main()


def get_aurora_scale(obj) -> float:
    """If the scale is uniform, i.e, x=y=z, we will return
    the value. Else we'll return 1.
    """
    scale = obj.scale
    if scale[0] == scale[1] == scale[2]:
        return scale[0]

    return 1.0


def get_aurora_rot_from_object(obj) -> list[float]:
    q = obj.rotation_quaternion
    return [q.axis[0], q.axis[1], q.axis[2], q.angle]
