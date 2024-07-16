from __future__ import annotations

import atexit
import faulthandler
import logging
import os

from ctypes import POINTER, Array, Structure, _Pointer, addressof, byref, c_byte, c_uint, c_wchar_p, create_unicode_buffer, sizeof, windll
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    TypeVar,
)

from utility.system.win32.hresult import decode_hresult, print_hresult
from utility.system.win32.windefs import SFGAO_FILESYSTEM, SIGDN_FILESYSPATH, S_FALSE, S_OK, CLSID_FileOpenDialog, IFileOpenDialog, IShellItem, IShellItemArray

if TYPE_CHECKING:
    from ctypes import _CData

    from utility.system.win32.windefs import GUID
    _CT = TypeVar("_CT", bound=_CData)


def dump_memory(address: int, size: int, file_name: str):
    """Dump memory contents starting from the given address for the given size."""
    with Path(file_name).open("wb") as f:
        buffer = (c_byte * size).from_address(address)
        f.write(buffer)

def dump_structure(structure: Structure, file_prefix: os.PathLike | str):
    """Dump the memory contents of a structure and its pointers recursively."""
    # Dump the main structure
    struct_address = addressof(structure)
    struct_size = sizeof(structure)
    dump_memory(struct_address, struct_size, f"{file_prefix}.bin")

    # Iterate through the fields of the structure
    for tup in structure._fields_:
        field_name = tup[0]
        _field_type_or_other_tup = tup[1]
        field = getattr(structure, field_name)
        if isinstance(field, _Pointer):
            # If the field is a pointer, dump its contents recursively
            if field:
                pointer_address = addressof(field.contents)
                pointer_size = sizeof(field.contents)
                dump_memory(pointer_address, pointer_size, f"{file_prefix}_{field_name}.bin")
                dump_structure(field.contents, f"{file_prefix}_{field_name}")
        elif isinstance(field, Array):
            # If the field is an array, dump its contents
            array_address = addressof(field)
            array_size = sizeof(field)
            dump_memory(array_address, array_size, f"{file_prefix}_{field_name}.bin")
        elif isinstance(field, Structure):
            # If the field is a nested structure or union, dump its contents recursively
            nested_struct_address = addressof(field)
            nested_struct_size = sizeof(field)
            dump_memory(nested_struct_address, nested_struct_size, f"{file_prefix}_{field_name}.bin")
            dump_structure(field, f"{file_prefix}_{field_name}")


def create_com_object(clsid: GUID, interface: type[_CT]) -> _Pointer[_CT]:
    p = POINTER(interface)()
    hr = windll.ole32.CoCreateInstance(byref(clsid), None, 1, byref(interface._iid_), byref(p))
    if hr != S_OK:
        raise OSError(f"CoCreateInstance failed! {decode_hresult(hr)}")
    return p


def process_selected_items(item_array_ptr: _Pointer[IShellItemArray]) -> list[str]:
    if not item_array_ptr:
        raise ValueError("Invalid pointer to IShellItemArray")

    count = c_uint()
    # Access the GetCount method from the VTable and call it
    hr = item_array_ptr.contents.lpVtbl.contents.GetCount(count)
    if hr != S_OK:
        if hr != S_FALSE:
            raise OSError(f"GetCount failed! {decode_hresult(hr)}")
        # raise ValueError("No items selected")
        print("No items selected maybe??")

    chosen_files: list[str] = []
    logging.debug(f"Item count: {count.value}")
    for i in range(count.value):
        item = POINTER(IShellItem)()
        get_item_func = item_array_ptr.contents.lpVtbl.contents.GetItemAt
        result = get_item_func(item_array_ptr, i, byref(item))
        if result != S_OK:
            raise OSError(f"GetItemAt failed for index {i}! {decode_hresult(result)}")

        attributes = c_uint()
        get_attributes_func = item.contents.lpVtbl.contents.GetAttributes
        result = get_attributes_func(item, c_uint(SFGAO_FILESYSTEM), byref(attributes))
        if result != S_OK:
            raise OSError(f"GetAttributes failed for item at index {i}! {decode_hresult(result)}")

        if attributes.value & SFGAO_FILESYSTEM:
            name_buffer = create_unicode_buffer(260)
            get_display_name_func = item.contents.lpVtbl.contents.GetDisplayName
            result = get_display_name_func(item, SIGDN_FILESYSPATH, byref(name_buffer))
            if result != S_OK:
                raise OSError(f"GetDisplayName failed for item at index {i}! {decode_hresult(result)}")

            path = os.path.normpath(name_buffer.value)
            chosen_files.append(path)
    return chosen_files


