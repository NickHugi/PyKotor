# Rigorously test the string result of each pathlib module.
# The goal isn't really to test pathlib.Path or utility.path, the goal is to determine if there was a breaking change in a python patch release.
from __future__ import annotations
import ctypes
from ctypes.wintypes import DWORD

import os
import pathlib
import platform
import sys
import unittest
from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath
from unittest import mock

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.tools.path import CaseAwarePath
from utility.system.path import Path as CustomPath
from utility.system.path import PosixPath as CustomPosixPath
from utility.system.path import PurePath as CustomPurePath
from utility.system.path import PurePosixPath as CustomPurePosixPath
from utility.system.path import PureWindowsPath as CustomPureWindowsPath
from utility.system.path import WindowsPath as CustomWindowsPath

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

            with mock.patch('os.name', "nt"):
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
    def test_windows_exists_alternatives(self):
        test_classes: tuple[type, ...] = (CustomPath, CaseAwarePath)
        test_path = "C:\\GitHub\\PyKotor\\.venv_wsl\\bin\\python"
        self.assertFalse(os.access("C:\\nonexistent\\path", os.F_OK))
        test_access: bool = os.access(test_path, os.F_OK)
        self.assertEqual(test_access, True)

        exists, is_file, is_dir = check_path_win_api(test_path)
        self.assertEqual(exists, True)
        self.assertEqual(is_file, True)
        self.assertEqual(is_dir, False)

        test_os_exists: bool = os.path.exists(test_path)
        self.assertEqual(test_os_exists, False)
        test_os_isfile: bool = os.path.isfile(test_path)
        self.assertEqual(test_os_isfile, False)

        self.assertRaises(OSError, Path(test_path).exists)
        self.assertRaises(OSError, Path(test_path).is_file)
        self.assertRaises(OSError, Path(test_path).is_dir)
        for PathType in test_classes:

            test_pathtype_exists: bool | None = PathType(test_path).safe_exists()
            self.assertEqual(test_pathtype_exists, None)
            self.assertRaises(OSError, PathType(test_path).exists)
            test_pathtype_isfile: bool | None = PathType(test_path).safe_isfile()
            self.assertEqual(test_pathtype_isfile, None)
            self.assertRaises(OSError, PathType(test_path).is_file)
            test_pathtype_isdir: bool | None = PathType(test_path).safe_isdir()
            self.assertEqual(test_pathtype_isdir, None)
            self.assertRaises(OSError, PathType(test_path).is_dir)

    def test_find_exists_problems(self):
        test_classes: tuple[type, ...] = (Path, CustomPath, CaseAwarePath)
        test_path = "/" if platform.system() != "Windows" else "C:\\"
        for PathType in test_classes:
            self.assertTrue(self.list_files_recursive_scandir(test_path, set(), PathType))

    def list_files_recursive_scandir(self, path: str, seen: set, PathType: type[pathlib.Path] | type[CustomPath] | type[CaseAwarePath]):
        if "/mnt/c" in path.lower():
            print("Skipping /mnt/c (wsl)")
            return True
        try:
            it = os.scandir(path)
        except Exception:
            return
        
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
                else:
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
                        #print(f"File: {path_entry}")
                    if is_file_check or is_dir_check:
                        continue

                    exist_check = PathType(path_entry).exists()
                    if exist_check is True:
                        print(f"exists: True but no permissions to {path_entry}")
                        raise RuntimeError(f"exists: True but no permissions to {path_entry}")
                    elif exist_check is False:
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

            with mock.patch('os.name', "posix"):
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
                self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:/Users/test")

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("//")), "//")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("///")), "/")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test")
                self.assertEqual(str(PathType("~/folder/")), "~/folder")

    def test_pathlib_path_edge_cases_windows(self):
        test_classes = (WindowsPath, PureWindowsPath) if os.name == "nt" else (PureWindowsPath)
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
                self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:\\Users\\test")

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
                self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:/Users/test".replace("/", os.sep))

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
                self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:/Users/test")

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
                self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:\\Users\\test")

                # Bizarre Scenarios
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("//")), ".")
                self.assertEqual(str(PathType("///")), ".")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_os_specific(self):
        # sourcery skip: extract-duplicate-method
        for PathType in {CaseAwarePath, CustomPath, CustomPurePath}:
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
                self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:/Users/test".replace("/", os.sep))

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
