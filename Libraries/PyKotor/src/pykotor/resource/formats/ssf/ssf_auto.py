from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ssf.io_ssf import SSFBinaryReader, SSFBinaryWriter
from pykotor.resource.formats.ssf.io_ssf_xml import SSFXMLReader, SSFXMLWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.ssf.ssf_data import SSF
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_ssf(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the SSF data is believed to be in.

    This function performs a basic check and does not guarantee accuracy of the result or integrity of the data.

    Args:
    ----
        source: Source of the SSF data.
        offset: Offset into the data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
    -------
        The format of the SSF data.
    """

    def check(first4: str) -> ResourceType:
        if first4 == "SSF ":
            return ResourceType.SSF
        if "<" in first4:  # sourcery skip: assign-if-exp, reintroduce-else
            return ResourceType.SSF_XML
        # if "{" in first4:
        #    return ResourceType.SSF_JSON
        # if "," in first4:
        #    return ResourceType.SSF_CSV
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


def read_ssf(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
    file_format: ResourceType | None = None,
) -> SSF:
    """Returns an SSF instance from the source.

    The file format (SSF or SSF_XML) is automatically determined before parsing the data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.
        file_format: The file format to use (ResourceType.SSF, ResourceType.SSF_XML). If not specified, it will be detected automatically.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        An SSF instance.
    """
    if file_format is None:
        file_format = detect_ssf(source, offset)

    if file_format is ResourceType.INVALID:
        msg = "Failed to determine the format of the GFF file."
        raise ValueError(msg)

    if file_format is ResourceType.SSF:
        return SSFBinaryReader(source, offset, size or 0).load()
    if file_format is ResourceType.SSF_XML:
        return SSFXMLReader(source, offset, size or 0).load()
    msg = "Failed to determine the format of the GFF file."
    raise ValueError(msg)


def write_ssf(
    ssf: SSF,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.SSF,
):
    """Writes the SSF data to the target location with the specified format (SSF or SSF_XML).

    Args:
    ----
        ssf: The SSF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.SSF:
        SSFBinaryWriter(ssf, target).write()
    elif file_format is ResourceType.SSF_XML:
        SSFXMLWriter(ssf, target).write()
    else:
        msg = "Unsupported format specified; use SSF or SSF_XML."
        raise ValueError(msg)


def bytes_ssf(
    ssf: SSF,
    file_format: ResourceType = ResourceType.SSF,
) -> bytes:
    """Returns the SSF data in the specified format (SSF or SSF_XML) as a bytes object.

    This is a convenience method that wraps the write_ssf() method.

    Args:
    ----
        ssf: The target SSF object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The SSF data.
    """
    data = bytearray()
    write_ssf(ssf, data, file_format)
    return bytes(data)
