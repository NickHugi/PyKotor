from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.erf.erf_data import ERFType
from pykotor.resource.formats.erf.io_erf import ERFBinaryReader, ERFBinaryWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.erf.erf_data import ERF
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def read_erf(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> ERF:
    """Returns an ERF instance from the source.

    The file format (ERF or MOD) is automatically determined before parsing the data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted.

    Returns:
    -------
        An ERF instance.
    """
    return ERFBinaryReader(source, offset, size or 0).load()


def write_erf(
    erf: ERF,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.ERF,
):
    """Writes the ERF data to the target location with the specified format (ERF or MOD).

    Args:
    ----
        erf: The ERF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if hasattr(file_format, "name") and file_format in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):
        ERFBinaryWriter(erf, target).write()
    else:
        msg = f"Unsupported format specified: '{file_format!r}'; expected one of {', '.join(f'ResourceType.{member.name}' for member in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV))}."
        raise ValueError(msg)


def bytes_erf(
    erf: ERF,
    file_format: ResourceType = ResourceType.ERF,
) -> bytes:
    """Returns the ERF data in the specified format (ERF or MOD) as a bytes object.

    This is a convenience method that wraps the write_erf() method.

    Args:
    ----
        erf: The target ERF object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The ERF data.
    """
    if hasattr(file_format, "name") and file_format in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):
        data = bytearray()
        write_erf(erf, data, file_format)
        return data

    msg = f"Unsupported format specified: '{file_format!r}'; expected one of [SAV, {', '.join(member.name for member in ERFType)}]"
    raise ValueError(msg)
