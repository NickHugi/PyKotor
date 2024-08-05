from __future__ import annotations

import errno
import json
import os
import random

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
    FOS_ALLNONSTORAGEITEMS,
    FOS_ALLOWMULTISELECT,
    FOS_CREATEPROMPT,
    FOS_DEFAULTNOMINIMODE,
    FOS_DONTADDTORECENT,
    FOS_FILEMUSTEXIST,
    FOS_FORCEFILESYSTEM,
    FOS_FORCEPREVIEWPANEON,
    FOS_FORCESHOWHIDDEN,
    FOS_HIDEMRUPLACES,
    FOS_HIDEPINNEDPLACES,
    FOS_NOCHANGEDIR,
    FOS_NODEREFERENCELINKS,
    FOS_NOREADONLYRETURN,
    FOS_NOTESTFILECREATE,
    FOS_NOVALIDATE,
    FOS_OVERWRITEPROMPT,
    FOS_PATHMUSTEXIST,
    FOS_PICKFOLDERS,
    FOS_SHAREAWARE,
    FOS_STRICTFILETYPES,
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
    from ctypes import Array, _FuncPointer, _Pointer
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

    def OnFolderChanging(self, ifd: IFileDialog, isiFolder: IShellItem) -> HRESULT:  # noqa: N803
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
) -> bool:
    """Shows the IFileDialog. Returns True if the user progressed to the end and found a file. False if they cancelled."""
    hr: HRESULT | int = -1
    CANCELLED_BY_USER = -2147023673

    try:
        hr = fileDialog.Show(hwndOwner)
        print(f"Dialog shown successfully, HRESULT: {hr}")
    except OSError as e:
        if e.winerror == CANCELLED_BY_USER:
            print("Operation was canceled by the user.")
            return False
        raise
    else:
        HRESULT.raise_for_status(hr, "An unexpected error occurred showing the file browser dialog")

    return True


def createShellItem(comFuncs: Any, path: str) -> _Pointer[IShellItem]:  # noqa: N803, ARG001
    if not comFuncs.pSHCreateItemFromParsingName:
        raise OSError("comFuncs.pSHCreateItemFromParsingName not found")
    shell_item = POINTER(IShellItem)()
    hr = comFuncs.pSHCreateItemFromParsingName(path, None, IShellItem._iid_, byref(shell_item))
    if hr != S_OK:
        raise HRESULT(hr).exception(f"Failed to create shell item from path: {path}")
    return shell_item


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


