# Rigorously test the string result of each pathlib module.
# The goal isn't really to test pathlib.Path or utility.path, the goal is to determine if there was a breaking change in a python patch release.
from __future__ import annotations

import ctypes
import os
import pathlib
import platform
import sys
import unittest

from ctypes.wintypes import DWORD
from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath
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
    @unittest.skipIf(os.name != "nt", "Test can only be run on Windows.")
    def test_low_granular_path_usage(self):
        override_path_str = r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II\Override"
        override_path = CustomPureWindowsPath(override_path_str) 
        testpath_str1 = r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II\Override\000react.dlg"
        testpath_1 = CustomPureWindowsPath(testpath_str1)
        self.assertEqual(str(testpath_1), testpath_str1)
        self.assertEqual(testpath_1.parts[0], override_path.parts[0])
        self.assertTrue(testpath_1.is_relative_to(override_path))
        testpath_2 = override_path.joinpath(testpath_str1)
        self.assertEqual(testpath_1.parts[0], testpath_2.parts[0])
        self.assertEqual(testpath_2, testpath_1)
        self.assertTrue(testpath_2.is_relative_to(override_path))

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

    @unittest.skipIf(os.name == "nt", "Test only supported on POSIX systems.")
    def test_posix_case_hashing_custom_posix_path(self):
        path1, path2 = CustomPosixPath("test\\\\path\\to\\nothing\\"), CustomPosixPath("tesT\\PATH\\to\\\\noTHinG")
        with mock.patch("os.name", "posix"):
            test_set = {path1, path2}
            self.assertNotEqual(path1, path2)
            self.assertNotEqual(hash(path1), hash(path2))
            self.assertNotEqual(test_set, {CustomPosixPath("TEST\\path\\\\to\\nothing")})

    def test_posix_case_hashing_custom_pure_posix_path(self):
        path1, path2 = CustomPurePosixPath("test\\\\path\\to\\nothing\\"), CustomPurePosixPath("tesT\\PATH\\to\\\\noTHinG")
        with mock.patch("os.name", "posix"):
            test_set = {path1, path2}
            self.assertNotEqual(path1, path2)
            self.assertNotEqual(hash(path1), hash(path2))
            self.assertNotEqual(test_set, {CustomPurePosixPath("TEST\\path\\\\to\\nothing")})

    def test_posix_case_hashing_custom_path(self):
        path1, path2 = CustomPath("test\\\\path\\to\\nothing\\"), CustomPath("tesT\\PATH\\to\\\\noTHinG")
        with mock.patch.object(path1._flavour, 'sep', '/'):
            with mock.patch.object(path2._flavour, 'sep', '/'):
                test_set = {path1, path2}
                self.assertNotEqual(path1, path2)
                self.assertNotEqual(hash(path1), hash(path2))
                self.assertNotEqual(test_set, {CustomPath("TEST/path/to/nothing/")})

    def test_windows_case_hashing_custom_path(self):
        path1, path2 = CustomPath("test\\\\path\\to\\nothing\\"), CustomPath("tesT\\PATH\\to\\\\noTHinG")
        with mock.patch.object(path1._flavour, 'sep', '\\'):
            with mock.patch.object(path2._flavour, 'sep', '\\'):
                test_set = {path1, path2}
                self.assertEqual(path1, path2)
                self.assertEqual(hash(path1), hash(path2))
                self.assertEqual(test_set, {CustomPath("TEST/path/to/nothing/")}) if os.name == "nt" else self.assertNotEqual(test_set, {CustomPath("TEST/path/to/nothing/")})

    @unittest.skipIf(os.name == "nt", "Test only supported on POSIX systems.")
    def test_pathlib_path_edge_cases_posix_posix_path(self):
        self.assertEqual(str(PosixPath("C:/")), "C:")
        self.assertEqual(str(PosixPath("C:/Users/test/")), "C:/Users/test")
        self.assertEqual(str(PosixPath("C:/Users/test\\")), "C:/Users/test\\")
        self.assertEqual(str(PosixPath("C://Users///test")), "C:/Users/test")
        self.assertEqual(str(PosixPath("C:/Users/TEST/")), "C:/Users/TEST")
        self.assertEqual(str(PosixPath("\\\\server\\folder")), "\\\\server\\folder")
        self.assertEqual(str(PosixPath("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
        self.assertEqual(str(PosixPath("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
        self.assertEqual(str(PosixPath("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
        self.assertEqual(str(PosixPath("\\\\wsl.localhost\\path\\to\\file with space ")), "\\\\wsl.localhost\\path\\to\\file with space ")
        self.assertEqual(str(PosixPath("C:/Users/test folder/")), "C:/Users/test folder")
        self.assertEqual(str(PosixPath("C:/Users/üser/")), "C:/Users/üser")
        self.assertEqual(str(PosixPath("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder")
        self.assertEqual(str(PosixPath("C:/Users").joinpath("test/")), "C:/Users/test")
        self.assertEqual(str(PosixPath("C:/Users") / "test/"), "C:/Users/test")
        self.assertEqual(str(PosixPath("C:/Users") / "test/"), "C:/Users/test")
        self.assertEqual(str(PosixPath("")), ".")
        self.assertEqual(str(PosixPath("//")), "//")
        self.assertEqual(str(PosixPath("C:")), "C:")
        self.assertEqual(str(PosixPath("///")), "/")
        self.assertEqual(str(PosixPath("C:/./Users/../test/")), "C:/Users/../test")
        self.assertEqual(str(PosixPath("~/folder/")), "~/folder")

    def test_pathlib_path_edge_cases_posix_pure_posix_path(self):
        self.assertEqual(str(PurePosixPath("C:/")), "C:")
        self.assertEqual(str(PurePosixPath("C:/Users/test/")), "C:/Users/test")
        self.assertEqual(str(PurePosixPath("C:/Users/test\\")), "C:/Users/test\\")
        self.assertEqual(str(PurePosixPath("C://Users///test")), "C:/Users/test")
        self.assertEqual(str(PurePosixPath("C:/Users/TEST/")), "C:/Users/TEST")
        self.assertEqual(str(PurePosixPath("\\\\server\\folder")), "\\\\server\\folder")
        self.assertEqual(str(PurePosixPath("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
        self.assertEqual(str(PurePosixPath("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
        self.assertEqual(str(PurePosixPath("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
        self.assertEqual(str(PurePosixPath("\\\\wsl.localhost\\path\\to\\file with space ")), "\\\\wsl.localhost\\path\\to\\file with space ")
        self.assertEqual(str(PurePosixPath("C:/Users/test folder/")), "C:/Users/test folder")
        self.assertEqual(str(PurePosixPath("C:/Users/üser/")), "C:/Users/üser")
        self.assertEqual(str(PurePosixPath("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder")
        self.assertEqual(str(PurePosixPath("C:/Users").joinpath("test/")), "C:/Users/test")
        self.assertEqual(str(PurePosixPath("C:/Users") / "test/"), "C:/Users/test")
        self.assertEqual(str(PurePosixPath("C:/Users") / "test/"), "C:/Users/test")
        self.assertEqual(str(PurePosixPath("")), ".")
        self.assertEqual(str(PurePosixPath("//")), "//")
        self.assertEqual(str(PurePosixPath("C:")), "C:")
        self.assertEqual(str(PurePosixPath("///")), "/")
        self.assertEqual(str(PurePosixPath("C:/./Users/../test/")), "C:/Users/../test")
        self.assertEqual(str(PurePosixPath("~/folder/")), "~/folder")

    @unittest.skipIf(os.name != "nt", "Test only supported on NT systems.")
    def test_pathlib_path_edge_cases_windows_windows_path(self):
        self.assertEqual(str(WindowsPath("C:/")), "C:\\")
        self.assertEqual(str(WindowsPath("C:\\")), "C:\\")
        self.assertEqual(str(WindowsPath("C:/Users/test/")), "C:\\Users\\test")
        self.assertEqual(str(WindowsPath("C:/Users/test\\")), "C:\\Users\\test")
        self.assertEqual(str(WindowsPath("C://Users///test")), "C:\\Users\\test")
        self.assertEqual(str(WindowsPath("C:/Users/TEST/")), "C:\\Users\\TEST")
        self.assertEqual(str(WindowsPath("\\\\server\\folder")), "\\\\server\\folder\\")
        if sys.version_info < (3, 12):
            self.assertEqual(str(WindowsPath("\\\\\\\\server\\folder/")), "\\server\\folder")
            self.assertEqual(str(WindowsPath("\\\\\\server\\\\folder")), "\\server\\folder")
        else:
            self.assertEqual(str(WindowsPath("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
            self.assertEqual(str(WindowsPath("\\\\\\server\\\\folder")), "\\\\\\server\\folder")
        self.assertEqual(str(WindowsPath("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
        self.assertEqual(str(WindowsPath("\\\\wsl.localhost\\path\\to\\file with space ")), "\\\\wsl.localhost\\path\\to\\file with space ")
        self.assertEqual(str(WindowsPath("C:/Users/test folder/")), "C:\\Users\\test folder")
        self.assertEqual(str(WindowsPath("C:/Users/üser/")), "C:\\Users\\üser")
        self.assertEqual(str(WindowsPath("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")
        self.assertEqual(str(WindowsPath("C:/Users").joinpath("test/")), "C:\\Users\\test")
        self.assertEqual(str(WindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(WindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(WindowsPath("")), ".")
        if sys.version_info < (3, 12):
            self.assertEqual(str(WindowsPath("//")), "\\")
            self.assertEqual(str(WindowsPath("///")), "\\")
        else:
            self.assertEqual(str(WindowsPath("//")), "\\\\")
            self.assertEqual(str(WindowsPath("///")), "\\\\\\")
        self.assertEqual(str(WindowsPath("C:")), "C:")
        self.assertEqual(str(WindowsPath("C:/./Users/../test/")), "C:\\Users\\..\\test")
        self.assertEqual(str(WindowsPath("~/folder/")), "~\\folder")

    def test_pathlib_path_edge_cases_windows_pure_windows_path(self):
        self.assertEqual(str(PureWindowsPath("C:/")), "C:\\")
        self.assertEqual(str(PureWindowsPath("C:\\")), "C:\\")
        self.assertEqual(str(PureWindowsPath("C:/Users/test/")), "C:\\Users\\test")
        self.assertEqual(str(PureWindowsPath("C:/Users/test\\")), "C:\\Users\\test")
        self.assertEqual(str(PureWindowsPath("C://Users///test")), "C:\\Users\\test")
        self.assertEqual(str(PureWindowsPath("C:/Users/TEST/")), "C:\\Users\\TEST")
        self.assertEqual(str(PureWindowsPath("\\\\server\\folder")), "\\\\server\\folder\\")
        if sys.version_info < (3, 12):
            self.assertEqual(str(PureWindowsPath("\\\\\\\\server\\folder/")), "\\server\\folder")
            self.assertEqual(str(PureWindowsPath("\\\\\\server\\\\folder")), "\\server\\folder")
        else:
            self.assertEqual(str(PureWindowsPath("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
            self.assertEqual(str(PureWindowsPath("\\\\\\server\\\\folder")), "\\\\\\server\\folder")
        self.assertEqual(str(PureWindowsPath("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
        self.assertEqual(str(PureWindowsPath("\\\\wsl.localhost\\path\\to\\file with space ")), "\\\\wsl.localhost\\path\\to\\file with space ")
        self.assertEqual(str(PureWindowsPath("C:/Users/test folder/")), "C:\\Users\\test folder")
        self.assertEqual(str(PureWindowsPath("C:/Users/üser/")), "C:\\Users\\üser")
        self.assertEqual(str(PureWindowsPath("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")
        self.assertEqual(str(PureWindowsPath("C:/Users").joinpath("test/")), "C:\\Users\\test")
        self.assertEqual(str(PureWindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(PureWindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(PureWindowsPath("")), ".")
        if sys.version_info < (3, 12):
            self.assertEqual(str(PureWindowsPath("//")), "\\")
            self.assertEqual(str(PureWindowsPath("///")), "\\")
        else:
            self.assertEqual(str(PureWindowsPath("//")), "\\\\")
            self.assertEqual(str(PureWindowsPath("///")), "\\\\\\")
        self.assertEqual(str(PureWindowsPath("C:")), "C:")
        self.assertEqual(str(PureWindowsPath("C:/./Users/../test/")), "C:\\Users\\..\\test")
        self.assertEqual(str(PureWindowsPath("~/folder/")), "~\\folder")

    def test_pathlib_path_edge_cases_os_specific_path(self):
        self.assertEqual(str(Path("C:\\")), "C:\\")
        if os.name == "nt":
            self.assertEqual(str(Path("C:/")), "C:\\")
        else:
            self.assertEqual(str(Path("C:/")), "C:")
        self.assertEqual(str(Path("C:")), "C:")
        self.assertEqual(str(Path("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(Path("C://Users///test")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(Path("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))
        if os.name == "posix":
            self.assertEqual(str(Path("C:/Users/test\\")), "C:/Users/test\\")
            self.assertEqual(str(Path("C:/")), "C:")
        elif os.name == "nt":
            self.assertEqual(str(Path("C:/Users/test")), "C:\\Users\\test")
            self.assertEqual(str(Path("C:/")), "C:\\")

        self.assertEqual(str(Path("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
        self.assertEqual(str(Path("\\\\wsl.localhost\\path\\to\\file with space ")), "\\\\wsl.localhost\\path\\to\\file with space ")
        if os.name == "posix":
            self.assertEqual(str(Path("\\\\server\\folder")), "\\\\server\\folder")
            self.assertEqual(str(Path("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
            self.assertEqual(str(Path("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
        elif os.name == "nt":
            self.assertEqual(str(Path("\\\\server\\folder")), "\\\\server\\folder\\")
            if sys.version_info < (3, 12):
                self.assertEqual(str(Path("\\\\\\\\server\\folder/")), "\\server\\folder")
                self.assertEqual(str(Path("\\\\\\server\\\\folder")), "\\server\\folder")
            else:
                self.assertEqual(str(Path("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                self.assertEqual(str(Path("\\\\\\server\\\\folder")), "\\\\\\server\\folder")

        self.assertEqual(str(Path("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
        self.assertEqual(str(Path("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
        self.assertEqual(str(Path("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder".replace("/", os.sep))

        self.assertEqual(str(Path("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(Path("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(Path("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))

        self.assertEqual(str(Path("")), ".")
        if os.name == "posix":
            self.assertEqual(str(Path("//")), "//".replace("/", os.sep))
        elif sys.version_info < (3, 12):
            self.assertEqual(str(Path("//")), "\\")
        else:
            self.assertEqual(str(Path("//")), "\\\\")
        self.assertEqual(str(Path("C:")), "C:")
        if sys.version_info < (3, 12) or os.name != "nt":
            self.assertEqual(str(Path("///")), "/".replace("/", os.sep))
        else:
            self.assertEqual(str(Path("///")), "///".replace("/", os.sep))
        self.assertEqual(str(Path("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
        self.assertEqual(str(Path("~/folder/")), "~/folder".replace("/", os.sep))

    def test_pathlib_path_edge_cases_os_specific_pure_path(self):
        self.assertEqual(str(PurePath("C:\\")), "C:\\")
        self.assertEqual(str(PurePath("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(PurePath("C://Users///test")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(PurePath("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))
        if os.name == "posix":
            self.assertEqual(str(PurePath("C:/Users/test\\")), "C:/Users/test\\")
            self.assertEqual(str(PurePath("C:/")), "C:")
        elif os.name == "nt":
            self.assertEqual(str(PurePath("C:/Users/test")), "C:\\Users\\test")
            self.assertEqual(str(PurePath("C:/")), "C:\\")

        self.assertEqual(str(PurePath("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
        self.assertEqual(str(PurePath("\\\\wsl.localhost\\path\\to\\file with space ")), "\\\\wsl.localhost\\path\\to\\file with space ")
        if os.name == "posix":
            self.assertEqual(str(PurePath("\\\\server\\folder")), "\\\\server\\folder")
            self.assertEqual(str(PurePath("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
            self.assertEqual(str(PurePath("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
        elif os.name == "nt":
            self.assertEqual(str(PurePath("\\\\server\\folder")), "\\\\server\\folder\\")
            if sys.version_info < (3, 12):
                self.assertEqual(str(PurePath("\\\\\\\\server\\folder/")), "\\server\\folder")
                self.assertEqual(str(PurePath("\\\\\\server\\\\folder")), "\\server\\folder")
            else:
                self.assertEqual(str(PurePath("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                self.assertEqual(str(PurePath("\\\\\\server\\\\folder")), "\\\\\\server\\folder")

        self.assertEqual(str(PurePath("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
        self.assertEqual(str(PurePath("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
        self.assertEqual(str(PurePath("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder".replace("/", os.sep))

        self.assertEqual(str(PurePath("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(PurePath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(PurePath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))

        self.assertEqual(str(PurePath("")), ".")
        if os.name == "posix":
            self.assertEqual(str(PurePath("//")), "//".replace("/", os.sep))
        elif sys.version_info < (3, 12):
            self.assertEqual(str(PurePath("//")), "\\")
        else:
            self.assertEqual(str(PurePath("//")), "\\\\")
        self.assertEqual(str(PurePath("C:")), "C:")
        if sys.version_info < (3, 12) or os.name != "nt":
            self.assertEqual(str(PurePath("///")), "/".replace("/", os.sep))
        else:
            self.assertEqual(str(PurePath("///")), "///".replace("/", os.sep))
        self.assertEqual(str(PurePath("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
        self.assertEqual(str(PurePath("~/folder/")), "~/folder".replace("/", os.sep))

    @unittest.skipIf(os.name == "nt", "Test only supported on POSIX systems.")
    def test_custom_path_edge_cases_posix_custom_posix_path(self):
        self.assertEqual(str(CustomPosixPath("C:/")), "C:")
        self.assertEqual(str(CustomPosixPath("C:/Users/test/")), "C:/Users/test")
        self.assertEqual(str(CustomPosixPath("C:/Users/test\\")), "C:/Users/test")
        self.assertEqual(str(CustomPosixPath("C://Users///test")), "C:/Users/test")
        self.assertEqual(str(CustomPosixPath("C:/Users/TEST/")), "C:/Users/TEST")
        self.assertEqual(str(CustomPosixPath("C:/Users/test folder/")), "C:/Users/test folder")
        self.assertEqual(str(CustomPosixPath("C:/Users/üser/")), "C:/Users/üser")
        self.assertEqual(str(CustomPosixPath("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder")
        self.assertEqual(str(CustomPosixPath("C:/Users").joinpath("test/")), "C:/Users/test")
        self.assertEqual(str(CustomPosixPath("C:/Users") / "test/"), "C:/Users/test")
        self.assertEqual(str(CustomPosixPath("C:/Users") / "test/"), "C:/Users/test")
        self.assertEqual(str(CustomPosixPath("")), ".")
        self.assertEqual(str(CustomPosixPath("//")), "/")
        self.assertEqual(str(CustomPosixPath("///")), "/")
        if os.name == "nt":
            self.assertEqual(str(CustomPosixPath("C:/./Users/../test/")), "C:/test")
        else:
            self.assertEqual(str(CustomPosixPath("C:/./Users/../test/")), "C:/Users/../test")
        self.assertEqual(str(CustomPosixPath("C:")), "C:")
        self.assertEqual(str(CustomPosixPath("~/folder/")), "~/folder")

    def test_custom_path_edge_cases_posix_custom_pure_posix_path(self):
        self.assertEqual(str(CustomPurePosixPath("C:/")), "C:")
        self.assertEqual(str(CustomPurePosixPath("C:/Users/test/")), "C:/Users/test")
        self.assertEqual(str(CustomPurePosixPath("C:/Users/test\\")), "C:/Users/test")
        self.assertEqual(str(CustomPurePosixPath("C://Users///test")), "C:/Users/test")
        self.assertEqual(str(CustomPurePosixPath("C:/Users/TEST/")), "C:/Users/TEST")
        self.assertEqual(str(CustomPurePosixPath("C:/Users/test folder/")), "C:/Users/test folder")
        self.assertEqual(str(CustomPurePosixPath("C:/Users/üser/")), "C:/Users/üser")
        self.assertEqual(str(CustomPurePosixPath("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder")
        self.assertEqual(str(CustomPurePosixPath("C:/Users").joinpath("test/")), "C:/Users/test")
        self.assertEqual(str(CustomPurePosixPath("C:/Users") / "test/"), "C:/Users/test")
        self.assertEqual(str(CustomPurePosixPath("C:/Users") / "test//"), "C:/Users/test")
        self.assertEqual(str(CustomPurePosixPath("")), ".")
        self.assertEqual(str(CustomPurePosixPath("//")), "/")
        self.assertEqual(str(CustomPurePosixPath("///")), "/")
        self.assertEqual(str(CustomPurePosixPath("C:/./Users/../test/")), "C:/Users/../test")
        self.assertEqual(os.path.normpath(str(CustomPurePosixPath("C:/./Users/../test/"))), f"C:{os.path.sep}test")
        self.assertEqual(str(CustomPurePosixPath("C:")), "C:")
        self.assertEqual(str(CustomPurePosixPath("~/folder/")), "~/folder".replace("\\", "/"))

    @unittest.skipIf(os.name != "nt", "Test only supported on NT systems.")
    def test_custom_path_edge_cases_windows_custom_windows_path(self):
        self.assertEqual(str(CustomWindowsPath("C:/")), "C:")
        self.assertEqual(str(CustomWindowsPath("C:\\")), "C:")
        self.assertEqual(str(CustomWindowsPath("C:")), "C:")
        self.assertEqual(str(CustomWindowsPath("C:/Users/test/")), "C:\\Users\\test")
        self.assertEqual(str(CustomWindowsPath("C:/Users/test\\")), "C:\\Users\\test")
        self.assertEqual(str(CustomWindowsPath("C://Users///test")), "C:\\Users\\test")
        self.assertEqual(str(CustomWindowsPath("C:/Users/TEST/")), "C:\\Users\\TEST")
        self.assertEqual(str(CustomWindowsPath("C:/Users/test folder/")), "C:\\Users\\test folder")
        self.assertEqual(str(CustomWindowsPath("C:/Users/üser/")), "C:\\Users\\üser")
        self.assertEqual(str(CustomWindowsPath("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")
        self.assertEqual(str(CustomWindowsPath("C:/Users").joinpath("test/")), "C:\\Users\\test")
        self.assertEqual(str(CustomWindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(CustomWindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(CustomWindowsPath("")), ".")
        self.assertEqual(str(CustomWindowsPath("//")), ".")
        self.assertEqual(str(CustomWindowsPath("///")), ".")
        self.assertEqual(str(CustomWindowsPath("C:")), "C:")
        self.assertEqual(str(CustomWindowsPath("C:/./Users/../test/")), "C:\\Users\\..\\test")
        self.assertEqual(str(CustomWindowsPath("C:/./Users/../test/").resolve()), "C:\\test")
        self.assertEqual(str(CustomWindowsPath("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_windows_custom_pure_windows_path(self):
        self.assertEqual(str(CustomPureWindowsPath("C:/")), "C:")
        self.assertEqual(str(CustomPureWindowsPath("C:\\")), "C:")
        self.assertEqual(str(CustomPureWindowsPath("C:")), "C:")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users/test/")), "C:\\Users\\test")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users/test\\")), "C:\\Users\\test")
        self.assertEqual(str(CustomPureWindowsPath("C://Users///test")), "C:\\Users\\test")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users/TEST/")), "C:\\Users\\TEST")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users/test folder/")), "C:\\Users\\test folder")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users/üser/")), "C:\\Users\\üser")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users").joinpath("test/")), "C:\\Users\\test")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(CustomPureWindowsPath("C:/Users") / "test/"), "C:\\Users\\test")
        self.assertEqual(str(CustomPureWindowsPath("")), ".")
        self.assertEqual(str(CustomPureWindowsPath("//")), ".")
        self.assertEqual(str(CustomPureWindowsPath("///")), ".")
        self.assertEqual(str(CustomPureWindowsPath("C:")), "C:")
        self.assertEqual(str(CustomPureWindowsPath("C:/./Users/../test/")), "C:\\Users\\..\\test")
        if os.name == "nt":
            self.assertEqual(os.path.normpath(str(CustomPureWindowsPath("C:/./Users/../test/"))), f"C:{os.path.sep}test")
        self.assertEqual(str(CustomPureWindowsPath("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_os_specific_case_aware_path(self):
        self.assertEqual(str(CaseAwarePath("C:/")), "C:")
        self.assertEqual(str(CaseAwarePath("C:\\")), "C:")
        self.assertEqual(str(CaseAwarePath("C:")), "C:")
        self.assertEqual(str(CaseAwarePath("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users/test\\")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C://Users///test")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("")), ".")
        self.assertEqual(str(CaseAwarePath("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
        if os.name == "nt":
            self.assertEqual(str(CaseAwarePath("C:/./Users/../test/").resolve()), "C:/test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:\\.\\Users\\..\\test\\")), "C:/Users/../test".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("~/folder/")), "~/folder".replace("/", os.sep))
        self.assertEqual(str(CaseAwarePath("C:")), "C:".replace("/", os.sep))
        if os.name == "posix":
            self.assertEqual(str(CaseAwarePath("//")), "/")
            self.assertEqual(str(CaseAwarePath("///")), "/")
        elif os.name == "nt":
            self.assertEqual(str(CaseAwarePath("//")), ".")
            self.assertEqual(str(CaseAwarePath("///")), ".")

    def test_custom_path_edge_cases_os_specific_custom_path(self):
        self.assertEqual(str(CustomPath("C:/")), "C:")
        self.assertEqual(str(CustomPath("C:\\")), "C:")
        self.assertEqual(str(CustomPath("C:")), "C:")
        self.assertEqual(str(CustomPath("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users/test\\")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C://Users///test")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("")), ".")
        self.assertEqual(str(CustomPath("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:\\.\\Users\\..\\test\\")), "C:/Users/../test".replace("/", os.sep))
        self.assertEqual(str(CustomPath("~/folder/")), "~/folder".replace("/", os.sep))
        self.assertEqual(str(CustomPath("C:")), "C:".replace("/", os.sep))
        if os.name == "posix":
            self.assertEqual(str(CustomPath("//")), "/")
            self.assertEqual(str(CustomPath("///")), "/")
        elif os.name == "nt":
            self.assertEqual(str(CustomPath("//")), ".")
            self.assertEqual(str(CustomPath("///")), ".")


    def test_custom_path_edge_cases_os_specific_custom_pure_path(self):
        self.assertEqual(str(CustomPurePath("C:/")), "C:")
        self.assertEqual(str(CustomPurePath("C:\\")), "C:")
        self.assertEqual(str(CustomPurePath("C:")), "C:")
        self.assertEqual(str(CustomPurePath("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users/test\\")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C://Users///test")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("")), ".")
        self.assertEqual(str(CustomPurePath("C:/./Users/../test/")), "C:\\Users\\..\\test".replace("/", os.sep).replace("\\", os.sep))
        self.assertEqual(os.path.normpath(str(CustomPurePath("C:/./Users/../test/"))), "C:\\test".replace("/", os.sep).replace("\\", os.sep))
        self.assertEqual(str(CustomPurePath("C:\\.\\Users\\..\\test\\")), "C:\\Users\\..\\test".replace("/", os.sep).replace("\\", os.sep))
        self.assertEqual(str(CustomPurePath("~/folder/")), "~/folder".replace("/", os.sep))
        self.assertEqual(str(CustomPurePath("C:")), "C:".replace("/", os.sep))
        if os.name == "posix":
            self.assertEqual(str(CustomPurePath("//")), "/")
            self.assertEqual(str(CustomPurePath("///")), "/")
        elif os.name == "nt":
            self.assertEqual(str(CustomPurePath("//")), ".")
            self.assertEqual(str(CustomPurePath("///")), ".")

if __name__ == "__main__":
    unittest.main()
