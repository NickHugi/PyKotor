from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.key.io_key import KEYBinaryReader, KEYBinaryWriter
from pykotor.resource.formats.key.key_data import KEY
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_key(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Detect if the source is a valid KEY file.

    Args:
        source: The source to check
        offset: Offset into the source to start checking

    Returns:
        ResourceType.KEY if valid, ResourceType.INVALID otherwise
    """
    try:
        with BinaryReader.from_auto(source) as reader:
            reader.seek(offset)
            file_type: str = reader.read_string(4)
            file_version: str = reader.read_string(4)

        if file_type == KEY.FILE_TYPE and file_version in [KEY.FILE_VERSION, "V1.1"]:
            return ResourceType.KEY
    except (OSError, ValueError):
        RobustLogger().warning("Invalid KEY file format")

    return ResourceType.INVALID


def read_key(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> KEY:
    """Returns a KEY instance from the source.

    Args:
        source: The source of the data
        offset: The byte offset of the file inside the data
        size: Number of bytes allowed to read from the stream. If not specified, uses the whole stream

    Raises:
        FileNotFoundError: If the file could not be found
        IsADirectoryError: If the specified path is a directory
        PermissionError: If the file could not be accessed
        ValueError: If the file was corrupted or invalid format

    Returns:
        A KEY instance
    """
    file_format: ResourceType = detect_key(source, offset)
    if file_format is not ResourceType.KEY:
        msg = "Invalid KEY file format"
        raise ValueError(msg)

    reader = KEYBinaryReader(source, offset, size or 0)
    key: KEY = reader.load()
    key.build_lookup_tables()
    return key


def write_key(
    key: KEY,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.KEY,
) -> None:
    """Write KEY data to target.

    Args:
        key: The KEY data to write
        target: Where to write the data
        file_format: The format to write in (only KEY supported)

    Raises:
        ValueError: If format not supported
    """
    if file_format is not ResourceType.KEY:
        msg = f"Unsupported KEY format: {file_format}"
        raise ValueError(msg)

    writer = KEYBinaryWriter(key, target)
    writer.write()


def bytes_key(
    key: KEY,
    file_format: ResourceType = ResourceType.KEY,
) -> bytes:
    """Get KEY data as bytes.

    Args:
        key: The KEY data
        file_format: The format to use

    Returns:
        The KEY data as bytes
    """
    data = bytearray()
    write_key(key, data, file_format)
    return bytes(data)