def configure_file_dialog(  # noqa: PLR0913, PLR0912, C901
    dialog_type: type[IFileOpenDialog | IFileSaveDialog],
    title: str | None = None,
    options: int = 0,
    default_folder: str | None = None,
    ok_button_label: str | None = None,
    file_name_label: str | None = None,
    file_types: list[tuple[str, str]] | None = None,
    default_extension: str | None = None,
) -> list[str] | None:
    comFuncs: COMFunctionPointers = LoadCOMFunctionPointers(dialog_type)
    clsid: GUID = CLSID_FileOpenDialog if dialog_type is IFileOpenDialog else CLSID_FileSaveDialog
    fileDialog: IFileOpenDialog | IFileSaveDialog = comtypes.client.CreateObject(clsid, interface=dialog_type)
    if default_folder:
        defaultFolder_path = WindowsPath(default_folder).resolve()
        defaultFolder_pathStr = str(defaultFolder_path)
        if not defaultFolder_path.safe_isdir():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), defaultFolder_pathStr)
        shell_item = createShellItem(comFuncs, defaultFolder_pathStr)
        with HandleCOMCall(f"SetFolder({defaultFolder_pathStr})") as check:
            check(fileDialog.SetFolder(shell_item))
        with HandleCOMCall(f"SetDefaultFolder({defaultFolder_pathStr})") as check:
            check(fileDialog.SetDefaultFolder(shell_item))

    # Resolve contradictory options
    if options & FOS_ALLNONSTORAGEITEMS:
        if options & FOS_FORCEFILESYSTEM:
            options &= ~FOS_FORCEFILESYSTEM  # Remove FOS_FORCEFILESYSTEM
        if options & FOS_PICKFOLDERS:
            options &= ~FOS_PICKFOLDERS  # Remove FOS_PICKFOLDERS

    original_dialog_options = fileDialog.GetOptions()
    print(f"Original dialog options: {original_dialog_options}")
    with HandleCOMCall(f"SetOptions({options})") as check:
        check(fileDialog.SetOptions(options))
    cur_options = fileDialog.GetOptions()
    print(f"GetOptions({cur_options})")
    assert original_dialog_options != cur_options, f"SetOptions call was completely ignored by the dialog interface, attempted to set {options}, but retrieved {cur_options} (the original)"
    #assert options == cur_options, f"GetOptions call directly after the SetOptions call somehow are not equal! attempted to set {options}, but retrieved {cur_options}"

    filters: Array[COMDLG_FILTERSPEC] = (COMDLG_FILTERSPEC * len(DEFAULT_FILTERS))(*DEFAULT_FILTERS)
    if file_types:
        print("Using custom file filters")
        filters = (COMDLG_FILTERSPEC * len(filters))(
            *[
                (c_wchar_p(name), c_wchar_p(spec))
                for name, spec in file_types
            ]
        )
    else:
        print("Using default file filters")
    # FIXME!!!
    #with HandleCOMCall(f"SetFileTypes({len(filters)})") as check:
    #    check(fileDialog.SetFileTypes(len(filters), cast_with_ctypes(filters, POINTER(c_void_p))))

    if title:
        fileDialog.SetTitle(title)

    if ok_button_label:
        fileDialog.SetOkButtonLabel(ok_button_label)
    elif isinstance(fileDialog, IFileSaveDialog):
        fileDialog.SetOkButtonLabel("Save")
    elif options & FOS_PICKFOLDERS:
        fileDialog.SetOkButtonLabel("Select Folder")
    else:
        fileDialog.SetOkButtonLabel("Select File")

    if file_name_label:
        fileDialog.SetFileNameLabel(file_name_label)
    if default_extension:
        fileDialog.SetDefaultExtension(default_extension)

    if showDialog(fileDialog, HWND(0)):
        return (
            get_open_file_dialog_results(fileDialog)
            if isinstance(fileDialog, IFileOpenDialog)
            else [get_save_file_dialog_results(comFuncs, fileDialog)]
        )
    return None


