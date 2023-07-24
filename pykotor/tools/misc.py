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

def is_mod_file(filename: str):
    """
    Returns true if the given filename has a MOD extension.
    """
    return filename.lower().endswith(".mod")

def is_erf_file(filename: str):
    """
    The function `is_erf_file` checks if a given filename ends with either ".mod" or ".erf"
    (case-insensitive).

    :param filename: A string representing the name of a file
    :type filename: str
    :return: a boolean value indicating whether the given filename has a ".mod" or ".erf" extension.
    """
    return filename.lower().endswith(".mod") or filename.lower().endswith(".erf")


def is_rim_file(filename: str):
    """
    Returns true if the given filename has a RIM extension.
    """
    return filename.lower().endswith(".rim")


def is_bif_file(filename: str):
    """
    Returns true if the given filename has a BIF extension.
    """
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
