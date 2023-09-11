from __future__ import annotations

import hashlib

from pykotor.tools.path import CaseAwarePath


def generate_filehash_sha1(filepath: str | CaseAwarePath) -> str:
    sha1_hash = hashlib.sha1()
    with open(filepath, "rb") as f:
        while (data := f.read(65536)):  # read in 64k chunks
            sha1_hash.update(data)
    return sha1_hash.hexdigest()


def is_int(string: str):
    """
    Can be cast to an_int without raising an error

    Args:
    ----
        string (str):

    """
    try:
        _ = int(string)
    except ValueError:
        return False
    else:
        return True


def is_float(string: str):
    """
    Can be cast to a float without raising an error.

    Args:
    ----
        string (str):

    """
    try:
        _ = float(string)
    except ValueError:
        return False
    else:
        return True


def is_nss_file(filename: str):
    return filename.lower().endswith(".nss")


def is_mod_file(filename: str):
    """Returns true if the given filename has a MOD file extension."""
    return filename.lower().endswith(".mod")


def is_erf_file(filename: str):
    """Returns true if the given filename has a ERF file extension."""
    return filename.lower().endswith(".erf")


def is_erf_or_mod_file(filename: str):
    """Returns true if the given filename has either an ERF or MOD file extension."""
    return filename.lower().endswith((".erf", ".mod"))


def is_rim_file(filename: str):
    """Returns true if the given filename has a RIM file extension."""
    return filename.lower().endswith(".rim")


def is_bif_file(filename: str):
    """Returns true if the given filename has a BIF file extension."""
    return filename.lower().endswith(".bif")


def is_capsule_file(filename: str):
    """Returns true if the given filename has either an ERF, MOD or RIM file extension."""
    return is_erf_or_mod_file(filename) or is_rim_file(filename)


def is_storage_file(filename: str):
    """Returns true if the given filename has either an BIF, ERF, MOD or RIM file extension."""
    return is_capsule_file(filename) or is_bif_file(filename)


def case_insensitive_replace(s: str, old: str, new: str) -> str:
    import re

    return re.sub(re.escape(old), new, s, flags=re.I)
