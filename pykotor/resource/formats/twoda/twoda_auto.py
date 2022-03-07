from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.twoda import TwoDA, TwoDABinaryReader, TwoDABinaryWriter, TwoDACSVWriter, TwoDACSVReader, \
    TwoDAJSONReader, TwoDAJSONWriter
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def detect_2da(
        source: SOURCE_TYPES,
        offset: int = 0
) -> ResourceType:
    """
    Returns what format the TwoDA data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the TwoDA data.
        offset: Offset into the data.

    Raises:
        IOError: If an error occured reading the file.

    Returns:
        The format of the TwoDA data.
    """

    def check(
            first4
    ):
        if first4 == "2DA ":
            return ResourceType.TwoDA
        elif "{" in first4:
            return ResourceType.TwoDA_JSON
        elif "," in first4:
            return ResourceType.TwoDA_CSV
        else:
            return ResourceType.INVALID

    if isinstance(source, str):
        with BinaryReader.from_file(source, offset) as reader:
            file_format = check(reader.read_string(4))
    elif isinstance(source, bytes) or isinstance(source, bytearray):
        file_format = check(source[:4].decode('ascii', 'ignore'))
    elif isinstance(source, BinaryReader):
        file_format = check(source.read_string(4))
        source.skip(-4)
    else:
        raise TypeError("Invalid type passed to 'source' argument.")

    return file_format


def read_2da(
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = None
) -> TwoDA:
    """
    Returns an TwoDA instance from the source. The file format (TwoDA, TwoDA_CSV, TwoDA_JSON) is automatically
    determined before parsing the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
        IOError: If an error occured reading the file.
        ValueError: If unable to determine the file format or the file data was corrupted.

    Returns:
        An TwoDA instance.
    """
    file_format = detect_2da(source, offset)

    if file_format == ResourceType.TwoDA:
        return TwoDABinaryReader(source, offset, size).load()
    elif file_format == ResourceType.TwoDA_CSV:
        return TwoDACSVReader(source, offset, size).load()
    elif file_format == ResourceType.TwoDA_JSON:
        return TwoDAJSONReader(source, offset, size).load()
    else:
        raise ValueError("Unable to determine the file format.")


def write_2da(
        twoda: TwoDA,
        target: TARGET_TYPES,
        file_format: ResourceType = ResourceType.TwoDA
) -> None:
    """
    Writes the TwoDA data to the target location with the specified format.

    Currently, the supported formats are: TwoDA, TwoDA_CSV and TwoDA_JSON.

    Args:
        twoda: The TwoDA file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        IOEroor: If an error occured writing to the file.
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.TwoDA:
        TwoDABinaryWriter(twoda, target).write()
    elif file_format == ResourceType.TwoDA_CSV:
        TwoDACSVWriter(twoda, target).write()
    elif file_format == ResourceType.TwoDA_JSON:
        TwoDAJSONWriter(twoda, target).write()
    else:
        raise ValueError("Unsupported format specified; use TwoDA, TwoDA_CSV or TwoDA_JSON.")


def bytes_2da(
        twoda: TwoDA,
        file_format: ResourceType = ResourceType.TwoDA
) -> bytes:
    """
    Returns the TwoDA data in the specified format (TwoDA, TwoDA_CSV or TwoDA_JSON) as a bytes object.

    This is a convience method that wraps the write_2da() method.

    Args:
        twoda: The target TwoDA object.
        file_format: The file format.

    Raises:
        ValueError: If an unsupported file format was given.

    Returns:
        The TwoDA data.
    """
    data = bytearray()
    write_2da(twoda, data, file_format)
    return data
