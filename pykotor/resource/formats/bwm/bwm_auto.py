from typing import Union

from pykotor.resource.type import ResourceType

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import BWM, BWMBinaryReader, BWMBinaryWriter


def load_bwm(source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0, size: int = None) -> BWM:
    """
    Returns an WOK instance from the source.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.
        IOError: If the file was inaccessible.

    Returns:
        An WOK instance.
    """
    return BWMBinaryReader(source, offset, size).load()


def write_bwm(wok: BWM, target: Union[str, bytearray, BinaryReader], file_format: ResourceType = ResourceType.WOK) -> None:
    """
    Writes the WOK data to the target location with the specified format (WOK only).

    Args:
        wok: The WOK file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.
        IOError: If the file was inaccessible.
    """
    if file_format == ResourceType.WOK:
        BWMBinaryWriter(wok, target).write()
    else:
        raise ValueError("Unsupported format specified; use WOK.")


def bytes_bwm(bwm: BWM, file_format: ResourceType = ResourceType.WOK) -> bytes:
    """
    Returns the BWM data in the specified format (WOK only) as a bytes object.

    This is a convience method that wraps the write_bwm() method.

    Args:
        bwm: The target BWM.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.

    Returns:
        The BWM data.
    """
    data = bytearray()
    write_bwm(bwm, data, file_format)
    return data
