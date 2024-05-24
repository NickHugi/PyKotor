from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices, QKeySequence

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.rim import read_rim
from pykotor.tools.misc import is_any_erf_type_file, is_rim_file
from utility.system.path import Path

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.erf import ERF
    from pykotor.resource.formats.rim import RIM
    from pykotor.resource.type import ResourceType

QtKey = QtCore.Qt.Key
QtMouse = QtCore.Qt.MouseButton

# Keyboard button mappings
MODIFIER_KEYS = {
    QtKey.Key_Control: "CTRL",
    QtKey.Key_Shift: "SHIFT",
    QtKey.Key_Alt: "ALT",
    QtKey.Key_Meta: "META",  # Often corresponds to the Windows or Command key
    QtKey.Key_AltGr: "ALTGR",  # Alt Graph key
    QtKey.Key_CapsLock: "CAPSLOCK",
    QtKey.Key_NumLock: "NUMLOCK",
    QtKey.Key_ScrollLock: "SCROLLLOCK",
}

# Create a reverse dictionary for easy lookup
STRING_TO_KEY = {v: k for k, v in MODIFIER_KEYS.items()}


def get_nums(string_input: str) -> list[int]:
    """Returns the numbers stored within a string.

    Numbers in a string are seperated by any non-numeric character.

    Args:
    ----
        string_input: String to search.

    Returns:
    -------
        List of numbers.
    """
    string: str = ""
    nums: list[int] = []
    for char in f"{string_input} ":
        if char.isdigit():
            string += char
        elif string.strip():
            nums.append(int(string))
            string = ""
    return nums


def openLink(link: str):
    url = QUrl(link)
    QDesktopServices.openUrl(url)


def clamp(value: float, minValue: float, maxValue: float) -> float:
    return max(minValue, min(value, maxValue))


def getStringFromKey(key: QtKey) -> str:
    """Returns the string for the given key code.

    This function will take into account edge cases (modifier keys like ctrl/alt) that QKeySequence.toString() fails to handle properly.

    Args:
    ----
        key: The key code.

    Returns:
    -------
        The matching string.
    """
    return MODIFIER_KEYS.get(key, QKeySequence(key).toString())


def getKeyFromString(string: str) -> int:
    """Returns the key code for the given string.

    This function handles special cases (modifier keys like ctrl/alt) that QKeySequence.fromString() might not handle properly.

    Args:
    ----
        string: The key string.

    Returns:
    -------
        The matching key code.
    """
    if string in STRING_TO_KEY:
        return STRING_TO_KEY[string]

    # Convert the string to QKeySequence and extract the key code
    key_sequence = QKeySequence.fromString(string)
    return key_sequence[0] if key_sequence.count() > 0 else 0


def getResourceFromFile(
    filepath: os.PathLike | str,
    resname: str,
    restype: ResourceType,
) -> bytes:
    """Gets a resource from a file by name and type.

    Args:
    ----
        filepath: The path to the file to read from.
        resname: The name of the resource to retrieve.
        restype: The type of the resource.

    Returns:
    -------
        data: The resource data as bytes or None if not found.

    Processing Logic:
    ----------------
        - Determines if the file is an ERF, RIM or generic file
        - Reads the file using the appropriate reader
        - Looks up the resource by name and type
        - Raises an error if the resource is not found
        - Returns the resource data or None.
    """
    data: bytes | None = None
    c_filepath = Path(filepath)

    if is_any_erf_type_file(c_filepath.name):
        erf: ERF = read_erf(filepath)
        data = erf.get(resname, restype)
    elif is_rim_file(c_filepath.name):
        rim: RIM = read_rim(filepath)
        data = rim.get(resname, restype)
    else:
        data = BinaryReader.load_file(filepath)

    if data is None:
        msg = "Could not find resource in RIM/ERF"
        raise ValueError(msg)

    return data

if __name__ == "__main__":  # quick test
    all_keys = [getattr(QtKey, key) for key in dir(QtKey) if key.startswith("Key_")]

    for key in all_keys:
        key_string = getStringFromKey(key)
        key_from_string = getKeyFromString(key_string)
        assert key == key_from_string, f"Key mismatch: {key} != {key_from_string}"

    print("All keys matched successfully!")
