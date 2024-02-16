from __future__ import annotations

import ctypes

# Constants for file attributes
FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

def get_win_attrs(file_path):
    # GetFileAttributesW is a Windows API function
    attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)

    # If the function fails, it returns INVALID_FILE_ATTRIBUTES
    if attrs == -1:
        msg = f"Cannot access attributes of file: {file_path}"
        raise FileNotFoundError(msg)

    # Check for specific attributes
    is_read_only = bool(attrs & FILE_ATTRIBUTE_READONLY)
    is_hidden = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    is_system = bool(attrs & FILE_ATTRIBUTE_SYSTEM)

    return is_read_only, is_hidden, is_system

file_path = r"C:\Users\boden\Documents\k1 mods\NPC_Alignment_Fix_v1_1\tslpatchdata\tk664.hid"
read_only, hidden, system = get_win_attrs(file_path)
print(f"Read-Only: {read_only}, Hidden: {hidden}, System: {system}")
