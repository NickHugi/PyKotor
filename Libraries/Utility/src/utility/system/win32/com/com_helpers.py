from __future__ import annotations

import sys

from contextlib import contextmanager
from ctypes import POINTER, PyDLL, byref, c_uint, c_void_p, py_object, windll
from ctypes.wintypes import BOOL, WIN32_FIND_DATAW
from os import fspath
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generator, Generic, Sequence, TypeVar

from utility.system.win32.com.com_types import GUID
from utility.system.win32.com.interfaces import SIGDN
from utility.system.win32.hresult import HRESULT, S_FALSE, S_OK

if TYPE_CHECKING:
    from ctypes import _CArgObject, _CData, _Pointer
    from types import TracebackType

    import comtypes  # pyright: ignore[reportMissingTypeStubs, reportMissingModuleSource]

    from _win32typing import PyIBindCtx, PyIUnknown  # pyright: ignore[reportMissingModuleSource]
    from comtypes._memberspec import _ComMemberSpec  # pyright: ignore[reportMissingTypeStubs]
    from typing_extensions import Self

    T = TypeVar("T", bound=_CData)
if not TYPE_CHECKING:
    _Pointer = POINTER(c_uint).__class__
    T = TypeVar("T")

class COMInitializeContext(Generic[T]):
    def __init__(self):
        self._should_uninitialize: bool = False

    def __enter__(self) -> T | comtypes.IUnknown | None:
        print("windll.ole32.CoInitialize()")
        hr = windll.ole32.CoInitialize(None)
        if hr == S_FALSE:
            print("COM library already initialized.", file=sys.stderr)
        elif hr != S_OK:
            HRESULT(hr).raise_for_status(hr, "CoInitialize failed!")
        self._should_uninitialize = True
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if self._should_uninitialize:
            print("windll.ole32.CoUninitialize()")
            windll.ole32.CoUninitialize()


class COMCreateInstanceContext(Generic[T]):
    def __init__(self, clsid: GUID | None = None, interface: type[T | comtypes.IUnknown] | None = None):
        self.clsid: GUID | None = clsid
        self.interface: type[T | comtypes.IUnknown] | None = interface
        self._should_uninitialize: bool = False

    def __enter__(self) -> T | comtypes.IUnknown | None:
        print("windll.ole32.CoInitialize()")
        hr = windll.ole32.CoInitialize(None)
        if hr == S_FALSE:
            print("COM library already initialized.", file=sys.stderr)
        elif hr != S_OK:
            raise OSError(f"CoInitialize failed! {hr}")

        self._should_uninitialize = True
        if self.interface is not None and self.clsid is not None:
            p: _Pointer[T | comtypes.IUnknown] = POINTER(self.interface)()
            iid: GUID | None = getattr(self.interface, "_iid_", None)
            if iid is None or not isinstance(iid, GUID.guid_ducktypes()):
                raise OSError("Incorrect interface definition")
            hr = windll.ole32.CoCreateInstance(byref(self.clsid), None, 1, byref(iid), byref(p))
            if hr != S_OK:
                raise HRESULT(hr).exception(f"CoCreateInstance failed on clsid '{self.clsid}', with interface '{iid}'!")
            return p.contents
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if self._should_uninitialize:
            print("windll.ole32.CoUninitialize()")
            windll.ole32.CoUninitialize()


@contextmanager
def HandleCOMCall(action_desc: str = "Unspecified COM function") -> Generator[Callable[..., None], Any, None]:
    print(f"Attempt to call COM func {action_desc}")
    try:
        from comtypes import COMError  # pyright: ignore[reportMissingTypeStubs, reportMissingModuleSource]
    except ImportError:
        COMError = OSError
    future_error_msg = f"An error has occurred in win32 COM function '{action_desc}'"
    try:
        # Yield back a callable function that will raise if hr is nonzero.
        yield lambda hr: HRESULT(hr).raise_for_status(hr, future_error_msg) and hr or hr
    except (COMError, OSError) as e:
        errcode = getattr(e, "winerror", getattr(e, "hresult", None))
        if errcode is None:
            raise
        raise HRESULT(errcode).exception(future_error_msg)  # noqa: B904  # pyright: ignore[reportAttributeAccessIssue]


