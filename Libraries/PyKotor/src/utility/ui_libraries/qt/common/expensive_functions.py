from __future__ import annotations

import mimetypes
import os
import platform
import shlex
import shutil
import stat
import struct
import subprocess
import tarfile
import time
import zipfile

from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import send2trash

from loggerplus import RobustLogger
from qtpy.QtWidgets import QFileDialog
from typing_extensions import Literal

from utility.misc import generate_hash, get_file_attributes
from utility.system.os_helper import get_size_on_disk
from utility.ui_libraries.qt.common.filesystem.file_properties_dialog import FileProperties

if TYPE_CHECKING:
    from collections.abc import Sequence
    from ctypes import _CData
    from multiprocessing import Queue
    from multiprocessing.managers import ValueProxy

    from qtpy.QtWidgets import QWidget
    from win32com.client.dynamic import CDispatch  # pyright: ignore[reportMissingImports, reportMissingModuleSource]


logger: RobustLogger = RobustLogger()


T = TypeVar("T")


def handle_operation(
    func: Callable[..., T],
) -> Callable[..., T | None]:
    @wraps(func)
    def wrapper(
        *args: Any,
        progress_queue: Queue[int],
        pause_flag: ValueProxy[bool],
        cancel_flag: ValueProxy[bool],
        **kwargs: Any,
    ) -> T | None:
        if cancel_flag and cancel_flag.value:
            return None

        while pause_flag and pause_flag.value:
            if cancel_flag and cancel_flag.value:
                return None
            time.sleep(0.1)

        result: T = func(*args, **kwargs)

        if not progress_queue:
            return result

        progress_queue.put(100)

        return result

    return wrapper


def handle_multiple(
    func: Callable[..., T],
) -> Callable[..., list[T | None]]:
    @wraps(func)
    def wrapper(
        cls: type[FileOperations],
        paths: list[Path],
        *args,
        progress_queue: Queue[int],
        pause_flag: ValueProxy[bool],
        cancel_flag: ValueProxy[bool],
        **kwargs: Any,
    ) -> list[T | None]:
        total_items: int = len(paths)
        results: list[T | None] = []
        for i, path in enumerate(paths, 1):
            if cancel_flag and cancel_flag.value:
                return results

            while pause_flag and pause_flag.value:
                if cancel_flag and cancel_flag.value:
                    return results
                time.sleep(0.1)

            result: T | None = func(cls, path, *args, **kwargs)
            results.append(result)

            if not progress_queue:
                continue

            progress_queue.put(int((i / total_items) * 100))

        return results

    return wrapper


