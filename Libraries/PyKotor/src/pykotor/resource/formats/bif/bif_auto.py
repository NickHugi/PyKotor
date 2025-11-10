from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bif.io_bif import BIFBinaryReader, BIFBinaryWriter, BIFType
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.bif import BIF
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_bif(
    source: SOURCE_TYPES,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the BIF data is believed to be in.

    This function performs a basic check and does not guarantee accuracy of the result or integrity of the data.

    Args:
    ----
        source: Source of the BIF data.
        offset: Offset into the data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
    -------
        The format of the BIF data.
    """
    with BinaryReader.from_auto(source, offset) as reader:
        file_type: str = reader.read_string(4)
        file_version: str = reader.read_string(4)
        if file_type not in (BIFType.BIF.value, BIFType.BZF.value):
            msg: str = f"Invalid BIF file type: {file_type}"
            raise ValueError(msg)

        if file_version != "V1  " and file_version != "V1.1":
            msg: str = f"Unsupported BIF version: {file_version}"
            raise ValueError(msg)

    return ResourceType.BIF


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
    _restype: ResourceType = detect_bif(source, offset)
    bif: BIF = BIFBinaryReader(source, offset, size or 0).load()

    if key_source:
        keys: dict[int, str] = _read_key_data(key_source)
        _merge_key_data(bif, keys)

    return bif


def _read_key_data(
    key_source: SOURCE_TYPES,
) -> dict[int, str]:
    with BinaryReader.from_auto(key_source) as reader:
        reader.skip(8)  # Skip file type and version
        bif_count: int = reader.read_uint32()
        key_count: int = reader.read_uint32()
        file_table_offset: int = reader.read_uint32()
        reader.skip(4)  # Skip key table offset

        reader.seek(file_table_offset + bif_count * 12)  # Skip file table

        keys: dict[int, str] = {}
        for _ in range(key_count):
            resref: str = reader.read_string(16)
            reader.skip(2)  # Skip restype_id
            res_id: int = reader.read_uint32()
            keys[res_id] = resref

    return keys


def _merge_key_data(
    bif: BIF,
    keys: dict[int, str],
) -> None:
    for i, resource in enumerate(bif):
        if i not in keys:
            continue
        resource.resref = ResRef(keys[i])


def write_bif(
    bif: BIF,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.BIF,
) -> None:
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
