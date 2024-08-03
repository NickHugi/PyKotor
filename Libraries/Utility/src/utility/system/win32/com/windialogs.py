from __future__ import annotations

import errno
import os

from ctypes import POINTER, WINFUNCTYPE, byref, c_ulong, c_void_p, c_wchar_p, cast as cast_with_ctypes, windll
from ctypes.wintypes import HMODULE, HWND, LPCWSTR
from typing import TYPE_CHECKING, Any, Sequence

import comtypes  # pyright: ignore[reportMissingTypeStubs]
import comtypes.client  # pyright: ignore[reportMissingTypeStubs]

from utility.system.path import WindowsPath
from utility.system.win32.com.com_helpers import HandleCOMCall
from utility.system.win32.com.com_types import GUID
from utility.system.win32.com.interfaces import (
    COMDLG_FILTERSPEC,
    FOS_ALLOWMULTISELECT,
    FOS_FILEMUSTEXIST,
    FOS_FORCEFILESYSTEM,
    FOS_FORCESHOWHIDDEN,
    FOS_OVERWRITEPROMPT,
    FOS_PATHMUSTEXIST,
    FOS_PICKFOLDERS,
    SFGAO_FILESYSTEM,
    SFGAO_FOLDER,
    SIGDN,
    CLSID_FileOpenDialog,
    CLSID_FileSaveDialog,
    COMFunctionPointers,
    IFileDialogEvents,
    IFileOpenDialog,
    IFileSaveDialog,
    IShellItem,
)
from utility.system.win32.hresult import HRESULT, S_FALSE, S_OK

if TYPE_CHECKING:
    from ctypes import _FuncPointer, _Pointer
    from ctypes.wintypes import LPWSTR

    from utility.system.win32.com.interfaces import IFileDialog, IShellItemArray


class FileDialogEventsHandler(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IFileDialogEvents]

    def OnFileOk(self, pfd: IFileDialog) -> HRESULT:
        ppsi: IShellItem = pfd.GetResult()
        pszFilePath = ppsi.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        print(f"OnFileOk, selected '{pszFilePath}'")
        resolved_path = WindowsPath(pszFilePath).resolve()
        if not resolved_path.safe_exists():
            print(f"Invalid file selected: {resolved_path}")
            return S_FALSE  # Cancel closing the dialog
        return S_OK

    def OnFolderChanging(self, ifd: IFileDialog, isiFolder: IShellItem) -> HRESULT:
        folder_path = isiFolder.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        print(f"OnFolderChanging to folder: {folder_path}")
        attributes = isiFolder.GetAttributes(0xFFFFFFFF)
        print(f"Folder attributes: {attributes}")
        return S_OK

    def OnFolderChange(self, pfd: IFileDialog) -> HRESULT:
        folder: IShellItem = pfd.GetFolder()
        folder_path = folder.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        print(f"OnFolderChange, current folder: {folder_path}")
        return S_OK

    def OnSelectionChange(self, pfd: IFileDialog) -> HRESULT:
        selection: IShellItem = pfd.GetCurrentSelection()
        selection_path = selection.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        print(f"OnSelectionChange, selected item: {selection_path}")
        return S_OK

    def OnShareViolation(self, pfd: IFileDialog, psi: IShellItem) -> int:
        file_path = psi.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        print(f"OnShareViolation for file: {file_path}!")
        return 1

    def OnTypeChange(self, ifd: IFileDialog) -> HRESULT:
        ftIndex = ifd.GetFileTypeIndex()
        print(f"OnTypeChange, new file type index: {ftIndex}")
        return S_OK

    def OnOverwrite(self, ifd: IFileDialog, isi: IShellItem) -> int:
        file_path = isi.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        # 1 = Allow Overwrite, 0 will disallow
        print(f"OnOverwrite for file: {file_path}. Allowing overwrite!")
        return 1


# Helper to convert std::wstring to LPCWSTR
def string_to_LPCWSTR(s: str) -> LPCWSTR:
    return c_wchar_p(s)


# Helper to convert LPCWSTR to std::wstring
def LPCWSTR_to_string(s: LPCWSTR) -> str | None:
    return s.value