def configure_file_dialog(
    title: str | None = None,
    options: int = 0,
    default_folder: str | None = None,
    ok_button_label: str | None = None,
    file_name_label: str | None = None,
    file_types: list[tuple[str, str]] | None = None,
    default_extension: str | None = None,
) -> list[str] | None:
    # sourcery skip: extract-method
    # Initialize COM library
    hr = windll.ole32.CoInitialize(None)
    if hr != 0:
        raise OSError(f"CoInitialize failed! HRESULT: {decode_hresult(hr)}")

    # Create FileOpenDialog object
    file_open_dialog = create_com_object(CLSID_FileOpenDialog, IFileOpenDialog)

    # Set options for the dialog
    file_open_dialog.contents.lpVtbl.contents.SetOptions(file_open_dialog, options)

    # Set file types
    if file_types:
        comdlg_filter_spec = (c_wchar_p * len(file_types))()
        comdlg_filter_spec_name = (c_wchar_p * len(file_types))()
        for i, (name, spec) in enumerate(file_types):
            comdlg_filter_spec[i] = spec
            comdlg_filter_spec_name[i] = name
        file_open_dialog.contents.lpVtbl.contents.SetFileTypes(file_open_dialog, len(file_types), comdlg_filter_spec)

    # Set default extension
    if default_extension:
        file_open_dialog.contents.lpVtbl.contents.SetDefaultExtension(file_open_dialog, default_extension)

    # Set title
    if title:
        file_open_dialog.contents.lpVtbl.contents.SetTitle(file_open_dialog, title)

    # Set OK button label
    if ok_button_label:
        file_open_dialog.contents.lpVtbl.contents.SetOkButtonLabel(file_open_dialog, ok_button_label)

    # Set file name label
    if file_name_label:
        file_open_dialog.contents.lpVtbl.contents.SetFileNameLabel(file_open_dialog, file_name_label)

    # Set default folder
    if default_folder:
        shell_item = IShellItem.from_path(default_folder)
        hr = file_open_dialog.contents.lpVtbl.contents.SetFolder(file_open_dialog, shell_item)
        if hr != S_OK:
            print_hresult(hr)
        # Not sure why this exists since SetFolder works fine. SetDefaultFolder seems broken.
        hr = file_open_dialog.contents.lpVtbl.contents.SetDefaultFolder(file_open_dialog, shell_item)
        if hr != S_OK:
            print_hresult(hr)

    # Show the dialog and collect results
    hr = file_open_dialog.contents.lpVtbl.contents.Show(file_open_dialog, None)
    chosen_files: list[str] | None = None
    if hr == S_OK:
        item_array_ptr = POINTER(IShellItemArray)()
        hr = file_open_dialog.contents.lpVtbl.contents.GetResults(file_open_dialog, byref(item_array_ptr))
        if hr != S_OK:
            raise OSError(f"GetResults failed! {decode_hresult(hr)}")
        chosen_files = process_selected_items(item_array_ptr)
    else:
        print("Dialog rejected")
        print_hresult(hr)

    # Clean up
    file_open_dialog.contents.lpVtbl.contents.Release(file_open_dialog)

    # Uninitialize COM library
    windll.ole32.CoUninitialize()

    return [] if chosen_files is None else chosen_files


