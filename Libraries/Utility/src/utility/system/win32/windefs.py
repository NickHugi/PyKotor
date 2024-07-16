from __future__ import annotations

from contextlib import suppress
from ctypes import HRESULT, POINTER, WINFUNCTYPE, Structure, byref, c_int, c_ubyte, c_uint, c_ulong, c_ushort, c_void_p, c_wchar_p, oledll, windll
from ctypes.wintypes import BOOL, HWND, LPCWSTR, LPWSTR, UINT
from typing import TYPE_CHECKING, ClassVar, Sequence

if TYPE_CHECKING:
    import os

    from ctypes import Array, _CData, _CDataMeta, _Pointer

    import comtypes  # type: ignore[stub file missing]

    from comtypes.GUID import GUID as COMTYPE_GUID  # type: ignore[stub file missing]
    from typing_extensions import Self



class GUID(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("Data1", c_ulong),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", c_ubyte * 8)
    ]

    def NULL(self) -> Self:
        return self.__class__("{00000000-0000-0000-0000-000000000000}")

    def __init__(
        self,
        d1: int | str | tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int]
        | tuple[int, int, int, int, int, int, int, int, int, int, int] | None = None,
        d2: int | None = None,
        d3: int | None = None,
        d4: tuple[int, int, int, int, int, int, int, int] | int | bytes | None = None,
        *args,
    ):
        super().__init__()
        d1, d2, d3, d4 = self._parse_args(d1, d2, d3, d4, *args)
        self.Data1: c_ulong = c_ulong(d1)
        self.Data2: c_ushort = c_ushort(d2)
        self.Data3: c_ushort = c_ushort(d3)
        self.Data4: Array[c_ubyte] = (c_ubyte * 8)(*d4)

    def __repr__(self):
        return f'GUID("{self!s}")'

    def __str__(self):
        p = c_wchar_p()
        windll.ole32.StringFromCLSID(byref(self), byref(p))
        result = p.value
        windll.ole32.CoTaskMemFree(p)
        if result is None:
            d4_hex = "".join(f"{byte:02X}" for byte in self.Data4)
            result = f"{{{self.Data1:08X}-{self.Data2:04X}-{self.Data3:04X}-{d4_hex[:4]}-{d4_hex[4:]}}}"
        return result and result.strip() or str(self.NULL())

    __unicode__ = __str__

    @classmethod
    def _get_known_guid_ducktypes(cls) -> tuple[type[GUID]] | tuple[type[COMTYPE_GUID], type[GUID]]:
        COMTYPE_GUID = None
        with suppress(ImportError, ModuleNotFoundError):
            from comtypes.GUID import GUID as COMTYPE_GUID  # type: ignore[stub file missing]
        return (GUID,) if COMTYPE_GUID is None else (COMTYPE_GUID, GUID)

    def __bool__(self):
        return self != self.NULL()

    def __eq__(self, other):
        return isinstance(other, self._get_known_guid_ducktypes()) and bytes(self) == bytes(other)

    def __hash__(self):
        # We make GUID instances hashable, although they are mutable.
        return hash(bytes(self))

    def copy(self) -> Self:
        return self.__class__(str(self))

    @classmethod
    def from_progid(cls, progid: str | comtypes.CoClass | Self | COMTYPE_GUID) -> Self | GUID | COMTYPE_GUID:
        """Get guid from progid, ..."""
        progid = getattr(progid, "_reg_clsid_", progid)
        if isinstance(progid, cls._get_known_guid_ducktypes()):
            return progid
        if not isinstance(progid, str):
            raise TypeError(f"Cannot construct GUID from {progid!r}")
        if progid.startswith("{"):
            return cls(progid)
        inst = cls()
        oledll.ole32.CLSIDFromProgID(str(progid), byref(inst))
        return inst

    def as_progid(self) -> str | None:
        """Convert a GUID into a progid."""
        progid = c_wchar_p()
        oledll.ole32.ProgIDFromCLSID(byref(self), byref(progid))
        result = progid.value
        oledll.ole32.CoTaskMemFree(progid)
        return result

    @classmethod
    def create_new(cls) -> Self:
        """Create a brand new guid."""
        guid = cls()
        oledll.ole32.CoCreateGuid(byref(guid))
        return guid

    def _parse_args(
        self,
        d1: int | str | tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int]
        | tuple[int, int, int, int, int, int, int, int, int, int, int] | None = None,
        d2: int | None = None,
        d3: int | None = None,
        d4: tuple[int, int, int, int, int, int, int, int] | int | bytes | None = None,
        *args,
    ) -> tuple[int, int, int, bytes]:  # sourcery skip: low-code-quality
        # Null GUID
        if not d1 and not d2 and not d3 and not d4 and not args:
            return self.NULL().Data1.value, self.NULL().Data2.value, self.NULL().Data3.value, self.NULL().Data4.value

        if d2 is None and d3 is None and d4 is None and not args:
            if isinstance(d1, str):
                return self.from_string(d1)
            if isinstance(d1, tuple):
                all_byte_ints = len(d1) == 16  # noqa: PLR2004
                altern_format = len(d1) == 11  # noqa: PLR2004
                if all_byte_ints or altern_format:
                    return self._parse_args(*d1)

        if isinstance(d1, int) and isinstance(d2, int) and isinstance(d3, int):
            if isinstance(d4, bytes):
                d4 = d4[:8]
                guid_str = f"{{{d1:08X}-{d2:04X}-{d3:04X}-{d4[0]:02X}{d4[1]:02X}-{d4[2]:02X}{d4[3]:02X}{d4[4]:02X}{d4[5]:02X}{d4[6]:02X}{d4[7]:02X}}}"
                return self.from_string(guid_str)
            if isinstance(d4, tuple) and len(d4) == 8:
                guid_str = f"{{{d1:08X}-{d2:04X}-{d3:04X}-{d4[0]:02X}{d4[1]:02X}-{d4[2]:02X}{d4[3]:02X}-{d4[4]:02X}{d4[5]:02X}{d4[6]:02X}{d4[7]:02X}}}"
                return self.from_string(guid_str)

        if args or isinstance(d4, int):
            all_byte_ints = len(args) == 12  # noqa: PLR2004
            altern_format = len(args) == 7  # noqa: PLR2004
            if not all_byte_ints and not altern_format:
                raise ValueError(f"Incorrect arguments passed to GUID({d1}, {d2}, {d3}, {d4}, *{args})")
            if all_byte_ints:
                gd = (d1, d2, d3, d4, *args)
                guid_str = f"{{{gd[0]:08X}-{gd[1]:04X}-{gd[2]:04X}-{gd[3]:02X}{gd[4]:02X}-{gd[5]:02X}{gd[6]:02X}{gd[7]:02X}-{gd[8]:02X}{gd[9]:02X}{gd[10]:02X}{gd[11]:02X}}}"
            else:
                guid_str = f"{{{d1:08X}-{d2:04X}-{d3:04X}-{d4:02X}{args[0]:02X}-{args[1]:02X}{args[2]:02X}{args[3]:02X}{args[4]:02X}{args[5]:02X}{args[6]:02X}}}"
            return self.from_string(guid_str)
        raise ValueError(f"Incorrect arguments passed to GUID({d1}, {d2}, {d3}, {d4}, *{args})")

    @staticmethod
    def from_string(guid_string: str) -> tuple[int, int, int, bytes]:
        hex_values = guid_string.strip("{}").split("-")
        data1 = int(hex_values[0], 16)
        data2 = int(hex_values[1], 16)
        data3 = int(hex_values[2], 16)
        data4 = bytes.fromhex(hex_values[3] + hex_values[4])
        return data1, data2, data3, data4


