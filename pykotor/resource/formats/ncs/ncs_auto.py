from pykotor.resource.formats.ncs import NCS, NCSBinaryReader, NCSBinaryWriter
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def read_ncs(
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = None
) -> NCS:
    """
    Returns an NCS instance from the source.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An NCS instance.
    """
    return NCSBinaryReader(source, offset, size).load()


def write_ncs(
        ncs: NCS,
        target: TARGET_TYPES,
        file_format: ResourceType = ResourceType.NCS
) -> None:
    """
    Writes the NCS data to the target location with the specified format (NCS only).

    Args:
        ncs: The NCS file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.NCS:
        NCSBinaryWriter(ncs, target).write()
    else:
        raise ValueError("Unsupported format specified; use NCS.")


def bytes_ncs(
        ncs: NCS,
        file_format: ResourceType = ResourceType.NCS
) -> bytes:
    """
    Returns the NCS data in the specified format (NCS only) as a bytes object.

    This is a convenience method that wraps the write_ncs() method.

    Args:
        ncs: The target NCS object.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.

    Returns:
        The NCS data.
    """
    data = bytearray()
    write_ncs(ncs, data, file_format)
    return data
