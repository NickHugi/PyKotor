from typing import Union

from pykotor.resource.type import ResourceType

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.lyt import LYT, LYTAsciiWriter, LYTAsciiReader


def load_lyt(source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0) -> LYT:
    """
    Returns an LYT instance from the source. The file format (LYT only) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An LYT instance.
    """
    try:
        return LYTAsciiReader(source, offset).load()
    except IOError:
        raise ValueError("Tried to load an unsupported or corrupted LYT file.")


def write_lyt(lyt: LYT, target: Union[str, bytearray, BinaryReader], file_format: ResourceType = ResourceType.LYT) -> None:
    """
    Writes the LYT data to the target location with the specified format (LYT only).

    Args:
        lyt: The LYT file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.LYT:
        LYTAsciiWriter(lyt, target).write()
    else:
        raise ValueError("Unsupported format specified; use LYT.")
