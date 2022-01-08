from typing import overload, Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.lip import LIP, LIPBinaryReader, LIPXMLReader, LIPBinaryWriter
from pykotor.resource.formats.lip.io_xml import LIPXMLWriter
from pykotor.resource.type import FileFormat, SOURCE_TYPES, TARGET_TYPES


@overload
def detect_lip(source: str, offset: int = 0):
    ...


@overload
def detect_lip(source: bytes, offset: int = 0):
    ...


@overload
def detect_lip(source: bytearray, offset: int = 0):
    ...


@overload
def detect_lip(source: BinaryReader, offset: int = 0):
    ...


def detect_lip(source: SOURCE_TYPES, offset: int = 0) -> FileFormat:
    """
    Returns what format the LIP data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the LIP data.
        offset: Offset into the data.

    Returns:
        The format of the LIP data.
    """
    try:
        if isinstance(source, str):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = FileFormat.BINARY if reader.read_string(4) == "LIP " else FileFormat.XML
        elif isinstance(source, bytes) or isinstance(source, bytearray):
            file_format = FileFormat.BINARY if source[:4].decode('ascii', 'ignore') == "LIP " else FileFormat.XML
        elif isinstance(source, BinaryReader):
            file_format = FileFormat.BINARY if source.read_string(4) == "LIP " else FileFormat.XML
            source.skip(-4)
        else:
            file_format = FileFormat.INVALID
    except IOError:
        file_format = FileFormat.INVALID

    return file_format


def load_lip(source: SOURCE_TYPES, offset: int = 0) -> LIP:
    """
    Returns an LIP instance from the source. The file format (binary or xml) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An LIP instance.
    """
    file_format = detect_lip(source, offset)

    try:
        if file_format == FileFormat.BINARY:
            return LIPBinaryReader(source, offset).load()
        elif file_format == FileFormat.XML:
            return LIPXMLReader(source).load()
        else:
            raise ValueError
    except (IOError, ValueError):
        raise ValueError("Tried to load an unsupported or corrupted LIP file.")


def write_lip(lip: LIP, target: TARGET_TYPES, file_format: FileFormat = FileFormat.BINARY) -> None:
    """
    Writes the LIP data to the target location with the specified format (binary or xml).

    Args:
        lip: The LIP file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.BINARY:
        LIPBinaryWriter(lip, target).write()
    elif file_format == FileFormat.XML:
        LIPXMLWriter(lip, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or XML.")
