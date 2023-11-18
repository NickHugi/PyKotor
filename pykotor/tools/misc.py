from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.utility.path import PurePath

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


def is_erf_or_mod_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF or MOD file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() in [".erf", ".mod"]


def is_rim_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a RIM file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".rim"


def is_bif_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has a BIF file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() == ".bif"


def is_capsule_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD or RIM file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() in [".erf", ".mod", ".rim"]


def is_storage_file(filepath: os.PathLike | str) -> bool:
    """Returns true if the given filename has either an ERF, MOD, RIM, or BIF file extension."""
    path = filepath if isinstance(filepath, PurePath) else PurePath(filepath)
    return path.suffix.lower() in [".erf", ".mod", ".rim", ".bif"]
