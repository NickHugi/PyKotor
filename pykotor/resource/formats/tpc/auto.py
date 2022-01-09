from typing import overload, Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPC, TPCBinaryReader, TPCBinaryWriter, TPCTGAWriter, TPCBMPWriter
from pykotor.resource.type import FileFormat, SOURCE_TYPES, TARGET_TYPES


def load_tpc(source: SOURCE_TYPES, offset: int = 0) -> TPC:
    """
    Returns an TPC instance from the source. This will only load TPC files, not other image formats.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An TPC instance.
    """
    return TPCBinaryReader(source, offset).load()


def write_tpc(tpc: TPC, target: TARGET_TYPES, file_format: FileFormat = FileFormat.BINARY) -> None:
    """
    Writes the TPC data to the target location with the specified format (tpc, tga, bmp).

    Args:
        tpc: The TPC file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.TGA:
        TPCTGAWriter(tpc, target).write()
    elif file_format == FileFormat.BMP:
        TPCBMPWriter(tpc, target).write()
    elif file_format == FileFormat.BINARY:
        TPCBinaryWriter(tpc, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or XML.")
