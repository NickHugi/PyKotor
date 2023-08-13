from pathlib import Path

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.mdl import (
    MDL,
    MDLAsciiReader,
    MDLAsciiWriter,
    MDLBinaryReader,
    MDLBinaryWriter,
)
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def detect_mdl(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the MDL data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

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
    try:
        if isinstance(source, str | Path):
            source = Path(source)
            with BinaryReader.from_file(source, offset) as reader:
                first4 = reader.read_bytes(4)
                file_format = (
                    ResourceType.MDL
                    if first4 == b"\x00\x00\x00\x00"
                    else ResourceType.MDL_ASCII
                )
        elif isinstance(source, bytes | bytearray):
            file_format = (
                ResourceType.MDL
                if source[:4] == b"\x00\x00\x00\x00"
                else ResourceType.MDL_ASCII
            )
        elif isinstance(source, BinaryReader):
            first4 = source.read_bytes(4)
            file_format = (
                ResourceType.MDL
                if first4 == b"\x00\x00\x00\x00"
                else ResourceType.MDL_ASCII
            )
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
    size: int = 0,
    source_ext: SOURCE_TYPES | None = None,
    offset_ext: int = 0,
    size_ext: int = 0,
) -> MDL:
    """Returns an MDL instance from the source. The file format (MDL or MDL_ASCII) is automatically determined before
    parsing the data.

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

    if file_format is ResourceType.INVALID:
        msg = "Failed to determine the format of the MDL file."
        raise ValueError(msg)

    if file_format == ResourceType.MDL:
        return MDLBinaryReader(
            source, offset, size, source_ext, offset_ext, size_ext
        ).load()
    elif file_format == ResourceType.MDL_ASCII:
        return MDLAsciiReader(source, offset, size).load()
    return None


def write_mdl(
    mdl: MDL,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.MDL,
    target_ext: TARGET_TYPES | None = None,
) -> None:
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
    if file_format == ResourceType.MDL:
        MDLBinaryWriter(mdl, target, target_ext).write()
    elif file_format == ResourceType.MDL_ASCII:
        MDLAsciiWriter(mdl, target).write()
    else:
        msg = "Unsupported format specified; use MDL or MDL_ASCII."
        raise ValueError(msg)
