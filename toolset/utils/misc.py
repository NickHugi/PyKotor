from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices, QKeySequence

from pykotor.common.stream import BinaryReader
from pykotor.helpers.path import Path
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.rim import read_rim
from pykotor.tools.misc import is_erf_or_mod_file, is_rim_file

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.erf import ERF
    from pykotor.resource.formats.rim import RIM
    from pykotor.resource.type import ResourceType

QtKey = QtCore.Qt.Key
QtMouse = QtCore.Qt.MouseButton


def get_nums(string_input: str) -> list[int]:
    """Returns the numbers stored within a string. Numbers in a string are seperated by any non-numeric character.

    Args:
    ----
        string_input: String to search.

    Returns:
    -------
        List of numbers.
    """
    string = ""
    nums = []
    for char in f"{string_input} ":
        if char.isdigit():
            string += char
        elif string != "":
            nums.append(int(string))
            string = ""
    return nums


def openLink(link: str) -> None:
    url = QUrl(link)
    QDesktopServices.openUrl(url)


def clamp(value: float, minValue: float, maxValue: float) -> float:
    return max(minValue, min(value, maxValue))


def getStringFromKey(key: int) -> str:
    """Returns the string for the given key code. This function will take into account edge cases that
    QKeySequence.toString() fails to handle properly.

    Args:
    ----
        key: The key code.

    Returns:
    -------
        The matching string.
    """
    if key == QtCore.Qt.Key.Key_Control:
        return "CTRL"
    if key == QtCore.Qt.Key.Key_Alt:
        return "ALT"
    if key == QtCore.Qt.Key.Key_Shift:
        return "SHIFT"
    return QKeySequence(key).toString()


def getResourceFromFile(filepath: os.PathLike | str, resname: str, restype: ResourceType) -> Optional[bytes]:
    data = None
    c_filepath = Path(filepath)

    if is_erf_or_mod_file(c_filepath.name):
        erf: ERF = read_erf(filepath)
        data: bytes | None = erf.get(resname, restype)
    elif is_rim_file(c_filepath.name):
        rim: RIM = read_rim(filepath)
        data: bytes | None = rim.get(resname, restype)
    else:
        data = BinaryReader.load_file(filepath)

    if data is None:
        msg = "Could not find resource in RIM/ERF/MOD."
        raise ValueError(msg)

    return data