def open_file_dialog(
    title: str | None = "Open File",
    default_folder: str | None = None,
    file_types: list[tuple[str, str]] | None = None,
    default_extension: str | None = None,
    *,
    allow_multiple_selection: bool = False,
    add_to_recent: bool = True,
    show_hidden_files: bool = False,
    no_change_dir: bool = False,
    open_actual_file: bool = True,
    hide_mru_places: bool = False,
    hide_pinned_places: bool = False,
    share_aware: bool = False
) -> list[str] | None:
    options = 0x00001000 | 0x00002000 | 0x00008000  # Default: FOS_FILEMUSTEXIST, FOS_PATHMUSTEXIST, FOS_FORCEFILESYSTEM
    if allow_multiple_selection:
        options |= 0x00000200
    if not add_to_recent:
        options |= 0x20000000
    if show_hidden_files:
        options |= 0x10000000
    if no_change_dir:
        options |= 0x00010000
    if not open_actual_file:
        options &= ~0x10000000
    if hide_mru_places:
        options |= 0x00020000
    if hide_pinned_places:
        options |= 0x00040000
    if share_aware:
        options |= 0x00400000
    return configure_file_dialog(title, options, default_folder, "Open", None, file_types, default_extension)


def save_file_dialog(
    title: str | None = "Save File",
    default_folder: str | None = None,
    file_types: list[tuple[str, str]] | None = None,
    default_extension: str | None = None,
    *,
    confirm_overwrite: bool = True,
    add_to_recent: bool = True,
    show_hidden_files: bool = False,
    no_change_dir: bool = False,
    save_actual_file: bool = True,
    hide_mru_places: bool = False,
    hide_pinned_places: bool = False,
    share_aware: bool = False
) -> list[str] | None:
    FOS_PATHMUSTEXIST = 0x00000800
    FOS_FILEMUSTEXIST = 0x00001000
    FOS_OVERWRITEPROMPT = 0x00000002
    options = FOS_PATHMUSTEXIST | FOS_OVERWRITEPROMPT

    if not add_to_recent:
        FOS_DONTADDTORECENT = 0x02000000
        options |= FOS_DONTADDTORECENT
    if show_hidden_files:
        FOS_FORCESHOWHIDDEN = 0x10000000
        options |= FOS_FORCESHOWHIDDEN
    if no_change_dir:
        FOS_NOCHANGEDIR = 0x00000008
        options |= FOS_NOCHANGEDIR
    if hide_mru_places:
        FOS_HIDEMRUPLACES = 0x00400000
        options |= FOS_HIDEMRUPLACES
    if hide_pinned_places:
        FOS_HIDEPINNEDPLACES = 0x00200000
        options |= FOS_HIDEPINNEDPLACES
    if not confirm_overwrite:
        options &= ~FOS_OVERWRITEPROMPT
    if share_aware:
        FOS_SHAREAWARE = 0x00004000
        options |= FOS_SHAREAWARE
    return configure_file_dialog(title, options, default_folder, "Save", None, file_types, default_extension)


def open_folder_dialog(
    title: str | None = "Select Folder",
    default_folder: str | None = None,
    *,
    allow_multiple_selection: bool = False,
    add_to_recent: bool = True,
    hide_mru_places: bool = False,
    hide_pinned_places: bool = False,
    no_change_dir: bool = False,
    share_aware: bool = False
) -> list[str] | None:
    options = 0x00000020 | 0x00002000  # Default: FOS_PICKFOLDERS, FOS_PATHMUSTEXIST
    if allow_multiple_selection:
        options |= 0x00000200
    if not add_to_recent:
        options |= 0x20000000
    if hide_mru_places:
        options |= 0x00020000
    if hide_pinned_places:
        options |= 0x00040000
    if no_change_dir:
        options |= 0x00010000
    if share_aware:
        options |= 0x00400000
    return configure_file_dialog(title, options, default_folder, "Open")


if __name__ == "__main__":
    handle = Path("ifileopendialog_test_crashdump.bin").open("wb")
    faulthandler.enable(handle, all_threads=True)  # noqa: SIM115
    atexit.register(lambda *args, **kwargs: handle.close())
    print(open_folder_dialog(default_folder=str(Path.cwd())))
    print(open_file_dialog(allow_multiple_selection=True))
    print(save_file_dialog())
    faulthandler.disable()  # noqa: SIM115
