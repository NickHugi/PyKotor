from typing import Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import BWM, BWMBinaryReader, BWMBinaryWriter
from pykotor.resource.type import TARGET_TYPES, ResourceType, SOURCE_TYPES


def read_bwm(
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = None
) -> BWM:
    """
    Returns an WOK instance from the source.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted.

    Returns:
        An WOK instance.
    """
    return BWMBinaryReader(source, offset, size).load()


def write_bwm(
        wok: BWM,
        target: TARGET_TYPES,
        file_format: ResourceType = ResourceType.WOK
) -> None:
    """
    Writes the WOK data to the target location with the specified format (WOK only).

    Args:
        wok: The WOK file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format == ResourceType.WOK:
        BWMBinaryWriter(wok, target).write()
    else:
        raise ValueError("Unsupported format specified; use WOK.")


def bytes_bwm(
        bwm: BWM,
        file_format: ResourceType = ResourceType.WOK
) -> bytes:
    """
    Returns the BWM data in the specified format (WOK only) as a bytes object.

    This is a convenience method that wraps the write_bwm() method.

    Args:
        bwm: The target BWM.
        file_format: The file format.

    Raises:
        ValueError: If the specified format was unsupported.

    Returns:
        The BWM data.
    """
    data = bytearray()
    write_bwm(bwm, data, file_format)
    return data
