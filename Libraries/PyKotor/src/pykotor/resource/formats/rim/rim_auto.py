from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.rim.io_rim import RIMBinaryReader, RIMBinaryWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def read_rim(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> RIM:
    """Returns an RIM instance from the source.

    The file format (RIM only) is automatically determined before parsing the data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        An RIM instance.
    """
    return RIMBinaryReader(source, offset, size or 0).load()


def write_rim(
    rim: RIM,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.RIM,
):
    """Writes the RIM data to the target location with the specified format (RIM only).

    Args:
    ----
        rim: The RIM file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.RIM:
        RIMBinaryWriter(rim, target).write()
    else:
        msg = "Unsupported format specified; use RIM."
        raise ValueError(msg)


def bytes_rim(
    rim: RIM,
    file_format: ResourceType = ResourceType.RIM,
) -> bytes:
    """Returns the RIM data in the specified format (RIM only) as a bytes object.

    This is a convenience method that wraps the write_rim() method.

    Args:
    ----
        rim: The target RIM object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The RIM data.
    """
    data = bytearray()
    write_rim(rim, data, file_format)
    return data
