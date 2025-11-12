"""Handles resource data validation/salvage strategies.

This module provides recovery mechanisms for damaged or corrupted GFF resource files,
attempting to parse and reconstruct valid data structures.

References:
----------
    vendor/reone/src/libs/resource/gff.cpp (GFF parsing error handling)
    vendor/xoreos-tools/src/resource/gff.cpp (GFF recovery logic)
    Note: Salvage operations try to recover data when primary parsing fails
"""

from __future__ import annotations

import os
import pathlib
import sys

from typing import TYPE_CHECKING

from pykotor.extract.file import FileResource
from pykotor.resource.formats.ltr.ltr_auto import bytes_ltr, read_ltr
from pykotor.resource.generics.are import bytes_are, construct_are
from pykotor.resource.generics.dlg import bytes_dlg, construct_dlg
from pykotor.resource.generics.git import bytes_git, construct_git
from pykotor.resource.generics.ifo import bytes_ifo, construct_ifo
from pykotor.resource.generics.jrl import bytes_jrl, construct_jrl
from pykotor.resource.generics.pth import bytes_pth, construct_pth
from pykotor.resource.generics.utc import bytes_utc, construct_utc
from pykotor.resource.generics.utd import bytes_utd, construct_utd
from pykotor.resource.generics.ute import bytes_ute, construct_ute
from pykotor.resource.generics.uti import bytes_uti, construct_uti
from pykotor.resource.generics.utm import bytes_utm, construct_utm
from pykotor.resource.generics.utp import bytes_utp, construct_utp
from pykotor.resource.generics.uts import bytes_uts, construct_uts
from pykotor.resource.generics.utt import bytes_utt, construct_utt
from pykotor.resource.generics.utw import bytes_utw, construct_utw
from pykotor.tools.misc import is_any_erf_type_file

if getattr(sys, "frozen", False) is False:

    def add_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    absolute_file_path = pathlib.Path(__file__).resolve()
    pykotor_font_path = absolute_file_path.parents[4] / "Libraries" / "PyKotorFont" / "src" / "pykotor"
    if pykotor_font_path.is_dir():
        add_sys_path(pykotor_font_path.parent)
    pykotor_path = absolute_file_path.parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.is_dir():
        add_sys_path(pykotor_path.parent)
    utility_path = absolute_file_path.parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.is_dir():
        add_sys_path(utility_path.parent)

from pathlib import Path

from loggerplus import RobustLogger

from pykotor.extract.capsule import LazyCapsule
from pykotor.resource.formats.bwm.bwm_auto import bytes_bwm, read_bwm
from pykotor.resource.formats.erf.erf_auto import bytes_erf, read_erf
from pykotor.resource.formats.erf.erf_data import ERF
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.formats.lip.lip_auto import bytes_lip, read_lip
from pykotor.resource.formats.lyt.lyt_auto import bytes_lyt, read_lyt
from pykotor.resource.formats.mdl.mdl_auto import bytes_mdl, read_mdl
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, read_ncs
from pykotor.resource.formats.rim.rim_auto import bytes_rim, read_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.ssf.ssf_auto import bytes_ssf, read_ssf
from pykotor.resource.formats.tlk.tlk_auto import bytes_tlk, read_tlk
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc, read_tpc
from pykotor.resource.formats.twoda.twoda_auto import bytes_2da, read_2da
from pykotor.resource.formats.vis.vis_auto import bytes_vis, read_vis
from pykotor.resource.type import BASE_SOURCE_TYPES, ResourceType

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.formats.erf.erf_data import ERFResource
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.formats.rim.rim_data import RIMResource