# Load COM function pointers
def LoadCOMFunctionPointers(dialog_type: type[IFileDialog | IFileOpenDialog | IFileSaveDialog]) -> COMFunctionPointers:
    comFuncPtrs = COMFunctionPointers()
    comFuncPtrs.hOle32 = comFuncPtrs.load_library("ole32.dll")
    comFuncPtrs.hShell32 = comFuncPtrs.load_library("shell32.dll")


    # Get function pointers
    if comFuncPtrs.hOle32:
        PFN_CoInitialize: type[_FuncPointer] = WINFUNCTYPE(HRESULT, POINTER(dialog_type))
        PFN_CoUninitialize: type[_FuncPointer] = WINFUNCTYPE(None)
        PFN_CoCreateInstance: type[_FuncPointer] = WINFUNCTYPE(HRESULT, POINTER(GUID), c_void_p, c_ulong, POINTER(GUID), POINTER(POINTER(dialog_type)))
        PFN_CoTaskMemFree: type[_FuncPointer] = WINFUNCTYPE(None, c_void_p)
        comFuncPtrs.pCoInitialize = comFuncPtrs.resolve_function(comFuncPtrs.hOle32, b"CoInitialize", PFN_CoInitialize)
        comFuncPtrs.pCoUninitialize = comFuncPtrs.resolve_function(comFuncPtrs.hOle32, b"CoUninitialize", PFN_CoUninitialize)
        comFuncPtrs.pCoCreateInstance = comFuncPtrs.resolve_function(comFuncPtrs.hOle32, b"CoCreateInstance", PFN_CoCreateInstance)
        comFuncPtrs.pCoTaskMemFree = comFuncPtrs.resolve_function(comFuncPtrs.hOle32, b"CoTaskMemFree", PFN_CoTaskMemFree)

    if comFuncPtrs.hShell32:
        PFN_SHCreateItemFromParsingName: type[_FuncPointer] = WINFUNCTYPE(HRESULT, LPCWSTR, c_void_p, POINTER(GUID), POINTER(POINTER(IShellItem)))
        comFuncPtrs.pSHCreateItemFromParsingName = comFuncPtrs.resolve_function(comFuncPtrs.hShell32, b"SHCreateItemFromParsingName", PFN_SHCreateItemFromParsingName)
    return comFuncPtrs


def FreeCOMFunctionPointers(comFuncPtrs: Any):  # noqa: N803
    if comFuncPtrs.hOle32:
        windll.kernel32.FreeLibrary(cast_with_ctypes(comFuncPtrs.hOle32, HMODULE))
    if comFuncPtrs.hShell32:
        windll.kernel32.FreeLibrary(cast_with_ctypes(comFuncPtrs.hShell32, HMODULE))


def showDialog(
    fileDialog: IFileOpenDialog | IFileSaveDialog | IFileDialog,  # noqa: N803
    hwndOwner: HWND,  # noqa: N803
):
    hr = fileDialog.Show(hwndOwner)
    if hr != S_OK:
        raise HRESULT(hr).exception("Failed to show the file dialog!")


def createShellItem(comFuncs: Any, path: str) -> _Pointer[IShellItem]:  # noqa: N803, ARG001
    if not comFuncs.pSHCreateItemFromParsingName:
        raise OSError("comFuncs.pSHCreateItemFromParsingName not found")
    shell_item = POINTER(IShellItem)()
    hr = comFuncs.pSHCreateItemFromParsingName(path, None, IShellItem._iid_, byref(shell_item))
    if hr != S_OK:
        raise HRESULT(hr).exception(f"Failed to create shell item from path: {path}")
    return shell_item


def setDialogAttributes(
    fileDialog: IFileDialog | IFileOpenDialog | IFileSaveDialog,  # noqa: N803
    title: str,
    okButtonLabel: str | None = None,  # noqa: N803
    fileNameLabel: str | None = None,  # noqa: N803
) -> None:
    if title:
        fileDialog.SetTitle(title)
    if okButtonLabel:
        fileDialog.SetOkButtonLabel(okButtonLabel)
    if fileNameLabel:
        fileDialog.SetFileNameLabel(fileNameLabel)


