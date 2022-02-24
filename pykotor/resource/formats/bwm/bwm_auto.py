from typing import Union

from pykotor.resource.type import ResourceType

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import BWM, BWMBinaryReader, BWMBinaryWriter


def load_bwm(source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0) -> BWM:
    """
    Returns an WOK instance from the source.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.
        IOError: If the file was inaccessible.

    Returns:
        An WOK instance.
    """
    return BWMBinaryReader(source, offset).load()


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
