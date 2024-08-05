from __future__ import annotations

import platform


def unix_open_file_browser(
    title: str = "Select the target file.",
    file_types: list | None = None,
) -> list[str] | None:
    if platform.system() == "Darwin":
        from utility.system.MacOS.file_folder_browser import open_file_dialog
        return open_file_dialog(title, file_types)
    if platform.system() == "Linux":
        from utility.system.Linux.file_browser_dialogs import open_file_dialog
        result = open_file_dialog(title, file_types)
        if not result:
            return []
        if isinstance(result, str):
            return [result]
        return result
    return None


def unix_open_folder_browser(
    title: str = "Select the target folder.",
) -> list[str] | None:
    if platform.system() == "Darwin":
        from utility.system.MacOS.file_folder_browser import open_folder_dialog
        return open_folder_dialog(title=title)
    if platform.system() == "Linux":
        from utility.system.Linux.file_browser_dialogs import open_folder_dialog
        result = open_folder_dialog(title=title)
        if not result:
            return []
        if isinstance(result, str):
            return [result]
        return result
    return None


def save_file_dialog(
    title: str = "Save the file.",
    default_name: str = "Untitled",
    file_types: list | None = None,
) -> str | None:
    if platform.system() == "Darwin":
        from utility.system.MacOS.file_folder_browser import save_file_dialog
        return save_file_dialog(title=title, default_name=default_name, file_types=file_types)
    if platform.system() == "Linux":
        from utility.system.Linux.file_browser_dialogs import save_file_dialog
        result = save_file_dialog(title=title, file_types=file_types)
        if not result:
            return None
        return result
    return None
