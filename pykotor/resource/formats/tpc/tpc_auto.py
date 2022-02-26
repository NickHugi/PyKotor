from typing import overload, Union

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPC, TPCBinaryReader, TPCBinaryWriter, TPCTGAWriter, TPCBMPWriter, TPCTGAReader
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def detect_tpc(source: SOURCE_TYPES, offset: int = 0) -> ResourceType:
    """
    Returns what format the TPC data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the TPC data.
        offset: Offset into the source data.

    Returns:
        The format of the TPC data.
    """
    def do_check(first100: bytes) -> ResourceType:
        file_format = ResourceType.TPC
        if len(first100) < 100:
            file_format = ResourceType.TGA
        else:
            for i in range(15, 100):
                if first100[i] != 0:
                    file_format = ResourceType.TGA
        return file_format

    try:
        if isinstance(source, str):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = do_check(reader.read_bytes(100))
        elif isinstance(source, bytes) or isinstance(source, bytearray):
            file_format = do_check(source[:100])
        elif isinstance(source, BinaryReader):
            file_format = do_check(source.read_bytes(100))
            source.skip(-100)
        else:
            file_format = ResourceType.INVALID
    except IOError:
        file_format = ResourceType.INVALID

    return file_format


def load_tpc(source: SOURCE_TYPES, offset: int = 0, size: int = None) -> TPC:
    """
    Returns an TPC instance from the source. The file format (TPC or TGA) is automatically determined before
    parsing the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An TPC instance.
    """
    file_format = detect_tpc(source, offset)

    try:
        if file_format == ResourceType.TPC:
            return TPCBinaryReader(source, offset, size).load()
        elif file_format == ResourceType.TGA:
            return TPCTGAReader(source, offset, size).load()
        else:
            raise ValueError
    except (IOError, ValueError):
        raise ValueError("Tried to load an unsupported or corrupted TPC file.")


def write_tpc(tpc: TPC, target: TARGET_TYPES, file_format: ResourceType = ResourceType.TPC) -> None:
    """
    Writes the TPC data to the target location with the specified format (TPC, TGA or BMP).

    Args:
        tpc: The TPC file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.TGA:
        TPCTGAWriter(tpc, target).write()
    elif file_format == ResourceType.BMP:
        TPCBMPWriter(tpc, target).write()
    elif file_format == ResourceType.TPC:
        TPCBinaryWriter(tpc, target).write()
    else:
        raise ValueError("Unsupported format specified; use TPC, TGA or BMP.")

