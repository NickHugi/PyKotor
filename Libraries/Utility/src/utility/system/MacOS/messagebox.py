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

libobjc.objc_msgSend_id_bool.restype = cID
libobjc.objc_msgSend_id_bool.argtypes = [cID, SEL, cID, c_bool]

libobjc.objc_msgSend_char.restype = ctypes.c_char_p
libobjc.objc_msgSend_char.argtypes = [cID, SEL]

# Define Objective-C constants
NSAlert = libobjc.objc_getClass(b"NSAlert")
NSString = libobjc.objc_getClass(b"NSString")
NSApplication = libobjc.objc_getClass(b"NSApplication")
NSTextField = libobjc.objc_getClass(b"NSTextField")

# Define NSAlert style constants
NSAlertStyle = {
    "NSAlertStyleWarning": 0,
    "NSAlertStyleInformational": 1,
    "NSAlertStyleCritical": 2,
}

# Utility function to convert Python string to NSString
def NSString_from_str(string):
    return libobjc.objc_msgSend_id(NSString, libobjc.sel_registerName(b"stringWithUTF8String:"), c_char_p(string.encode("utf-8")))

# Utility function to convert NSString to Python string
def str_from_NSString(nsstring):
    utf8_string = libobjc.objc_msgSend(nsstring, libobjc.sel_registerName(b"UTF8String"))
    return ctypes.string_at(utf8_string).decode("utf-8")

# Function to show a message box
def show_message_box(title: str, message: str, style: str):
    # Initialize the app and create the alert
    app = libobjc.objc_msgSend(NSApplication, libobjc.sel_registerName(b"sharedApplication"))
    alert = libobjc.objc_msgSend(NSAlert, libobjc.sel_registerName(b"new"))

    # Set the alert properties
    title_nsstring = NSString_from_str(title)
    message_nsstring = NSString_from_str(message)
    libobjc.objc_msgSend_id(alert, libobjc.sel_registerName(b"setMessageText:"), title_nsstring)
    libobjc.objc_msgSend_id(alert, libobjc.sel_registerName(b"setInformativeText:"), message_nsstring)
    libobjc.objc_msgSend(alert, libobjc.sel_registerName(b"setAlertStyle:"), NSAlertStyle[style])

    # Display the alert
    libobjc.objc_msgSend(alert, libobjc.sel_registerName(b"runModal"))

# Function to show an error message box
def show_error_message_box(title: str, message: str):
    show_message_box(title, message, "NSAlertStyleCritical")

# Function to show a warning message box
def show_warning_message_box(title: str, message: str):
    show_message_box(title, message, "NSAlertStyleWarning")

# Function to show an informational message box
def show_info_message_box(title: str, message: str):
    show_message_box(title, message, "NSAlertStyleInformational")

# Function to show an input dialog
def show_input_dialog(title: str, message: str) -> str:
    # Initialize the app and create the alert
    app = libobjc.objc_msgSend(NSApplication, libobjc.sel_registerName(b"sharedApplication"))
    alert = libobjc.objc_msgSend(NSAlert, libobjc.sel_registerName(b"new"))

    # Set the alert properties
    title_nsstring = NSString_from_str(title)
    message_nsstring = NSString_from_str(message)
    libobjc.objc_msgSend_id(alert, libobjc.sel_registerName(b"setMessageText:"), title_nsstring)
    libobjc.objc_msgSend_id(alert, libobjc.sel_registerName(b"setInformativeText:"), message_nsstring)
    libobjc.objc_msgSend(alert, libobjc.sel_registerName(b"setAlertStyle:"), NSAlertStyle["NSAlertStyleInformational"])

    # Add text input field
    input_field = libobjc.objc_msgSend(NSTextField, libobjc.sel_registerName(b"alloc"))
    input_field = libobjc.objc_msgSend(input_field, libobjc.sel_registerName(b"initWithFrame:"), ctypes.c_void_p(0), ctypes.c_void_p(0), ctypes.c_void_p(200), ctypes.c_void_p(24))
    libobjc.objc_msgSend(alert, libobjc.sel_registerName(b"setAccessoryView:"), input_field)

    # Add OK and Cancel buttons
    ok_button = NSString_from_str("OK")
    cancel_button = NSString_from_str("Cancel")
    libobjc.objc_msgSend(alert, libobjc.sel_registerName(b"addButtonWithTitle:"), ok_button)
    libobjc.objc_msgSend(alert, libobjc.sel_registerName(b"addButtonWithTitle:"), cancel_button)

    # Display the alert and get the response
    response = libobjc.objc_msgSend_uint(alert, libobjc.sel_registerName(b"runModal"))

    # Process the result
    if response == 1000:  # NSAlertFirstButtonReturn
        result_nsstring = libobjc.objc_msgSend(input_field, libobjc.sel_registerName(b"stringValue"))
        result = str_from_NSString(result_nsstring)
        return result

    return ""

# Example usage
if __name__ == "__main__":
    show_error_message_box("Error", "An unexpected error occurred.")
    show_warning_message_box("Warning", "This action may cause data loss.")
    show_info_message_box("Information", "This is an informational message.")
    user_input = show_input_dialog("Input Required", "Please enter your name:")
    print("User Input:", user_input)