def setupFileDialogEvents(
    fileDialog: IFileOpenDialog | IFileSaveDialog | IFileDialog,  # noqa: N803
) -> int:
    #events_interface = IFileDialogEvents()
    events_handler = FileDialogEventsHandler()
    return fileDialog.Advise(events_handler)


DEFAULT_FILTERS: list[COMDLG_FILTERSPEC] = [
    COMDLG_FILTERSPEC("All Files", "*.*"),
    COMDLG_FILTERSPEC("Text Files", "*.txt"),
    COMDLG_FILTERSPEC("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
    COMDLG_FILTERSPEC("Document Files", "*.doc;*.docx;*.pdf;*.xls;*.xlsx"),
    COMDLG_FILTERSPEC("Audio Files", "*.mp3;*.wav;*.wma;*.aac"),
    COMDLG_FILTERSPEC("Video Files", "*.mp4;*.avi;*.mkv;*.mov;*.wmv"),
    COMDLG_FILTERSPEC("Archive Files", "*.zip;*.rar;*.7z;*.tar;*.gz"),
    COMDLG_FILTERSPEC("Executable Files", "*.exe;*.bat;*.msi"),
    COMDLG_FILTERSPEC("HTML Files", "*.htm;*.html"),
    COMDLG_FILTERSPEC("XML Files", "*.xml"),
    COMDLG_FILTERSPEC("JavaScript Files", "*.js"),
    COMDLG_FILTERSPEC("CSS Files", "*.css"),
    COMDLG_FILTERSPEC("Python Files", "*.py"),
    COMDLG_FILTERSPEC("C/C++ Files", "*.c;*.cpp;*.h;*.hpp"),
    COMDLG_FILTERSPEC("Java Files", "*.java"),
    COMDLG_FILTERSPEC("Ruby Files", "*.rb"),
    COMDLG_FILTERSPEC("Perl Files", "*.pl"),
    COMDLG_FILTERSPEC("PHP Files", "*.php"),
    COMDLG_FILTERSPEC("Shell Script Files", "*.sh"),
    COMDLG_FILTERSPEC("Batch Files", "*.bat"),
    COMDLG_FILTERSPEC("INI Files", "*.ini"),
    COMDLG_FILTERSPEC("Log Files", "*.log"),
    COMDLG_FILTERSPEC("SVG Files", "*.svg"),
    COMDLG_FILTERSPEC("Markdown Files", "*.md"),
    COMDLG_FILTERSPEC("YAML Files", "*.yaml;*.yml"),
    COMDLG_FILTERSPEC("JSON Files", "*.json"),
    COMDLG_FILTERSPEC("PowerShell Files", "*.ps1"),
    COMDLG_FILTERSPEC("MATLAB Files", "*.m"),
    COMDLG_FILTERSPEC("R Files", "*.r"),
    COMDLG_FILTERSPEC("Lua Files", "*.lua"),
    COMDLG_FILTERSPEC("Rust Files", "*.rs"),
    COMDLG_FILTERSPEC("Go Files", "*.go"),
    COMDLG_FILTERSPEC("Swift Files", "*.swift"),
    COMDLG_FILTERSPEC("Kotlin Files", "*.kt;*.kts"),
    COMDLG_FILTERSPEC("Objective-C Files", "*.m;*.mm"),
    COMDLG_FILTERSPEC("SQL Files", "*.sql"),
    COMDLG_FILTERSPEC("Config Files", "*.conf"),
    COMDLG_FILTERSPEC("CSV Files", "*.csv"),
    COMDLG_FILTERSPEC("TSV Files", "*.tsv"),
    COMDLG_FILTERSPEC("LaTeX Files", "*.tex"),
    COMDLG_FILTERSPEC("BibTeX Files", "*.bib"),
    COMDLG_FILTERSPEC("Makefiles", "Makefile"),
    COMDLG_FILTERSPEC("Gradle Files", "*.gradle"),
    COMDLG_FILTERSPEC("Ant Build Files", "*.build.xml"),
    COMDLG_FILTERSPEC("Maven POM Files", "pom.xml"),
    COMDLG_FILTERSPEC("Dockerfiles", "Dockerfile"),
    COMDLG_FILTERSPEC("Vagrantfiles", "Vagrantfile"),
    COMDLG_FILTERSPEC("Terraform Files", "*.tf"),
    COMDLG_FILTERSPEC("HCL Files", "*.hcl"),
    COMDLG_FILTERSPEC("Kubernetes YAML Files", "*.yaml;*.yml")
]


def configureFileDialog(  # noqa: PLR0913
    comFuncs: Any,  # noqa: N803
    fileDialog: IFileOpenDialog | IFileSaveDialog | IFileDialog,  # noqa: N803
    filters: list[COMDLG_FILTERSPEC] | None = None,  # noqa: N803
    defaultFolder: str | os.PathLike | None = None,  # noqa: N803
    options: int | None = None,
):
    if defaultFolder:
        defaultFolder_path = WindowsPath(defaultFolder).resolve()
        defaultFolder_pathStr = str(defaultFolder_path)
        if not defaultFolder_path.safe_isdir():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), defaultFolder_pathStr)
        shell_item = createShellItem(comFuncs, defaultFolder_pathStr)
        with HandleCOMCall(f"SetFolder({defaultFolder_pathStr})") as check:
            check(fileDialog.SetFolder(shell_item))
        with HandleCOMCall(f"SetDefaultFolder({defaultFolder_pathStr})") as check:
            check(fileDialog.SetDefaultFolder(shell_item))

    if options is not None:
        with HandleCOMCall(f"SetOptions({options})") as check:
            check(fileDialog.SetOptions(options))
        cur_options = fileDialog.GetOptions()
        assert options == cur_options

    if filters is None:  # if empty actually leave it empty. None means default.
        filters = DEFAULT_FILTERS
    filter_array = (COMDLG_FILTERSPEC * len(filters))()
    for i, dialogFilter in enumerate(filters):
        filter_array[i].pszName = dialogFilter.pszName
        filter_array[i].pszSpec = dialogFilter.pszSpec

    # FIXME(th3w1zard1): Extension filters don't work.
    #hr = fileDialog.SetFileTypes(len(filters), c_void_p(addressof(filter_array)))
    #if hr != S_OK:
    #    raise HRESULT(hr).exception("Failed to set file types")


