from __future__ import annotations

import contextlib
import os

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import GFFContent, bytes_gff, read_gff
from pykotor.resource.formats.lip import bytes_lip, read_lip
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.ssf import bytes_ssf, read_ssf
from pykotor.resource.formats.tlk import bytes_tlk, read_tlk
from pykotor.resource.formats.tpc import bytes_tpc, read_tpc
from pykotor.resource.formats.twoda import bytes_2da, read_2da
from pykotor.resource.type import SOURCE_TYPES, ResourceType
from utility.error_handling import universal_simplify_exception
from utility.path import PurePath


def read_resource(source: SOURCE_TYPES, resource_type: ResourceType | None = None) -> bytes:
    """Reads a resource from a source and returns it as bytes.

    This is a convenience method to make getting the resource's data easier.
    Can handle various formats (XML/CSV/JSON etc).

    Args:
    ----
        source: SOURCE_TYPES: The source of the resource
        resource_type: ResourceType | None: The type of the resource

    Returns:
    -------
        bytes: The resource data as bytes

    Processing Logic:
    ----------------
        - Determines the resource type from the source or extension
        - Reads the resource differently based on type:
            - Talk Tables, GFF, TGA/TPC: Use specialized reader functions
            - SSF, 2DA, MDL, LIP: Use specialized reader functions
            - Default: Read entire source as bytes
        - Handles errors and retries with bytes if path failed
    """
    source_path = None
    if not resource_type:
        if not isinstance(source, (os.PathLike, str)):
            return get_resource_from_bytes(source)

        source_path = source if isinstance(source, PurePath) else PurePath(source)
        _filestem, ext = source_path.split_filename(dots=2)
        try:
            resource_type = ResourceType.from_extension(ext)
            resource_ext, _ = PurePath(resource_type.extension).split_filename()
            if resource_type.category == "Talk Tables":
                return bytes_tlk(read_tlk(source))
            if resource_type.extension.upper() in GFFContent:
                return bytes_gff(read_gff(source))
            if resource_type in [ResourceType.TGA, ResourceType.TPC]:
                return bytes_tpc(read_tpc(source))
            if resource_ext == "ssf":
                return bytes_ssf(read_ssf(source))
            if resource_ext == "2da":
                return bytes_2da(read_2da(source))
            if resource_ext == "mdl":
                mdl_data = bytearray()
                write_mdl(read_mdl(source), mdl_data)
                return bytes(mdl_data)
            if resource_ext == "lip":
                return bytes_lip(read_lip(source))
        except Exception as e:
            print(f"Could not load resource '{source_path!s}' as resource type '{resource_type!s}'")
            print(universal_simplify_exception(e))
            if isinstance(source, (os.PathLike, str)):  # try again as bytes
                file_data = BinaryReader.from_file(source).read_all()
                return read_resource(file_data)
    return BinaryReader.from_auto(source).read_all()


def get_resource_from_bytes(source: SOURCE_TYPES) -> bytes:
    result: bytes | None = None
    with contextlib.suppress(OSError):
        result = bytes_tlk(read_tlk(source))
    with contextlib.suppress(OSError):
        result = bytes_ssf(read_ssf(source))
    with contextlib.suppress(OSError):
        result = bytes_2da(read_2da(source))
    with contextlib.suppress(OSError):
        mdl_data = bytearray()
        write_mdl(read_mdl(source), mdl_data)
        return bytes(mdl_data)
    with contextlib.suppress(OSError):
        result = bytes_lip(read_lip(source))
    with contextlib.suppress(OSError):
        result = bytes_tpc(read_tpc(source))
    with contextlib.suppress(OSError):
        result = bytes_gff(read_gff(source))
    if not result:
        msg = "Source resource data not recognized as any kotor file formats."
        raise ValueError(msg)

    return result  # noqa: RET504
