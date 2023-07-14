from pathlib import Path
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ssf import SSF, SSFBinaryReader, SSFXMLReader, SSFBinaryWriter
from pykotor.resource.formats.ssf.io_ssf_xml import SSFXMLWriter
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def detect_ssf(
        source: SOURCE_TYPES,
        offset: int = 0
) -> ResourceType:
    """
    Returns what format the SSF data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the SSF data.
        offset: Offset into the data.

    Raises:
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
        The format of the SSF data.
    """
    try:
        if isinstance(source, (str, Path)):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = ResourceType.SSF if reader.read_string(4) == "SSF " else ResourceType.SSF_XML
        elif isinstance(source, (bytes, bytearray)):
            file_format = ResourceType.SSF if source[:4].decode('ascii', 'ignore') == "SSF " else ResourceType.SSF_XML
        elif isinstance(source, BinaryReader):
            file_format = ResourceType.SSF if source.read_string(4) == "SSF " else ResourceType.SSF_XML
            source.skip(-4)
        else:
            file_format = ResourceType.INVALID
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        raise e
    except IOError:
        file_format = ResourceType.INVALID

    return file_format


def read_ssf(
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = None
) -> SSF:
    """
    Returns an SSF instance from the source. The file format (SSF or SSF_XML) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
        An SSF instance.
    """
    file_format = detect_ssf(source, offset)

    if file_format is ResourceType.INVALID:
        raise ValueError("Failed to determine the format of the GFF file.")

    if file_format == ResourceType.SSF:
        return SSFBinaryReader(source, offset, size).load()
    elif file_format == ResourceType.SSF_XML:
        return SSFXMLReader(source, offset, size).load()


def write_ssf(
        ssf: SSF,
        target: TARGET_TYPES,
        file_format: ResourceType = ResourceType.SSF
) -> None:
    """
    Writes the SSF data to the target location with the specified format (SSF or SSF_XML).

    Args:
        ssf: The SSF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format == ResourceType.SSF:
        SSFBinaryWriter(ssf, target).write()
    elif file_format == ResourceType.SSF_XML:
        SSFXMLWriter(ssf, target).write()
    else:
        raise ValueError("Unsupported format specified; use SSF or SSF_XML.")


def bytes_ssf(
        ssf: SSF,
        file_format: ResourceType = ResourceType.SSF
) -> bytes:
    """
    Returns the SSF data in the specified format (SSF or SSF_XML) as a bytes object.

    This is a convience method that wraps the write_ssf() method.

    Args:
        ssf: The target SSF object.
        file_format: The file format.

    Raises:
        ValueError: If the specified format was unsupported.

    Returns:
        The SSF data.
    """
    data = bytearray()
    write_ssf(ssf, data, file_format)
    return data
