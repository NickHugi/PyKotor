from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.bwm.io_bwm import BWMBinaryReader, BWMBinaryWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def read_bwm(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> BWM:
    """Returns an WOK instance from the source.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted.

    Returns:
    -------
        An WOK instance.
    """
    return BWMBinaryReader(source, offset, size or 0).load()


def write_bwm(
    wok: BWM,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.WOK,
):
    """Writes the WOK data to the target location with the specified format (WOK only).

    Args:
    ----
        wok: The WOK file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.WOK:
        BWMBinaryWriter(wok, target).write()
    else:
        msg = "Unsupported format specified; use WOK."
        raise ValueError(msg)


def bytes_bwm(
    bwm: BWM,
    file_format: ResourceType = ResourceType.WOK,
) -> bytes:
    """Returns the BWM data in the specified format (WOK only) as a bytes object.

    This is a convenience method that wraps the write_bwm() method.

    Args:
    ----
        bwm: The target BWM.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The BWM data.
    """
    data = bytearray()
    write_bwm(bwm, data, file_format)
    return data
