from __future__ import annotations

import contextlib
import os

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import GFFContent, bytes_gff, detect_gff, read_gff
from pykotor.resource.formats.lip import bytes_lip, detect_lip, read_lip
from pykotor.resource.formats.mdl import detect_mdl, read_mdl, write_mdl
from pykotor.resource.formats.ssf import bytes_ssf, detect_ssf, read_ssf
from pykotor.resource.formats.tlk import bytes_tlk, detect_tlk, read_tlk
from pykotor.resource.formats.tpc import bytes_tpc, detect_tpc, read_tpc
from pykotor.resource.formats.twoda import bytes_2da, detect_2da, read_2da
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
        if isinstance(source, (os.PathLike, str)):
            source_path = source if isinstance(source, PurePath) else PurePath(source)
            _filestem, ext = source_path.split_filename(dots=2)
            with contextlib.suppress(Exception):
                resource_type = ResourceType.from_extension(ext)
        else:
            resource_type = detect_resource_bytes(source)
    try:
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
            mdl = read_mdl(source)
            assert mdl is not None
            write_mdl(mdl, mdl_data)
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


def detect_resource_bytes(source: SOURCE_TYPES):
    """Detect resource type of source file bytes.

    This is a convenience method for determining the resource's type when the source is unknown.
    Ideally you shouldn't rely on this function, it only performs basic file header checks.

    Args:
    ----
        source: (SOURCE_TYPES): Source file bytes

    Returns:
    -------
        result (ResourceType): Detected resource type

    Processing Logic:
    ----------------
        - Try detecting file as TLK
        - Try detecting file as GFF if TLK detection failed
        - Try detecting file as SSF if GFF detection failed
        - Try detecting file as 2DA if SSF detection failed
        - Try detecting file as MDL if 2DA detection failed
        - Try detecting file as LIP if MDL detection failed
        - Try detecting file as TPC if LIP detection failed
        - Return ResourceType result
    """
    result = ResourceType.INVALID
    with contextlib.suppress(OSError):
        result = detect_tlk(source)
    with contextlib.suppress(OSError):
        result = detect_gff(source)
    with contextlib.suppress(OSError):
        result = detect_ssf(source)
    with contextlib.suppress(OSError):
        result = detect_2da(source)
    with contextlib.suppress(OSError):
        result = detect_mdl(source)
    with contextlib.suppress(OSError):
        result = detect_lip(source)
    with contextlib.suppress(OSError):
        result = detect_tpc(source)

    return result  # noqa: RET504
