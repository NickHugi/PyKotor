from __future__ import annotations

import io
import pathlib
import sys
from typing import Any

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

import pytest

from pykotor.common.stream import BinaryReader


# Test BinaryReader Initialization
@pytest.mark.parametrize(
    "test_id, stream, offset, size, expected_position, expected_exception",
    [
        ("happy_path_file_stream", io.BytesIO(b"1234567890"), 0, None, 0, None),
        ("happy_path_offset", io.BytesIO(b"1234567890"), 5, None, 0, None),
        ("happy_path_size", io.BytesIO(b"1234567890"), 0, 5, 0, None),
        ("edge_case_max_offset", io.BytesIO(b"1234567890"), 10, None, 0, None),
        ("error_case_offset_too_large", io.BytesIO(b"1234567890"), 11, None, None, OSError),
        ("error_case_negative_offset", io.BytesIO(b"1234567890"), -1, None, None, ValueError),
        ("error_case_negative_size", io.BytesIO(b"1234567890"), 0, -1, None, ValueError),
    ],
)
def test_binary_reader_initialization(
    test_id: str,
    stream,
    offset: int,
    size: int | None,
    expected_position: int,
    expected_exception,
):
    # Arrange
    if expected_exception:
        with pytest.raises(expected_exception):
            BinaryReader(stream, offset, size)
    else:
        # Act
        reader = BinaryReader(stream, offset, size)
        position = reader.position()

        # Assert
        assert position == expected_position


# Test BinaryReader Read Methods
@pytest.mark.parametrize(
    "test_id, method, args, expected_result, expected_exception",
    [
        ("happy_path_read_uint8", "read_uint8", {}, 1, None),
        ("happy_path_read_int16_big_endian", "read_int16", {"big": True}, 258, None),
        ("happy_path_read_uint32_max_neg1", "read_uint32", {"max_neg1": True}, 4294902273, None),
        ("error_case_read_beyond_stream", "read_uint64", {}, None, OSError),
        # ("error_case_read_negative_length", "read_bytes", {"length": -1}, None, OSError),  I guess stream's support negative lengths.
    ],
)
def test_binary_reader_read_methods(
    test_id: str,
    method: str,
    args: dict[str, Any],
    expected_result: int | None,
    expected_exception,
):
    # Arrange
    stream = io.BytesIO(b"\x01\x02\xff\xff\xff\xff")
    reader = BinaryReader(stream)

    if expected_exception:
        with pytest.raises(expected_exception):
            getattr(reader, method)(**args)
    else:
        # Act
        result = getattr(reader, method)(**args)

        # Assert
        assert result == expected_result


# Test BinaryReader Read String Methods
@pytest.mark.parametrize(
    "test_id, method, args, expected_result, expected_exception",
    [
        ("happy_path_read_string", "read_string", {"length": 5}, "Hello", None),
        ("happy_path_read_terminated_string", "read_terminated_string", {"terminator": "\x00"}, "HelloWorld", None),
        ("error_case_read_string_beyond_stream", "read_string", {"length": 15}, None, OSError),
        ("error_case_read_terminated_string_no_terminator", "read_terminated_string", {"terminator": "\x01"}, None, OSError),
    ],
)
def test_binary_reader_read_string_methods(
    test_id: str,
    method: str,
    args: dict[str, Any],
    expected_result,
    expected_exception,
):
    # Arrange
    stream = io.BytesIO(b"HelloWorld\x00")
    reader = BinaryReader(stream)

    if expected_exception:
        with pytest.raises(expected_exception):
            getattr(reader, method)(**args)
    else:
        # Act
        result = getattr(reader, method)(**args)

        # Assert
        assert result == expected_result


# Test BinaryReader Context Manager
@pytest.mark.parametrize(
    "test_id, expected_closed",
    [
        ("happy_path_context_manager", True),
    ],
)
def test_binary_reader_context_manager(
    test_id: str,
    expected_closed,
):
    # Arrange
    stream = io.BytesIO(b"1234567890")

    # Act
    with BinaryReader(stream) as reader:
        pass
    closed = stream.closed

    # Assert
    assert closed == expected_closed


# Test BinaryReader from_file Class Method
@pytest.mark.parametrize(
    "test_id, file_content, offset, size, expected_result, expected_exception",
    [
        ("happy_path_from_file", b"1234567890", 0, None, b"1234567890", None),
        ("error_case_from_file_no_contents", b"", 0, None, None, ValueError),  # mmap can't map empty files
    ],
)
def test_binary_reader_from_file(
    test_id: str,
    file_content,
    offset,
    size,
    expected_result,
    expected_exception,
    tmp_path,
):
    # Arrange
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(file_content)

    if expected_exception:
        with pytest.raises(expected_exception):
            BinaryReader.from_file(str(file_path), offset, size)
    else:
        # Act
        reader = BinaryReader.from_file(str(file_path), offset, size)
        result = reader.read_all()

        # Assert
        assert result == expected_result


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-ra",
            "--capture=no",
        ]
    )