def browse_folders(
    title: str = "Select Folder",
    default_folder: str = "C:\\",
    allow_multiple: bool = False,  # noqa: FBT001, FBT002
    show_hidden: bool = False  # noqa: FBT001, FBT002
) -> list[str]:
    comFuncs = LoadCOMFunctionPointers(IFileOpenDialog)
    fileOpenDialog = comtypes.client.CreateObject(CLSID_FileOpenDialog, interface=IFileOpenDialog)

    options = FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST | FOS_FILEMUSTEXIST
    if allow_multiple:
        options |= FOS_ALLOWMULTISELECT
    if show_hidden:
        options |= FOS_FORCESHOWHIDDEN

    filters = []
    configureFileDialog(comFuncs, fileOpenDialog, filters, default_folder, options)
    setDialogAttributes(fileOpenDialog, title)
    showDialog(fileOpenDialog, HWND(0))

    return getFileOpenDialogResults(comFuncs, fileOpenDialog)

def browse_files(
    title: str = "Select File(s)",
    default_folder: str = "C:\\",
    allow_multiple: bool = False,  # noqa: FBT001, FBT002
    show_hidden: bool = True,  # noqa: FBT001, FBT002
    filters: list[COMDLG_FILTERSPEC] | None = None
) -> list[str]:
    comFuncs: COMFunctionPointers = LoadCOMFunctionPointers(IFileOpenDialog)
    fileOpenDialog: IFileOpenDialog = comtypes.client.CreateObject(CLSID_FileOpenDialog, interface=IFileOpenDialog)

    options = FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST | FOS_FILEMUSTEXIST
    if allow_multiple:
        options |= FOS_ALLOWMULTISELECT
    if show_hidden:
        options |= FOS_FORCESHOWHIDDEN

    if filters is None:
        filters = DEFAULT_FILTERS

    configureFileDialog(comFuncs, fileOpenDialog, filters, default_folder, options)
    setDialogAttributes(fileOpenDialog, title)
    showDialog(fileOpenDialog, HWND(0))

    results = getFileOpenDialogResults(comFuncs, fileOpenDialog)
    return results

