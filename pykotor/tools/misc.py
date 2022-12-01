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


def is_erf_file(filename: str):
    return filename.lower().endswith(".mod") or filename.lower().endswith(".erf")


def is_rim_file(filename: str):
    return filename.lower().endswith(".rim")


def is_bif_file(filename: str):
    return filename.lower().endswith(".bif")


def is_capsule_file(filename: str):
    """
    Returns true if the given filename has either an ERF, MOD or RIM file extension.
    """
    return is_erf_file(filename) or is_rim_file(filename)


def is_storage_file(filename: str):
    """
    Returns true if the given filename has either an BIF, ERF, MOD or RIM file extension.
    """
    return is_capsule_file(filename) or is_bif_file(filename)


