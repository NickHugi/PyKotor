from __future__ import annotations

from typing import TYPE_CHECKING

from utility.path import PurePath

if TYPE_CHECKING:
    import os


def is_nss_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a NSS file extension."""
    return PurePath.pathify(filepath).suffix.lower() == ".nss"


def is_mod_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a MOD file extension."""
    return PurePath.pathify(filepath).suffix.lower() == ".mod"

def is_erf_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a ERF file extension."""
    return PurePath.pathify(filepath).suffix.lower() == ".erf"

def is_sav_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a SAV file extension."""
    return PurePath.pathify(filepath).suffix.lower() == ".sav"


def is_any_erf_type_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD, or SAV file extension."""
    from pykotor.resource.formats.erf.erf_data import ERFType
    return PurePath.pathify(filepath).suffix[1:].upper() in ERFType.__members__


def is_rim_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a RIM file extension."""
    return PurePath.pathify(filepath).suffix.lower() == ".rim"


def is_bif_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a BIF or BZF file extension."""
    return PurePath.pathify(filepath).suffix.lower() in {".bif", ".bzf"}

def is_bzf_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a BZF file extension (lzma-compressed bif archive usually used on iOS)."""
    return PurePath.pathify(filepath).suffix.lower() == ".bzf"

def is_capsule_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD, SAV, or RIM file extension."""
    return PurePath.pathify(filepath).suffix.lower() in {".erf", ".mod", ".rim", ".sav"}


def is_storage_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD, SAV, RIM, or BIF file extension."""
    return PurePath.pathify(filepath).suffix.lower() in {".erf", ".mod", ".sav", ".rim", ".bif"}
