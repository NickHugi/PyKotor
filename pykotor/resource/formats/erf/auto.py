from typing import Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.erf import ERF, ERFBinaryReader, ERFBinaryWriter
from pykotor.resource.type import FileFormat


def load_erf(source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0) -> ERF:
    """
    Returns an ERF instance from the source. The file format (binary or xml) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An ERF instance.
    """
    try:
        return ERFBinaryReader(source, offset).load()
    except IOError:
        raise ValueError("Tried to load an unsupported or corrupted ERF file.")


def write_erf(erf: ERF, target: Union[str, bytearray, BinaryReader], file_format: FileFormat = FileFormat.BINARY) -> None:
    """
    Writes the ERF data to the target location with the specified format (binary only).

    Args:
        erf: The ERF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.BINARY:
        ERFBinaryWriter(erf, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or XML.")