S_OK = 0
S_FALSE = 1
SFGAOF = c_ulong
SFGAO_FILESYSTEM = 0x40000000
SIGDN_FILESYSPATH = c_uint(0x80058000)
CLSID_FileOpenDialog = GUID("{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}")
CLSID_FileSaveDialog = GUID("{C0B4E2F3-BA21-4773-8DBA-335EC946EB8B}")
CLSID_IShellLibrary = GUID(0xd9b3211d, 0xe57f, 0x4426, (0xaa, 0xef, 0x30, 0xa8, 0x6, 0xad, 0xd3, 0x97))
IID_IUnknown = GUID((0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46))
IID_IEnumShellItems = GUID("{70629033-e363-4a28-a567-0db78006e6d7}")
IID_IPropertyStore = GUID("{886d8eeb-8cf2-4446-8d02-cdba1dbdcf99}")
IID_IFileOperationProgressSink = GUID("{04b0f1a7-9490-44bc-96e1-4296a31252e2}")
IID_IShellItemFilter = GUID("{2659B475-EEB8-48b7-8F07-B378810F48CF}")
IID_IShellItem = GUID("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")
IID_IShellItemArray = GUID("{b63ea76d-1f85-456f-a19c-48159efa858b}")
IID_IShellLibrary = GUID(0x11a66efa, 0x382e, 0x451a, (0x92, 0x34, 0x1e, 0xe, 0x12, 0xef, 0x30, 0x85))
IID_IFileDialog = GUID((0x42, 0x92, 0xC6, 0x89, 0x92, 0x98, 0x4A, 0x37, 0xB8, 0xF0, 0x03, 0x83, 0x5B, 0x7B, 0x6E, 0xE6))
IID_IFileDialogEvents = GUID(0x973510db, 0x7d7f, 0x452b, (0x89, 0x75, 0x74, 0xa8, 0x58, 0x28, 0xd3, 0x54))  # GUID("{973510db-7d7f-452b-8975-74a85828d354}")
IID_IFileOpenDialog = GUID("{d57c7288-d4ad-4768-be02-9d969532d960}")
IID_IFileSaveDialog = GUID((0x84BCCD23, 0x5FDE, 0x4CDB, 0xAE, 0xAA, 0xAE, 0x8C, 0xD7, 0xA4, 0xD5, 0x75))  # GUID("{84bccd23-5fde-4cdb-aea4-af64b83d78ab}")

