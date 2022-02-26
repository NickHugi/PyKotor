from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tlk import TLK, TLKBinaryReader, TLKXMLReader, TLKBinaryWriter
from pykotor.resource.formats.tlk.io_tlk_json import TLKJSONReader, TLKJSONWriter
from pykotor.resource.formats.tlk.io_tlk_xml import TLKXMLWriter
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def detect_tlk(source: SOURCE_TYPES, offset: int = 0) -> ResourceType:
    """
    Returns what format the TLK data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
        source: Source of the TLK data.
        offset: Offset into the data.

    Raises:
        IOError: If an error occured reading the file.

    Returns:
        The format of the TLK data.
    """
    def check(first4):
        if first4 == "TLK ":
            return ResourceType.TLK
        elif "{" in first4:
            return ResourceType.TLK_JSON
        elif "<" in first4:
            return ResourceType.TLK_XML
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
        file_format = ResourceType.INVALID

    return file_format


def load_tlk(source: SOURCE_TYPES, offset: int = 0) -> TLK:
    """
    Returns an TLK instance from the source. The file format (TLK, TLK_XML or TLK_JSON) is automatically determined
    before parsing the data.

    Args:
        source: The source of the data.
        offset: The byte offset of the file inside the data.

    Raises:
        IOError: If an error occured reading the file.
        ValueError: If unable to determine the file format or the file data was corrupted.

    Returns:
        An TLK instance.
    """
    file_format = detect_tlk(source, offset)

    if file_format == ResourceType.TLK:
        return TLKBinaryReader(source, offset).load()
    elif file_format == ResourceType.TLK_XML:
        return TLKXMLReader(source, offset).load()
    elif file_format == ResourceType.TLK_JSON:
        return TLKJSONReader(source, offset).load()
    else:
        raise ValueError("Unable to determine the file format.")


def write_tlk(tlk: TLK, target: TARGET_TYPES, file_format: ResourceType = ResourceType.TLK) -> None:
    """
    Writes the TLK data to the target location with the specified format (TLK, TLK_XML or TLK_JSON).

    Args:
        tlk: The TLK file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
        IOError: If an error occured writing to the file.
        ValueError: If an unsupported file format was given.
    """
    if file_format == ResourceType.TLK:
        TLKBinaryWriter(tlk, target).write()
    elif file_format == ResourceType.TLK_XML:
        TLKXMLWriter(tlk, target).write()
    elif file_format == ResourceType.TLK_JSON:
        TLKJSONWriter(tlk, target).write()
    else:
        raise ValueError("Unsupported format specified; use TLK or TLK_XML.")
