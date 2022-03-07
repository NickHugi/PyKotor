from typing import Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.erf import ERF, ERFBinaryReader, ERFBinaryWriter
from pykotor.resource.type import ResourceType


def read_erf(
        source: Union[str, bytes, bytearray, BinaryReader],
        offset: int = 0,
        size: int = None
) -> ERF:
    """
    Returns an ERF instance from the source. The file format (ERF or MOD) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An ERF instance.
    """
    try:
        return ERFBinaryReader(source, offset).load()
    except IOError:
        raise ValueError("Tried to load an unsupported or corrupted ERF file.")


def write_erf(
        erf: ERF,
        target: Union[str, bytearray, BinaryReader],
        file_format: ResourceType = ResourceType.ERF
) -> None:
    """
    Writes the ERF data to the target location with the specified format (ERF or MOD).

    Args:
        erf: The ERF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.ERF or file_format == ResourceType.MOD:
        ERFBinaryWriter(erf, target).write()
    else:
        raise ValueError("Unsupported format specified; use ERF or MOD.")


def bytes_erf(
        erf: ERF,
        file_format: ResourceType = ResourceType.ERF
) -> bytes:
    """
    Returns the ERF data in the specified format (ERF or MOD) as a bytes object.

    This is a convience method that wraps the write_erf() method.

    Args:
        erf: The target ERF object.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.

    Returns:
        The ERF data.
    """
    data = bytearray()
    write_erf(erf, data, file_format)
    return data