def comtypes_get_refcount(ptr):
    """Helper function for testing: return the COM reference count of a comtypes COM object."""
    ptr.AddRef()
    return ptr.Release()


def comtypes2pywin(
    ptr: comtypes.COMObject,
    interface: type[comtypes.IUnknown] | None = None,
) -> PyIUnknown:
    """Convert a comtypes pointer 'ptr' into a pythoncom
    PyI<interface> object.

    'interface' specifies the interface we want; it must be a comtypes
    interface class.  The interface must be implemented by the object;
    and the interface must be known to pythoncom.

    If 'interface' is specified, comtypes.IUnknown is used.
    """
    import comtypes  # pyright: ignore[reportMissingTypeStubs, reportMissingModuleSource]
    import pythoncom
    if interface is None:
        interface = comtypes.IUnknown
    # ripped from
    # https://github.com/enthought/comtypes/blob/main/comtypes/test/test_win32com_interop.py
    # We use the PyCom_PyObjectFromIUnknown function in pythoncomxxx.dll to
    # convert a comtypes COM pointer into a pythoncom COM pointer.
    # This is the C prototype; we must pass 'True' as third argument:
    # PyObject *PyCom_PyObjectFromIUnknown(IUnknown *punk, REFIID riid, BOOL bAddRef)
    _PyCom_PyObjectFromIUnknown = PyDLL(pythoncom.__file__).PyCom_PyObjectFromIUnknown
    _PyCom_PyObjectFromIUnknown.restype = py_object
    _PyCom_PyObjectFromIUnknown.argtypes = (POINTER(comtypes.IUnknown), c_void_p, BOOL)
    return _PyCom_PyObjectFromIUnknown(ptr, byref(interface._iid_), True)  # noqa: FBT003, SLF001


def register_idispatch_object(
    com_object: comtypes.COMObject,
    name: str,
    interface: type[comtypes.IUnknown] | None = None,
) -> PyIBindCtx:
    import pythoncom
    ctx = pythoncom.CreateBindCtx()
    py_data = comtypes2pywin(com_object, interface)
    ctx.RegisterObjectParam(name, py_data)
    return ctx


if __name__ == "__main__":
    # Small test.
    import comtypes  # pyright: ignore[reportMissingTypeStubs]

    from win32com.shell import shell  # pyright: ignore[reportMissingModuleSource]
    IID_IFileSystemBindData = GUID("{01e18d10-4d8b-11d2-855d-006008059367}")
    class IFileSystemBindData(comtypes.IUnknown):
        """The IFileSystemBindData interface
        https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nn-shobjidl_core-ifilesystembinddata.
        """
        _iid_ = IID_IFileSystemBindData
        _methods_: ClassVar[list[_ComMemberSpec]] = [
            comtypes.COMMETHOD([], HRESULT, "SetFindData",
                    (["in"], POINTER(WIN32_FIND_DATAW), "pfd")),
            comtypes.COMMETHOD([], HRESULT, "GetFindData",
                    (["out"], POINTER(WIN32_FIND_DATAW), "pfd"))
        ]
    class FileSystemBindData(comtypes.COMObject):
        """Implements the IFileSystemBindData interface:
        https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nn-shobjidl_core-ifilesystembinddata.
        """
        _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IFileSystemBindData]
        def IFileSystemBindData_SetFindData(self: Self, this: Self, pfd: _Pointer | _CArgObject) -> HRESULT:
            self.pfd: _Pointer = pfd  # pyright: ignore[reportAttributeAccessIssue]
            return S_OK
        def IFileSystemBindData_GetFindData(self: Self, this: Self, pfd: _Pointer | _CArgObject) -> HRESULT:
            return S_OK
    find_data = WIN32_FIND_DATAW()  # from wintypes
    bind_data: FileSystemBindData = FileSystemBindData()  # pyright: ignore[reportAssignmentType]
    bind_data.IFileSystemBindData_SetFindData(bind_data, byref(find_data))
    ctx = register_idispatch_object(bind_data, "File System Bind Data")

    item = shell.SHCreateItemFromParsingName(
        fspath(r"Z:\blah\blah"), ctx, shell.IID_IShellItem2)
    print(item.GetDisplayName(SIGDN.SIGDN_DESKTOPABSOLUTEPARSING))  # prints Z:\blah\blah
