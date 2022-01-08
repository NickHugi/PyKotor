from typing import Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.rim import RIM, RIMBinaryReader, RIMBinaryWriter
from pykotor.resource.type import FileFormat


def load_rim(source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0) -> RIM:
    """
    Returns an RIM instance from the source. The file format (binary or xml) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An RIM instance.
    """
    try:
        return RIMBinaryReader(source, offset).load()
    except IOError:
        raise ValueError("Tried to load an unsupported or corrupted RIM file.")


def write_rim(rim: RIM, target: Union[str, bytearray, BinaryReader], file_format: FileFormat = FileFormat.BINARY) -> None:
    """
    Writes the RIM data to the target location with the specified format (binary only).

    Args:
        rim: The RIM file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.BINARY:
        RIMBinaryWriter(rim, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or XML.")
