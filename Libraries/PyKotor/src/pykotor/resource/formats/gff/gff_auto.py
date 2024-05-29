from __future__ import annotations

import os

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff.gff_data import GFFContent
from pykotor.resource.formats.gff.io_gff import GFFBinaryReader, GFFBinaryWriter
from pykotor.resource.formats.gff.io_gff_xml import GFFXMLReader, GFFXMLWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_gff(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the GFF data is believed to be in.

    This function performs a basic check and does not guarantee accuracy of the result or integrity of the data.

    Args:
    ----
        source: Source of the GFF data.
        offset: Offset into the data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
    -------
        The format of the GFF data.
    """

    def check(first4: str) -> ResourceType:
        if any(x.value == first4 for x in GFFContent):
            return ResourceType.GFF
        if "<" in first4:  # sourcery skip: assign-if-exp, reintroduce-else
            return ResourceType.GFF_XML
        # if "{" in first4:
        #    return ResourceType.GFF_JSON
        # if "," in first4:
        #    return ResourceType.GFF_CSV
        return ResourceType.INVALID

    file_format: ResourceType
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


def read_gff(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> GFF:  # sourcery skip: hoist-statement-from-if, reintroduce-else
    """Returns an GFF instance from the source.

    The file format (GFF or GFF_XML) is automatically determined before parsing the data.

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
        A GFF instance.
    """
    file_format = detect_gff(source, offset)

    if file_format is ResourceType.GFF:
        return GFFBinaryReader(source, offset, size or 0).load()
    if file_format is ResourceType.GFF_XML:
        return GFFXMLReader(source, offset, size or 0).load()

    msg = "Failed to determine the format of the GFF file."
    # if file_format is ResourceType.INVALID:
    raise ValueError(msg)


def write_gff(
    gff: GFF,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.GFF,
):
    """Writes the GFF data to the target location with the specified format (GFF or GFF_XML).

    Args:
    ----
        gff: The GFF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.GFF:
        GFFBinaryWriter(gff, target).write()
    elif file_format is ResourceType.GFF_XML:
        GFFXMLWriter(gff, target).write()
    else:
        msg = "Unsupported format specified; use GFF or GFF_XML."
        raise ValueError(msg)


def bytes_gff(
    gff: GFF,
    file_format: ResourceType = ResourceType.GFF,
) -> bytes:
    """Returns the GFF data in the specified format (GFF or GFF_XML) as a bytes object.

    This is a convenience method that wraps the write_gff() and read_gff() methods.

    Args:
    ----
        gff: GFF: The target GFF.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The GFF data.
    """
    data = bytearray()
    write_gff(gff, data, file_format)
    return data
