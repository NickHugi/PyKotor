from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.mdl import MDL, MDLBinaryReader, MDLBinaryWriter, MDLAsciiReader, MDLAsciiWriter
from pykotor.resource.type import FileFormat, SOURCE_TYPES, TARGET_TYPES


def detect_mdl(source: SOURCE_TYPES, offset: int = 0) -> FileFormat:
    """
    Returns what format the MDL data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the MDL data.
        offset: Offset into the source data.

    Returns:
        The format of the MDL data.
    """
    try:
        if isinstance(source, str):
            with BinaryReader.from_file(source, offset) as reader:
                first4 = reader.read_bytes(4)
                file_format = FileFormat.BINARY if first4 == b'\x00\x00\x00\x00' else FileFormat.ASCII
        elif isinstance(source, bytes) or isinstance(source, bytearray):
            file_format = FileFormat.BINARY if source[:4] == b'\x00\x00\x00\x00' else FileFormat.ASCII
        elif isinstance(source, BinaryReader):
            first4 = source.read_bytes(4)
            file_format = FileFormat.BINARY if first4 == b'\x00\x00\x00\x00' else FileFormat.ASCII
            source.skip(-4)
        else:
            file_format = FileFormat.INVALID
    except IOError:
        file_format = FileFormat.INVALID

    return file_format


def load_mdl(source: SOURCE_TYPES, offset: int = 0, source_ext: SOURCE_TYPES = None, offset_ext: int = 0) -> MDL:
    """
    Returns an MDL instance from the source. The file format (binary or ascii) is automatically determined before
    parsing the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        source_ext: Source of the MDX data, if available.
        offset_ext: Offset into the source_ext data.

    Raises:
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
        An MDL instance.
    """
    file_format = detect_mdl(source, offset)

    try:
        if file_format == FileFormat.BINARY:
            return MDLBinaryReader(source, offset).load()
        elif file_format == FileFormat.ASCII:
            return MDLAsciiReader(source).load()
        else:
            raise ValueError
    except (IOError, ValueError):
        raise ValueError("Tried to load an unsupported or corrupted MDL file.")


def write_mdl(mdl: MDL, target: TARGET_TYPES, file_format: FileFormat = FileFormat.BINARY,
              target_ext: TARGET_TYPES = None) -> None:
    """
    Writes the MDL data to the target location with the specified format (binary or ascii).

    Args:
        mdl: The MDL file being written.
        target: The location to write the data to.
        file_format: The file format.
        target_ext: The location to write the MDX data to (if binary).

    Raises:
        ValueError: If an unsupported FileFormat is passed.
    """
    if file_format == FileFormat.BINARY:
        MDLBinaryWriter(mdl, target).write()
    elif file_format == FileFormat.ASCII:
        MDLAsciiWriter(mdl, target).write()
    else:
        raise ValueError("Unsupported format specified; use BINARY or ASCII.")
