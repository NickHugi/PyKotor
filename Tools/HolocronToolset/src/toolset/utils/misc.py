from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

import qtpy

from qtpy import API_NAME
from qtpy.QtCore import QUrl, Qt
from qtpy.QtGui import QDesktopServices, QKeySequence

from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.rim import read_rim
from pykotor.tools.misc import is_any_erf_type_file, is_rim_file

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.erf import ERF
    from pykotor.resource.formats.rim import RIM
    from pykotor.resource.type import ResourceType

T = TypeVar("T")

MODIFIER_KEY_NAMES: dict[Qt.Key, str] = {
    Qt.Key.Key_Control: "CTRL",
    Qt.Key.Key_Shift: "SHIFT",
    Qt.Key.Key_Alt: "ALT",
    Qt.Key.Key_Meta: "META",  # Often corresponds to the Windows or Command key
    Qt.Key.Key_AltGr: "ALTGR",  # Alt Graph key
    Qt.Key.Key_CapsLock: "CAPSLOCK",
    Qt.Key.Key_NumLock: "NUMLOCK",
    Qt.Key.Key_ScrollLock: "SCROLLLOCK",
}
MODIFIER_KEYNAME_TO_KEY: dict[str, Qt.Key] = {v: k for k, v in MODIFIER_KEY_NAMES.items()}


MOUSE_BUTTON_NAMES: dict[Qt.MouseButton, str] = {
    Qt.MouseButton.LeftButton: "LeftButton",
    Qt.MouseButton.RightButton: "RightButton",
    Qt.MouseButton.MiddleButton: "MiddleButton",
    Qt.MouseButton.BackButton: "BackButton",
    Qt.MouseButton.ForwardButton: "ForwardButton",
    Qt.MouseButton.TaskButton: "TaskButton",
    Qt.MouseButton.ExtraButton1: "ExtraButton1",
    Qt.MouseButton.ExtraButton2: "ExtraButton2",
    Qt.MouseButton.ExtraButton3: "ExtraButton3",
    Qt.MouseButton.ExtraButton4: "ExtraButton4",
    Qt.MouseButton.ExtraButton5: "ExtraButton5",
    Qt.MouseButton.ExtraButton6: "ExtraButton6",
    Qt.MouseButton.ExtraButton7: "ExtraButton7",
    Qt.MouseButton.ExtraButton8: "ExtraButton8",
    Qt.MouseButton.ExtraButton9: "ExtraButton9",
    Qt.MouseButton.ExtraButton10: "ExtraButton10",
    Qt.MouseButton.ExtraButton11: "ExtraButton11",
    Qt.MouseButton.ExtraButton12: "ExtraButton12",
    Qt.MouseButton.ExtraButton13: "ExtraButton13",
    Qt.MouseButton.ExtraButton14: "ExtraButton14",
    Qt.MouseButton.ExtraButton15: "ExtraButton15",
    Qt.MouseButton.ExtraButton16: "ExtraButton16",
    Qt.MouseButton.ExtraButton17: "ExtraButton17",
    Qt.MouseButton.ExtraButton18: "ExtraButton18",
    Qt.MouseButton.ExtraButton19: "ExtraButton19",
    Qt.MouseButton.ExtraButton20: "ExtraButton20",
    Qt.MouseButton.ExtraButton21: "ExtraButton21",
    Qt.MouseButton.ExtraButton22: "ExtraButton22",
    Qt.MouseButton.ExtraButton23: "ExtraButton23",
    Qt.MouseButton.ExtraButton24: "ExtraButton24",
    # not actual buttons:
    # Qt.MouseButton.NoButton: "NoButton"
    # Qt.MouseButton.AllButtons: "AllButtons"
}
STRING_TO_MOUSE: dict[str, Qt.MouseButton] = {k: v for k, v in Qt.MouseButton.__dict__.items() if "Button" in k}
STRING_TO_MOUSE.update({v: k for k, v in MOUSE_BUTTON_NAMES.items()})