def save_file(
    title: str = "Save File",
    default_folder: str = "C:\\",
    default_file_name: str = "Untitled",
    overwrite_prompt: bool = True,  # noqa: FBT001, FBT002
    show_hidden: bool = False,  # noqa: FBT001, FBT002
    filters: list[COMDLG_FILTERSPEC] | None = None
) -> str:
    comFuncs = LoadCOMFunctionPointers(IFileSaveDialog)
    fileSaveDialog = comtypes.client.CreateObject(CLSID_FileSaveDialog, interface=IFileSaveDialog)

    options = FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST | FOS_FILEMUSTEXIST
    if overwrite_prompt:
        options |= FOS_OVERWRITEPROMPT
    if show_hidden:
        options |= FOS_FORCESHOWHIDDEN

    if filters is None:
        filters = DEFAULT_FILTERS

    configureFileDialog(comFuncs, fileSaveDialog, filters, default_folder, options)
    setDialogAttributes(fileSaveDialog, title)
    fileSaveDialog.SetFileName(default_file_name)
    showDialog(fileSaveDialog, HWND(0))

    result = getFileSaveDialogResults(comFuncs, fileSaveDialog)
    return result


def getFileOpenDialogResults(  # noqa: C901, PLR0912, PLR0915
    comFuncs: COMFunctionPointers,  # noqa: N803
    fileOpenDialog: IFileOpenDialog,  # noqa: N803
) -> list[str]:
    results: list[str] = []
    resultsArray: IShellItemArray = fileOpenDialog.GetResults()
    itemCount = resultsArray.GetCount()

    for i in range(itemCount):
        shell_item: IShellItem = resultsArray.GetItemAt(i)
        szFilePath = shell_item.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        szFilePathStr = str(szFilePath)
        if szFilePathStr and szFilePathStr.strip():
            results.append(szFilePathStr)
            print(f"Item {i} file path: {szFilePath}")
            #comFuncs.pCoTaskMemFree(szFilePath)   # line crashes
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(szFilePath))

        attributes: c_ulong = shell_item.GetAttributes(SFGAO_FILESYSTEM | SFGAO_FOLDER)
        print(f"Item {i} attributes: {attributes}")

        parentItem: IShellItem | comtypes.IUnknown = shell_item.GetParent()
        if isinstance(parentItem, IShellItem) or hasattr(parentItem, "GetDisplayName"):
            szParentName: LPWSTR | str = parentItem.GetDisplayName(SIGDN.SIGDN_NORMALDISPLAY)
            print(f"Item {i} parent: {szParentName}")
            comFuncs.pCoTaskMemFree(szParentName)
            parentItem.Release()

        shell_item.Release()

    resultsArray.Release()
    return results


def getFileSaveDialogResults(  # noqa: C901, PLR0912, PLR0915
    comFuncs: COMFunctionPointers,  # noqa: N803
    fileSaveDialog: IFileSaveDialog,  # noqa: N803
) -> str:
    results = ""
    resultItem: IShellItem = fileSaveDialog.GetResult()

    szFilePath = resultItem.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
    szFilePathStr = str(szFilePath)
    if szFilePathStr and szFilePathStr.strip():
        results = szFilePathStr
        print(f"Selected file path: {szFilePath}")
        comFuncs.pCoTaskMemFree(szFilePath)
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(szFilePath))

    attributes: c_ulong = resultItem.GetAttributes(SFGAO_FILESYSTEM | SFGAO_FOLDER)
    print(f"Selected item attributes: {attributes}")

    parentItem: IShellItem | comtypes.IUnknown = resultItem.GetParent()
    if isinstance(parentItem, IShellItem) or hasattr(parentItem, "GetDisplayName"):
        szParentName: LPWSTR | str = parentItem.GetDisplayName(SIGDN.SIGDN_NORMALDISPLAY)
        print(f"Selected item parent: {szParentName}")
        comFuncs.pCoTaskMemFree(szParentName)
        parentItem.Release()

    resultItem.Release()

    return results


# Example usage
if __name__ == "__main__":
    selected_folders = browse_folders()
    print("Selected folders:", selected_folders)

    selected_files = browse_files()
    print("Selected files:", selected_files)

    saved_file = save_file()
    print("Saved file:", saved_file)