def open_file_dialog(  # noqa: C901, PLR0913, PLR0912
    title: str | None = "Open File",
    default_folder: str | None = None,
    file_types: list[tuple[str, str]] | None = None,
    default_extension: str | None = None,
    *,
    overwrite_prompt: bool = False,
    strict_file_types: bool = False,
    no_change_dir: bool = True,
    force_filesystem: bool = True,
    all_non_storage_items: bool = False,
    no_validate: bool = False,
    allow_multiple_selection: bool = False,
    path_must_exist: bool = True,
    file_must_exist: bool = True,
    create_prompt: bool = False,
    share_aware: bool = False,
    no_readonly_return: bool = False,
    no_test_file_create: bool = False,
    hide_mru_places: bool = False,
    hide_pinned_places: bool = False,
    no_dereference_links: bool = False,
    add_to_recent: bool = True,
    show_hidden_files: bool = False,
    default_no_minimode: bool = False,
    force_preview_pane_on: bool = False,
    ok_button_text: str | None = None,
) -> list[str] | None:
    """Opens a file dialog to select files.

    Args:
        title (str | None): The title of the dialog.
        default_folder (str | None): The initial folder to open.
        file_types (list[tuple[str, str]] | None): A list of file type filters.
        default_extension (str | None): The default file extension.
        overwrite_prompt (bool): Prompts if the selected file already exists. FOS_OVERWRITEPROMPT.
        strict_file_types (bool): Restricts selection to specified file types. FOS_STRICTFILETYPES.
        no_change_dir (bool): Prevents changing the current working directory. FOS_NOCHANGEDIR.
        force_filesystem (bool): Ensures only file system items are shown. FOS_FORCEFILESYSTEM.
        all_non_storage_items (bool): Allows selection of non-file system items. FOS_ALLNONSTORAGEITEMS.
        no_validate (bool): Disables file name validation. FOS_NOVALIDATE.
        allow_multiple_selection (bool): Allows selecting multiple files. FOS_ALLOWMULTISELECT.
        path_must_exist (bool): Requires the path to exist. FOS_PATHMUSTEXIST.
        file_must_exist (bool): Requires the file to exist. FOS_FILEMUSTEXIST.
        create_prompt (bool): Prompts to create a new file if it doesn't exist. FOS_CREATEPROMPT.
        share_aware (bool): Ensures the dialog is aware of sharing conflicts. FOS_SHAREAWARE.
        no_readonly_return (bool): Prevents selection of read-only items. FOS_NOREADONLYRETURN.
        no_test_file_create (bool): Disables testing file creation ability. FOS_NOTESTFILECREATE.
        hide_mru_places (bool): Hides most recently used places. FOS_HIDEMRUPLACES.
        hide_pinned_places (bool): Hides pinned places. FOS_HIDEPINNEDPLACES.
        no_dereference_links (bool): Prevents dereferencing shortcuts. FOS_NODEREFERENCELINKS.
        add_to_recent (bool): Prevents adding the file to recent files. FOS_DONTADDTORECENT.
        show_hidden_files (bool): Shows hidden files and folders. FOS_FORCESHOWHIDDEN.
        default_no_minimode (bool): Uses default non-minimized mode. FOS_DEFAULTNOMINIMODE.
        force_preview_pane_on (bool): Forces the preview pane to be visible. FOS_FORCEPREVIEWPANEON.
        ok_button_text (str): The text for the button used to select/confirm the dialog.

    Returns:
        list[str] | None: A list of selected file paths or None if cancelled.
    """
    options = 0
    if overwrite_prompt:
        options |= FOS_OVERWRITEPROMPT
    if strict_file_types:
        options |= FOS_STRICTFILETYPES
    if no_change_dir:
        options |= FOS_NOCHANGEDIR
    options |= FOS_PICKFOLDERS
    if force_filesystem:
        options |= FOS_FORCEFILESYSTEM
    if all_non_storage_items:
        options |= FOS_ALLNONSTORAGEITEMS
    if no_validate:
        options |= FOS_NOVALIDATE
    if allow_multiple_selection:
        options |= FOS_ALLOWMULTISELECT
    if path_must_exist:
        options |= FOS_PATHMUSTEXIST
    if file_must_exist:
        options |= FOS_FILEMUSTEXIST
    if create_prompt:
        options |= FOS_CREATEPROMPT
    if share_aware:
        options |= FOS_SHAREAWARE
    if no_readonly_return:
        options |= FOS_NOREADONLYRETURN
    if no_test_file_create:
        options |= FOS_NOTESTFILECREATE
    if hide_mru_places:
        options |= FOS_HIDEMRUPLACES
    if hide_pinned_places:
        options |= FOS_HIDEPINNEDPLACES
    if no_dereference_links:
        options |= FOS_NODEREFERENCELINKS
    if not add_to_recent:
        options |= FOS_DONTADDTORECENT
    if show_hidden_files:
        options |= FOS_FORCESHOWHIDDEN
    if default_no_minimode:
        options |= FOS_DEFAULTNOMINIMODE
    if force_preview_pane_on:
        options |= FOS_FORCEPREVIEWPANEON
    return configure_file_dialog(IFileOpenDialog, title, options, default_folder, ok_button_text, None, file_types, default_extension)


