from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.lip import LIP, LIPBinaryReader, LIPXMLReader, LIPBinaryWriter
from pykotor.resource.formats.lip.io_lip_xml import LIPXMLWriter
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def detect_lip(
        source: SOURCE_TYPES | object,
        offset: int = 0
) -> ResourceType:
    """
    Returns what format the LIP data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the LIP data.
        offset: Offset into the data.

    Raises:
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
        The format of the LIP data.
    """
    try:
        if isinstance(source, str):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = ResourceType.LIP if reader.read_string(4) == "LIP " else ResourceType.LIP_XML
        elif isinstance(source, (bytes, bytearray)):
            file_format = ResourceType.LIP if source[:4].decode('ascii', 'ignore') == "LIP " else ResourceType.LIP_XML
        elif isinstance(source, BinaryReader):
            file_format = ResourceType.LIP if source.read_string(4) == "LIP " else ResourceType.LIP_XML
            source.skip(-4)
        else:
            file_format = ResourceType.INVALID
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        raise e
    except IOError:
        file_format = ResourceType.INVALID

    return file_format


def read_lip(
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = None
) -> LIP:
    """
    Returns an LIP instance from the source. The file format (LIP or LIP_XML) is automatically determined before parsing
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
        An LIP instance.
    """
    file_format = detect_lip(source, offset)

    if file_format is ResourceType.INVALID:
        raise ValueError("Failed to determine the format of the GFF file.")

    if file_format == ResourceType.LIP:
        return LIPBinaryReader(source, offset, size).load()
    elif file_format == ResourceType.LIP_XML:
        return LIPXMLReader(source, offset, size).load()


def write_lip(
        lip: LIP,
        target: TARGET_TYPES,
        file_format: ResourceType = ResourceType.LIP
) -> None:
    """
    Writes the LIP data to the target location with the specified format (LIP or LIP_XML).

    Args:
        lip: The LIP file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format == ResourceType.LIP:
        LIPBinaryWriter(lip, target).write()
    elif file_format == ResourceType.LIP_XML:
        LIPXMLWriter(lip, target).write()
    else:
        raise ValueError("Unsupported format specified; use LIP or LIP_XML.")


def bytes_lip(
        lip: LIP,
        file_format: ResourceType = ResourceType.LIP
) -> bytes:
    """
    Returns the LIP data in the specified format (LIP or LIP_XML) as a bytes object.

    This is a convenience method that wraps the write_lip() method.

    Args:
        lip: The target LIP object.
        file_format: The file format.

    Raises:
        ValueError: If the specified format was unsupported.

    Returns:
        The LIP data.
    """
    data = bytearray()
    write_lip(lip, data, file_format)
    return data
