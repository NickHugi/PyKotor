# Rigorously test the string result of each pathlib module.
# The goal isn't really to test pathlib.Path or utility.path, the goal is to determine if there was a breaking change in a python patch release.
from __future__ import annotations

import ctypes
import os
import pathlib
import platform
import subprocess
import sys
import unittest

from ctypes.wintypes import DWORD
from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath
from tempfile import TemporaryDirectory
from unittest import mock

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.tools.path import CaseAwarePath
from utility.system.path import (
    Path as CustomPath,
    PosixPath as CustomPosixPath,
    PurePath as CustomPurePath,
    PurePosixPath as CustomPurePosixPath,
    PureWindowsPath as CustomPureWindowsPath,
    WindowsPath as CustomWindowsPath,
)


def check_path_win_api(path) -> tuple[bool, bool, bool]:
    GetFileAttributes = ctypes.windll.kernel32.GetFileAttributesW
    INVALID_FILE_ATTRIBUTES: int = DWORD(-1).value

    attrs = GetFileAttributes(path)
    if attrs == INVALID_FILE_ATTRIBUTES:
        return False, False, False  # Path does not exist or cannot be accessed

    FILE_ATTRIBUTE_DIRECTORY = 0x10
    is_dir = bool(attrs & FILE_ATTRIBUTE_DIRECTORY)
    is_file: bool = not is_dir  # Simplistic check; may need refinement for special files
    return True, is_file, is_dir

