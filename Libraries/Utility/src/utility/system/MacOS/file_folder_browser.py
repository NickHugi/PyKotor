# The following code is completely boilerplate and untested. Requires finding a mac user to do testing.

from __future__ import annotations

import ctypes

from ctypes import c_bool, c_char_p, c_uint, c_void_p
from ctypes.util import find_library

# Load the Cocoa framework
libobjc = ctypes.cdll.LoadLibrary(find_library("objc"))
libAppKit = ctypes.cdll.LoadLibrary(find_library("AppKit"))

# Define basic Objective-C types
cID = c_void_p
SEL = c_void_p
IMP = c_void_p
Class = c_void_p

# Define utility functions for working with Objective-C
libobjc.objc_getClass.restype = Class
libobjc.objc_getClass.argtypes = [c_char_p]

libobjc.sel_registerName.restype = SEL
libobjc.sel_registerName.argtypes = [c_char_p]

libobjc.objc_msgSend.restype = cID
libobjc.objc_msgSend.argtypes = [cID, SEL]

libobjc.objc_msgSend_bool.restype = c_bool
libobjc.objc_msgSend_bool.argtypes = [cID, SEL, c_bool]

libobjc.objc_msgSend_uint.restype = c_uint
libobjc.objc_msgSend_uint.argtypes = [cID, SEL]

libobjc.objc_msgSend_id.restype = cID
libobjc.objc_msgSend_id.argtypes = [cID, SEL, cID]

libobjc.objc_msgSend_id_uint.restype = cID
libobjc.objc_msgSend_id_uint.argtypes = [cID, SEL, cID, c_uint]

libobjc.objc_msgSend_id_bool.restype = cID
libobjc.objc_msgSend_id_bool.argtypes = [cID, SEL, cID, c_bool]

# Define Objective-C constants
NSOpenPanel = libobjc.objc_getClass(b"NSOpenPanel")
NSSavePanel = libobjc.objc_getClass(b"NSSavePanel")
NSURL = libobjc.objc_getClass(b"NSURL")
NSString = libobjc.objc_getClass(b"NSString")
NSApplication = libobjc.objc_getClass(b"NSApplication")

# Utility function to convert Python string to NSString
def NSString_from_str(string):
    return libobjc.objc_msgSend_id(NSString, libobjc.sel_registerName(b"stringWithUTF8String:"), c_char_p(string.encode("utf-8")))

# Utility function to convert NSURL to Python string
def str_from_NSURL(nsurl):
    utf8_string = libobjc.objc_msgSend(nsurl, libobjc.sel_registerName(b"absoluteString"))
    return ctypes.string_at(libobjc.objc_msgSend(utf8_string, libobjc.sel_registerName(b"UTF8String"))).decode("utf-8")

# Define the main function to create and display a file open dialog
def browse_files(title: str = "Select File(s)", *, allow_multiple: bool = False, show_hidden: bool = False) -> list[str]:
    # Initialize the app and create the open panel
    app = libobjc.objc_msgSend(NSApplication, libobjc.sel_registerName(b"sharedApplication"))
    panel = libobjc.objc_msgSend(NSOpenPanel, libobjc.sel_registerName(b"openPanel"))

    # Set the panel properties
    if title:
        title_nsstring = NSString_from_str(title)
        libobjc.objc_msgSend_id(panel, libobjc.sel_registerName(b"setTitle:"), title_nsstring)

    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setAllowsMultipleSelection:"), c_bool(allow_multiple))
    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setCanChooseFiles:"), c_bool(True))
    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setCanChooseDirectories:"), c_bool(False))
    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setShowsHiddenFiles:"), c_bool(show_hidden))

    # Display the panel
    response = libobjc.objc_msgSend_uint(panel, libobjc.sel_registerName(b"runModal"))

    # Process the result
    if response == 1:  # NSModalResponseOK
        urls = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"URLs"))
        count = libobjc.objc_msgSend_uint(urls, libobjc.sel_registerName(b"count"))

        file_paths = []
        for i in range(count):
            nsurl = libobjc.objc_msgSend_id_uint(urls, libobjc.sel_registerName(b"objectAtIndex:"), i)
            file_paths.append(str_from_NSURL(nsurl))

        return file_paths

    return []

# Define the function to create and display a folder open dialog
def browse_folders(title: str = "Select Folder", *, allow_multiple: bool = False, show_hidden: bool = False) -> list[str]:
    # Initialize the app and create the open panel
    app = libobjc.objc_msgSend(NSApplication, libobjc.sel_registerName(b"sharedApplication"))
    panel = libobjc.objc_msgSend(NSOpenPanel, libobjc.sel_registerName(b"openPanel"))

    # Set the panel properties
    if title:
        title_nsstring = NSString_from_str(title)
        libobjc.objc_msgSend_id(panel, libobjc.sel_registerName(b"setTitle:"), title_nsstring)

    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setAllowsMultipleSelection:"), c_bool(allow_multiple))
    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setCanChooseFiles:"), c_bool(False))
    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setCanChooseDirectories:"), c_bool(True))
    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setShowsHiddenFiles:"), c_bool(show_hidden))

    # Display the panel
    response = libobjc.objc_msgSend_uint(panel, libobjc.sel_registerName(b"runModal"))

    # Process the result
    if response == 1:  # NSModalResponseOK
        urls = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"URLs"))
        count = libobjc.objc_msgSend_uint(urls, libobjc.sel_registerName(b"count"))

        folder_paths = []
        for i in range(count):
            nsurl = libobjc.objc_msgSend_id_uint(urls, libobjc.sel_registerName(b"objectAtIndex:"), i)
            folder_paths.append(str_from_NSURL(nsurl))

        return folder_paths

    return []

# Define the function to create and display a save file dialog
def save_file(title: str = "Save File", default_name: str = "Untitled", show_hidden: bool = False) -> str:
    # Initialize the app and create the save panel
    app = libobjc.objc_msgSend(NSApplication, libobjc.sel_registerName(b"sharedApplication"))
    panel = libobjc.objc_msgSend(NSSavePanel, libobjc.sel_registerName(b"savePanel"))

    # Set the panel properties
    if title:
        title_nsstring = NSString_from_str(title)
        libobjc.objc_msgSend_id(panel, libobjc.sel_registerName(b"setTitle:"), title_nsstring)

    if default_name:
        default_name_nsstring = NSString_from_str(default_name)
        libobjc.objc_msgSend_id(panel, libobjc.sel_registerName(b"setNameFieldStringValue:"), default_name_nsstring)

    libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setShowsHiddenFiles:"), c_bool(show_hidden))

    # Display the panel
    response = libobjc.objc_msgSend_uint(panel, libobjc.sel_registerName(b"runModal"))

    # Process the result
    if response == 1:  # NSModalResponseOK
        nsurl = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"URL"))
        file_path = str_from_NSURL(nsurl)
        return file_path

    return ""

# Example usage
if __name__ == "__main__":
    selected_files = browse_files()
    print("Selected files:", selected_files)

    selected_folders = browse_folders()
    print("Selected folders:", selected_folders)

    saved_file = save_file()
    print("Saved file:", saved_file)
