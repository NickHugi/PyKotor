
def is_float(string: str):
    try:
        _ = float(string)
    except ValueError:
        return False
    else:
        return True
