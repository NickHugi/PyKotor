import hashlib

from pykotor.tools.path import CaseAwarePath


def generate_filehash_sha1(filepath: str | CaseAwarePath) -> str:
    sha1_hash = hashlib.sha1()
    with open(filepath, "rb") as f:
        while (data := f.read(65536)):  # read in 64k chunks
            sha1_hash.update(data)
    return sha1_hash.hexdigest()


def is_int(string: str, strict=True):
    try:
        return int(string) and True
    except ValueError:
        if not strict or not isinstance(string, str):
            return False
        # If conversion to int fails in strict mode, check for valid float forms 
        # where numbers after the decimal point are 0.
        parts = string.split(".")
        if len(parts) == 2 and all(ch.isdigit() for ch in parts[1]) and int(parts[1]) == 0:
            try:
                _ = float(string)
                return True
            except ValueError:
                return False


def is_float(string: str, strict=True):
    try:
        _ = float(string)
    except ValueError:
        return False
    else:
        return "." in string if strict else True


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
