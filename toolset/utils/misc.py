from typing import List, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices, QKeySequence

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.type import ResourceType


QtKey = QtCore.Qt.Key
QtMouse = QtCore.Qt.MouseButton


def get_nums(string_input: str) -> List[int]:
    """
    Returns the numbers stored within a string. Numbers in a string are seperated by any non-numeric character.

    Args:
        string_input: String to search.

    Returns:
        List of numbers.
    """
    string = ""
    nums = []
    for char in string_input + " ":
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
    """
    Returns the string for the given key code. This function will take into account edge cases that
    QKeySequence.toString() fails to handle properly.

    Args:
        key: The key code.

    Returns:
        The matching string.
    """
    if key == QtCore.Qt.Key.Key_Control:
        return "CTRL"
    elif key == QtCore.Qt.Key.Key_Alt:
        return "ALT"
    elif key == QtCore.Qt.Key.Key_Shift:
        return "SHIFT"
    else:
        return QKeySequence(key).toString()


def getResourceFromFile(filepath: str, resname: str, restype: ResourceType) -> Optional[bytes]:
    data = None

    if filepath.endswith(".erf") or filepath.endswith(".mod"):
        erf = read_erf(filepath)
        data = erf.get(resname, restype)
    elif filepath.endswith(".rim"):
        rim = read_rim(filepath)
        data = rim.get(resname, restype)
    else:
        data = BinaryReader.load_file(filepath)

    if data is None:
        raise ValueError("Could not find resource in RIM/ERF/MOD.")

    return data
