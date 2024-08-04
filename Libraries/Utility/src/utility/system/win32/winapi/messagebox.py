from __future__ import annotations

from ctypes import WINFUNCTYPE, c_int, c_wchar_p, windll
from ctypes.wintypes import LPARAM, WPARAM

MB_OK = 0x0
MB_OKCANCEL = 0x1
MB_ABORTRETRYIGNORE = 0x2
MB_YESNOCANCEL = 0x3
MB_YESNO = 0x4
MB_RETRYCANCEL = 0x5
MB_CANCELTRYCONTINUE = 0x6

MB_ICONHAND = 0x10
MB_ICONQUESTION = 0x20
MB_ICONEXCLAMATION = 0x30
MB_ICONASTERISK = 0x40

MB_DEFBUTTON1 = 0x0
MB_DEFBUTTON2 = 0x100
MB_DEFBUTTON3 = 0x200
MB_DEFBUTTON4 = 0x300

MB_APPLMODAL = 0x0
MB_SYSTEMMODAL = 0x1000
MB_TASKMODAL = 0x2000

MB_ICONERROR = MB_ICONHAND
MB_ICONWARNING = MB_ICONEXCLAMATION
MB_ICONINFORMATION = MB_ICONASTERISK

MB_RIGHT = 0x800
MB_RTLREADING = 0x1000

IDOK = 1
IDCANCEL = 2
IDABORT = 3
IDRETRY = 4
IDIGNORE = 5
IDYES = 6
IDNO = 7
IDTRYAGAIN = 10
IDCONTINUE = 11

windll.user32.MessageBoxW.argtypes = [c_int, c_wchar_p, c_wchar_p, c_int]
windll.user32.MessageBoxW.restype = c_int

CBTProc = WINFUNCTYPE(c_int, c_int, WPARAM, LPARAM)
SetWindowsHookExW = windll.user32.SetWindowsHookExW
UnhookWindowsHookEx = windll.user32.UnhookWindowsHookEx
CallNextHookEx = windll.user32.CallNextHookEx
GetWindowRect = windll.user32.GetWindowRect
MoveWindow = windll.user32.MoveWindow


def windows_message_box(  # noqa: PLR0913
    message: str,
    title: str,
    box_type: int = MB_OK,
    icon: int = 0,
    default_button: int = MB_DEFBUTTON1,
    modality: int = MB_APPLMODAL,
    options: int = 0,
    detailed_text: str | None = None,
) -> int:
    """Create a message box with specified parameters.

    :param message: The message to be displayed.
    :param title: The title of the message box.
    :param box_type: The type of the message box (e.g., MB_OK, MB_YESNO).
    :param icon: The icon to be displayed (e.g., MB_ICONQUESTION).
    :param default_button: The default button (e.g., MB_DEFBUTTON1).
    :param modality: The modality of the message box (e.g., MB_APPLMODAL).
    :param options: Additional options (e.g., MB_RIGHT).
    :param detailed_text: Additional detailed text to be displayed.
    :return: The response from the message box.
    """
    if detailed_text:
        message = f"{message}\n\n{detailed_text}"

    style = box_type | icon | default_button | modality | options
    result = windll.user32.MessageBoxW(0, message, title, style)
    return result


def show_ok_message_box(message: str, title: str, detailed_text: str | None = None) -> int:
    return windows_message_box(message, title, MB_OK, MB_ICONINFORMATION, detailed_text=detailed_text)


def show_yes_no_message_box(message: str, title: str, detailed_text: str | None = None) -> int:
    return windows_message_box(message, title, MB_YESNO, MB_ICONQUESTION, detailed_text=detailed_text)


def show_retry_cancel_message_box(message: str, title: str, detailed_text: str | None = None) -> int:
    return windows_message_box(message, title, MB_RETRYCANCEL, MB_ICONWARNING, detailed_text=detailed_text)


def show_error_message_box(message: str, title: str, detailed_text: str | None = None) -> int:
    return windows_message_box(message, title, MB_OK, MB_ICONERROR, detailed_text=detailed_text)


def show_warning_message_box(message: str, title: str, detailed_text: str | None = None) -> int:
    return windows_message_box(message, title, MB_OK, MB_ICONWARNING, detailed_text=detailed_text)


if __name__ == "__main__":
    response = windows_message_box(
        "Do you want to save changes?",
        "Save Changes",
        box_type=MB_YESNOCANCEL,
        icon=MB_ICONQUESTION,
        default_button=MB_DEFBUTTON2,
        modality=MB_SYSTEMMODAL,
        options=MB_RTLREADING,
        detailed_text="This will overwrite the existing file.",
    )
    print(f"Response: {response}")  # 6=YES, 7=NO, 2=CANCEL/X button.

    response = show_ok_message_box("Operation completed successfully.", "Success")
    if response == IDOK:
        print("User clicked OK")

    response = show_yes_no_message_box("Do you want to continue?", "Continue?", detailed_text="This action cannot be undone.")
    if response == IDYES:
        print("User chose Yes")
    elif response == IDNO:
        print("User chose No")

    response = show_retry_cancel_message_box("Operation failed. Retry?", "Error", detailed_text="Make sure the file is accessible and try again.")
    if response == IDRETRY:
        print("User chose Retry")
    elif response == IDCANCEL:
        print("User chose Cancel")

    response = show_error_message_box("An unexpected error occurred.", "Error", detailed_text="Please contact support with the error code 0x1234.")
    if response == IDOK:
        print("User acknowledged the error")

    response = show_warning_message_box("This action may cause data loss.", "Warning", detailed_text="Ensure you have backed up your data.")
    if response == IDOK:
        print("User acknowledged the warning")
