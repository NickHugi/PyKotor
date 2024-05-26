from __future__ import annotations

import os

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.mdl.io_mdl import MDLBinaryReader, MDLBinaryWriter
from pykotor.resource.formats.mdl.io_mdl_ascii import MDLAsciiReader, MDLAsciiWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_mdl(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the MDL data is believed to be in.

    This function performs a basic check and does not guarantee accuracy of the result or integrity of the data.

    Args:
    ----
        source: Source of the MDL data.
        offset: Offset into the source data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
    -------
        The format of the MDL data.
    """

    def check(first4):
        if first4 == b"\x00\x00\x00\x00":
            return ResourceType.MDL
        return ResourceType.MDL_ASCII
        # if "<" in first4:
        #    return ResourceType.MDL_XML
        # if "{" in first4:
        #    return ResourceType.MDL_JSON
        # if "," in first4:
        #    return ResourceType.MDL_CSV
        # return ResourceType.INVALID

    try:
        if isinstance(source, (os.PathLike, str)):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = check(reader.read_bytes(4))
        elif isinstance(source, (memoryview, bytes, bytearray)):
            file_format = check(bytes(source[:4]))
        elif isinstance(source, BinaryReader):
            file_format = check(source.read_bytes(4))
            source.skip(-4)
        else:
            file_format = ResourceType.INVALID
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        raise
    except OSError:
        file_format = ResourceType.INVALID

    return file_format


def read_mdl(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
    source_ext: SOURCE_TYPES | None = None,
    offset_ext: int = 0,
    size_ext: int = 0,
) -> MDL:
    """Returns an MDL instance from the source.

    The file format (MDL or MDL_ASCII) is automatically determined before parsing the data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: The number of bytes to read from the source.
        source_ext: Source of the MDX data, if available.
        offset_ext: Offset into the source_ext data.
        size_ext: The number of bytes to read from the MDX source.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        An MDL instance.
    """
    file_format = detect_mdl(source, offset)

    if file_format is ResourceType.MDL:
        return MDLBinaryReader(
            source,
            offset,
            size or 0,
            source_ext,
            offset_ext,
            size_ext,
        ).load()
    if file_format is ResourceType.MDL_ASCII:
        return MDLAsciiReader(source, offset, size or 0).load()
    msg = "Failed to determine the format of the MDL file."
    raise ValueError(msg)


def write_mdl(
    mdl: MDL,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.MDL,
    target_ext: TARGET_TYPES | None = None,
):
    """Writes the MDL data to the target location with the specified format (MDL or MDL_ASCII).

    Args:
    ----
        mdl: The MDL file being written.
        target: The location to write the data to.
        file_format: The file format.
        target_ext: The location to write the MDX data to (if file format is MDL).

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.MDL:
        MDLBinaryWriter(mdl, target, target_ext or target).write()
    elif file_format is ResourceType.MDL_ASCII:
        MDLAsciiWriter(mdl, target).write()
    else:
        msg = "Unsupported format specified; use MDL or MDL_ASCII."
        raise ValueError(msg)


def bytes_mdl(
    mdl: MDL,
    file_format: ResourceType = ResourceType.MDL,
) -> bytes:
    """Returns the MDL data in the specified format (MDL or MDL_ASCII) as a bytes object.

    This is a convenience method that wraps the write_mdl() and read_mdl() methods.

    Args:
    ----
        mdl: MDL: The target MDL.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The MDL data.
    """
    data = bytearray()
    write_mdl(mdl, data, file_format)
    return data
