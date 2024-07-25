from __future__ import annotations

import ctypes

from ctypes import windll
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ctypes import _CData
    from types import TracebackType

    from _win32typing import PyResourceId  # pyright: ignore[reportMissingModuleSource]

try:
    from ctypes.wintypes import HWND, LPARAM
except Exception:  # noqa: BLE001  # pyinstaller frozen-related issue observed.
    # just grab from ctypes.wintypes src I suppose
    # WPARAM is defined as UINT_PTR (unsigned type)
    # LPARAM is defined as LONG_PTR (signed type)
    if ctypes.sizeof(ctypes.c_long) == ctypes.sizeof(ctypes.c_void_p):
        WPARAM = ctypes.c_ulong
        LPARAM = ctypes.c_long
    elif ctypes.sizeof(ctypes.c_longlong) == ctypes.sizeof(ctypes.c_void_p):
        WPARAM = ctypes.c_ulonglong
        LPARAM = ctypes.c_longlong
    HWND = ctypes.c_void_p


# Define window class and procedure
WNDPROC: type[ctypes._FuncPointer] = ctypes.WINFUNCTYPE(ctypes.c_long, HWND, ctypes.c_uint, ctypes.c_uint, LPARAM)

# Windows constants
WM_DESTROY = 0x0002
IDC_ARROW = 32512
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001


class WNDCLASS(ctypes.Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.c_void_p),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
    ]


def wnd_proc(hwnd: int | None, message: int, wparam: float | None, lparam: float | None) -> int:
    if message == WM_DESTROY:
        windll.user32.PostQuitMessage(0)
        return 0
    return windll.user32.DefWindowProcW(hwnd, message, wparam, lparam)


class HInvisibleWindow:
    """Context manager for creating and destroying an invisible window."""
    CLASS_NAME: str = "HInvisibleWindow"
    DISPLAY_NAME: str = "Python Invisible Window"

    def __init__(self):
        self.hwnd: int | None = None

    def __enter__(self) -> int:
        self.register_class()
        self.hwnd = self.create_window()
        return self.hwnd


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if self.hwnd is not None:
            windll.user32.DestroyWindow(self.hwnd)
        self.unregister_class()

    def register_class(self):
        """Register the window class."""
        wc = WNDCLASS()
        wc.lpfnWndProc = WNDPROC(wnd_proc)
        wc.lpszClassName = self.CLASS_NAME
        wc.hInstance = windll.kernel32.GetModuleHandleW(None)
        wc.hCursor = windll.user32.LoadCursorW(None, IDC_ARROW)
        wc.style = CS_HREDRAW | CS_VREDRAW
        try:
            self._class_atom: PyResourceId = windll.user32.RegisterClassW(ctypes.byref(wc))
        except Exception as e:
            if getattr(e, "winerror", None) != 1410:  # class already registered
                raise

    def unregister_class(self):
        """Unregister the window class."""
        windll.user32.UnregisterClassW(self.CLASS_NAME, windll.kernel32.GetModuleHandleW(None))

    def create_window(self) -> int:
        """Create an invisible window."""
        return windll.user32.CreateWindowExW(
            0, self.CLASS_NAME, self.DISPLAY_NAME, 0, 0, 0, 0, 0, None, None,
            windll.kernel32.GetModuleHandleW(None), None)