class FileOperations:
    """Class dedicated to file operations.

    This class is for offloading computationally or otherwise expensive functions to child processes.
    All functions executed here will be in a child process executed through ProcessPoolExecutor!
    This means QApplication/qt is not available here! Do preparation work beforehand and offload the
    computationally expensive logic here!

    Don't define things like e.g. open_in_new_window or open_in_new_tab as those are not tasks that can be offloaded here.
    """

    @classmethod
    @handle_operation
    def open_containing_folder(
        cls,
        file_path: Path,
    ) -> None:
        assert isinstance(file_path, Path)
        system: str = platform.system()

        if system == "Windows":
            from utility.system.os_helper import win_get_system32_dir

            explorer_path: Path = win_get_system32_dir().parent / "explorer.exe"
            cmd: list[str] = [str(explorer_path), "/select,", str(file_path)]
            subprocess.run(cmd, check=True)  # noqa: S603
        elif system == "Darwin":  # macOS
            script_reveal: str = f'tell application "Finder" to reveal POSIX file "{file_path}"'
            script_activate = 'tell application "Finder" to activate'
            subprocess.run(["osascript", "-e", script_reveal], check=False)  # noqa: S603, S607
            subprocess.run(["osascript", "-e", script_activate], check=False)  # noqa: S603, S607
        else:
            file_managers: list[list[str]] = [
                ["xdg-open", str(file_path.parent)],  # Generic fallback
                ["nautilus", "--select", str(file_path)],  # GNOME
                ["dolphin", "--select", str(file_path)],  # KDE
                ["nemo", "--no-desktop", str(file_path)],  # Cinnamon
                ["pcmanfm", str(file_path)],  # LXDE/LXQt
                ["thunar", str(file_path)],  # XFCE
                ["caja", str(file_path)],  # MATE
                ["krusader", str(file_path)],  # KDE twin-panel
                ["rox", str(file_path)],  # ROX desktop
                ["doublecmd", str(file_path)],  # Dual-panel
                ["spacefm", str(file_path)],  # Multi-panel
                ["qtfm", str(file_path)],  # Qt-based
                ["lffm", str(file_path)],  # Simple & fast
                ["xplore", str(file_path)],  # Tree view
                ["lf", str(file_path)],  # Terminal-based
                ["nnn", str(file_path)],  # Minimalist
                ["vifm", str(file_path)],  # Vi-like
                ["ranger", str(file_path)],  # Vi-like
                ["mc", str(file_path)],  # Text-mode
            ]

            for command in file_managers:
                try:
                    subprocess.run(command, check=True)  # noqa: S603
                except subprocess.CalledProcessError:  # noqa: PERF203, S112
                    continue
                else:
                    return

        # Fallback to opening the parent directory
        subprocess.run(["xdg-open", str(file_path.parent)], check=True)  # noqa: S603, S607

    @classmethod
    @handle_multiple
    def read_file(
        cls,
        file_path: Path,
    ) -> str:
        return file_path.read_text()

    @classmethod
    @handle_multiple
    def create_file(
        cls,
        file_path: Path,
        content: str,
    ) -> None:
        file_path.write_text(content)

    @classmethod
    @handle_multiple
    def open_dir(
        cls,
        dir_path: Path,
    ) -> None:
        if platform.system() == "Windows":
            from utility.system.os_helper import win_get_system32_dir

            explorer_path: Path = win_get_system32_dir().parent / "explorer.exe"
            cmd: list[str] = [str(explorer_path), "/select,", str(dir_path)]
            subprocess.run(cmd, check=True)  # noqa: S607, S603
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(dir_path)], check=True)  # noqa: S607, S603
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", str(dir_path)], check=True)  # noqa: S607, S603

    @classmethod
    @handle_multiple
    def open_with(
        cls,
        file_path: Path,
    ) -> None:
        if platform.system() == "Windows":
            from utility.system.os_helper import win_get_system32_dir

            cmd: list[str] = shlex.split(f'"{win_get_system32_dir() / "rundll32.exe"}" shell32.dll,OpenAs_RunDLL "{file_path}"')
            subprocess.run(cmd, check=True)  # noqa: S603
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", "-a", file_path], check=True)  # noqa: S607, S603
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", "--choose-application", file_path], check=True)  # noqa: S607, S603

    @classmethod
    @handle_multiple
    def delete_item(
        cls,
        path: Path,
    ) -> None:
        if not path.exists():
            return
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)

    @classmethod
    @handle_multiple
    def rename_item(
        cls,
        old_path: Path,
        new_name: str,
    ) -> None:
        new_path: Path = old_path.parent / new_name
        old_path.rename(new_path)

    @classmethod
    @handle_multiple
    def create_new_folder(
        cls,
        parent_path: Path,
        name: str,
    ) -> None:
        new_folder: Path = parent_path / name
        new_folder.mkdir(parents=True, exist_ok=True)

    @classmethod
    @handle_multiple
    def copy_item(
        cls,
        source: Path,
        destination: Path,
    ) -> None:
        if source.is_file():
            shutil.copy2(source, destination)
        elif source.is_dir():
            shutil.copytree(source, destination / source.name)

    @classmethod
    @handle_multiple
    def move_item(
        cls,
        source: Path,
        destination: Path,
    ) -> None:
        shutil.move(str(source), str(destination))

    @classmethod
    @handle_multiple
    def get_properties(
        cls,
        path: Path,
    ) -> FileProperties:
        info: os.stat_result = path.stat()

        is_symlink: bool = path.is_symlink()
        symlink_target: str = os.readlink(path) if is_symlink else ""  # noqa: PTH115

        if os.name == "posix":
            try:
                import pwd

                owner = pwd.getpwuid(info.st_uid).pw_name
            except KeyError:
                owner = str(info.st_uid)

            try:
                import grp

                group = grp.getgrgid(info.st_gid).gr_name
            except KeyError:
                group = str(info.st_gid)
        elif os.name == "nt":
            import ctypes

            from ctypes import wintypes

            # Define necessary structures and functions
            class SECURITY_DESCRIPTOR(ctypes.Structure):  # noqa: N801
                _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [("buf", wintypes.BYTE * 256)]  # noqa: RUF012

            class ACL(ctypes.Structure):
                _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [("buf", wintypes.BYTE * 256)]  # noqa: RUF012

            GetFileSecurity = ctypes.windll.advapi32.GetFileSecurityW
            GetSecurityDescriptorOwner = ctypes.windll.advapi32.GetSecurityDescriptorOwner
            LookupAccountSid = ctypes.windll.advapi32.LookupAccountSidW

            # Get file security information
            sd = SECURITY_DESCRIPTOR()
            owner_sid = ctypes.c_void_p()
            GetFileSecurity(str(path), 1, ctypes.byref(sd), 256, ctypes.byref(ctypes.c_uint32()))  # noqa: S113
            GetSecurityDescriptorOwner(ctypes.byref(sd), ctypes.byref(owner_sid), ctypes.byref(ctypes.c_bool()))

            # Look up owner name
            owner_name = ctypes.create_unicode_buffer(256)
            owner_name_size = wintypes.DWORD(256)
            domain_name = ctypes.create_unicode_buffer(256)
            domain_name_size = wintypes.DWORD(256)
            sid_type = wintypes.DWORD()
            LookupAccountSid(None, owner_sid, owner_name, ctypes.byref(owner_name_size), domain_name, ctypes.byref(domain_name_size), ctypes.byref(sid_type))

            owner: str = owner_name.value
            group: str = domain_name.value

        attributes: dict[str, bool] = get_file_attributes(path)

        return FileProperties(
            name=path.name,
            path=str(path.absolute()),
            type="Directory" if path.is_dir() else "File",
            size=cls.format_size(info.st_size),
            size_on_disk=cls.format_size(get_size_on_disk(path, info)),
            created=cls.format_time(info.st_ctime),
            modified=cls.format_time(info.st_mtime),
            accessed=cls.format_time(info.st_atime),
            mime_type=mimetypes.guess_type(path)[0] or "Unknown",
            owner=owner,
            group=group,
            permissions=stat.filemode(info.st_mode),
            inode=info.st_ino,
            num_hard_links=info.st_nlink,
            device=info.st_dev,
            is_symlink=is_symlink,
            symlink_target=symlink_target,
            md5=generate_hash(path, "md5"),
            sha1=generate_hash(path, "sha1"),
            sha256=generate_hash(path, "sha256"),
            is_hidden=attributes["is_hidden"],
            is_system=attributes["is_system"],
            is_archive=attributes["is_archive"],
            is_compressed=attributes["is_compressed"],
            is_encrypted=attributes["is_encrypted"],
            is_readonly=attributes["is_readonly"],
            is_temporary=attributes["is_temporary"],
            extension=path.suffix,
        )

    @classmethod
    @handle_multiple
    def take_ownership_item(
        cls,
        path: Path,
    ) -> None:
        # This is a placeholder. The actual implementation would depend on your OS and permissions.
        print(f"Taking ownership of {path}")

    @classmethod
    @handle_multiple
    def create_shortcut(
        cls,
        source_path: Path,
        shortcut_path: Path,
    ) -> None:
        def get_unique_shortcut_path(
            path: Path,
        ) -> Path:
            base: str = path.stem
            ext: str = path.suffix
            counter = 1
            while path.exists():
                path = path.with_name(f"{base} ({counter}){ext}")
                counter += 1
            return path

        if platform.system() == "Windows":
            shortcut_path = get_unique_shortcut_path(shortcut_path.with_suffix(".lnk"))
            try:
                import win32com.client  # pyright: ignore[reportMissingModuleSource]

                shell: CDispatch = win32com.client.Dispatch("WScript.Shell")
                shortcut: Any = shell.CreateShortCut(str(shortcut_path))
                shortcut.Targetpath = str(source_path)
                shortcut.save()
            except ImportError:
                try:
                    from comtypes.client import CreateObject  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

                    shell = CreateObject("WScript.Shell")
                    shortcut = shell.CreateShortCut(str(shortcut_path))
                    shortcut.TargetPath = str(source_path)
                    shortcut.save()
                except ImportError:
                    target: bytes = str(Path(source_path).resolve()).encode("utf-16le")
                    header: bytes = b"\x4c\x00\x00\x00\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46"
                    flags: int = 0x00000001  # FILE_ATTRIBUTE_READONLY
                    file_attributes: bytes = struct.pack("<I", flags)
                    creation_time: bytes = struct.pack("<Q", 0)
                    modification_time: bytes = struct.pack("<Q", 0)
                    access_time: bytes = struct.pack("<Q", 0)
                    file_size: bytes = struct.pack("<I", 0)
                    icon_index: bytes = struct.pack("<I", 0)
                    show_command: bytes = struct.pack("<I", 1)  # SW_SHOWNORMAL
                    hotkey: bytes = struct.pack("<H", 0)
                    reserved: bytes = struct.pack("<H", 0)
                    reserved2: bytes = struct.pack("<Q", 0)
                    terminal_id: bytes = struct.pack("<I", 0)

                    link_flags: bytes = struct.pack("<I", 0x0000001)  # HasLinkTargetIDList
                    link_info_flags: bytes = struct.pack("<I", 0x1 | 0x2)  # VolumeIDAndLocalBasePath
                    local_base_path: bytes = str(source_path).encode("utf-16le") + b"\x00\x00"

                    data: bytes = (
                        header
                        + link_flags
                        + file_attributes
                        + creation_time
                        + access_time
                        + modification_time
                        + file_size
                        + icon_index
                        + show_command
                        + hotkey
                        + reserved
                        + reserved2
                        + terminal_id
                        + struct.pack("<H", len(target) + 2)
                        + target
                        + b"\x00\x00"
                        + link_info_flags
                        + struct.pack("<I", len(local_base_path))
                        + local_base_path
                    )

                    shortcut_path.open("wb").write(data)
        else:
            shortcut_path = get_unique_shortcut_path(shortcut_path)
            os.symlink(source_path, shortcut_path)

    @classmethod
    @handle_multiple
    def open_file(
        cls,
        file_path: Path,
    ) -> None:
        if platform.system() == "Windows":
            os.startfile(file_path)  # noqa: S606
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=True)  # noqa: S607, S603
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", str(file_path)], check=True)  # noqa: S607, S603

    @classmethod
    @handle_multiple
    def open_terminal(
        cls,
        path: Path,
    ) -> None:
        if platform.system() == "Windows":
            from utility.system.os_helper import win_get_system32_dir

            cmd: list[str] = [f'"{win_get_system32_dir() / "cmd.exe"}"', "/k", f"cd /d {path}"]
            subprocess.run(cmd, check=True)  # noqa: S603
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", "-a", "Terminal", path], check=True)  # noqa: S607, S603
        else:  # Linux and other Unix-like
            subprocess.run(["x-terminal-emulator", "--working-directory", path], check=True)  # noqa: S607, S603

    @classmethod
    def compress_items(
        cls,
        paths: list[Path],
        archive_path: Path,
        **kwargs,
    ):
        casefold_name: str = archive_path.name.casefold()
        if casefold_name.endswith(".zip"):
            cls._compress_zip(paths, archive_path, **kwargs)
        elif casefold_name.endswith((".tar", ".tar.gz", ".tgz")):
            cls._compress_tar(paths, archive_path, **kwargs)
        else:
            raise ValueError(f"Unsupported archive format: '{archive_path}'")

    @classmethod
    def _compress_zip(
        cls,
        paths: list[Path],
        archive_path: Path,
        **kwargs,
    ):
        total_size: int = sum(f.stat().st_size for path in paths for f in path.rglob("*") if f.is_file())
        compressed_size: int = 0

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in paths:
                if path is None or not path.exists():
                    continue
                if path.is_file():
                    archive.write(path, arcname=path.name)
                    compressed_size += path.stat().st_size
                elif path.is_dir():
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = Path(root, file)
                            relative_path: Path = file_path.relative_to(path.parent)
                            archive.write(file_path, arcname=relative_path)
                            compressed_size += file_path.stat().st_size

                    progress: int = int((compressed_size / total_size) * 100) if total_size > 0 else 100
                    kwargs["progress_queue"].put(progress)

    @classmethod
    def _compress_tar(
        cls,
        paths: list[Path],
        archive_path: Path,
        **kwargs,
    ):
        total_size: int = sum(f.stat().st_size for path in paths for f in path.rglob("*") if f.is_file())
        compressed_size: int = 0

        mode: Literal["w:gz", "w"] = "w:gz" if archive_path.name.casefold().endswith((".tar.gz", ".tgz")) else "w"
        with tarfile.open(archive_path, mode) as archive:
            for path in paths:
                if path is None or not path.exists():
                    continue
                archive.add(path, arcname=path.name)
                compressed_size += sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

                progress: int = int((compressed_size / total_size) * 100) if total_size > 0 else 100
                kwargs["progress_queue"].put(progress)

    @classmethod
    def extract_items(
        cls,
        archive_path: Path,
        destination_path: Path,
        **kwargs,
    ):
        casefold_name: str = archive_path.name.casefold()
        if casefold_name.endswith(".zip"):
            open_func, mode = zipfile.ZipFile, "r"
        elif casefold_name.endswith((".tar", ".tar.gz", ".tgz")):
            open_func, mode = tarfile.open, "r:*"
        else:
            raise ValueError(f"Unsupported archive format: '{archive_path.name}'")

        with open_func(archive_path, mode) as archive:  # pyright: ignore[reportArgumentType]
            total_items: int = len(archive.namelist() if isinstance(archive, zipfile.ZipFile) else archive.getmembers())
            for i, item in enumerate(archive.namelist() if isinstance(archive, zipfile.ZipFile) else archive.getmembers(), 1):
                item_path = Path(item if isinstance(item, str) else item.name)
                if item_path.is_absolute() or ".." in item_path.parts:
                    continue
                archive.extract(item, path=destination_path)  # pyright: ignore[reportArgumentType]
                kwargs["progress_queue"].put(int((i / total_items) * 100))

    @staticmethod
    def format_size(
        size: float,
    ) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:  # noqa: PLR2004
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @staticmethod
    def format_time(
        timestamp: float,
    ) -> str:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ006

    @classmethod
    @handle_multiple
    def show_properties_windows(
        cls,
        file_path: Path,
    ) -> None:
        import ctypes
        import ctypes.wintypes

        SEE_MASK_NOCLOSEPROCESS: int = 0x00000040
        SEE_MASK_INVOKEIDLIST: int = 0x0000000C

        class SHELLEXECUTEINFO(ctypes.Structure):
            _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = (
                ("cbSize", ctypes.wintypes.DWORD),
                ("fMask", ctypes.c_ulong),
                ("hwnd", ctypes.wintypes.HANDLE),
                ("lpVerb", ctypes.c_char_p),
                ("lpFile", ctypes.c_char_p),
                ("lpParameters", ctypes.c_char_p),
                ("lpDirectory", ctypes.c_char_p),
                ("nShow", ctypes.c_int),
                ("hInstApp", ctypes.wintypes.HINSTANCE),
                ("lpIDList", ctypes.c_void_p),
                ("lpClass", ctypes.c_char_p),
                ("hKeyClass", ctypes.wintypes.HKEY),
                ("dwHotKey", ctypes.wintypes.DWORD),
                ("hIconOrMonitor", ctypes.wintypes.HANDLE),
                ("hProcess", ctypes.wintypes.HANDLE),
            )

        sei = SHELLEXECUTEINFO()
        sei.cbSize = ctypes.sizeof(sei)
        sei.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_INVOKEIDLIST
        sei.lpVerb = b"properties"
        sei.lpFile = str(file_path).encode("utf-8")
        sei.nShow = 1
        ctypes.windll.shell32.ShellExecuteEx(ctypes.byref(sei))

    @classmethod
    @handle_multiple
    def send_to_recycle_bin(
        cls,
        file_path: Path,
    ) -> None:
        send2trash.send2trash(str(file_path))

    @classmethod
    @handle_multiple
    def delete_permanently(
        cls,
        file_path: Path,
    ) -> None:
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            shutil.rmtree(file_path)

    @classmethod
    @handle_multiple
    def save_file(
        cls,
        file_path: Path,
        destination: Path | None = None,
    ) -> None:
        if destination is not None:
            shutil.copy2(file_path, destination)
            return

        # Extract the original filename from the file path
        original_filename: str = file_path.name
        # Open a file dialog to choose the save location
        save_path, _ = QFileDialog.getSaveFileName(None, "Save As", original_filename)
        if not save_path:
            return
        destination = Path(save_path)

        # Copy the file to the destination
        shutil.copy2(file_path, destination)

    @classmethod
    @handle_multiple
    def open_windows_explorer_context_menu(
        cls,
        file_path: Path,
    ) -> None:
        if platform.system() != "Windows":
            return
        from qtpy.QtWidgets import QApplication

        from utility.system.win32.context_menu import windows_context_menu_file

        active_window: QWidget | None = QApplication.activeWindow()
        if active_window is None:
            return
        windows_context_menu_file(file_path, int(active_window.winId()))
