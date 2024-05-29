from __future__ import annotations

import os

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tlk.io_tlk import TLKBinaryReader, TLKBinaryWriter
from pykotor.resource.formats.tlk.io_tlk_json import TLKJSONReader, TLKJSONWriter
from pykotor.resource.formats.tlk.io_tlk_xml import TLKXMLReader, TLKXMLWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.language import Language
    from pykotor.resource.formats.tlk.tlk_data import TLK
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_tlk(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the TLK data is believed to be in.

    This function performs a basic check and does not guarantee accuracy of the result or integrity of the data.
    Catch OSError to catch any exceptions this function could throw.

    Args:
    ----
        source: Source of the TLK data.
        offset: Offset into the data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        OSError: Other various system-level exceptions.

    Returns:
    -------
        The format of the TLK data.
    """

    def check(
        first4,
    ):
        if first4 == "TLK ":
            return ResourceType.TLK
        if "{" in first4:
            return ResourceType.TLK_JSON
        if "<" in first4:  # sourcery skip: assign-if-exp, reintroduce-else
            return ResourceType.TLK_XML
        return ResourceType.INVALID

    try:
        if isinstance(source, (os.PathLike, str)):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = check(reader.read_string(4))
        elif isinstance(source, (memoryview, bytes, bytearray)):
            file_format = check(bytes(source[:4]).decode("ascii", "ignore"))
        elif isinstance(source, BinaryReader):
            file_format = check(source.read_string(4))
            source.skip(-4)
        else:
            file_format = ResourceType.INVALID
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        raise
    except OSError:
        file_format = ResourceType.INVALID

    return file_format


def read_tlk(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
    language: Language | None = None,
) -> TLK:
    """Returns an TLK instance from the source.

    The file format (TLK, TLK_XML or TLK_JSON) is automatically determined before parsing the data.

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
        An TLK instance.
    """
    file_format: ResourceType = detect_tlk(source, offset)

    if file_format is ResourceType.INVALID:
        msg = "Failed to determine the format of the TLK file."
        raise ValueError(msg)

    if file_format is ResourceType.TLK:
        return TLKBinaryReader(source, offset, size or 0, language).load()
    if file_format is ResourceType.TLK_XML:
        return TLKXMLReader(source, offset, size or 0).load()
    if file_format is ResourceType.TLK_JSON:
        return TLKJSONReader(source, offset, size or 0).load()
    msg = "Unsupported TLK format specified."
    raise ValueError(msg)


def write_tlk(
    tlk: TLK,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.TLK,
):
    """Writes the TLK data to the target location with the specified format (TLK, TLK_XML or TLK_JSON).

    Args:
    ----
        tlk: The TLK file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.TLK:
        TLKBinaryWriter(tlk, target).write()
    elif file_format is ResourceType.TLK_XML:
        TLKXMLWriter(tlk, target).write()
    elif file_format is ResourceType.TLK_JSON:
        TLKJSONWriter(tlk, target).write()
    else:
        msg = "Unsupported format specified; use TLK or TLK_XML."
        raise ValueError(msg)


def bytes_tlk(
    tlk: TLK,
    file_format: ResourceType = ResourceType.TLK,
) -> bytes:
    """Returns the TLK data in the specified format (TLK or TLK_XML or TLK_JSON) as a bytes object.

    This is a convenience method that wraps the write_tlk() method.

    Args:
    ----
        tlk: The target TLK object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The TLK data.
    """
    data = bytearray()
    write_tlk(tlk, data, file_format)
    return data