# Define enums and other constants
class SIATTRIBFLAGS(c_int):
    SIATTRIBFLAGS_AND = 0x1
    SIATTRIBFLAGS_OR = 0x2
    SIATTRIBFLAGS_APPCOMPAT = 0x3
    SIATTRIBFLAGS_MASK = 0x3
# Or use these constants
SIATTRIBFLAGS_AND = 0x00000001
SIATTRIBFLAGS_OR = 0x00000002
SIATTRIBFLAGS_APPCOMPAT = 0x00000003
SIATTRIBFLAGS_MASK = 0x00000003
SIATTRIBFLAGS_ALLITEMS = 0x00004000

class SIGDN(c_int):
    SIGDN_NORMALDISPLAY = 0x00000000
    SIGDN_PARENTRELATIVEPARSING = 0x80018001
    SIGDN_PARENTRELATIVEFORADDRESSBAR = 0x8001c001
    SIGDN_DESKTOPABSOLUTEPARSING = 0x80028000
    SIGDN_PARENTRELATIVEEDITING = 0x80031001
    SIGDN_DESKTOPABSOLUTEEDITING = 0x8004c000
    SIGDN_FILESYSPATH = 0x80058000
    SIGDN_URL = 0x80068000

class FDAP(c_int):
    FDAP_BOTTOM = 0x00000000
    FDAP_TOP = 0x00000001

class FDE_SHAREVIOLATION_RESPONSE(c_int):  # noqa: N801
    FDESVR_DEFAULT = 0x00000000
    FDESVR_ACCEPT = 0x00000001
    FDESVR_REFUSE = 0x00000002

FDE_OVERWRITE_RESPONSE = FDE_SHAREVIOLATION_RESPONSE

class COMDLG_FILTERSPEC(Structure):  # noqa: N801
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [("pszName", LPCWSTR), ("pszSpec", LPCWSTR)]


class IUnknown(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IUnknownVTable]
class IUnknownVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IUnknown), POINTER(GUID), POINTER(c_void_p))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IUnknown))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IUnknown))),
    ]
IUnknown._iid_ = IID_IUnknown
IUnknown._fields_ = [("lpVtbl", POINTER(IUnknownVTable))]

class _ITEMIDLIST(Structure):
    _fields_: ClassVar[list[tuple[str, _CDataMeta]]] = [("mkid", c_ushort), ("abID", c_ubyte)]


class IShellItem(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IFileOpenDialogVTable]

    @classmethod
    def from_path(cls, path: os.PathLike | str) -> _Pointer[IShellItem]:
        item = POINTER(IShellItem)()
        hr = SHCreateItemFromParsingName(path, None, byref(IID_IShellItem), byref(item))
        if hr != 0:
            raise OSError(f"SHCreateItemFromParsingName failed! HRESULT: {hr}")
        return item
class IShellItemVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        # IUnknown methods
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IShellItem), POINTER(GUID), POINTER(POINTER(IShellItem)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IShellItem))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IShellItem))),

        # IShellItem methods
        ("BindToHandler", WINFUNCTYPE(HRESULT, POINTER(IShellItem), POINTER(IShellItem), POINTER(GUID), POINTER(GUID), POINTER(c_void_p))),
        ("GetDisplayName", WINFUNCTYPE(HRESULT, POINTER(IShellItem), c_ulong, POINTER(LPWSTR))),
        ("GetAttributes", WINFUNCTYPE(HRESULT, POINTER(IShellItem), c_ulong, POINTER(c_ulong))),
        ("Compare", WINFUNCTYPE(HRESULT, POINTER(IShellItem), POINTER(IShellItem), c_ulong, POINTER(c_int))),
        ("GetParent", WINFUNCTYPE(HRESULT, POINTER(IShellItem), POINTER(POINTER(IShellItem)))),
    ]
IShellItem._iid_ = IID_IShellItem
IShellItem._fields_ = [("lpVtbl", POINTER(IShellItemVTable))]


class IModalWindow(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IModalWindowVTable]
class IModalWindowVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IModalWindow), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IModalWindow))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IModalWindow))),
        ("Show", WINFUNCTYPE(HRESULT, POINTER(IModalWindow), HWND)),
    ]


class IEnumShellItems(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IEnumShellItemsVTable]
class IEnumShellItemsVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IEnumShellItems), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IEnumShellItems))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IEnumShellItems))),
        ("Next", WINFUNCTYPE(HRESULT, POINTER(IEnumShellItems), c_ulong, POINTER(POINTER(IShellItem)), POINTER(c_ulong))),
        ("Skip", WINFUNCTYPE(HRESULT, POINTER(IEnumShellItems), c_ulong)),
        ("Reset", WINFUNCTYPE(HRESULT, POINTER(IEnumShellItems))),
        ("Clone", WINFUNCTYPE(HRESULT, POINTER(IEnumShellItems), POINTER(POINTER(IEnumShellItems)))),
    ]
IEnumShellItems._iid_ = IID_IEnumShellItems
IEnumShellItems._fields_ = [("lpVtbl", POINTER(IEnumShellItemsVTable))]


class IPropertyStore(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IPropertyStoreVTable]
class IPropertyStoreVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IPropertyStore))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IPropertyStore))),
        ("GetCount", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore), POINTER(c_ulong))),
        ("GetAt", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore), c_ulong, POINTER(GUID))),
        ("GetValue", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore), POINTER(GUID), POINTER(c_void_p))),
        ("SetValue", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore), POINTER(GUID), POINTER(c_void_p))),
        ("Commit", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore))),
    ]
IPropertyStore._iid_ = IID_IPropertyStore
IPropertyStore._fields_ = [("lpVtbl", POINTER(IPropertyStoreVTable))]


class IFileOperationProgressSink(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IPropertyStoreVTable]
class IFileOperationProgressSinkVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IFileOperationProgressSink))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IFileOperationProgressSink))),
        ("StartOperations", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink))),
        ("FinishOperations", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), HRESULT)),
        ("PreRenameItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), LPCWSTR)),
        ("PostRenameItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), LPCWSTR, HRESULT, POINTER(IShellItem))),
        ("PreMoveItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), POINTER(IShellItem), LPCWSTR)),
        ("PostMoveItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), POINTER(IShellItem), LPCWSTR, HRESULT, POINTER(IShellItem))),
        ("PreCopyItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), POINTER(IShellItem), LPCWSTR)),
        ("PostCopyItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), POINTER(IShellItem), LPCWSTR, HRESULT, POINTER(IShellItem))),
        ("PreDeleteItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem))),
        ("PostDeleteItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), HRESULT, POINTER(IShellItem))),
        ("PreNewItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), LPCWSTR)),
        ("PostNewItem", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), c_ulong, POINTER(IShellItem), LPCWSTR, LPCWSTR, c_ulong, HRESULT, POINTER(IShellItem))),
        ("UpdateProgress", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink), UINT, UINT)),
        ("ResetTimer", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink))),
        ("PauseTimer", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink))),
        ("ResumeTimer", WINFUNCTYPE(HRESULT, POINTER(IFileOperationProgressSink))),
    ]

