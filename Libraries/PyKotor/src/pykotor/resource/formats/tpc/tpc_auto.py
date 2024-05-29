from __future__ import annotations

import os

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc.io_bmp import TPCBMPWriter
from pykotor.resource.formats.tpc.io_tga import TPCTGAReader, TPCTGAWriter
from pykotor.resource.formats.tpc.io_tpc import TPCBinaryReader, TPCBinaryWriter
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc.tpc_data import TPC
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_tpc(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the TPC data is believed to be in.

    This function performs a basic check and does not guarantee accuracy of the result or integrity of the data.

    Args:
    ----
        source: Source of the TPC data.
        offset: Offset into the source data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
    -------
        The format of the TPC data.
    """

    def do_check(
        first100: bytes,
    ) -> ResourceType:
        file_format = ResourceType.TPC
        if len(first100) < 100:
            file_format = ResourceType.TGA
        else:
            for i in range(15, 100):
                if first100[i] != 0:
                    file_format = ResourceType.TGA
        return file_format

    try:
        if isinstance(source, (str, CaseAwarePath)):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = do_check(reader.read_bytes(100))
        elif isinstance(source, (bytes, bytearray)):
            file_format = do_check(source[:100])
        elif isinstance(source, BinaryReader):
            file_format = do_check(source.read_bytes(100))
            source.skip(-100)
        else:
            file_format = ResourceType.INVALID
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        raise
    except OSError:
        file_format = ResourceType.INVALID

    return file_format


def read_tpc(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
    txi_source: SOURCE_TYPES | None = None,
) -> TPC:
    """Returns an TPC instance from the source.

    The file format (TPC or TGA) is automatically determined before parsing the data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.
        txi_source: An optional source to the TXI data to use. If this is a filepath, it *must* exist on disk.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        An TPC instance.
    """
    file_format: ResourceType = detect_tpc(source, offset)

    if file_format is ResourceType.TPC:
        loaded_tpc = TPCBinaryReader(source, offset, size or 0).load()
    elif file_format is ResourceType.TGA:
        loaded_tpc = TPCTGAReader(source, offset, size or 0).load()
    else:
        msg = "Failed to determine the format of the TPC/TGA file."
        raise ValueError(msg)
    if txi_source is None and isinstance(source, (os.PathLike, str)):
        txi_source = CaseAwarePath.pathify(source).with_suffix(".txi")
        if not txi_source.safe_isfile():
            return loaded_tpc
    elif isinstance(txi_source, (os.PathLike, str)):
        txi_source = CaseAwarePath.pathify(txi_source).with_suffix(".txi")
        if not txi_source.safe_isfile():
            return loaded_tpc

    if txi_source is None:
        return loaded_tpc
    with BinaryReader.from_auto(txi_source) as f:
        loaded_tpc.txi = f.read_all().decode(encoding="ascii", errors="ignore")
    return loaded_tpc


def write_tpc(
    tpc: TPC,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.TPC,
):
    """Writes the TPC data to the target location with the specified format (TPC, TGA or BMP).

    Args:
    ----
        tpc: The TPC file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.TGA:
        TPCTGAWriter(tpc, target).write()
    elif file_format is ResourceType.BMP:
        TPCBMPWriter(tpc, target).write()
    elif file_format is ResourceType.TPC:
        TPCBinaryWriter(tpc, target).write()
    else:
        msg = "Unsupported format specified; use TPC, TGA or BMP."
        raise ValueError(msg)


def bytes_tpc(
    tpc: TPC,
    file_format: ResourceType = ResourceType.TPC,
) -> bytes:
    """Returns the TPC data in the specified format (TPC, TGA or BMP) as a bytes object.

    This is a convenience method that wraps the write_tpc() method.

    Args:
    ----
        tpc: The target TPC object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The TPC data.
    """
    data = bytearray()
    write_tpc(tpc, data, file_format)
    return data
