from pykotor.resource.formats.ltr.data import LTR
from pykotor.resource.formats.ltr.io_ltr import LTRBinaryReader, LTRBinaryWriter
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def load_ltr(source: SOURCE_TYPES, offset: int = 0) -> LTR:
    """
    Returns an LTR instance from the source.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An LTR instance.
    """
    try:
        return LTRBinaryReader(source, offset).load()
    except (IOError, ValueError):
        raise ValueError("Tried to load an unsupported or corrupted LTR file.")


def write_ltr(ltr: LTR, target: TARGET_TYPES, file_format: ResourceType = ResourceType.LTR) -> None:
    """
    Writes the LTR data to the target location with the specified format (LTR only).

    Args:
        ltr: The LTR file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.LTR:
        LTRBinaryWriter(ltr, target).write()
    else:
        raise ValueError("Unsupported format specified; use LTR.")
