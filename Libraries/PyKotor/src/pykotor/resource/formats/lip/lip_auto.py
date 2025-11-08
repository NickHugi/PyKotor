from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.lip.io_lip import LIPBinaryReader, LIPBinaryWriter
from pykotor.resource.formats.lip.io_lip_json import LIPJSONReader, LIPJSONWriter
from pykotor.resource.formats.lip.io_lip_xml import LIPXMLReader, LIPXMLWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.lip.lip_data import LIP
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_lip(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the LIP data is believed to be in.

    This function performs a basic check and does not guarantee accuracy of the result or integrity of the data.

    Args:
    ----
        source: Source of the LIP data.
        offset: Offset into the data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
    -------
        The format of the LIP data.
    """

    def check(first4):
        if first4 == "LIP ":
            return ResourceType.LIP
        if "<" in first4:  # sourcery skip: assign-if-exp, reintroduce-else
            return ResourceType.LIP_XML
        if "{" in first4:
            return ResourceType.LIP_JSON
        # if "," in first4:
        #    return ResourceType.LIP_CSV
        return ResourceType.INVALID

    file_format: ResourceType
    try:
        with BinaryReader.from_auto(source, offset) as reader:
            file_format = check(reader.read_string(4))
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        raise
    except OSError:
        file_format = ResourceType.INVALID

    return file_format


def read_lip(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> LIP:
    """Returns an LIP instance from the source.

    The file format (LIP or LIP_XML) is automatically determined before parsing the data.

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
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        An LIP instance.
    """
    file_format = detect_lip(source, offset)

    if file_format is ResourceType.LIP:
        return LIPBinaryReader(source, offset, size or 0).load()
    if file_format is ResourceType.LIP_XML:
        return LIPXMLReader(source, offset, size or 0).load()
    if file_format is ResourceType.LIP_JSON:
        return LIPJSONReader(source, offset, size or 0).load()
    # if file_format is ResourceType.INVALID:
    msg = "Failed to determine the format of the GFF file."
    raise ValueError(msg)


def write_lip(
    lip: LIP,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.LIP,
):
    """Writes the LIP data to the target location with the specified format (LIP or LIP_XML).

    Args:
    ----
        lip: The LIP file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.LIP:
        LIPBinaryWriter(lip, target).write()
    elif file_format is ResourceType.LIP_XML:
        LIPXMLWriter(lip, target).write()
    elif file_format is ResourceType.LIP_JSON:
        LIPJSONWriter(lip, target).write()
    else:
        msg = "Unsupported format specified; use LIP or LIP_XML or LIP_JSON."
        raise ValueError(msg)


def bytes_lip(
    lip: LIP,
    file_format: ResourceType = ResourceType.LIP,
) -> bytes:
    """Returns the LIP data in the specified format (LIP or LIP_XML) as a bytes object.

    This is a convenience method that wraps the write_lip() method.

    Args:
    ----
        lip: The target LIP object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The LIP data.
    """
    data = bytearray()
    write_lip(lip, data, file_format)
    return data
