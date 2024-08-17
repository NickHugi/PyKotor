from __future__ import annotations

from ctypes import HRESULT, POINTER, Structure, byref, c_char_p, c_int, c_ulong, c_void_p, c_wchar_p, windll
from ctypes.wintypes import BOOL, DWORD, HANDLE, HINSTANCE, HKEY
from typing import TYPE_CHECKING, Any

from utility.system.win32.com.com_types import GUID
from utility.system.win32.com.interfaces import IShellItem

if TYPE_CHECKING:
    from ctypes import _Pointer

SHCreateItemFromParsingName = windll.shell32.SHCreateItemFromParsingName
SHCreateItemFromParsingName.argtypes = [c_wchar_p, c_void_p, POINTER(GUID), POINTER(POINTER(IShellItem))]
SHCreateItemFromParsingName.restype = HRESULT

def create_shell_item_from_path(path: str) -> _Pointer[IShellItem]:
    item = POINTER(IShellItem)()
    hr = SHCreateItemFromParsingName(path, None, byref(GUID("{00000000-0000-0000-C000-000000000046}")), byref(item))
    if hr != 0:
        raise OSError(f"SHCreateItemFromParsingName failed! HRESULT: {hr}")
    return item



# context menu properties
SEE_MASK_NOCLOSEPROCESS = 0x00000040
SEE_MASK_INVOKEIDLIST = 0x0000000C

class SHELLEXECUTEINFO(Structure):
    _fields_ = (
        ("cbSize", DWORD),
        ("fMask", c_ulong),
        ("hwnd", HANDLE),
        ("lpVerb", c_char_p),
        ("lpFile", c_char_p),
        ("lpParameters", c_char_p),
        ("lpDirectory", c_char_p),
        ("nShow", c_int),
        ("hInstApp", HINSTANCE),
        ("lpIDList", c_void_p),
        ("lpClass", c_char_p),
        ("hKeyClass", HKEY),
        ("dwHotKey", DWORD),
        ("hIconOrMonitor", HANDLE),
        ("hProcess", HANDLE),
    )
    cbSize: int
    fMask: int
    hwnd: int
    lpVerb: bytes
    lpFile: bytes
    lpParameters: bytes
    lpDirectory: bytes
    nShow: int
    hInstApp: Any | c_void_p
    lpIDList: Any | c_void_p
    lpClass: bytes
    hKeyClass: Any | c_void_p
    dwHotKey: int
    hIconOrMonitor: int
    hProcess: int

ShellExecuteEx = windll.shell32.ShellExecuteEx
ShellExecuteEx.restype = BOOL
