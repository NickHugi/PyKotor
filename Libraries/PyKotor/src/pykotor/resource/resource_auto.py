from __future__ import annotations

import contextlib
import os
from typing import TYPE_CHECKING

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.erf import ERFType, read_erf
from pykotor.resource.formats.gff import GFFContent, read_gff
from pykotor.resource.formats.lip import read_lip
from pykotor.resource.formats.ltr import read_ltr
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.formats.mdl import read_mdl
from pykotor.resource.formats.ncs import read_ncs
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.formats.ssf import read_ssf
from pykotor.resource.formats.tlk import read_tlk
from pykotor.resource.formats.tpc import read_tpc
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.formats.vis import read_vis
from pykotor.resource.type import SOURCE_TYPES, ResourceType
from utility.error_handling import universal_simplify_exception
from utility.path import PurePath

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.formats.erf.erf_data import ERF
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.formats.lip.lip_data import LIP
    from pykotor.resource.formats.ltr.ltr_data import LTR
    from pykotor.resource.formats.lyt.lyt_data import LYT
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.ncs.ncs_data import NCS
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.formats.ssf.ssf_data import SSF
    from pykotor.resource.formats.tlk.tlk_data import TLK
    from pykotor.resource.formats.tpc.tpc_data import TPC
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.formats.vis.vis_data import VIS


def read_resource(source: SOURCE_TYPES, resource_type: ResourceType | None = None) -> TLK | SSF | TwoDA | LIP | TPC | ERF | RIM | NCS | GFF | MDL | VIS | LYT | LTR | BWM:
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
            return read_tlk(source)
        if resource_type in {ResourceType.TGA, ResourceType.TPC}:
            return read_tpc(source)
        if resource_ext == "ssf":
            return read_ssf(source)
        if resource_ext == "2da":
            return read_2da(source)
        if resource_ext == "lip":
            return read_lip(source)
        if resource_ext.upper() in ERFType.__members__:
            return read_erf(source)
        if resource_ext == "rim":
            return read_rim(source)
        if resource_type.extension.upper() in GFFContent:
            return read_gff(source)
        if resource_ext == "ncs":
            return read_ncs(source)
        if resource_ext == "mdl":
            return read_mdl(source)
        if resource_ext == "vis":
            return read_vis(source)
        if resource_ext == "lyt":
            return read_lyt(source)
        if resource_ext == "ltr":
            return read_ltr(source)
        if resource_type.category == "Walkmeshes":
            return read_bwm(source)
    except Exception as e:
        new_err = ValueError(f"Could not load resource '{source_path}' as resource type '{resource_type}")
        print(universal_simplify_exception(new_err))
        raise new_err from e

    msg = f"Resource type {resource_type!r} is not supported by this library."
    raise ValueError(msg)


def read_unknown_resource(source: SOURCE_TYPES) -> TLK | SSF | TwoDA | LIP | TPC | ERF | RIM | NCS | GFF | MDL | VIS | LYT | LTR | BWM:
    with contextlib.suppress(OSError, ValueError):
        return read_tlk(source)
    with contextlib.suppress(OSError, ValueError):
        return read_ssf(source)
    with contextlib.suppress(OSError, ValueError):
        return read_2da(source)
    with contextlib.suppress(OSError, ValueError):
        return read_lip(source)
    with contextlib.suppress(OSError, ValueError):
        return read_tpc(source)
    with contextlib.suppress(OSError, ValueError):
        return read_erf(source)
    with contextlib.suppress(OSError, ValueError):
        return read_rim(source)
    with contextlib.suppress(OSError, ValueError):
        return read_ncs(source)
    with contextlib.suppress(OSError, ValueError):
        return read_gff(source)
    with contextlib.suppress(OSError, ValueError):
        return read_mdl(source)
    with contextlib.suppress(OSError, ValueError):
        return read_vis(source)
    with contextlib.suppress(OSError, ValueError):
        return read_lyt(source)
    with contextlib.suppress(OSError, ValueError):
        return read_ltr(source)
    with contextlib.suppress(OSError, ValueError):
        return read_bwm(source)
    msg = "Source resource data not recognized as any kotor file formats."
    raise ValueError(msg)
