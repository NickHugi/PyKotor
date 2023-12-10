from __future__ import annotations

import contextlib
import os

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import bytes_gff, detect_gff, read_gff, GFFContent
from pykotor.resource.formats.lip import bytes_lip, detect_lip, read_lip
from pykotor.resource.formats.mdl import detect_mdl, read_mdl, write_mdl
from pykotor.resource.formats.ssf import bytes_ssf, detect_ssf, read_ssf
from pykotor.resource.formats.tlk import bytes_tlk, detect_tlk, read_tlk
from pykotor.resource.formats.tpc import bytes_tpc, detect_tpc, read_tpc
from pykotor.resource.formats.twoda import bytes_2da, detect_2da, read_2da
from pykotor.resource.type import SOURCE_TYPES, ResourceType

from utility.error_handling import universal_simplify_exception
from utility.path import Path, PurePath
    


def load_resource_file(source: SOURCE_TYPES, resource_type: ResourceType | None = None) -> bytes:
    is_path = False
    source_path = None
    if not resource_type:
        if isinstance(source, (os.PathLike, str)):
            source_path = source if isinstance(source, Path) else Path(source)
            _filestem, ext = source_path.split_filename(dots=2)
            resource_type = ResourceType.from_extension(ext)
            is_path = True
        else:
            resource_type = ResourceType.INVALID
            with contextlib.suppress(OSError):
                resource_type = detect_tlk(source)
            with contextlib.suppress(OSError):
                resource_type = detect_gff(source)
            with contextlib.suppress(OSError):
                resource_type = detect_ssf(source)
            with contextlib.suppress(OSError):
                resource_type = detect_2da(source)
            with contextlib.suppress(OSError):
                resource_type = detect_mdl(source)
            with contextlib.suppress(OSError):
                resource_type = detect_lip(source)
            with contextlib.suppress(OSError):
                resource_type = detect_tpc(source)

    resource_ext, _ = PurePath(resource_type.extension).split_filename()
    try:
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
    except (ValueError, OSError) as e:
        print(f"Could not load resource '{source_path!s}' as resource type '{resource_type!s}'")
        print(universal_simplify_exception(e))
        if is_path:  # try again as bytes
            file_data = BinaryReader.from_auto(source).read_all()
            return load_resource_file(file_data)

    return BinaryReader.from_auto(source).read_all()