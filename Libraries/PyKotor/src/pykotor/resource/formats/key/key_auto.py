from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.key.io_key import KEYBinaryReader, KEYBinaryWriter
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.key.key_data import KEY
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def detect_key(source: SOURCE_TYPES, offset: int = 0):
    ...


def read_key(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> KEY:  # sourcery skip: hoist-statement-from-if, reintroduce-else
    """Returns an KEY instance from the source.

    The file format (KEY or KEY_XML) is automatically determined before parsing the data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        A KEY instance.
    """
    file_format = detect_key(source, offset)

    if file_format is ResourceType.KEY:
        reader = KEYBinaryReader(source, offset, size or 0)
        return reader.load()

    # TODO(th3w1zard1):
    #if file_format is ResourceType.KEY_XML:
    #    return KEYXMLReader(source, offset, size or 0).load()

    msg = "Failed to determine the format of the KEY file."
    # if file_format is ResourceType.INVALID:
    raise ValueError(msg)
    reader = KEYBinaryReader(source)
    return reader.read()


def write_key(
    key: KEY,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.KEY,
):
    if file_format is not ResourceType.KEY:
        raise ValueError(f"Unsupported file format: {file_format!r}, expected ResourceType.KEY")
    writer = KEYBinaryWriter(key, target)
    writer.write()


def bytes_key(
    key: KEY,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.KEY,
) -> bytes:
    """Returns the KEY data in the specified format (KEY or KEY_XML) as a bytes object.

    This is a convenience method that wraps the write_key() and read_key() methods.

    Args:
    ----
        key: KEY: The target KEY.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The KEY data.
    """
    data = bytearray()
    write_key(key, target, file_format)
    return data