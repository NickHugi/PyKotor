from __future__ import annotations

from ctypes import HRESULT, POINTER, byref, c_void_p, c_wchar_p, windll
from typing import TYPE_CHECKING

from comtypes.GUID import GUID

from utility.system.win32.windefs_inheritence import IShellItem

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
