from __future__ import annotations

from ctypes import (
    WINFUNCTYPE,
    Structure,
    c_int,
    c_long,
    c_uint,
    c_void_p,
    windll,
)
from ctypes.wintypes import HBRUSH, HICON, HINSTANCE, HWND, LPARAM, LPCWSTR, UINT, WPARAM
from enum import IntEnum
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ctypes import (
        _CData,
        _FuncPointer,
    )
    from ctypes.wintypes import HMENU, LPVOID
    from types import TracebackType

    from _win32typing import PyResourceId  # pyright: ignore[reportMissingModuleSource]


WNDPROC: type[_FuncPointer] = WINFUNCTYPE(c_long, HWND, c_uint, WPARAM, LPARAM)
WM_DESTROY = 0x0002
WS_OVERLAPPEDWINDOW = (0x00CF0000)
WS_VISIBLE = 0x10000000
HCURSOR = c_void_p


class ctypesWNDCLASS(Structure):  # noqa: N801
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("style", UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", c_int),
        ("cbWndExtra", c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", LPCWSTR),
        ("lpszClassName", LPCWSTR)
    ]


def wnd_proc(
    hwnd: HWND,
    message: c_uint,
    wparam: WPARAM,
    lparam: LPARAM,
) -> c_long:
    if message == WM_DESTROY:
        windll.user32.PostQuitMessage(0)
        return c_long(0)
    print(f"wnd_proc(hwnd={hwnd}, message={message}, wparam={wparam}, lparam={lparam})")
    result = windll.user32.DefWindowProcW(hwnd, message, wparam, lparam)
    if isinstance(result, int):
        return c_long(result)
    print(result, "result is unexpectedly class:", result.__class__.__name__)
    return result


class CursorType(IntEnum):
    ARROW = 32512
    IBEAM = 32513
    WAIT = 32514
    CROSS = 32515
    UPARROW = 32516
    SIZE = 32640
    ICON = 32641
    SIZENWSE = 32642
    SIZENESW = 32643
    SIZEWE = 32644
    SIZENS = 32645
    SIZEALL = 32646
    NO = 32648
    HAND = 32649
    APPSTARTING = 32650
    HELP = 32651


class SimplePyHWND:
    """Context manager for creating and destroying a simple custom window."""
    CLASS_NAME: str = "SimplePyHWND"
    DISPLAY_NAME: str = "Python Simple Window"

    def __init__(
        self,
        *,
        visible: bool = False,
        dwExStyle: int = 0,  # noqa: N803
        lpClassName: PyResourceId | str | None = None,  # noqa: N803
        lpWindowName: str | None = None,  # noqa: N803
        dwStyle: int | None = None,  # noqa: N803
        x: int = 0,
        y: int = 0,
        nWidth: int = 1280,  # noqa: N803
        nHeight: int = 720,  # noqa: N803
        hWndParent: HWND | None = None,  # noqa: N803
        hMenu: HMENU | None = None,  # noqa: N803
        hInstance: HINSTANCE | None = None,  # noqa: N803
        lpParam: LPVOID | None = None,  # noqa: N803
    ):
        self.hwnd: int | None = None
        self.visible: bool = visible
        self.dwExStyle: int = dwExStyle
        self.lpClassName: PyResourceId | str | None = lpClassName or self.CLASS_NAME
        self.lpWindowName: str | None = lpWindowName or self.DISPLAY_NAME
        self.dwStyle: int | None = WS_OVERLAPPEDWINDOW | WS_VISIBLE if visible else (dwStyle or 0)
        self.x: int = x
        self.y: int = y
        self.nWidth: int = nWidth
        self.nHeight: int = nHeight
        self.hWndParent: HWND | None = hWndParent
        self.hMenu: HMENU | None = hMenu
        self.hInstance: HINSTANCE | None = hInstance
        self.lpParam: LPVOID | None = lpParam

    def __enter__(self) -> int:
        self.register_class()
        self.hwnd = self.create_window()
        self._class_atom: PyResourceId | None = None
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
        import win32gui
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = WNDPROC(wnd_proc)  # pyright: ignore[reportAttributeAccessIssue]
        wc.lpszClassName = self.CLASS_NAME  # pyright: ignore[reportAttributeAccessIssue]
        self.hinst = wc.hInstance = win32gui.GetModuleHandle(None)  # pyright: ignore[reportAttributeAccessIssue]
        wc.hCursor = windll.user32.LoadCursorW(None, CursorType.ARROW.value)  # pyright: ignore[reportAttributeAccessIssue]
        try:
            self._class_atom = win32gui.RegisterClass(wc)
        except Exception as e:  # pywintypes.error
            if getattr(e, "winerror", None) != 1410:  # class already registered
                raise
            print(f"{e} (Class already registered)")

    def unregister_class(self):
        """Unregister the window class."""
        if self._class_atom is not None:
            win32gui.UnregisterClass(self._class_atom, windll.kernel32.GetModuleHandleW(None))

    def create_window(self) -> int:
        """Create the window."""
        return windll.user32.CreateWindowExW(
            self.dwExStyle, self.lpClassName, self.lpWindowName, self.dwStyle,
            self.x, self.y, self.nWidth, self.nHeight,
            self.hWndParent, self.hMenu,
            windll.kernel32.GetModuleHandleW(None) if self.hInstance is None else self.hInstance,
            self.lpParam)


if __name__ == "__main__":
    import time

    with SimplePyHWND(visible=True) as hwnd:
        print(f"Created SimplePyHWND with handle: {hwnd}")
        time.sleep(3)
    print("SimplePyHWND has been destroyed.")
