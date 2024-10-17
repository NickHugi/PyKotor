from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bif.io_bif import BIFBinaryReader, BIFBinaryWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.bif.bif_data import BIF
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def read_bif(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
    key_source: SOURCE_TYPES | None = None,
) -> BIF:
    """Returns a BIF instance from the source.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes allowed to read from the stream. If not specified, uses the whole stream.
        key_source: The source of the KEY file associated with this BIF.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        A BIF instance.
    """
    bif = BIFBinaryReader(source, offset, size or 0).load()

    if key_source:
        keys = _read_key_data(key_source)
        _merge_key_data(bif, keys)

    return bif


def _read_key_data(key_source: SOURCE_TYPES) -> dict[int, str]:
    with BinaryReader.from_auto(key_source) as reader:
        reader.skip(8)  # Skip file type and version
        bif_count = reader.read_uint32()
        key_count = reader.read_uint32()
        file_table_offset = reader.read_uint32()
        reader.skip(4)  # Skip key table offset

        reader.seek(file_table_offset + bif_count * 12)  # Skip file table

        keys = {}
        for _ in range(key_count):
            resref = reader.read_string(16)
            reader.skip(2)  # Skip restype_id
            res_id = reader.read_uint32()
            keys[res_id] = resref

    return keys


def _merge_key_data(bif: BIF, keys: dict[int, str]):
    for i, resource in enumerate(bif._resources):  # noqa: SLF001
        if i in keys:
            resource.resref = ResRef(keys[i])


def write_bif(
    bif: BIF,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.BIF,
):
    """Writes the BIF data to the target location with the specified format.

    Args:
    ----
        bif: The BIF file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.BIF:
        BIFBinaryWriter(bif, target).write()
    else:
        msg = "Unsupported format specified; use BIF."
        raise ValueError(msg)


def bytes_bif(
    bif: BIF,
    file_format: ResourceType = ResourceType.BIF,
) -> bytes:
    """Returns the BIF data in the specified format as a bytes object.

    This is a convenience method that wraps the write_bif() method.

    Args:
    ----
        bif: The target BIF object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The BIF data.
    """
    data = bytearray()
    write_bif(bif, data, file_format)
    return bytes(data)