def save_file_dialog(  # noqa: C901, PLR0913, PLR0912
    title: str | None = "Save File",
    default_folder: str | None = None,
    file_types: list[tuple[str, str]] | None = None,
    default_extension: str | None = None,
    *,
    overwrite_prompt: bool = True,
    strict_file_types: bool = False,
    no_change_dir: bool = True,
    force_filesystem: bool = True,
    all_non_storage_items: bool = False,
    no_validate: bool = False,
    path_must_exist: bool = True,
    file_must_exist: bool = False,
    create_prompt: bool = False,
    share_aware: bool = False,
    no_readonly_return: bool = False,
    no_test_file_create: bool = False,
    hide_mru_places: bool = False,
    hide_pinned_places: bool = False,
    no_dereference_links: bool = False,
    add_to_recent: bool = True,
    show_hidden_files: bool = False,
    default_no_minimode: bool = False,
    force_preview_pane_on: bool = False,
    ok_button_text: str | None = None,
) -> list[str] | None:
    """Opens a file dialog to save a file.

    Args:
        title (str | None): The title of the dialog.
        default_folder (str | None): The initial folder to open.
        file_types (list[tuple[str, str]] | None): A list of file type filters.
        default_extension (str | None): The default file extension.
        overwrite_prompt (bool): Prompts if the selected file already exists. FOS_OVERWRITEPROMPT.
        strict_file_types (bool): Restricts selection to specified file types. FOS_STRICTFILETYPES.
        no_change_dir (bool): Prevents changing the current working directory. FOS_NOCHANGEDIR.
        force_filesystem (bool): Ensures only file system items are shown. FOS_FORCEFILESYSTEM.
        all_non_storage_items (bool): Allows selection of non-file system items. FOS_ALLNONSTORAGEITEMS.
        no_validate (bool): Disables file name validation. FOS_NOVALIDATE.
        path_must_exist (bool): Requires the path to exist. FOS_PATHMUSTEXIST.
        file_must_exist (bool): Requires the file to exist. FOS_FILEMUSTEXIST.
        create_prompt (bool): Prompts to create a new file if it doesn't exist. FOS_CREATEPROMPT.
        share_aware (bool): Ensures the dialog is aware of sharing conflicts. FOS_SHAREAWARE.
        no_readonly_return (bool): Prevents selection of read-only items. FOS_NOREADONLYRETURN.
        no_test_file_create (bool): Disables testing file creation ability. FOS_NOTESTFILECREATE.
        hide_mru_places (bool): Hides most recently used places. FOS_HIDEMRUPLACES.
        hide_pinned_places (bool): Hides pinned places. FOS_HIDEPINNEDPLACES.
        no_dereference_links (bool): Prevents dereferencing shortcuts. FOS_NODEREFERENCELINKS.
        add_to_recent (bool): Prevents adding the file to recent files. FOS_DONTADDTORECENT.
        show_hidden_files (bool): Shows hidden files and folders. FOS_FORCESHOWHIDDEN.
        default_no_minimode (bool): Uses default non-minimized mode. FOS_DEFAULTNOMINIMODE.
        force_preview_pane_on (bool): Forces the preview pane to be visible. FOS_FORCEPREVIEWPANEON.
        ok_button_text (str): The text for the button used to select/confirm the dialog.

    Returns:
        list[str] | None: A list of selected file paths or None if cancelled.
    """
    options = 0
    if overwrite_prompt:
        options |= FOS_OVERWRITEPROMPT
    if strict_file_types:
        options |= FOS_STRICTFILETYPES
    if no_change_dir:
        options |= FOS_NOCHANGEDIR
    #if pick_folders:  # Incompatible (exceptions)
    #    options |= FOS_PICKFOLDERS
    if force_filesystem:
        options |= FOS_FORCEFILESYSTEM
    if all_non_storage_items:
        options |= FOS_ALLNONSTORAGEITEMS
    if no_validate:
        options |= FOS_NOVALIDATE
    #if allow_multiple_selection:  # Incompatible (exceptions)
    #    options |= FOS_ALLOWMULTISELECT
    if path_must_exist:
        options |= FOS_PATHMUSTEXIST
    if file_must_exist:
        options |= FOS_FILEMUSTEXIST
    if create_prompt:
        options |= FOS_CREATEPROMPT
    if share_aware:
        options |= FOS_SHAREAWARE
    if no_readonly_return:
        options |= FOS_NOREADONLYRETURN
    if no_test_file_create:
        options |= FOS_NOTESTFILECREATE
    if hide_mru_places:
        options |= FOS_HIDEMRUPLACES
    if hide_pinned_places:
        options |= FOS_HIDEPINNEDPLACES
    if no_dereference_links:
        options |= FOS_NODEREFERENCELINKS
    if not add_to_recent:
        options |= FOS_DONTADDTORECENT
    if show_hidden_files:
        options |= FOS_FORCESHOWHIDDEN
    if default_no_minimode:
        options |= FOS_DEFAULTNOMINIMODE
    if force_preview_pane_on:
        options |= FOS_FORCEPREVIEWPANEON
    return configure_file_dialog(IFileSaveDialog, title, options, default_folder, ok_button_text, None, file_types, default_extension)


