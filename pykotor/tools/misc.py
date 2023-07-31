def is_int(string: str):
    try:
        _ = int(string)
    except ValueError:
        return False
    else:
        return True


def is_float(string: str):
    try:
        _ = float(string)
    except ValueError:
        return False
    else:
        return True

def is_nss_file(filename: str):
    return filename.lower().endswith(".nss")

def is_mod_file(filename: str):
    """
    Returns true if the given filename has a MOD file extension.
    """
    return filename.lower().endswith(".mod")

def is_erf_file(filename: str):
    """
    Returns true if the given filename has a ERF file extension.
    """
    return filename.lower().endswith(".erf")

def is_erf_or_mod_file(filename: str):
    """
    Returns true if the given filename has either an ERF or MOD file extension.
    """
    filename = filename.lower()
    return filename.endswith(".erf") or filename.endswith(".mod")

def is_rim_file(filename: str):
    """
    Returns true if the given filename has a RIM file extension.
    """
    return filename.lower().endswith(".rim")

def is_bif_file(filename: str):
    """
    Returns true if the given filename has a BIF file extension.
    """
    return filename.lower().endswith(".bif")

def is_capsule_file(filename: str):
    """
    Returns true if the given filename has either an ERF, MOD or RIM file extension.
    """
    return is_erf_or_mod_file(filename) or is_rim_file(filename)


def is_storage_file(filename: str):
    """
    Returns true if the given filename has either an BIF, ERF, MOD or RIM file extension.
    """
    return is_capsule_file(filename) or is_bif_file(filename)


