from typing import Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.vis import VIS, VISAsciiWriter, VISAsciiReader
from pykotor.resource.type import FileFormat


def load_vis(source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0) -> VIS:
    """
    Returns an VIS instance from the source. The file format (ascii only) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An VIS instance.
    """
    try:
        return VISAsciiReader(source, offset).load()
    except IOError:
        raise ValueError("Tried to load an unsupported or corrupted VIS file.")


def write_vis(vis: VIS, target: Union[str, bytearray, BinaryReader], file_format: FileFormat = FileFormat.ASCII) -> None:
    """
    Writes the VIS data to the target location with the specified format (ascii only).

    Args:
        vis: The VIS file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.ASCII:
        VISAsciiWriter(vis, target).write()
    else:
        raise ValueError("Unsupported format specified; use ASCII.")