def validate_capsule(
    capsule_obj: ERF | RIM | LazyCapsule | BASE_SOURCE_TYPES,
    *,
    strict: bool = False,
    game: Game | None = None,
) -> None | ERF | RIM:
    """Attempts to validate an ERF/RIM/MOD/SAV by looping through all resources inside of it.

    In base terms, for every resource iterated will read it into memory and if it throws OSError/ValueError will simply omit it from the new ERF/RIM written back to disk.

    Args:
    ----
        capsule_obj - The path to the ERF/RIM, or the object representation, to validate.
        strict: bool - Defaults to False. Will write back the loaded data in memory back to disk even for files that didn't exception.
        game: Game | None. Defaults to None. If this is set to a game, improve the quality of `strict` by constructing/deconstructing them further. Recommended.

    Returns:
    -------
        The validated ERF/RIM or None if could not be validated.

    Raises:
    ------
        TypeError - Invalid argument type passed to capsule_obj. This is the ONLY time this function will ever throw.
    """
    container: ERF | RIM | None = _load_as_erf_rim(capsule_obj)
    if container is None:  # Corrupted too far to even load into memory.
        return None
    new_container: ERF | RIM = ERF(container.erf_type) if isinstance(container, ERF) else RIM()
    try:
        for resource in container:
            RobustLogger().info(f"Validating '{resource.resref}.{resource.restype}'")
            if resource.restype is ResourceType.NCS:  # FIXME(th3w1zard1): This is a workaround for a current read_ncs bug.
                new_container.set_data(str(resource.resref), resource.restype, resource.data)
                continue
            try:
                new_data: bytes | bytearray | None = validate_resource(
                    resource,  # pyright: ignore[reportArgumentType]
                    strict=strict,
                    game=game,
                    should_raise=True,
                )

                # At this point the data should be valid since it hasn't thrown an exception.
                # The data may not match what was loaded, use strict arg to determine which one to use.
                new_data = new_data if strict else resource.data
                if new_data is None:  # unrecognized resource
                    RobustLogger().info(f"Not packaging unknown resource '{resource.resref}.{resource.restype}'")
                    continue

                # Set the data to the new container
                new_container.set_data(str(resource.resref), resource.restype, new_data)
            except (OSError, ValueError):  # noqa: PERF203
                RobustLogger().error(f" - Corrupted resource: '{resource.resref}.{resource.restype.extension}'")
    except (OSError, ValueError):
        RobustLogger().error(f"Corrupted ERF/RIM, could not salvage: '{capsule_obj}'")
    RobustLogger().info(f"Returning salvaged ERF/RIM container with {len(new_container)} total resources in it.")
    return new_container if new_container is not None else None


def validate_resource(  # noqa: C901, PLR0911, PLR0912
    resource: FileResource | ERFResource | RIMResource, *, strict: bool = False, game: Game | None = None, should_raise: bool = False
) -> bytes | bytearray | None:
    """Attempts to validate a kotor resource by loading into memory.

    Args:
    ----
        resource: FileResource - the resource to validate.
        strict: bool - Defaults to False. Whether to dismantle/construct gffs to further validate.
        game: Game | None. Defaults to None. If this is set to a game, improve the quality of `strict` by constructing/deconstructing them further. Recommended.
        should_raise: bool. Default to False. Whether to raise on corrupted resource.

    Returns:
    -------
        The validated ERF/RIM or None if could not be validated.

    Raises:
    ------
        TypeError - Invalid argument type passed to capsule_obj. This is the ONLY time this function will ever throw.
    """
    try:
        data: bytes | bytearray = resource.data() if isinstance(resource, FileResource) else resource.data  # pyright: ignore[reportArgumentType]
        restype: ResourceType = resource.restype() if isinstance(resource, FileResource) else resource.restype  # pyright: ignore[reportArgumentType]
        if restype.is_gff():
            loaded_gff: GFF = read_gff(data)
            if strict and game is not None:
                return validate_gff(loaded_gff, restype)
            return bytes_gff(read_gff(data))
        if restype in (ResourceType.WOK, ResourceType.PWK, ResourceType.DWK):
            return bytes_bwm(read_bwm(data))
        if restype is ResourceType.ERF:
            return bytes_erf(read_erf(data))
        if restype is ResourceType.RIM:
            return bytes_rim(read_rim(data))
        if restype is ResourceType.LIP:
            return bytes_lip(read_lip(data))
        if restype is ResourceType.LTR:
            return bytes_ltr(read_ltr(data))
        if restype is ResourceType.LYT:
            return bytes_lyt(read_lyt(data))
        if restype is ResourceType.MDL:
            return bytes_mdl(read_mdl(data))
        if restype is ResourceType.NCS:
            return bytes_ncs(read_ncs(data))
        if restype is ResourceType.SSF:
            return bytes_ssf(read_ssf(data))
        if restype is ResourceType.TLK:
            return bytes_tlk(read_tlk(data))
        if restype in (ResourceType.TPC, ResourceType.TGA):
            return bytes_tpc(read_tpc(data))
        if restype is ResourceType.TwoDA:
            return bytes_2da(read_2da(data))
        if restype is ResourceType.TXI:
            return data.decode(encoding="ascii", errors="ignore").encode(encoding="ascii")
        if restype is ResourceType.VIS:
            return bytes_vis(read_vis(data))
        # unknown resource.
        # return data
    except Exception as e:
        if should_raise:
            raise
        RobustLogger().error(f"Corrupted resource: {resource!r}", exc_info=not isinstance(e, (OSError, ValueError)))
    return None


