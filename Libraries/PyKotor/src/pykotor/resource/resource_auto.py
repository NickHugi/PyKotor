from __future__ import annotations

import contextlib
import os

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.bwm import bytes_bwm, read_bwm
from pykotor.resource.formats.erf import ERFType, bytes_erf, read_erf
from pykotor.resource.formats.gff import GFFContent, bytes_gff, read_gff
from pykotor.resource.formats.lip import bytes_lip, read_lip
from pykotor.resource.formats.ltr import bytes_ltr, read_ltr
from pykotor.resource.formats.lyt import bytes_lyt, read_lyt
from pykotor.resource.formats.mdl import bytes_mdl, read_mdl
from pykotor.resource.formats.ncs import bytes_ncs, read_ncs
from pykotor.resource.formats.rim import bytes_rim, read_rim
from pykotor.resource.formats.ssf import bytes_ssf, read_ssf
from pykotor.resource.formats.tlk import bytes_tlk, read_tlk
from pykotor.resource.formats.tpc import bytes_tpc, read_tpc
from pykotor.resource.formats.twoda import bytes_2da, read_2da
from pykotor.resource.formats.vis import bytes_vis, read_vis
from pykotor.resource.type import SOURCE_TYPES, ResourceType
from utility.error_handling import universal_simplify_exception
from utility.system.path import PurePath


def read_resource(source: SOURCE_TYPES, resource_type: ResourceType | None = None) -> bytes:  # noqa: C901, PLR0911, PLR0912
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
    """
    source_path: os.PathLike | str | None = None
    with contextlib.suppress(Exception):
        if isinstance(source, (os.PathLike, str)):
            source_path = source
            if not resource_type:
                _resname, resource_type = ResourceIdentifier.from_path(source)

    if not resource_type:
        return read_unknown_resource(source)

    try:  # try from extension/resource_type arg
        ext_obj = PurePath(resource_type.extension)
        resource_ext = ext_obj.stem.lower() if "." in ext_obj.name else ext_obj.suffix.lower()[1:]
        if resource_type.category == "Talk Tables":
            return bytes_tlk(read_tlk(source))
        if resource_type in {ResourceType.TGA, ResourceType.TPC}:
            return bytes_tpc(read_tpc(source))
        if resource_ext == "ssf":
            return bytes_ssf(read_ssf(source))
        if resource_ext == "2da":
            return bytes_2da(read_2da(source))
        if resource_ext == "lip":
            return bytes_lip(read_lip(source))
        if resource_ext.upper() in ERFType.__members__:
            return bytes_erf(read_erf(source))
        if resource_ext == "rim":
            return bytes_rim(read_rim(source))
        if resource_type.extension.upper() in GFFContent.__members__:
            return bytes_gff(read_gff(source))
        if resource_ext == "ncs":
            return bytes_ncs(read_ncs(source))
        if resource_ext == "mdl":
            return bytes_mdl(read_mdl(source))
        if resource_ext == "vis":
            return bytes_vis(read_vis(source))
        if resource_ext == "lyt":
            return bytes_lyt(read_lyt(source))
        if resource_ext == "ltr":
            return bytes_ltr(read_ltr(source))
        if resource_type.category == "Walkmeshes":
            return bytes_bwm(read_bwm(source))
    except Exception as e:  # noqa: BLE001
        new_err = ValueError(f"Could not load resource '{source_path}' as resource type '{resource_type}")
        print(universal_simplify_exception(new_err))
        raise new_err from e

    msg = f"Resource type {resource_type!r} is not supported by this library."
    raise ValueError(msg)


def read_unknown_resource(source: SOURCE_TYPES) -> bytes:  # noqa: PLR0911
    with contextlib.suppress(OSError, ValueError):
        return bytes_tlk(read_tlk(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_ssf(read_ssf(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_2da(read_2da(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_lip(read_lip(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_tpc(read_tpc(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_erf(read_erf(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_rim(read_rim(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_ncs(read_ncs(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_gff(read_gff(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_mdl(read_mdl(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_vis(read_vis(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_lyt(read_lyt(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_ltr(read_ltr(source))
    with contextlib.suppress(OSError, ValueError):
        return bytes_bwm(read_bwm(source))
    msg = "Source resource data not recognized as any kotor file formats."
    raise ValueError(msg)