BUTTON_TO_INT: dict[Qt.MouseButton | str, int] = {
    Qt.MouseButton.LeftButton: int(Qt.MouseButton.LeftButton) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.LeftButton.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.RightButton: int(Qt.MouseButton.RightButton) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.RightButton.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.MiddleButton: int(Qt.MouseButton.MiddleButton) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.MiddleButton.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.BackButton: int(Qt.MouseButton.BackButton) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.BackButton.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ForwardButton: int(Qt.MouseButton.ForwardButton) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ForwardButton.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.TaskButton: int(Qt.MouseButton.TaskButton) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.TaskButton.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton1: int(Qt.MouseButton.ExtraButton1) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton1.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton2: int(Qt.MouseButton.ExtraButton2) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton2.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton3: int(Qt.MouseButton.ExtraButton3) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton3.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton4: int(Qt.MouseButton.ExtraButton4) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton4.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton5: int(Qt.MouseButton.ExtraButton5) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton5.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton6: int(Qt.MouseButton.ExtraButton6) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton6.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton7: int(Qt.MouseButton.ExtraButton7) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton7.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton8: int(Qt.MouseButton.ExtraButton8) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton8.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton9: int(Qt.MouseButton.ExtraButton9) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton9.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton10: int(Qt.MouseButton.ExtraButton10) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton10.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton11: int(Qt.MouseButton.ExtraButton11) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton11.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton12: int(Qt.MouseButton.ExtraButton12) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton12.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton13: int(Qt.MouseButton.ExtraButton13) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton13.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton14: int(Qt.MouseButton.ExtraButton14) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton14.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton15: int(Qt.MouseButton.ExtraButton15) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton15.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton16: int(Qt.MouseButton.ExtraButton16) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton16.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton17: int(Qt.MouseButton.ExtraButton17) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton17.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton18: int(Qt.MouseButton.ExtraButton18) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton18.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton19: int(Qt.MouseButton.ExtraButton19) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton19.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton20: int(Qt.MouseButton.ExtraButton20) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton20.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton21: int(Qt.MouseButton.ExtraButton21) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton21.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton22: int(Qt.MouseButton.ExtraButton22) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton22.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton23: int(Qt.MouseButton.ExtraButton23) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton23.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.ExtraButton24: int(Qt.MouseButton.ExtraButton24) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.ExtraButton24.value,  # pyright: ignore[reportArgumentType]
    Qt.MouseButton.NoButton: int(Qt.MouseButton.NoButton) if API_NAME in ("PyQt5", "PySide2") else Qt.MouseButton.NoButton.value,  # pyright: ignore[reportArgumentType]
}
if API_NAME in ("PySide2", "PySide6"):
    BUTTON_TO_INT[Qt.MouseButton.MouseButtonMask] = int(Qt.MouseButton.MouseButtonMask) if API_NAME == "PySide2" else Qt.MouseButton.MouseButtonMask.value  # pyright: ignore[reportAttributeAccessIssue]
INT_TO_BUTTON: dict[int, Qt.MouseButton] = {v: k for k, v in BUTTON_TO_INT.items()}  # pyright: ignore[reportAssignmentType]


STRING_KEY_TO_INT: dict[str, int] = {k: v.value if API_NAME in ("PyQt6", "PySide6") else v for k, v in Qt.Key.__dict__.items() if k.startswith("Key_")}


def get_nums(
    string_input: str,
) -> list[int]:
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


def open_link(link: str):
    url = QUrl(link)
    QDesktopServices.openUrl(url)


def clamp(
    value: float,
    min_value: float,
    max_value: float,
) -> float:
    return max(min_value, min(value, max_value))


def get_qt_key(
    obj: Qt.Key | T,
) -> Qt.Key | T:
    if isinstance(obj, bytes):
        obj = obj.decode(errors="replace")

    key: Qt.Key | int | None = MODIFIER_KEYNAME_TO_KEY.get(obj)  # pyright: ignore[reportArgumentType]
    if key is not None:
        return key
    if isinstance(obj, int) and qtpy.QT6:
        return Qt.Key(obj)
    if obj in dir(Qt.Key):
        return Qt.Key.__dict__[obj]

    # Convert the string to QKeySequence and extract the key code
    try:
        key_sequence: QKeySequence = QKeySequence.fromString(obj)  # pyright: ignore[reportArgumentType]
    except TypeError:
        return obj
    return key_sequence[0] if key_sequence.count() > 0 else obj  # pyright: ignore[reportReturnType]


