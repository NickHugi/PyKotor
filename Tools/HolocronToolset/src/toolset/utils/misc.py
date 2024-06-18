from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from qtpy import API_NAME, QtCore
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
T = TypeVar("T")

MODIFIER_KEY_NAMES = {
    QtKey.Key_Control: "CTRL",
    QtKey.Key_Shift: "SHIFT",
    QtKey.Key_Alt: "ALT",
    QtKey.Key_Meta: "META",  # Often corresponds to the Windows or Command key
    QtKey.Key_AltGr: "ALTGR",  # Alt Graph key
    QtKey.Key_CapsLock: "CAPSLOCK",
    QtKey.Key_NumLock: "NUMLOCK",
    QtKey.Key_ScrollLock: "SCROLLLOCK",
}
MODIFIER_KEYNAME_TO_KEY: dict[str, QtKey] = {v: k for k, v in MODIFIER_KEY_NAMES.items()}



MOUSE_BUTTON_NAMES: dict[QtMouse, str] = {
    QtMouse.LeftButton: "LeftButton",
    QtMouse.RightButton: "RightButton",
    QtMouse.MiddleButton: "MiddleButton",
    QtMouse.BackButton: "BackButton",
    QtMouse.ForwardButton: "ForwardButton",
    QtMouse.TaskButton: "TaskButton",
    QtMouse.ExtraButton1: "ExtraButton1",
    QtMouse.ExtraButton2: "ExtraButton2",
    QtMouse.ExtraButton3: "ExtraButton3",
    QtMouse.ExtraButton4: "ExtraButton4",
    QtMouse.ExtraButton5: "ExtraButton5",
    QtMouse.ExtraButton6: "ExtraButton6",
    QtMouse.ExtraButton7: "ExtraButton7",
    QtMouse.ExtraButton8: "ExtraButton8",
    QtMouse.ExtraButton9: "ExtraButton9",
    QtMouse.ExtraButton10: "ExtraButton10",
    QtMouse.ExtraButton11: "ExtraButton11",
    QtMouse.ExtraButton12: "ExtraButton12",
    QtMouse.ExtraButton13: "ExtraButton13",
    QtMouse.ExtraButton14: "ExtraButton14",
    QtMouse.ExtraButton15: "ExtraButton15",
    QtMouse.ExtraButton16: "ExtraButton16",
    QtMouse.ExtraButton17: "ExtraButton17",
    QtMouse.ExtraButton18: "ExtraButton18",
    QtMouse.ExtraButton19: "ExtraButton19",
    QtMouse.ExtraButton20: "ExtraButton20",
    QtMouse.ExtraButton21: "ExtraButton21",
    QtMouse.ExtraButton22: "ExtraButton22",
    QtMouse.ExtraButton23: "ExtraButton23",
    QtMouse.ExtraButton24: "ExtraButton24",
    #not actual buttons:
    #QtMouse.NoButton: "NoButton"
    #QtMouse.AllButtons: "AllButtons"
}
STRING_TO_MOUSE: dict[str, QtMouse] = {k: v for k, v in QtMouse.__dict__.items() if "Button" in k}
STRING_TO_MOUSE.update({v: k for k, v in MOUSE_BUTTON_NAMES.items()})

BUTTON_TO_INT: dict[QtMouse, int] = {
    QtMouse.LeftButton: int(QtMouse.LeftButton) if API_NAME in ("PyQt5", "PySide2") else QtMouse.LeftButton.value,
    QtMouse.RightButton: int(QtMouse.RightButton) if API_NAME in ("PyQt5", "PySide2") else QtMouse.RightButton.value,
    QtMouse.MiddleButton: int(QtMouse.MiddleButton) if API_NAME in ("PyQt5", "PySide2") else QtMouse.MiddleButton.value,
    QtMouse.BackButton: int(QtMouse.BackButton) if API_NAME in ("PyQt5", "PySide2") else QtMouse.BackButton.value,
    QtMouse.ForwardButton: int(QtMouse.ForwardButton) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ForwardButton.value,
    QtMouse.TaskButton: int(QtMouse.TaskButton) if API_NAME in ("PyQt5", "PySide2") else QtMouse.TaskButton.value,
    QtMouse.ExtraButton1: int(QtMouse.ExtraButton1) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton1.value,
    QtMouse.ExtraButton2: int(QtMouse.ExtraButton2) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton2.value,
    QtMouse.ExtraButton3: int(QtMouse.ExtraButton3) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton3.value,
    QtMouse.ExtraButton4: int(QtMouse.ExtraButton4) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton4.value,
    QtMouse.ExtraButton5: int(QtMouse.ExtraButton5) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton5.value,
    QtMouse.ExtraButton6: int(QtMouse.ExtraButton6) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton6.value,
    QtMouse.ExtraButton7: int(QtMouse.ExtraButton7) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton7.value,
    QtMouse.ExtraButton8: int(QtMouse.ExtraButton8) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton8.value,
    QtMouse.ExtraButton9: int(QtMouse.ExtraButton9) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton9.value,
    QtMouse.ExtraButton10: int(QtMouse.ExtraButton10) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton10.value,
    QtMouse.ExtraButton11: int(QtMouse.ExtraButton11) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton11.value,
    QtMouse.ExtraButton12: int(QtMouse.ExtraButton12) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton12.value,
    QtMouse.ExtraButton13: int(QtMouse.ExtraButton13) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton13.value,
    QtMouse.ExtraButton14: int(QtMouse.ExtraButton14) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton14.value,
    QtMouse.ExtraButton15: int(QtMouse.ExtraButton15) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton15.value,
    QtMouse.ExtraButton16: int(QtMouse.ExtraButton16) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton16.value,
    QtMouse.ExtraButton17: int(QtMouse.ExtraButton17) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton17.value,
    QtMouse.ExtraButton18: int(QtMouse.ExtraButton18) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton18.value,
    QtMouse.ExtraButton19: int(QtMouse.ExtraButton19) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton19.value,
    QtMouse.ExtraButton20: int(QtMouse.ExtraButton20) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton20.value,
    QtMouse.ExtraButton21: int(QtMouse.ExtraButton21) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton21.value,
    QtMouse.ExtraButton22: int(QtMouse.ExtraButton22) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton22.value,
    QtMouse.ExtraButton23: int(QtMouse.ExtraButton23) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton23.value,
    QtMouse.ExtraButton24: int(QtMouse.ExtraButton24) if API_NAME in ("PyQt5", "PySide2") else QtMouse.ExtraButton24.value,
    QtMouse.NoButton: int(QtMouse.NoButton) if API_NAME in ("PyQt5", "PySide2") else QtMouse.NoButton.value,
}
if API_NAME in ("PySide2", "PySide6"):
    BUTTON_TO_INT[QtMouse.MouseButtonMask] = int(QtMouse.MouseButtonMask) if API_NAME == "PySide2" else QtMouse.MouseButtonMask.value