IFileOperationProgressSink._iid_ = IID_IFileOperationProgressSink
IFileOperationProgressSink._fields_ = [("lpVtbl", POINTER(IFileOperationProgressSinkVTable))]


LPCITEMIDLIST = POINTER(_ITEMIDLIST)
SHGetPathFromIDListW = windll.shell32.SHGetPathFromIDListW
SHGetPathFromIDListW.argtypes = [LPCITEMIDLIST, c_wchar_p]
SHGetPathFromIDListW.restype = BOOL
SHCreateItemFromParsingName = windll.shell32.SHCreateItemFromParsingName
SHCreateItemFromParsingName.argtypes = [c_wchar_p, c_void_p, POINTER(GUID), POINTER(POINTER(IShellItem))]
SHCreateItemFromParsingName.restype = HRESULT


class IShellItemArray(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IShellItemArrayVTable]
class IShellItemArrayVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        # IUnknown-inherited
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IShellItemArray), POINTER(GUID), POINTER(c_void_p))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IShellItemArray))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IShellItemArray))),

        # IShellItemArray methods
        ("EnumItems", WINFUNCTYPE(HRESULT, POINTER(IShellItemArray), POINTER(POINTER(c_uint)))),
        ("GetCount", WINFUNCTYPE(HRESULT, POINTER(c_uint))),
        ("GetAttributes", WINFUNCTYPE(HRESULT, POINTER(IShellItemArray), c_uint, POINTER(c_uint))),
        ("GetItemAt", WINFUNCTYPE(HRESULT, POINTER(IShellItemArray), c_uint, POINTER(POINTER(IShellItem)))),
    ]
IShellItemArray._iid_ = IID_IShellItemArray
IShellItemArray._fields_ = [("lpVtbl", POINTER(IShellItemArrayVTable))]


class IShellItemFilter(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IShellItemFilterVTable]
class IShellItemFilterVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IShellItemFilter), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IShellItemFilter))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IShellItemFilter))),
        ("IncludeItem", WINFUNCTYPE(HRESULT, POINTER(IShellItemFilter), POINTER(IShellItem))),
        ("GetEnumFlagsForItem", WINFUNCTYPE(HRESULT, POINTER(IShellItemFilter), POINTER(IShellItem), POINTER(c_ulong))),
    ]
IShellItemFilter._iid_ = IID_IShellItemFilter
IShellItemFilter._fields_ = [("lpVtbl", POINTER(IShellItemFilterVTable))]


class IFileDialog(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IFileDialogVTable]
class IFileDialogEvents(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IFileDialogEventsVTable]
class IFileDialogEventsVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IFileDialogEvents))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IFileDialogEvents))),
        ("OnFileOk", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(IFileDialog))),
        ("OnFolderChanging", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(IFileDialog), POINTER(IShellItem))),
        ("OnFolderChange", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(IFileDialog))),
        ("OnSelectionChange", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(IFileDialog))),
        ("OnShareViolation", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(IFileDialog), POINTER(IShellItem), POINTER(FDE_SHAREVIOLATION_RESPONSE))),
        ("OnTypeChange", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(IFileDialog))),
        ("OnOverwrite", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(IFileDialog), POINTER(IShellItem), POINTER(FDE_OVERWRITE_RESPONSE))),
    ]
class IFileDialogVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IFileDialog), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IFileDialog))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IFileDialog))),
        ("Show", WINFUNCTYPE(HRESULT, HWND)),  # IModalWindow
        ("SetFileTypes", WINFUNCTYPE(HRESULT, UINT, POINTER(COMDLG_FILTERSPEC))),
        ("SetFileTypeIndex", WINFUNCTYPE(HRESULT, UINT)),
        ("GetFileTypeIndex", WINFUNCTYPE(HRESULT, POINTER(UINT))),
        ("Advise", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(c_ulong))),
        ("Unadvise", WINFUNCTYPE(HRESULT, c_ulong)),
        ("SetOptions", WINFUNCTYPE(HRESULT, c_ulong)),
        ("GetOptions", WINFUNCTYPE(HRESULT, POINTER(c_ulong))),
        ("SetDefaultFolder", WINFUNCTYPE(HRESULT, POINTER(IShellItem))),
        ("SetFolder", WINFUNCTYPE(HRESULT, POINTER(IShellItem))),
        ("GetFolder", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItem)))),
        ("GetCurrentSelection", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItem)))),
        ("SetFileName", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("GetFileName", WINFUNCTYPE(HRESULT, POINTER(LPWSTR))),
        ("SetTitle", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("SetOkButtonLabel", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("SetFileNameLabel", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("GetResult", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItem)))),
        ("AddPlace", WINFUNCTYPE(HRESULT, POINTER(IShellItem), FDAP)),
        ("SetDefaultExtension", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("Close", WINFUNCTYPE(HRESULT, HRESULT)),
        ("SetClientGuid", WINFUNCTYPE(HRESULT, POINTER(GUID))),  # REFGUID
        ("ClearClientData", WINFUNCTYPE(HRESULT)),
        ("SetFilter", WINFUNCTYPE(HRESULT, POINTER(IShellItemFilter))),
    ]
IFileDialogEvents._iid_ = IID_IFileDialogEvents
IFileDialogEvents._fields_ = [("lpVtbl", POINTER(IFileDialogEventsVTable))]
IFileDialog._iid_ = IID_IFileDialog
IFileDialog._fields_ = [("lpVtbl", POINTER(IFileDialogVTable))]


class IShellLibrary(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IShellLibrary]
class IShellLibraryVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IShellLibrary))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IShellLibrary))),
        ("LoadLibraryFromItem", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(IShellItem), c_ulong)),
        ("LoadLibraryFromKnownFolder", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(GUID), c_ulong)),
        ("AddFolder", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(IShellItem))),
        ("RemoveFolder", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(IShellItem))),
        ("GetFolders", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), c_int, POINTER(GUID), POINTER(POINTER(c_void_p)))),  # REFIID
        ("ResolveFolder", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(IShellItem), c_ulong, POINTER(GUID), POINTER(POINTER(c_void_p)))),  # REFIID
        ("GetDefaultSaveFolder", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), c_int, POINTER(GUID), POINTER(POINTER(c_void_p)))),  # REFIID
        ("SetDefaultSaveFolder", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), c_int, POINTER(IShellItem))),
        ("GetOptions", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(c_ulong))),
        ("SetOptions", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), c_ulong, c_ulong)),
        ("GetFolderType", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(GUID))),
        ("SetFolderType", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(GUID))),
        ("GetIcon", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(LPWSTR))),
        ("SetIcon", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), LPCWSTR)),
        ("Commit", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary))),
        ("Save", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(IShellItem), LPCWSTR, c_ulong, POINTER(POINTER(IShellItem)))),
        ("SaveInKnownFolder", WINFUNCTYPE(HRESULT, POINTER(IShellLibrary), POINTER(GUID), LPCWSTR, c_ulong, POINTER(POINTER(IShellItem)))),
    ]
IShellLibrary._iid_ = IID_IShellLibrary
IShellLibrary._fields_ = [("lpVtbl", POINTER(IShellLibraryVTable))]


