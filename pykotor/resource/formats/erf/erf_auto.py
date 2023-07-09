from typing import Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.erf import ERF, ERFBinaryReader, ERFBinaryWriter, ERFType
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
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted.

    Returns:
        An ERF instance.
    """
    return ERFBinaryReader(source, offset).load()


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
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format == ResourceType.ERF or file_format == ResourceType.MOD:
        # Correct the ERF's ERFType to match the file extension
        if file_format == ResourceType.ERF:
            erf.erf_type = ERFType.ERF
        elif file_format == ResourceType.MOD:
            erf.erf_type = ERFType.MOD

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
        ValueError: If the specified format was unsupported.

    Returns:
        The ERF data.
    """
    data = bytearray()
    write_erf(erf, data, file_format)
    return data
