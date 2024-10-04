from __future__ import annotations


def _i(
    ascii_block: list[list[str]],
    int_list: list[tuple[int, ...]],
    num_vals: int,
    initial_float: bool = True,
):
    """Parse a float and integers into a num_vals tuple into int_list."""
    l_float = float
    l_int = int
    for line in ascii_block:
        vals = []
        for idx in range(num_vals):
            if num_vals < 2 or idx > 0 or not initial_float:
                try:
                    vals.append(l_int(line[idx]))
                except ValueError:
                    vals.append(l_int(l_float(line[idx])))
            else:
                vals.append(l_float(line[idx]))
        if len(vals) > 1:
            int_list.append(tuple(vals))
        else:
            int_list.append(vals[0])


def _f(
    ascii_block: list[list[str]],
    float_list: list[tuple[float, ...]],
    num_vals: int,
):
    """Parse floats into a num_vals tuple into float_list."""
    l_float = float
    for line in ascii_block:
        vals = [l_float(val) for val in line[:num_vals]]
        float_list.append(tuple(vals) if len(vals) > 1 else vals[0])


def f1(ascii_block: list[list[str]], float_list: list[tuple[float, ...]]):
    """Parse a series on floats into a list."""
    _f(ascii_block, float_list, 1)


def f2(ascii_block: list[list[str]], float_list: list[tuple[float, ...]]):
    """Parse a series on float tuples into a list."""
    _f(ascii_block, float_list, 2)


def f3(ascii_block: list[list[str]], float_list: list[tuple[float, ...]]):
    """Parse a series on float 3-tuples into a list."""
    _f(ascii_block, float_list, 3)


def f4(ascii_block: list[list[str]], float_list: list[tuple[float, ...]]):
    """Parse a series on float 4-tuples into a list."""
    _f(ascii_block, float_list, 4)


def f5(ascii_block: list[list[str]], float_list: list[tuple[float, ...]]):
    """Parse a series on float 5-tuples into a list."""
    _f(ascii_block, float_list, 5)


def i2(
    ascii_block: list[list[str]],
    int_list: list[tuple[int, ...]],
):
    l_int = int
    int_list.extend((l_int(line[0]), l_int(line[1])) for line in ascii_block)


def i3(
    ascii_block: list[list[str]],
    int_list: list[tuple[int, ...]],
    initial_float: bool = True,
):
    _i(ascii_block, int_list, 3, initial_float)


def txt(
    ascii_block: list[list[str]],
    txt_block: str,
):
    # txtBlock = ['\n'+' '.join(l) for l in aciiBlock]
    for line in ascii_block:
        txt_block = txt_block + "\n" + " ".join(line)
