from typing import Union

from pykotor.resource.type import ResourceType

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.rim import RIM, RIMBinaryReader, RIMBinaryWriter


def read_rim(
        source: Union[str, bytes, bytearray, BinaryReader],
        offset: int = 0,
        size: int = None
) -> RIM:
    """
    Returns an RIM instance from the source. The file format (RIM) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An RIM instance.
    """
    try:
        return RIMBinaryReader(source, offset, size).load()
    except IOError:
        raise ValueError("Tried to load an unsupported or corrupted RIM file.")


def write_rim(
        rim: RIM,
        target: Union[str, bytearray, BinaryReader],
        file_format: ResourceType = ResourceType.RIM
) -> None:
    """
    Writes the RIM data to the target location with the specified format (RIM only).

    Args:
        rim: The RIM file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.RIM:
        RIMBinaryWriter(rim, target).write()
    else:
        raise ValueError("Unsupported format specified; use RIM.")


def bytes_rim(
        rim: RIM,
        file_format: ResourceType = ResourceType.RIM
) -> bytes:
    """
    Returns the RIM data in the specified format (RIM only) as a bytes object.

    This is a convience method that wraps the write_rim() method.

    Args:
        rim: The target RIM object.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.

    Returns:
        The RIM data.
    """
    data = bytearray()
    write_rim(rim, data, file_format)
    return data
