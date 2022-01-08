from typing import overload, Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tlk import TLK, TLKBinaryReader, TLKXMLReader, TLKBinaryWriter
from pykotor.resource.formats.tlk.io_xml import TLKXMLWriter
from pykotor.resource.type import FileFormat, SOURCE_TYPES, TARGET_TYPES


@overload
def detect_tlk(source: str, offset: int = 0):
    ...


@overload
def detect_tlk(source: bytes, offset: int = 0):
    ...


@overload
def detect_tlk(source: bytearray, offset: int = 0):
    ...


@overload
def detect_tlk(source: BinaryReader, offset: int = 0):
    ...


def detect_tlk(source: SOURCE_TYPES, offset: int = 0) -> FileFormat:
    """
    Returns what format the TLK data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the TLK data.
        offset: Offset into the data.

    Returns:
        The format of the TLK data.
    """
    try:
        if isinstance(source, str):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = FileFormat.BINARY if reader.read_string(4) == "TLK " else FileFormat.XML
        elif isinstance(source, bytes) or isinstance(source, bytearray):
            file_format = FileFormat.BINARY if source[:4].decode('ascii', 'ignore') == "TLK " else FileFormat.XML
        elif isinstance(source, BinaryReader):
            file_format = FileFormat.BINARY if source.read_string(4) == "TLK " else FileFormat.XML
            source.skip(-4)
        else:
            file_format = FileFormat.INVALID
    except IOError:
        file_format = FileFormat.INVALID

    return file_format


def load_tlk(source: SOURCE_TYPES, offset: int = 0) -> TLK:
    """
    Returns an TLK instance from the source. The file format (binary or xml) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An TLK instance.
    """
    file_format = detect_tlk(source, offset)

    try:
        if file_format == FileFormat.BINARY:
            return TLKBinaryReader(source, offset).load()
        elif file_format == FileFormat.XML:
            return TLKXMLReader(source).load()
        else:
            raise ValueError
    except (IOError, ValueError):
        raise ValueError("Tried to load an unsupported or corrupted TLK file.")


def write_tlk(tlk: TLK, target: TARGET_TYPES, file_format: FileFormat = FileFormat.BINARY) -> None:
    """
    Writes the TLK data to the target location with the specified format (binary or xml).

    Args:
        tlk: The TLK file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.BINARY:
        TLKBinaryWriter(tlk, target).write()
    elif file_format == FileFormat.XML:
        TLKXMLWriter(tlk, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or XML.")
