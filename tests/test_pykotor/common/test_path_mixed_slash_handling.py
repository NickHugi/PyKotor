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
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath

from utility.system.path import (
    Path as CustomPath,
    PosixPath as CustomPosixPath,
    PurePath as CustomPurePath,
    PurePosixPath as CustomPurePosixPath,
    PureWindowsPath as CustomPureWindowsPath,
    WindowsPath as CustomWindowsPath,
)

from pykotor.tools.path import CaseAwarePath


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
        assert str(testpath_1) == testpath_str1
        assert testpath_1.parts[0] == override_path.parts[0]
        assert testpath_1.is_relative_to(override_path)
        testpath_2 = override_path.joinpath(testpath_str1)
        assert testpath_1.parts[0] == testpath_2.parts[0]
        assert testpath_2 == testpath_1
        assert testpath_2.is_relative_to(override_path)

    @unittest.skipIf(os.name != "posix", "Test only supported on POSIX systems.")
    def test_posix_exists_alternatives(self):
        test_classes: tuple[type, ...] = (CustomPath, CaseAwarePath)
        test_path = "/dev/vcsa6"
        assert not os.access("C:\\nonexistent\\path", os.F_OK)
        test_access: bool = os.access(test_path, os.F_OK)
        assert test_access == True

        test_os_exists: bool = os.path.exists(test_path)
        assert test_os_exists == True
        test_os_isfile: bool = os.path.isfile(test_path)
        assert test_os_isfile == False  # This is the bug
        test_os_isdir: bool = os.path.isdir(test_path)
        assert test_os_isfile == False  # This is the bug

        assert Path(test_path).exists() == True
        assert Path(test_path).is_file() == False  # This is the bug
        assert Path(test_path).is_dir() == False  # This is the bug
        for PathType in test_classes:
            test_pathtype_exists: bool | None = PathType(test_path).safe_exists()
            assert test_pathtype_exists == True, repr(PathType)
            assert PathType(test_path).exists() == True, repr(PathType)
            test_pathtype_isfile: bool | None = PathType(test_path).is_file()
            assert test_pathtype_isfile == False, repr(PathType)
            assert PathType(test_path).is_file() == False, repr(PathType)  # This is the bug
            test_pathtype_isdir: bool | None = PathType(test_path).is_dir()
            assert test_pathtype_isdir == False, repr(PathType)
            assert PathType(test_path).is_dir() == False, repr(PathType)  # This is the bug

    def find_exists_problems(self):
        test_classes: tuple[type, ...] = (Path, CustomPath, CaseAwarePath)
        test_path = "/" if platform.system() != "Windows" else "C:\\"
        for PathType in test_classes:
            assert self.list_files_recursive_scandir(test_path, set(), PathType)

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
            assert path1 != path2
            assert hash(path1) != hash(path2)
            assert test_set != {CustomPosixPath("TEST\\path\\\\to\\nothing")}

    def test_posix_case_hashing_custom_pure_posix_path(self):
        path1, path2 = CustomPurePosixPath("test\\\\path\\to\\nothing\\"), CustomPurePosixPath("tesT\\PATH\\to\\\\noTHinG")
        with mock.patch("os.name", "posix"):
            test_set = {path1, path2}
            assert path1 != path2
            assert hash(path1) != hash(path2)
            assert test_set != {CustomPurePosixPath("TEST\\path\\\\to\\nothing")}

    def test_posix_case_hashing_custom_path(self):
        path1, path2 = CustomPath("test\\\\path\\to\\nothing\\"), CustomPath("tesT\\PATH\\to\\\\noTHinG")
        with mock.patch.object(path1._flavour, "sep", "/"):
            with mock.patch.object(path2._flavour, "sep", "/"):
                test_set = {path1, path2}
                assert path1 != path2
                assert hash(path1) != hash(path2)
                assert test_set != {CustomPath("TEST/path/to/nothing/")}

    def test_windows_case_hashing_custom_path(self):
        path1, path2 = CustomPath("test\\\\path\\to\\nothing\\"), CustomPath("tesT\\PATH\\to\\\\noTHinG")
        with mock.patch.object(path1._flavour, "sep", "\\"):
            with mock.patch.object(path2._flavour, "sep", "\\"):
                test_set = {path1, path2}
                assert path1 == path2
                assert hash(path1) == hash(path2)
                self.assertEqual(test_set, {CustomPath("TEST/path/to/nothing/")}) if os.name == "nt" else self.assertNotEqual(test_set, {CustomPath("TEST/path/to/nothing/")})

    @unittest.skipIf(os.name == "nt", "Test only supported on POSIX systems.")
    def test_pathlib_path_edge_cases_posix_posix_path(self):
        assert str(PosixPath("C:/")) == "C:"
        assert str(PosixPath("C:/Users/test/")) == "C:/Users/test"
        assert str(PosixPath("C:/Users/test\\")) == "C:/Users/test\\"
        assert str(PosixPath("C://Users///test")) == "C:/Users/test"
        assert str(PosixPath("C:/Users/TEST/")) == "C:/Users/TEST"
        assert str(PosixPath("\\\\server\\folder")) == "\\\\server\\folder"
        assert str(PosixPath("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
        assert str(PosixPath("\\\\\\server\\\\folder")) == "\\\\\\server\\\\folder"
        assert str(PosixPath("\\\\wsl.localhost\\path\\to\\file")) == "\\\\wsl.localhost\\path\\to\\file"
        assert str(PosixPath("\\\\wsl.localhost\\path\\to\\file with space ")) == "\\\\wsl.localhost\\path\\to\\file with space "
        assert str(PosixPath("C:/Users/test folder/")) == "C:/Users/test folder"
        assert str(PosixPath("C:/Users/üser/")) == "C:/Users/üser"
        assert str(PosixPath("C:/Users/test\\nfolder/")) == "C:/Users/test\\nfolder"
        assert str(PosixPath("C:/Users").joinpath("test/")) == "C:/Users/test"
        assert str(PosixPath("C:/Users") / "test/") == "C:/Users/test"
        assert str(PosixPath("C:/Users") / "test/") == "C:/Users/test"
        assert str(PosixPath("")) == "."
        assert str(PosixPath("//")) == "//"
        assert str(PosixPath("C:")) == "C:"
        assert str(PosixPath("///")) == "/"
        assert str(PosixPath("C:/./Users/../test/")) == "C:/Users/../test"
        assert str(PosixPath("~/folder/")) == "~/folder"

    def test_pathlib_path_edge_cases_posix_pure_posix_path(self):
        assert str(PurePosixPath("C:/")) == "C:"
        assert str(PurePosixPath("C:/Users/test/")) == "C:/Users/test"
        assert str(PurePosixPath("C:/Users/test\\")) == "C:/Users/test\\"
        assert str(PurePosixPath("C://Users///test")) == "C:/Users/test"
        assert str(PurePosixPath("C:/Users/TEST/")) == "C:/Users/TEST"
        assert str(PurePosixPath("\\\\server\\folder")) == "\\\\server\\folder"
        assert str(PurePosixPath("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
        assert str(PurePosixPath("\\\\\\server\\\\folder")) == "\\\\\\server\\\\folder"
        assert str(PurePosixPath("\\\\wsl.localhost\\path\\to\\file")) == "\\\\wsl.localhost\\path\\to\\file"
        assert str(PurePosixPath("\\\\wsl.localhost\\path\\to\\file with space ")) == "\\\\wsl.localhost\\path\\to\\file with space "
        assert str(PurePosixPath("C:/Users/test folder/")) == "C:/Users/test folder"
        assert str(PurePosixPath("C:/Users/üser/")) == "C:/Users/üser"
        assert str(PurePosixPath("C:/Users/test\\nfolder/")) == "C:/Users/test\\nfolder"
        assert str(PurePosixPath("C:/Users").joinpath("test/")) == "C:/Users/test"
        assert str(PurePosixPath("C:/Users") / "test/") == "C:/Users/test"
        assert str(PurePosixPath("C:/Users") / "test/") == "C:/Users/test"
        assert str(PurePosixPath("")) == "."
        assert str(PurePosixPath("//")) == "//"
        assert str(PurePosixPath("C:")) == "C:"
        assert str(PurePosixPath("///")) == "/"
        assert str(PurePosixPath("C:/./Users/../test/")) == "C:/Users/../test"
        assert str(PurePosixPath("~/folder/")) == "~/folder"

    @unittest.skipIf(os.name != "nt", "Test only supported on NT systems.")
    def test_pathlib_path_edge_cases_windows_windows_path(self):
        assert str(WindowsPath("C:/")) == "C:\\"
        assert str(WindowsPath("C:\\")) == "C:\\"
        assert str(WindowsPath("C:/Users/test/")) == "C:\\Users\\test"
        assert str(WindowsPath("C:/Users/test\\")) == "C:\\Users\\test"
        assert str(WindowsPath("C://Users///test")) == "C:\\Users\\test"
        assert str(WindowsPath("C:/Users/TEST/")) == "C:\\Users\\TEST"
        assert str(WindowsPath("\\\\server\\folder")) == "\\\\server\\folder\\"
        if sys.version_info < (3, 12):
            assert str(WindowsPath("\\\\\\\\server\\folder/")) == "\\server\\folder"
            assert str(WindowsPath("\\\\\\server\\\\folder")) == "\\server\\folder"
        else:
            assert str(WindowsPath("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
            assert str(WindowsPath("\\\\\\server\\\\folder")) == "\\\\\\server\\folder"
        assert str(WindowsPath("\\\\wsl.localhost\\path\\to\\file")) == "\\\\wsl.localhost\\path\\to\\file"
        assert str(WindowsPath("\\\\wsl.localhost\\path\\to\\file with space ")) == "\\\\wsl.localhost\\path\\to\\file with space "
        assert str(WindowsPath("C:/Users/test folder/")) == "C:\\Users\\test folder"
        assert str(WindowsPath("C:/Users/üser/")) == "C:\\Users\\üser"
        assert str(WindowsPath("C:/Users/test\\nfolder/")) == "C:\\Users\\test\\nfolder"
        assert str(WindowsPath("C:/Users").joinpath("test/")) == "C:\\Users\\test"
        assert str(WindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(WindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(WindowsPath("")) == "."
        if sys.version_info < (3, 12):
            assert str(WindowsPath("//")) == "\\"
            assert str(WindowsPath("///")) == "\\"
        else:
            assert str(WindowsPath("//")) == "\\\\"
            assert str(WindowsPath("///")) == "\\\\\\"
        assert str(WindowsPath("C:")) == "C:"
        assert str(WindowsPath("C:/./Users/../test/")) == "C:\\Users\\..\\test"
        assert str(WindowsPath("~/folder/")) == "~\\folder"

    def test_pathlib_path_edge_cases_windows_pure_windows_path(self):
        assert str(PureWindowsPath("C:/")) == "C:\\"
        assert str(PureWindowsPath("C:\\")) == "C:\\"
        assert str(PureWindowsPath("C:/Users/test/")) == "C:\\Users\\test"
        assert str(PureWindowsPath("C:/Users/test\\")) == "C:\\Users\\test"
        assert str(PureWindowsPath("C://Users///test")) == "C:\\Users\\test"
        assert str(PureWindowsPath("C:/Users/TEST/")) == "C:\\Users\\TEST"
        assert str(PureWindowsPath("\\\\server\\folder")) == "\\\\server\\folder\\"
        if sys.version_info < (3, 12):
            assert str(PureWindowsPath("\\\\\\\\server\\folder/")) == "\\server\\folder"
            assert str(PureWindowsPath("\\\\\\server\\\\folder")) == "\\server\\folder"
        else:
            assert str(PureWindowsPath("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
            assert str(PureWindowsPath("\\\\\\server\\\\folder")) == "\\\\\\server\\folder"
        assert str(PureWindowsPath("\\\\wsl.localhost\\path\\to\\file")) == "\\\\wsl.localhost\\path\\to\\file"
        assert str(PureWindowsPath("\\\\wsl.localhost\\path\\to\\file with space ")) == "\\\\wsl.localhost\\path\\to\\file with space "
        assert str(PureWindowsPath("C:/Users/test folder/")) == "C:\\Users\\test folder"
        assert str(PureWindowsPath("C:/Users/üser/")) == "C:\\Users\\üser"
        assert str(PureWindowsPath("C:/Users/test\\nfolder/")) == "C:\\Users\\test\\nfolder"
        assert str(PureWindowsPath("C:/Users").joinpath("test/")) == "C:\\Users\\test"
        assert str(PureWindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(PureWindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(PureWindowsPath("")) == "."
        if sys.version_info < (3, 12):
            assert str(PureWindowsPath("//")) == "\\"
            assert str(PureWindowsPath("///")) == "\\"
        else:
            assert str(PureWindowsPath("//")) == "\\\\"
            assert str(PureWindowsPath("///")) == "\\\\\\"
        assert str(PureWindowsPath("C:")) == "C:"
        assert str(PureWindowsPath("C:/./Users/../test/")) == "C:\\Users\\..\\test"
        assert str(PureWindowsPath("~/folder/")) == "~\\folder"

    def test_pathlib_path_edge_cases_os_specific_path(self):
        assert str(Path("C:\\")) == "C:\\"
        if os.name == "nt":
            assert str(Path("C:/")) == "C:\\"
        else:
            assert str(Path("C:/")) == "C:"
        assert str(Path("C:")) == "C:"
        assert str(Path("C:/Users/test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(Path("C://Users///test")) == "C:/Users/test".replace("/", os.sep)
        assert str(Path("C:/Users/TEST/")) == "C:/Users/TEST".replace("/", os.sep)
        if os.name == "posix":
            assert str(Path("C:/Users/test\\")) == "C:/Users/test\\"
            assert str(Path("C:/")) == "C:"
        elif os.name == "nt":
            assert str(Path("C:/Users/test")) == "C:\\Users\\test"
            assert str(Path("C:/")) == "C:\\"

        assert str(Path("\\\\wsl.localhost\\path\\to\\file")) == "\\\\wsl.localhost\\path\\to\\file"
        assert str(Path("\\\\wsl.localhost\\path\\to\\file with space ")) == "\\\\wsl.localhost\\path\\to\\file with space "
        if os.name == "posix":
            assert str(Path("\\\\server\\folder")) == "\\\\server\\folder"
            assert str(Path("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
            assert str(Path("\\\\\\server\\\\folder")) == "\\\\\\server\\\\folder"
        elif os.name == "nt":
            assert str(Path("\\\\server\\folder")) == "\\\\server\\folder\\"
            if sys.version_info < (3, 12):
                assert str(Path("\\\\\\\\server\\folder/")) == "\\server\\folder"
                assert str(Path("\\\\\\server\\\\folder")) == "\\server\\folder"
            else:
                assert str(Path("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
                assert str(Path("\\\\\\server\\\\folder")) == "\\\\\\server\\folder"

        assert str(Path("C:/Users/test folder/")) == "C:/Users/test folder".replace("/", os.sep)
        assert str(Path("C:/Users/üser/")) == "C:/Users/üser".replace("/", os.sep)
        assert str(Path("C:/Users/test\\nfolder/")) == "C:/Users/test\\nfolder".replace("/", os.sep)

        assert str(Path("C:/Users").joinpath("test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(Path("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(Path("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)

        assert str(Path("")) == "."
        if os.name == "posix":
            assert str(Path("//")) == "//".replace("/", os.sep)
        elif sys.version_info < (3, 12):
            assert str(Path("//")) == "\\"
        else:
            assert str(Path("//")) == "\\\\"
        assert str(Path("C:")) == "C:"
        if sys.version_info < (3, 12) or os.name != "nt":
            assert str(Path("///")) == "/".replace("/", os.sep)
        else:
            assert str(Path("///")) == "///".replace("/", os.sep)
        assert str(Path("C:/./Users/../test/")) == "C:/Users/../test".replace("/", os.sep)
        assert str(Path("~/folder/")) == "~/folder".replace("/", os.sep)

    def test_pathlib_path_edge_cases_os_specific_pure_path(self):
        assert str(PurePath("C:\\")) == "C:\\"
        assert str(PurePath("C:/Users/test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(PurePath("C://Users///test")) == "C:/Users/test".replace("/", os.sep)
        assert str(PurePath("C:/Users/TEST/")) == "C:/Users/TEST".replace("/", os.sep)
        if os.name == "posix":
            assert str(PurePath("C:/Users/test\\")) == "C:/Users/test\\"
            assert str(PurePath("C:/")) == "C:"
        elif os.name == "nt":
            assert str(PurePath("C:/Users/test")) == "C:\\Users\\test"
            assert str(PurePath("C:/")) == "C:\\"

        assert str(PurePath("\\\\wsl.localhost\\path\\to\\file")) == "\\\\wsl.localhost\\path\\to\\file"
        assert str(PurePath("\\\\wsl.localhost\\path\\to\\file with space ")) == "\\\\wsl.localhost\\path\\to\\file with space "
        if os.name == "posix":
            assert str(PurePath("\\\\server\\folder")) == "\\\\server\\folder"
            assert str(PurePath("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
            assert str(PurePath("\\\\\\server\\\\folder")) == "\\\\\\server\\\\folder"
        elif os.name == "nt":
            assert str(PurePath("\\\\server\\folder")) == "\\\\server\\folder\\"
            if sys.version_info < (3, 12):
                assert str(PurePath("\\\\\\\\server\\folder/")) == "\\server\\folder"
                assert str(PurePath("\\\\\\server\\\\folder")) == "\\server\\folder"
            else:
                assert str(PurePath("\\\\\\\\server\\folder/")) == "\\\\\\\\server\\folder"
                assert str(PurePath("\\\\\\server\\\\folder")) == "\\\\\\server\\folder"

        assert str(PurePath("C:/Users/test folder/")) == "C:/Users/test folder".replace("/", os.sep)
        assert str(PurePath("C:/Users/üser/")) == "C:/Users/üser".replace("/", os.sep)
        assert str(PurePath("C:/Users/test\\nfolder/")) == "C:/Users/test\\nfolder".replace("/", os.sep)

        assert str(PurePath("C:/Users").joinpath("test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(PurePath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(PurePath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)

        assert str(PurePath("")) == "."
        if os.name == "posix":
            assert str(PurePath("//")) == "//".replace("/", os.sep)
        elif sys.version_info < (3, 12):
            assert str(PurePath("//")) == "\\"
        else:
            assert str(PurePath("//")) == "\\\\"
        assert str(PurePath("C:")) == "C:"
        if sys.version_info < (3, 12) or os.name != "nt":
            assert str(PurePath("///")) == "/".replace("/", os.sep)
        else:
            assert str(PurePath("///")) == "///".replace("/", os.sep)
        assert str(PurePath("C:/./Users/../test/")) == "C:/Users/../test".replace("/", os.sep)
        assert str(PurePath("~/folder/")) == "~/folder".replace("/", os.sep)

    @unittest.skipIf(os.name == "nt", "Test only supported on POSIX systems.")
    def test_custom_path_edge_cases_posix_custom_posix_path(self):
        assert str(CustomPosixPath("C:/")) == "C:"
        assert str(CustomPosixPath("C:/Users/test/")) == "C:/Users/test"
        assert str(CustomPosixPath("C:/Users/test\\")) == "C:/Users/test"
        assert str(CustomPosixPath("C://Users///test")) == "C:/Users/test"
        assert str(CustomPosixPath("C:/Users/TEST/")) == "C:/Users/TEST"
        assert str(CustomPosixPath("C:/Users/test folder/")) == "C:/Users/test folder"
        assert str(CustomPosixPath("C:/Users/üser/")) == "C:/Users/üser"
        assert str(CustomPosixPath("C:/Users/test\\nfolder/")) == "C:/Users/test/nfolder"
        assert str(CustomPosixPath("C:/Users").joinpath("test/")) == "C:/Users/test"
        assert str(CustomPosixPath("C:/Users") / "test/") == "C:/Users/test"
        assert str(CustomPosixPath("C:/Users") / "test/") == "C:/Users/test"
        assert str(CustomPosixPath("")) == "."
        assert str(CustomPosixPath("//")) == "/"
        assert str(CustomPosixPath("///")) == "/"
        if os.name == "nt":
            assert str(CustomPosixPath("C:/./Users/../test/")) == "C:/test"
        else:
            assert str(CustomPosixPath("C:/./Users/../test/")) == "C:/Users/../test"
        assert str(CustomPosixPath("C:")) == "C:"
        assert str(CustomPosixPath("~/folder/")) == "~/folder"

    def test_custom_path_edge_cases_posix_custom_pure_posix_path(self):
        assert str(CustomPurePosixPath("C:/")) == "C:"
        assert str(CustomPurePosixPath("C:/Users/test/")) == "C:/Users/test"
        assert str(CustomPurePosixPath("C:/Users/test\\")) == "C:/Users/test"
        assert str(CustomPurePosixPath("C://Users///test")) == "C:/Users/test"
        assert str(CustomPurePosixPath("C:/Users/TEST/")) == "C:/Users/TEST"
        assert str(CustomPurePosixPath("C:/Users/test folder/")) == "C:/Users/test folder"
        assert str(CustomPurePosixPath("C:/Users/üser/")) == "C:/Users/üser"
        assert str(CustomPurePosixPath("C:/Users/test\\nfolder/")) == "C:/Users/test/nfolder"
        assert str(CustomPurePosixPath("C:/Users").joinpath("test/")) == "C:/Users/test"
        assert str(CustomPurePosixPath("C:/Users") / "test/") == "C:/Users/test"
        assert str(CustomPurePosixPath("C:/Users") / "test//") == "C:/Users/test"
        assert str(CustomPurePosixPath("")) == "."
        assert str(CustomPurePosixPath("//")) == "/"
        assert str(CustomPurePosixPath("///")) == "/"
        assert str(CustomPurePosixPath("C:/./Users/../test/")) == "C:/Users/../test"
        assert os.path.normpath(str(CustomPurePosixPath("C:/./Users/../test/"))) == f"C:{os.path.sep}test"
        assert str(CustomPurePosixPath("C:")) == "C:"
        assert str(CustomPurePosixPath("~/folder/")) == "~/folder".replace("\\", "/")

    @unittest.skipIf(os.name != "nt", "Test only supported on NT systems.")
    def test_custom_path_edge_cases_windows_custom_windows_path(self):
        assert str(CustomWindowsPath("C:/")) == "C:"
        assert str(CustomWindowsPath("C:\\")) == "C:"
        assert str(CustomWindowsPath("C:")) == "C:"
        assert str(CustomWindowsPath("C:/Users/test/")) == "C:\\Users\\test"
        assert str(CustomWindowsPath("C:/Users/test\\")) == "C:\\Users\\test"
        assert str(CustomWindowsPath("C://Users///test")) == "C:\\Users\\test"
        assert str(CustomWindowsPath("C:/Users/TEST/")) == "C:\\Users\\TEST"
        assert str(CustomWindowsPath("C:/Users/test folder/")) == "C:\\Users\\test folder"
        assert str(CustomWindowsPath("C:/Users/üser/")) == "C:\\Users\\üser"
        assert str(CustomWindowsPath("C:/Users/test\\nfolder/")) == "C:\\Users\\test\\nfolder"
        assert str(CustomWindowsPath("C:/Users").joinpath("test/")) == "C:\\Users\\test"
        assert str(CustomWindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(CustomWindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(CustomWindowsPath("")) == "."
        assert str(CustomWindowsPath("//")) == "."
        assert str(CustomWindowsPath("///")) == "."
        assert str(CustomWindowsPath("C:")) == "C:"
        assert str(CustomWindowsPath("C:/./Users/../test/")) == "C:\\Users\\..\\test"
        assert str(CustomWindowsPath("C:/./Users/../test/").resolve()) == "C:\\test"
        assert str(CustomWindowsPath("~/folder/")) == "~\\folder"

    def test_custom_path_edge_cases_windows_custom_pure_windows_path(self):
        assert str(CustomPureWindowsPath("C:/")) == "C:"
        assert str(CustomPureWindowsPath("C:\\")) == "C:"
        assert str(CustomPureWindowsPath("C:")) == "C:"
        assert str(CustomPureWindowsPath("C:/Users/test/")) == "C:\\Users\\test"
        assert str(CustomPureWindowsPath("C:/Users/test\\")) == "C:\\Users\\test"
        assert str(CustomPureWindowsPath("C://Users///test")) == "C:\\Users\\test"
        assert str(CustomPureWindowsPath("C:/Users/TEST/")) == "C:\\Users\\TEST"
        assert str(CustomPureWindowsPath("C:/Users/test folder/")) == "C:\\Users\\test folder"
        assert str(CustomPureWindowsPath("C:/Users/üser/")) == "C:\\Users\\üser"
        assert str(CustomPureWindowsPath("C:/Users/test\\nfolder/")) == "C:\\Users\\test\\nfolder"
        assert str(CustomPureWindowsPath("C:/Users").joinpath("test/")) == "C:\\Users\\test"
        assert str(CustomPureWindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(CustomPureWindowsPath("C:/Users") / "test/") == "C:\\Users\\test"
        assert str(CustomPureWindowsPath("")) == "."
        assert str(CustomPureWindowsPath("//")) == "."
        assert str(CustomPureWindowsPath("///")) == "."
        assert str(CustomPureWindowsPath("C:")) == "C:"
        assert str(CustomPureWindowsPath("C:/./Users/../test/")) == "C:\\Users\\..\\test"
        if os.name == "nt":
            assert os.path.normpath(str(CustomPureWindowsPath("C:/./Users/../test/"))) == f"C:{os.path.sep}test"
        assert str(CustomPureWindowsPath("~/folder/")) == "~\\folder"

    def test_custom_path_edge_cases_os_specific_case_aware_path(self):
        assert str(CaseAwarePath("C:/")) == "C:"
        assert str(CaseAwarePath("C:\\")) == "C:"
        assert str(CaseAwarePath("C:")) == "C:"
        assert str(CaseAwarePath("C:/Users/test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users/test\\")) == "C:/Users/test".replace("/", os.sep)
        assert str(CaseAwarePath("C://Users///test")) == "C:/Users/test".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users/TEST/")) == "C:/Users/TEST".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users/test folder/")) == "C:/Users/test folder".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users/üser/")) == "C:/Users/üser".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users/test\\nfolder/")) == "C:/Users/test/nfolder".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users").joinpath("test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(CaseAwarePath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(CaseAwarePath("")) == "."
        assert str(CaseAwarePath("C:/./Users/../test/")) == "C:/Users/../test".replace("/", os.sep)
        if os.name == "nt":
            assert str(CaseAwarePath("C:/./Users/../test/").resolve()) == "C:/test".replace("/", os.sep)
        assert str(CaseAwarePath("C:\\.\\Users\\..\\test\\")) == "C:/Users/../test".replace("/", os.sep)
        assert str(CaseAwarePath("~/folder/")) == "~/folder".replace("/", os.sep)
        assert str(CaseAwarePath("C:")) == "C:".replace("/", os.sep)
        if os.name == "posix":
            assert str(CaseAwarePath("//")) == "/"
            assert str(CaseAwarePath("///")) == "/"
        elif os.name == "nt":
            assert str(CaseAwarePath("//")) == "."
            assert str(CaseAwarePath("///")) == "."

    def test_custom_path_edge_cases_os_specific_custom_path(self):
        assert str(CustomPath("C:/")) == "C:"
        assert str(CustomPath("C:\\")) == "C:"
        assert str(CustomPath("C:")) == "C:"
        assert str(CustomPath("C:/Users/test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPath("C:/Users/test\\")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPath("C://Users///test")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPath("C:/Users/TEST/")) == "C:/Users/TEST".replace("/", os.sep)
        assert str(CustomPath("C:/Users/test folder/")) == "C:/Users/test folder".replace("/", os.sep)
        assert str(CustomPath("C:/Users/üser/")) == "C:/Users/üser".replace("/", os.sep)
        assert str(CustomPath("C:/Users/test\\nfolder/")) == "C:/Users/test/nfolder".replace("/", os.sep)
        assert str(CustomPath("C:/Users").joinpath("test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPath("")) == "."
        assert str(CustomPath("C:/./Users/../test/")) == "C:/Users/../test".replace("/", os.sep)
        assert str(CustomPath("C:\\.\\Users\\..\\test\\")) == "C:/Users/../test".replace("/", os.sep)
        assert str(CustomPath("~/folder/")) == "~/folder".replace("/", os.sep)
        assert str(CustomPath("C:")) == "C:".replace("/", os.sep)
        if os.name == "posix":
            assert str(CustomPath("//")) == "/"
            assert str(CustomPath("///")) == "/"
        elif os.name == "nt":
            assert str(CustomPath("//")) == "."
            assert str(CustomPath("///")) == "."

    def test_custom_path_edge_cases_os_specific_custom_pure_path(self):
        assert str(CustomPurePath("C:/")) == "C:"
        assert str(CustomPurePath("C:\\")) == "C:"
        assert str(CustomPurePath("C:")) == "C:"
        assert str(CustomPurePath("C:/Users/test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users/test\\")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPurePath("C://Users///test")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users/TEST/")) == "C:/Users/TEST".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users/test folder/")) == "C:/Users/test folder".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users/üser/")) == "C:/Users/üser".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users/test\\nfolder/")) == "C:/Users/test/nfolder".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users").joinpath("test/")) == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPurePath("C:/Users") / "test/") == "C:/Users/test".replace("/", os.sep)
        assert str(CustomPurePath("")) == "."
        assert str(CustomPurePath("C:/./Users/../test/")) == "C:\\Users\\..\\test".replace("/", os.sep).replace("\\", os.sep)
        assert os.path.normpath(str(CustomPurePath("C:/./Users/../test/"))) == "C:\\test".replace("/", os.sep).replace("\\", os.sep)
        assert str(CustomPurePath("C:\\.\\Users\\..\\test\\")) == "C:\\Users\\..\\test".replace("/", os.sep).replace("\\", os.sep)
        assert str(CustomPurePath("~/folder/")) == "~/folder".replace("/", os.sep)
        assert str(CustomPurePath("C:")) == "C:".replace("/", os.sep)
        if os.name == "posix":
            assert str(CustomPurePath("//")) == "/"
            assert str(CustomPurePath("///")) == "/"
        elif os.name == "nt":
            assert str(CustomPurePath("//")) == "."
            assert str(CustomPurePath("///")) == "."


if __name__ == "__main__":
    unittest.main()