INT_TO_BUTTON: dict[int, QtMouse] = {v: k for k, v in BUTTON_TO_INT.items()}


STRING_KEY_TO_INT: dict[str, int] = {k: v.value if API_NAME in ("PyQt6", "PySide6") else v for k, v in QtKey.__dict__.items() if k.startswith("Key_")}

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

def getQtKey(obj: QtKey | T) -> QtKey | T:
    if isinstance(obj, bytes):
        obj = obj.decode(errors="replace")

    key = MODIFIER_KEYNAME_TO_KEY.get(obj)
    if key is not None:
        return key
    if isinstance(obj, int) and API_NAME in ("PyQt6", "PySide6"):
        return QtKey(obj)
    if obj in dir(QtKey):
        return QtKey.__dict__[obj]

    # Convert the string to QKeySequence and extract the key code
    try:
        key_sequence = QKeySequence.fromString(obj)
    except TypeError:
        return obj
    return key_sequence[0] if key_sequence.count() > 0 else obj

def getQtKeyString(key: QtKey | T) -> str:
    result = getattr(key, "name", MODIFIER_KEY_NAMES.get(key, QKeySequence(key).toString()))  # type: ignore[arg-type]
    return result.decode(errors="replace") if isinstance(result, bytes) else result

def getQtKeyStringLocalized(key: QtKey | str | int | bytes) -> str:
    return MODIFIER_KEY_NAMES.get(key, getattr(key, "name", QKeySequence(key).toString())).upper().strip().replace("KEY_", "").replace("CONTROL", "CTRL")  # type: ignore[arg-type]


def getQtButtonString(button: QtMouse | int) -> str:
    # sourcery skip: assign-if-exp, reintroduce-else
    if isinstance(button, bytes):
        button = button.decode(errors="replace")
    attrButtonName = getattr(button, "name", None)
    if isinstance(attrButtonName, bytes):
        return attrButtonName.decode(errors="replace")
    if attrButtonName is None:
        return MOUSE_BUTTON_NAMES.get(button)
    return attrButtonName  # type: ignore[arg-type]


def getQtMouseButton(obj: QtMouse | T) -> QtMouse | T:
    # sourcery skip: assign-if-exp, reintroduce-else
    buttonFromString = STRING_TO_MOUSE.get(str(obj))
    if buttonFromString is not None:
        return buttonFromString
    buttonFromInt = INT_TO_BUTTON.get(obj)
    if buttonFromInt is not None:
        return buttonFromInt
    buttonFromDict = QtMouse.__dict__.get(obj)
    if buttonFromDict is not None:
        return buttonFromDict
    return None  # type: ignore[arg-type]


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
    all_buttons = [getattr(QtMouse, button) for button in dir(QtMouse) if "Button" in button and button not in ("AllButtons", "NoButton")]

    for key in all_keys:
        key_string = getQtKeyString(key)
        key_from_string = getQtKey(key_string)
        assert key is key_from_string, f"Key str mismatch: {key} != {key_from_string}"
        key_int = STRING_KEY_TO_INT[key_string]
        key_from_int = QtKey(key_int)
        assert key_from_string == key_from_int, f"Key int mismatch: {key_from_string} ({id(key_from_string)}) != {key_from_int} ({id(key_from_int)})"

    for button in all_buttons:
        button_string = getQtButtonString(button)
        button_from_string = getQtMouseButton(button_string)
        assert button == button_from_string, f"Button str mismatch: {button} != {button_from_string}"
        button_int = BUTTON_TO_INT[button_from_string]
        button_from_int = INT_TO_BUTTON[button_int]
        assert button_from_string == button_from_int, f"Button int mismatch: {button_from_string} != {button_from_int}"

    print("All keys/buttons matched successfully!")