def validate_gff(  # noqa: C901, PLR0911, PLR0912
    gff: GFF,
    restype: ResourceType,
) -> bytes:
    """Validates a GFF and returns it as bytes.

    Args:
    ----
        gff: GFF - The gff to validate.
        restype: ResourceType - the expected type of resource this is.
    """
    if restype is ResourceType.ARE:
        return bytes_are(construct_are(gff))
    if restype is ResourceType.DLG:
        return bytes_dlg(construct_dlg(gff))
    if restype is ResourceType.GIT:
        return bytes_git(construct_git(gff))
    if restype is ResourceType.IFO:
        return bytes_ifo(construct_ifo(gff))
    if restype is ResourceType.JRL:
        return bytes_jrl(construct_jrl(gff))
    if restype is ResourceType.PTH:
        return bytes_pth(construct_pth(gff))
    if restype is ResourceType.UTC:
        return bytes_utc(construct_utc(gff))
    if restype is ResourceType.UTD:
        return bytes_utd(construct_utd(gff))
    if restype is ResourceType.UTE:
        return bytes_ute(construct_ute(gff))
    if restype is ResourceType.UTI:
        return bytes_uti(construct_uti(gff))
    if restype is ResourceType.UTM:
        return bytes_utm(construct_utm(gff))
    if restype is ResourceType.UTS:
        return bytes_uts(construct_uts(gff))
    if restype is ResourceType.UTP:
        return bytes_utp(construct_utp(gff))
    if restype is ResourceType.UTT:
        return bytes_utt(construct_utt(gff))
    if restype is ResourceType.UTW:
        return bytes_utw(construct_utw(gff))

    RobustLogger().warning(f"Unrecognized GFF of type '{restype}' will not be reconstructed!")
    return bytes_gff(gff)


def _load_as_erf_rim(  # noqa: C901, PLR0912, PLR0911
    capsule_obj: LazyCapsule | ERF | RIM | BASE_SOURCE_TYPES,
) -> ERF | RIM | None:
    if isinstance(capsule_obj, LazyCapsule):
        try:
            return capsule_obj.as_cached()
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Corrupted {type(capsule_obj).__name__} object passed to `validate_capsule` could not be loaded into memory", exc_info=True)
            return None

    if isinstance(capsule_obj, (ERF, RIM)):
        return capsule_obj

    if isinstance(capsule_obj, (os.PathLike, str)):
        try:
            path = Path(capsule_obj)
            return LazyCapsule(path, create_nonexisting=True).as_cached()
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Invalid path passed to `validate_capsule`: '{capsule_obj}'", exc_info=True)
            return None

    if isinstance(capsule_obj, BASE_SOURCE_TYPES):
        if isinstance(capsule_obj, (bytes, bytearray, memoryview)):
            try:
                return read_erf(capsule_obj)
            except Exception:  # noqa: BLE001
                RobustLogger().debug("Doesn't look like an ERF.", exc_info=True)
                try:
                    return read_rim(capsule_obj)
                except Exception:  # noqa: BLE001
                    RobustLogger().error("the binary data passed to `validate_capsule` could not be loaded as an ERF/RIM.", exc_info=True)
                    return None
        elif is_any_erf_type_file(capsule_obj):
            try:
                return read_erf(capsule_obj)
            except Exception:  # noqa: BLE001
                RobustLogger().error(f"'{capsule_obj}' is not a valid filepath to an ERF", exc_info=True)
                return None
        else:
            try:
                return read_rim(capsule_obj)
            except Exception:  # noqa: BLE001
                RobustLogger().error(f"'{capsule_obj}' is not a valid filepath to a RIM", exc_info=True)
                return None

    raise TypeError(f"Invalid capsule argument: '{capsule_obj}' type '{type(capsule_obj)}', expected one of ERF | RIM | LazyCapsule | SOURCE_TYPES")
