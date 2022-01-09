from typing import overload, Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import GFF, GFFBinaryReader, GFFBinaryWriter, GFFContent, GFFXMLWriter, GFFXMLReader
from pykotor.resource.type import FileFormat, SOURCE_TYPES, TARGET_TYPES


@overload
def detect_gff(source: str, offset: int = 0):
    ...


@overload
def detect_gff(source: bytes, offset: int = 0):
    ...


@overload
def detect_gff(source: bytearray, offset: int = 0):
    ...


@overload
def detect_gff(source: BinaryReader, offset: int = 0):
    ...


def detect_gff(source: SOURCE_TYPES, offset: int = 0) -> FileFormat:
    """
    Returns what format the GFF data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the GFF data.
        offset: Offset into the data.

    Returns:
        The format of the GFF data.
    """
    try:
        if isinstance(source, str):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = FileFormat.BINARY if any(x for x in GFFContent if x.value == reader.read_string(4)) else FileFormat.XML
        elif isinstance(source, bytes) or isinstance(source, bytearray):
            file_format = FileFormat.BINARY if any(x for x in GFFContent if x.value == source[:4].decode('ascii', 'ignore')) else FileFormat.XML
        elif isinstance(source, BinaryReader):
            file_format = FileFormat.BINARY if any(x for x in GFFContent if x.value == source.read_string(4)) else FileFormat.XML
            source.skip(-4)
        else:
            file_format = FileFormat.INVALID
    except IOError:
        file_format = FileFormat.INVALID

    return file_format


def load_gff(source: SOURCE_TYPES, offset: int = 0) -> GFF:
    """
    Returns an GFF instance from the source. The file format (binary or xml) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An GFF instance.
    """
    file_format = detect_gff(source, offset)

    try:
        if file_format == FileFormat.BINARY:
            return GFFBinaryReader(source, offset).load()
        elif file_format == FileFormat.XML:
            return GFFXMLReader(source).load()
        else:
            raise ValueError
    except (IOError, ValueError):
        raise ValueError("Tried to load an unsupported or corrupted GFF file.")


def write_gff(gff: GFF, target: TARGET_TYPES, file_format: FileFormat = FileFormat.BINARY) -> None:
    """
    Writes the GFF data to the target location with the specified format (binary or xml).

    Args:
        gff: The GFF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.BINARY:
        GFFBinaryWriter(gff, target).write()
    elif file_format == FileFormat.XML:
        GFFXMLWriter(gff, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or XML.")