def open_folder_dialog(  # noqa: C901, PLR0913, PLR0912
    title: str | None = "Select Folder",
    default_folder: str | None = None,
    *,
    overwrite_prompt: bool = False,
    strict_file_types: bool = False,
    no_change_dir: bool = False,
    force_filesystem: bool = True,
    all_non_storage_items: bool = False,
    no_validate: bool = False,
    allow_multiple_selection: bool = False,
    path_must_exist: bool = True,
    file_must_exist: bool = False,
    create_prompt: bool = False,
    share_aware: bool = False,
    no_readonly_return: bool = False,
    no_test_file_create: bool = False,
    hide_mru_places: bool = False,
    hide_pinned_places: bool = False,
    no_dereference_links: bool = False,
    add_to_recent: bool = True,
    show_hidden_files: bool = False,
    default_no_minimode: bool = False,
    force_preview_pane_on: bool = False,
    ok_button_text: str | None = None,
) -> list[str] | None:
    """Opens a dialog to select folders.

    Args:
        title (str | None): The title of the dialog.
        default_folder (str | None): The initial folder to open.
        overwrite_prompt (bool): Prompts if the selected file already exists. FOS_OVERWRITEPROMPT.
        strict_file_types (bool): Restricts selection to specified file types. FOS_STRICTFILETYPES.
        no_change_dir (bool): Prevents changing the current working directory. FOS_NOCHANGEDIR.
        force_filesystem (bool): Ensures only file system items are shown. FOS_FORCEFILESYSTEM.
        all_non_storage_items (bool): Allows selection of non-file system items. FOS_ALLNONSTORAGEITEMS.
        no_validate (bool): Disables file name validation. FOS_NOVALIDATE.
        allow_multiple_selection (bool): Allows selecting multiple files. FOS_ALLOWMULTISELECT.
        path_must_exist (bool): Requires the path to exist. FOS_PATHMUSTEXIST.
        file_must_exist (bool): Requires the file to exist. FOS_FILEMUSTEXIST.
        create_prompt (bool): Prompts to create a new file if it doesn't exist. FOS_CREATEPROMPT.
        share_aware (bool): Ensures the dialog is aware of sharing conflicts. FOS_SHAREAWARE.
        no_readonly_return (bool): Prevents selection of read-only items. FOS_NOREADONLYRETURN.
        no_test_file_create (bool): Disables testing file creation ability. FOS_NOTESTFILECREATE.
        hide_mru_places (bool): Hides most recently used places. FOS_HIDEMRUPLACES.
        hide_pinned_places (bool): Hides pinned places. FOS_HIDEPINNEDPLACES.
        no_dereference_links (bool): Prevents dereferencing shortcuts. FOS_NODEREFERENCELINKS.
        add_to_recent (bool): Prevents adding the file to recent files. FOS_DONTADDTORECENT.
        show_hidden_files (bool): Shows hidden files and folders. FOS_FORCESHOWHIDDEN.
        default_no_minimode (bool): Uses default non-minimized mode. FOS_DEFAULTNOMINIMODE.
        force_preview_pane_on (bool): Forces the preview pane to be visible. FOS_FORCEPREVIEWPANEON.
        ok_button_text (str): The text for the button used to select/confirm the dialog.

    Returns:
        list[str] | None: A list of selected folder paths or None if cancelled.
    """
    options = 0
    if overwrite_prompt:
        options |= FOS_OVERWRITEPROMPT
    if strict_file_types:
        options |= FOS_STRICTFILETYPES
    if no_change_dir:
        options |= FOS_NOCHANGEDIR
    options |= FOS_PICKFOLDERS
    if force_filesystem:
        options |= FOS_FORCEFILESYSTEM
    if all_non_storage_items:
        options |= FOS_ALLNONSTORAGEITEMS
    if no_validate:
        options |= FOS_NOVALIDATE
    if allow_multiple_selection:
        options |= FOS_ALLOWMULTISELECT
    if path_must_exist:
        options |= FOS_PATHMUSTEXIST
    if file_must_exist:
        options |= FOS_FILEMUSTEXIST
    if create_prompt:
        options |= FOS_CREATEPROMPT
    if share_aware:
        options |= FOS_SHAREAWARE
    if no_readonly_return:
        options |= FOS_NOREADONLYRETURN
    if no_test_file_create:
        options |= FOS_NOTESTFILECREATE
    if hide_mru_places:
        options |= FOS_HIDEMRUPLACES
    if hide_pinned_places:
        options |= FOS_HIDEPINNEDPLACES
    if no_dereference_links:
        options |= FOS_NODEREFERENCELINKS
    if not add_to_recent:
        options |= FOS_DONTADDTORECENT
    if show_hidden_files:
        options |= FOS_FORCESHOWHIDDEN
    if default_no_minimode:
        options |= FOS_DEFAULTNOMINIMODE
    if force_preview_pane_on:
        options |= FOS_FORCEPREVIEWPANEON
    return configure_file_dialog(IFileOpenDialog, title, options, default_folder, ok_button_text, None, None, None)