class IFileOpenDialog(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IFileOpenDialogVTable]
class IFileOpenDialogVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        # IUnknown methods
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IFileOpenDialog), POINTER(GUID), POINTER(c_void_p))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IFileOpenDialog), POINTER(IFileOpenDialog))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IFileOpenDialog), POINTER(IFileOpenDialog))),

        # IModalWindow method
        ("Show", WINFUNCTYPE(HRESULT, POINTER(IFileOpenDialog), HWND)),

        # IFileDialog methods
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IFileDialog), POINTER(GUID), POINTER(POINTER(IUnknown)))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IFileDialog))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IFileDialog))),
        ("Show", WINFUNCTYPE(HRESULT, HWND)),  # IModalWindow
        ("SetFileTypes", WINFUNCTYPE(HRESULT, UINT, POINTER(COMDLG_FILTERSPEC))),
        ("SetFileTypeIndex", WINFUNCTYPE(HRESULT, UINT)),
        ("GetFileTypeIndex", WINFUNCTYPE(HRESULT, POINTER(UINT))),
        ("Advise", WINFUNCTYPE(HRESULT, POINTER(IFileDialogEvents), POINTER(c_ulong))),
        ("Unadvise", WINFUNCTYPE(HRESULT, c_ulong)),
        ("SetOptions", WINFUNCTYPE(HRESULT, c_ulong)),
        ("GetOptions", WINFUNCTYPE(HRESULT, POINTER(c_ulong))),
        ("SetDefaultFolder", WINFUNCTYPE(HRESULT, POINTER(IShellItem))),
        ("SetFolder", WINFUNCTYPE(HRESULT, POINTER(IShellItem))),
        ("GetFolder", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItem)))),
        ("GetCurrentSelection", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItem)))),
        ("SetFileName", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("GetFileName", WINFUNCTYPE(HRESULT, POINTER(LPWSTR))),
        ("SetTitle", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("SetOkButtonLabel", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("SetFileNameLabel", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("GetResult", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItem)))),
        ("AddPlace", WINFUNCTYPE(HRESULT, POINTER(IShellItem), FDAP)),
        ("SetDefaultExtension", WINFUNCTYPE(HRESULT, LPCWSTR)),
        ("Close", WINFUNCTYPE(HRESULT, HRESULT)),
        ("SetClientGuid", WINFUNCTYPE(HRESULT, POINTER(GUID))),  # REFGUID
        ("ClearClientData", WINFUNCTYPE(HRESULT)),
        ("SetFilter", WINFUNCTYPE(HRESULT, POINTER(IShellItemFilter))),

        # IFileOpenDialog specific methods
        ("GetResults", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItemArray)))),
        ("GetSelectedItems", WINFUNCTYPE(HRESULT, POINTER(POINTER(IShellItemArray)))),
    ]
IFileOpenDialog._iid_ = IID_IFileOpenDialog
IFileOpenDialog._fields_ = [("lpVtbl", POINTER(IFileOpenDialogVTable))]

class IFileSaveDialog(Structure):
    _iid_: GUID
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]]
    lpVtbl: _Pointer[IFileSaveDialogVTable]
class IFileSaveDialogVTable(Structure):
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        # IUnknown-inherited
        ("QueryInterface", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(GUID), POINTER(c_void_p))),
        ("AddRef", WINFUNCTYPE(c_ulong, POINTER(IFileSaveDialog))),
        ("Release", WINFUNCTYPE(c_ulong, POINTER(IFileSaveDialog))),
        # IFileDialog-inherited methods
        ("AddPlace", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(IShellItem), c_uint)),
        ("Advise", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(IFileSaveDialog), POINTER(c_uint))),
        ("ClearClientData", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog))),
        ("Close", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), HRESULT)),
        ("GetCurrentSelection", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(POINTER(IShellItem)))),
        ("GetFileName", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(c_wchar_p))),
        ("GetFileTypeIndex", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(c_uint))),
        ("GetFolder", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(POINTER(IShellItem)))),
        ("GetOptions", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(c_uint))),
        ("GetResult", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(POINTER(IShellItemArray)))),
        ("SetClientGuid", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(GUID))),
        ("SetDefaultExtension", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_wchar_p)),
        ("SetDefaultFolder", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(IShellItem))),
        ("SetFileName", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_wchar_p)),
        ("SetFileTypes", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_uint, POINTER(c_void_p))),
        ("SetFileTypeIndex", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_uint)),
        ("SetFilter", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(IUnknown))),
        ("SetFolder", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), POINTER(IShellItem))),
        ("SetOkButtonLabel", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_wchar_p)),
        ("SetOptions", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_uint)),
        ("SetFileNameLabel", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_wchar_p)),
        ("SetTitle", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_wchar_p)),
        ("Show", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), HWND)),
        ("Unadvise", WINFUNCTYPE(HRESULT, POINTER(IFileSaveDialog), c_uint)),
        # Save-specific methods
        ("SetSaveAsItem", WINFUNCTYPE(HRESULT, POINTER(IShellItem))),
        ("SetProperties", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore))),
        ("SetCollectedProperties", WINFUNCTYPE(HRESULT, POINTER(IPropertyStore), BOOL)),
        ("GetProperties", WINFUNCTYPE(HRESULT, POINTER(POINTER(IPropertyStore)))),
        ("ApplyProperties", WINFUNCTYPE(HRESULT, POINTER(IShellItem), POINTER(IPropertyStore), HWND, POINTER(IFileOperationProgressSink))),
    ]
IFileSaveDialog._iid_ = IID_IFileSaveDialog
IFileSaveDialog._fields_ = [("lpVtbl", POINTER(IFileSaveDialogVTable))]
