from __future__ import annotations

from typing import TYPE_CHECKING

from utility.path import PurePath

if TYPE_CHECKING:
    import os


def is_nss_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a NSS file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".nss"


def is_mod_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a MOD file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".mod"


def is_erf_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a ERF file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".erf"

def is_sav_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a SAV file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".sav"


def is_any_erf_type_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD, or SAV file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() in [".erf", ".mod", ".sav"]


def is_rim_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a RIM file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".rim"


def is_bif_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a BIF file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".bif"


def is_capsule_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD, SAV, or RIM file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() in [".erf", ".mod", ".rim", ".sav"]


def is_storage_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD, SAV, RIM, or BIF file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() in [".erf", ".mod", ".sav", ".rim", ".bif"]
