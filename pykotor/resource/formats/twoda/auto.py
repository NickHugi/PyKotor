from typing import overload, Union

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.twoda import TwoDA, TwoDABinaryReader, TwoDABinaryWriter, TwoDACSVWriter, TwoDACSVReader
from pykotor.resource.type import FileFormat, SOURCE_TYPES, TARGET_TYPES


@overload
def detect_2da(source: str, offset: int = 0):
    ...


@overload
def detect_2da(source: bytes, offset: int = 0):
    ...


@overload
def detect_2da(source: bytearray, offset: int = 0):
    ...


@overload
def detect_2da(source: BinaryReader, offset: int = 0):
    ...


def detect_2da(source: SOURCE_TYPES, offset: int = 0) -> FileFormat:
    """
    Returns what format the TwoDA data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the TwoDA data.
        offset: Offset into the data.

    Returns:
        The format of the TwoDA data.
    """
    try:
        if isinstance(source, str):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = FileFormat.BINARY if reader.read_string(4) == "2DA " else FileFormat.CSV
        elif isinstance(source, bytes) or isinstance(source, bytearray):
            file_format = FileFormat.BINARY if source[:4].decode('ascii', 'ignore') == "2DA " else FileFormat.CSV
        elif isinstance(source, BinaryReader):
            file_format = FileFormat.BINARY if source.read_string(4) == "2DA " else FileFormat.CSV
            source.skip(-4)
        else:
            file_format = FileFormat.INVALID
    except IOError:
        file_format = FileFormat.INVALID

    return file_format



@overload
def load_2da(source: str, offset: int = 0):
    ...


@overload
def load_2da(source: bytes, offset: int = 0):
    ...


@overload
def load_2da(source: bytearray, offset: int = 0):
    ...


@overload
def load_2da(source: BinaryReader, offset: int = 0):
    ...


def load_2da(source: SOURCE_TYPES, offset: int = 0) -> TwoDA:
    """
    Returns an TwoDA instance from the source. The file format (binary or xml) is automatically determined before parsing
    the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An TwoDA instance.
    """
    file_format = detect_2da(source, offset)

    try:
        if file_format == FileFormat.BINARY:
            return TwoDABinaryReader(source, offset).load()
        elif file_format == FileFormat.CSV:
            return TwoDACSVReader(source).load()
        else:
            raise ValueError
    except (IOError, ValueError):
        raise ValueError("Tried to load an unsupported or corrupted TwoDA file.")



@overload
def write_2da(twoda: TwoDA, target: str, file_format: FileFormat = FileFormat.BINARY)-> None:
    ...


@overload
def write_2da(twoda: TwoDA, target: bytearray, file_format: FileFormat = FileFormat.BINARY) -> None:
    ...


@overload
def write_2da(twoda: TwoDA, target: BinaryWriter, file_format: FileFormat = FileFormat.BINARY) -> None:
    ...


def write_2da(twoda: TwoDA, target: TARGET_TYPES, file_format: FileFormat = FileFormat.BINARY) -> None:
    """
    Writes the TwoDA data to the target location with the specified format (binary or xml).

    Args:
        twoda: The TwoDA file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.BINARY:
        TwoDABinaryWriter(twoda, target).write()
    elif file_format == FileFormat.CSV:
        TwoDACSVWriter(twoda, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or CSV.")