def get_open_file_dialog_results(  # noqa: C901, PLR0912, PLR0915
    fileOpenDialog: IFileOpenDialog,  # noqa: N803
) -> list[str]:
    results: list[str] = []
    resultsArray: IShellItemArray = fileOpenDialog.GetResults()
    itemCount: int = resultsArray.GetCount()

    for i in range(itemCount):
        shell_item: IShellItem = resultsArray.GetItemAt(i)
        szFilePath: str = shell_item.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        if szFilePath and szFilePath.strip():
            results.append(szFilePath)
            print(f"Item {i} file path: {szFilePath}")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(szFilePath))
    return results


def get_save_file_dialog_results(  # noqa: C901, PLR0912, PLR0915
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
    # Randomizing arguments for open_folder_dialog
    open_folder_args = {
        "title": "Select Folder" if random.choice([True, False]) else None,
        "default_folder": "C:\\Users" if random.choice([True, False]) else None,
        "overwrite_prompt": random.choice([True, False]),
        "strict_file_types": random.choice([True, False]),
        "no_change_dir": random.choice([True, False]),
        "force_filesystem": random.choice([True, False]),
        "all_non_storage_items": random.choice([True, False]),
        "no_validate": random.choice([True, False]),
        "allow_multiple_selection": random.choice([True, False]),
        "path_must_exist": random.choice([True, False]),
        "file_must_exist": random.choice([True, False]),
        "create_prompt": random.choice([True, False]),
        "share_aware": random.choice([True, False]),
        "no_readonly_return": random.choice([True, False]),
        "no_test_file_create": random.choice([True, False]),
        "hide_mru_places": random.choice([True, False]),
        "hide_pinned_places": random.choice([True, False]),
        "no_dereference_links": random.choice([True, False]),
        "add_to_recent": random.choice([True, False]),
        "show_hidden_files": random.choice([True, False]),
        "default_no_minimode": random.choice([True, False]),
        "force_preview_pane_on": random.choice([True, False]),
    }
    print("\nOpen folder args")
    print(json.dumps(open_folder_args, indent=4, sort_keys=True))
    selected_folders: list[str] | None = open_folder_dialog(**open_folder_args)
    print("Selected folders:", selected_folders)

    # Randomizing arguments for open_file_dialog
    open_file_args = {
        "title": "Open File" if random.choice([True, False]) else None,
        "default_folder": "C:\\Users" if random.choice([True, False]) else None,
        "file_types": [("Text Files", "*.txt")] if random.choice([True, False]) else None,
        "default_extension": "txt" if random.choice([True, False]) else None,
        "overwrite_prompt": random.choice([True, False]),
        "strict_file_types": random.choice([True, False]),
        "no_change_dir": random.choice([True, False]),
        "force_filesystem": random.choice([True, False]),
        "all_non_storage_items": random.choice([True, False]),
        "no_validate": random.choice([True, False]),
        "allow_multiple_selection": random.choice([True, False]),
        "path_must_exist": random.choice([True, False]),
        "file_must_exist": random.choice([True, False]),
        "create_prompt": random.choice([True, False]),
        "share_aware": random.choice([True, False]),
        "no_readonly_return": random.choice([True, False]),
        "no_test_file_create": random.choice([True, False]),
        "hide_mru_places": random.choice([True, False]),
        "hide_pinned_places": random.choice([True, False]),
        "no_dereference_links": random.choice([True, False]),
        "add_to_recent": random.choice([True, False]),
        "show_hidden_files": random.choice([True, False]),
        "default_no_minimode": random.choice([True, False]),
        "force_preview_pane_on": random.choice([True, False]),
    }
    print("\nOpen file args")
    print(json.dumps(open_file_args, indent=4, sort_keys=True))
    selected_files: list[str] | None = open_file_dialog(**open_file_args)
    print("Selected files:", selected_files)

    # Randomizing arguments for save_file_dialog
    save_file_args = {
        "title": "Save File" if random.choice([True, False]) else None,
        "default_folder": "C:\\Users" if random.choice([True, False]) else None,
        "file_types": [("Text Files", "*.txt")] if random.choice([True, False]) else None,
        "default_extension": "txt" if random.choice([True, False]) else None,
        "overwrite_prompt": random.choice([True, False]),
        "strict_file_types": random.choice([True, False]),
        "no_change_dir": random.choice([True, False]),
        "force_filesystem": random.choice([True, False]),
        "all_non_storage_items": random.choice([True, False]),
        "no_validate": random.choice([True, False]),
        "path_must_exist": random.choice([True, False]),
        "file_must_exist": random.choice([True, False]),
        "create_prompt": random.choice([True, False]),
        "share_aware": random.choice([True, False]),
        "no_readonly_return": random.choice([True, False]),
        "no_test_file_create": random.choice([True, False]),
        "hide_mru_places": random.choice([True, False]),
        "hide_pinned_places": random.choice([True, False]),
        "no_dereference_links": random.choice([True, False]),
        "add_to_recent": random.choice([True, False]),
        "show_hidden_files": random.choice([True, False]),
        "default_no_minimode": random.choice([True, False]),
        "force_preview_pane_on": random.choice([True, False]),
    }
    print("\nSave file args")
    print(json.dumps(save_file_args, indent=4, sort_keys=True))
    saved_file: list[str] | None = save_file_dialog(**save_file_args)
    print("Saved file:", saved_file)