def get_qt_key_string(
    key: Qt.Key | T,
) -> str:
    result: str | bytes = getattr(key, "name", MODIFIER_KEY_NAMES.get(key, QKeySequence(key).toString()))  # type: ignore[arg-type]
    return result.decode(errors="replace") if isinstance(result, bytes) else result  # pyright: ignore[reportReturnType]


def get_qt_key_string_localized(
    key: Qt.Key | str | int | bytes,
) -> str:
    return MODIFIER_KEY_NAMES.get(key, getattr(key, "name", QKeySequence(key).toString())).upper().strip().replace("KEY_", "").replace("CONTROL", "CTRL")  # type: ignore[arg-type]


def get_qt_button_string(
    button: Qt.MouseButton | int | str,
) -> str:
    # sourcery skip: assign-if-exp, reintroduce-else
    if isinstance(button, bytes):
        button = button.decode(errors="replace")  # pyright: ignore[reportArgumentType]
    attr_button_name: str | None = getattr(button, "name", None)
    if isinstance(attr_button_name, bytes):
        return attr_button_name.decode(errors="replace")
    if attr_button_name is None:
        return MOUSE_BUTTON_NAMES.get(button)  # pyright: ignore[reportArgumentType, reportReturnType]
    return attr_button_name  # type: ignore[arg-type]


def get_qt_mouse_button(
    obj: Qt.MouseButton | T,
) -> Qt.MouseButton | T:
    # sourcery skip: assign-if-exp, reintroduce-else
    button_from_string: Qt.MouseButton | None = STRING_TO_MOUSE.get(str(obj))
    if button_from_string is not None:
        return button_from_string
    button_from_int: Qt.MouseButton | None = INT_TO_BUTTON.get(obj)
    if button_from_int is not None:
        return button_from_int
    button_from_dict: Qt.MouseButton | None = Qt.MouseButton.__dict__.get(obj)
    if button_from_dict is not None:
        return button_from_dict
    return None  # type: ignore[arg-type]


def get_resource_from_file(
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
    r_filepath = Path(filepath)

    if is_any_erf_type_file(r_filepath.name):
        erf: ERF = read_erf(filepath)
        data = erf.get(resname, restype)
    elif is_rim_file(r_filepath.name):
        rim: RIM = read_rim(filepath)
        data = rim.get(resname, restype)
    else:
        data = r_filepath.read_bytes()

    if data is None:
        msg = "Could not find resource in RIM/ERF"
        raise ValueError(msg)

    return data


if __name__ == "__main__":  # quick test
    all_keys: list[Qt.Key] = [getattr(Qt.Key, key) for key in dir(Qt.Key) if key.startswith("Key_")]
    all_buttons: list[Qt.MouseButton] = [getattr(Qt.MouseButton, button) for button in dir(Qt.MouseButton) if "Button" in button and button not in ("AllButtons", "NoButton")]

    for key in all_keys:
        key_string: str = get_qt_key_string(key)
        key_from_string: Qt.Key | str = get_qt_key(key_string)
        assert key is key_from_string, f"Key str mismatch: {key} == {key_from_string}"
        key_int: int = STRING_KEY_TO_INT[key_string]
        key_from_int: Qt.Key = Qt.Key(key_int)
        assert key_from_string == key_from_int, f"Key int mismatch: {key_from_string} ({id(key_from_string)}) != {key_from_int} ({id(key_from_int)})"

    for button in all_buttons:
        button_string: str = get_qt_button_string(button)
        button_from_string: Qt.MouseButton | str = get_qt_mouse_button(button_string)
        assert button == button_from_string, f"Button str mismatch: {button} == {button_from_string}"
        button_int: int | None = BUTTON_TO_INT.get(button_from_string)
        if button_int is None:
            continue
        button_from_int: Qt.MouseButton = INT_TO_BUTTON[button_int]
        assert button_from_string == button_from_int, f"Button int mismatch: {button_from_string} == {button_from_int}"

    print("All keys/buttons matched successfully!")
