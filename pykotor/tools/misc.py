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