class TestPathlibMixedSlashes(unittest.TestCase):

    def create_and_run_batch_script(self, cmd: list[str], pause_after_command: bool = False):
        with TemporaryDirectory() as tempdir:
            # Ensure the script path is absolute
            script_path = str(Path(tempdir, "temp_script.bat").absolute())

            # Write the commands to a batch file
            with open(script_path, "w") as file:
                for command in cmd:
                    file.write(command + "\n")
                if pause_after_command:
                    file.write("pause\nexit\n")

            # Determine the CMD switch to use
            cmd_switch = "/K" if pause_after_command else "/C"

            # Construct the command to run the batch script with elevated privileges
            run_script_cmd: list[str] = [
                "Powershell",
                "-Command",
                f"Start-Process cmd.exe -ArgumentList '{cmd_switch} \"{script_path}\"' -Verb RunAs -Wait"
            ]

            # Execute the batch script
            subprocess.run(run_script_cmd, check=False)

            # Optionally, delete the batch script after execution
            try:
                os.remove(script_path)
            except Exception:
                ...

    def remove_permissions(self, path_str: str):
        is_file = os.path.isfile(path_str)

        # Define the commands
        combined_commands: list[str] = [
            f'icacls "{path_str}" /reset',
            f'attrib +S +R "{path_str}"',
            f'icacls "{path_str}" /inheritance:r',
            f'icacls "{path_str}" /deny Everyone:(F)'
        ]

        # Create and run the batch script
        self.create_and_run_batch_script(combined_commands)

        # self.run_command(isfile_or_dir_args(["icacls", path_str, "/setowner", "dummy_user"]))
        # self.run_command(isfile_or_dir_args(["icacls", path_str, "/deny", "dummy_user:(D,WDAC,WO)"]))
        # self.run_command(["cipher", "/e", path_str])

    @unittest.skipIf(os.name == "posix", "This test can only run on Windows.")
    def test_gain_file_access(self):  # sourcery skip: extract-method
        test_file = Path("this file has no permissions.txt").absolute()
        try:
            with test_file.open("w") as f:
                f.write("test")
        except PermissionError as e:
            ...
            # raise e
        self.remove_permissions(str(test_file))
        try:

            # Remove all permissions from the file

            test_filepath = CustomPath(test_file)
            # self.assertFalse(os.access(test_file, os.W_OK), "Write access should be denied")  # this only checks attrs on windows
            # self.assertFalse(os.access(test_file, os.R_OK), "Read access should be denied")   # this only checks attrs on windows

            self.assertEqual(test_filepath.has_access(mode=0o1), True)  # this is a bug with os.access
            self.assertEqual(test_filepath.has_access(mode=0o7), False)

            self.assertEqual(test_filepath.gain_access(mode=0o6), True)
            self.assertEqual(test_filepath.has_access(mode=0o6), True)

            # self.assertFalse(os.access(test_file, os.R_OK), "Read access should be denied")   # this only checks attrs on windows
            # self.assertFalse(os.access(test_file, os.W_OK), "Write access should be denied")  # this only checks attrs on windows
        finally:
            # Clean up: Delete the temporary file
            # test_file.unlink()
            ...

    def test_nt_case_hashing(self):
        test_classes: tuple[type, ...] = (
            (CustomPureWindowsPath,)
            if os.name == "posix"
            else (CustomWindowsPath, CustomPureWindowsPath, CustomPath)
        )
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                path1 = PathType("test\\path\\to\\nothing")
                path2 = PathType("tesT\\PATH\\\\to\\noTHinG\\")

            with mock.patch("os.name", "nt"):
                test_set = {path1, path2}
                self.assertEqual(path1, path2)
                self.assertEqual(hash(path1), hash(path2))
                self.assertSetEqual(test_set, {PathType("TEST\\path\\to\\\\nothing")})

    @unittest.skipIf(os.name != "posix", "Test only supported on POSIX systems.")
    def test_posix_exists_alternatives(self):
        test_classes: tuple[type, ...] = (CustomPath, CaseAwarePath)
        test_path = "/dev/vcsa6"
        self.assertFalse(os.access("C:\\nonexistent\\path", os.F_OK))
        test_access: bool = os.access(test_path, os.F_OK)
        self.assertEqual(test_access, True)

        test_os_exists: bool = os.path.exists(test_path)
        self.assertEqual(test_os_exists, True)
        test_os_isfile: bool = os.path.isfile(test_path)
        self.assertEqual(test_os_isfile, False)  # This is the bug
        test_os_isdir: bool = os.path.isdir(test_path)
        self.assertEqual(test_os_isfile, False)  # This is the bug

        self.assertEqual(True, Path(test_path).exists())
        self.assertEqual(False, Path(test_path).is_file())  # This is the bug
        self.assertEqual(False, Path(test_path).is_dir())  # This is the bug
        for PathType in test_classes:

            test_pathtype_exists: bool | None = PathType(test_path).safe_exists()
            self.assertEqual(test_pathtype_exists, True, repr(PathType))
            self.assertEqual(True, PathType(test_path).exists(), repr(PathType))
            test_pathtype_isfile: bool | None = PathType(test_path).safe_isfile()
            self.assertEqual(test_pathtype_isfile, False, repr(PathType))
            self.assertEqual(False, PathType(test_path).is_file(), repr(PathType))  # This is the bug
            test_pathtype_isdir: bool | None = PathType(test_path).safe_isdir()
            self.assertEqual(test_pathtype_isdir, False, repr(PathType))
            self.assertEqual(False, PathType(test_path).is_dir(), repr(PathType))  # This is the bug

    @unittest.skipIf(os.name != "nt", "Test only supported on Windows.")
    def test_windows_exists_alternatives_dir(self):
        test_classes: tuple[type, ...] = (CustomPath, CaseAwarePath)
        test_path = "C:\\WINDOWS"
        self.assertFalse(os.access("C:\\nonexistent\\path", os.F_OK))
        test_access: bool = os.access(test_path, os.F_OK)
        self.assertEqual(test_access, True)

        exists, is_file, is_dir = check_path_win_api(test_path)
        self.assertEqual(exists, True)
        self.assertEqual(is_file, False)
        self.assertEqual(is_dir, True)

        test_os_exists: bool = os.path.exists(test_path)
        self.assertEqual(test_os_exists, True)
        test_os_isfile: bool = os.path.isfile(test_path)
        self.assertEqual(test_os_isfile, False)

        for PathType in test_classes:

            test_pathtype_exists: bool | None = PathType(test_path).safe_exists()
            self.assertEqual(test_pathtype_exists, True)
            test_pathtype_isfile: bool | None = PathType(test_path).safe_isfile()
            self.assertEqual(test_pathtype_isfile, False)
            test_pathtype_isdir: bool | None = PathType(test_path).safe_isdir()
            self.assertEqual(test_pathtype_isdir, True)

    def find_exists_problems(self):
        test_classes: tuple[type, ...] = (Path, CustomPath, CaseAwarePath)
        test_path = "/" if platform.system() != "Windows" else "C:\\"
        for PathType in test_classes:
            self.assertTrue(self.list_files_recursive_scandir(test_path, set(), PathType))

    def list_files_recursive_scandir(self, path: str, seen: set, PathType: type[pathlib.Path | CustomPath | CaseAwarePath]):
        if "/mnt/c" in path.lower():
            print("Skipping /mnt/c (wsl)")
            return True
        try:
            it = os.scandir(path)
        except Exception:
            return None

        known_issue_paths: set[str] = {
            "C:\\GitHub\\PyKotor\\.venv_wsl\\bin\\python",
            "C:\\GitHub\\PyKotor\\.venv_wsl\\bin\\python3",
            "C:\\GitHub\\PyKotor\\.venv_wsl\\bin\\python3.10",
        }
        try:
            for entry in it:
                path_entry: str = entry.path
                if path_entry in known_issue_paths:
                    continue
                if path_entry.replace("\\", "/").count("/") > 5 or path_entry in seen:  # Handle links
                    continue
                seen.add(path_entry)
                try:
                    is_dir_check = PathType(path_entry).is_dir()
                    assert is_dir_check is True or is_dir_check is False, f"is_file_check returned nonbool '{is_dir_check}' at '{path_entry}'"
                    if is_dir_check:
                        print(f"Directory: {path_entry}")
                        self.list_files_recursive_scandir(path_entry, seen, PathType)  # Recursively list subdirectories
                    is_file_check = PathType(path_entry).is_file()
                    assert is_file_check is True or is_file_check is False, f"is_file_check returned nonbool '{is_file_check}' at '{path_entry}'"
                    if is_file_check:
                        ...
                        # print(f"File: {path_entry}")
                    if is_file_check or is_dir_check:
                        continue

                    exist_check = PathType(path_entry).exists()
                    if exist_check is True:
                        print(f"exists: True but no permissions to {path_entry}")
                        raise RuntimeError(f"exists: True but no permissions to {path_entry}")
                    if exist_check is False:
                        print(f"exists: False but no permissions to {path_entry}")
                    else:
                        raise ValueError(f"Unexpected ret value of exist_check at {path_entry}: {exist_check}")
                except Exception as e:
                    print(f"Exception encountered during is_dir() call on {path_entry}: {e}")
                    raise
        except Exception as e:
            print(f"Exception encountered while scanning {path}: {e}")
            raise
        return True

    def test_posix_case_hashing(self):
        test_classes: list[type] = (
            [CustomPosixPath, CustomPurePosixPath, CustomPath]
            if os.name == "posix"
            else [CustomPurePosixPath]
        )
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                path1 = PathType("test\\\\path\\to\\nothing\\")
                path2 = PathType("tesT\\PATH\\to\\\\noTHinG")

            with mock.patch("os.name", "posix"):
                test_set = {path1, path2}
                self.assertNotEqual(path1, path2)
                self.assertNotEqual(hash(path1), hash(path2))
                self.assertNotEqual(test_set, {PathType("TEST\\path\\\\to\\nothing")})

    def test_pathlib_path_edge_cases_posix(self):
        test_classes = (PosixPath, PurePosixPath) if os.name == "posix" else (PurePosixPath,)
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/test\\")), "C:/Users/test\\")
                self.assertEqual(str(PathType("C://Users///test")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:/Users/TEST")

                # Network Paths
                self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )

                # Special Characters
                self.assertEqual(str(PathType("C:/Users/test folder/")), "C:/Users/test folder")
                self.assertEqual(str(PathType("C:/Users/üser/")), "C:/Users/üser")
                self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test")

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("//")), "//")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("///")), "/")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test")
                self.assertEqual(str(PathType("~/folder/")), "~/folder")

    def test_pathlib_path_edge_cases_windows(self):
        test_classes = (WindowsPath, PureWindowsPath) if os.name == "nt" else (PureWindowsPath,)
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:\\")
                self.assertEqual(str(PathType("C:\\")), "C:\\")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/test\\")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C://Users///test")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder\\")
                if sys.version_info < (3, 12):
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\server\\folder")
                else:
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\\\server\\folder")
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )

                # Special Characters
                self.assertEqual(str(PathType("C:/Users/test folder/")), "C:\\Users\\test folder")
                self.assertEqual(str(PathType("C:/Users/üser/")), "C:\\Users\\üser")
                self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:\\Users\\test")

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                if sys.version_info < (3, 12):
                    self.assertEqual(str(PathType("//")), "\\")
                    self.assertEqual(str(PathType("///")), "\\")
                else:
                    self.assertEqual(str(PathType("//")), "\\\\")
                    self.assertEqual(str(PathType("///")), "\\\\\\")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_pathlib_path_edge_cases_os_specific(self):
        for PathType in (Path, PurePath):
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:\\")), "C:\\")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C://Users///test")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))
                if os.name == "posix":
                    self.assertEqual(str(PathType("C:/Users/test\\")), "C:/Users/test\\")
                    self.assertEqual(str(PathType("C:/")), "C:")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("C:/Users/test")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/")), "C:\\")

                # Network Paths
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )
                if os.name == "posix":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder\\")
                    if sys.version_info < (3, 12):
                        self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\server\\folder")
                        self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\server\\folder")
                    else:
                        self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                        self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\\\server\\folder")

                # Special Characters
                self.assertEqual(str(PathType("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder".replace("/", os.sep))

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                if os.name == "posix":
                    self.assertEqual(str(PathType("//")), "//".replace("/", os.sep))
                elif sys.version_info < (3, 12):
                    self.assertEqual(str(PathType("//")), "\\")
                else:
                    self.assertEqual(str(PathType("//")), "\\\\")
                self.assertEqual(str(PathType("C:")), "C:")
                if sys.version_info < (3, 12) or os.name != "nt":
                    self.assertEqual(str(PathType("///")), "/".replace("/", os.sep))
                else:
                    self.assertEqual(str(PathType("///")), "///".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
                self.assertEqual(str(PathType("~/folder/")), "~/folder".replace("/", os.sep))

    def test_custom_path_edge_cases_posix(self):
        test_classes = [CustomPosixPath, CustomPurePosixPath] if os.name == "posix" else [CustomPurePosixPath]
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/test\\")), "C:/Users/test")
                self.assertEqual(str(PathType("C://Users///test")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:/Users/TEST")

                # Network Paths
                self.assertEqual(str(PathType("\\\\server\\folder")), "/server/folder")
                self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "/server/folder")
                self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "/server/folder")
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "/wsl.localhost/path/to/file with space ",
                )

                # Special Characters
                self.assertEqual(str(PathType("C:/Users/test folder/")), "C:/Users/test folder")
                self.assertEqual(str(PathType("C:/Users/üser/")), "C:/Users/üser")
                self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test")

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("//")), "/")
                self.assertEqual(str(PathType("///")), "/")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("~/folder/")), "~/folder")

    def test_custom_path_edge_cases_windows(self):
        test_classes = [CustomWindowsPath, CustomPureWindowsPath] if os.name == "nt" else [CustomPureWindowsPath]
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/test\\")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C://Users///test")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\server\\folder")
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )

                # Special Characters
                self.assertEqual(str(PathType("C:/Users/test folder/")), "C:\\Users\\test folder")
                self.assertEqual(str(PathType("C:/Users/üser/")), "C:\\Users\\üser")
                self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:\\Users\\test")

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("//")), ".")
                self.assertEqual(str(PathType("///")), ".")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_os_specific(self):
        # sourcery skip: extract-duplicate-method
        for PathType in (CaseAwarePath, CustomPath, CustomPurePath):
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                self.assertEqual(str(PathType("C:\\")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users/test\\")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C://Users///test")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))

                # Network Paths
                if os.name == "posix":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "/server/folder")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "/server/folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "/server/folder")
                    self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                    self.assertEqual(
                        str(PathType("\\\\wsl.localhost\\path\\to\\file with space ")),
                        "/wsl.localhost/path/to/file with space ",
                    )
                elif os.name == "nt":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                    self.assertEqual(
                        str(PathType("\\\\wsl.localhost\\path\\to\\file with space ")),
                        "\\\\wsl.localhost\\path\\to\\file with space ",
                    )

                # Special Characters
                self.assertEqual(str(PathType("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder".replace("/", os.sep))

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
                self.assertEqual(str(PathType("C:\\.\\Users\\..\\test\\")), "C:/Users/../test".replace("/", os.sep))
                self.assertEqual(str(PathType("~/folder/")), "~/folder".replace("/", os.sep))
                self.assertEqual(str(PathType("C:")), "C:".replace("/", os.sep))
                if os.name == "posix":
                    self.assertEqual(str(PathType("//")), "/")
                    self.assertEqual(str(PathType("///")), "/")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("//")), ".")
                    self.assertEqual(str(PathType("///")), ".")


if __name__ == "__main__":
    unittest.main()
