# Rigorously test the string result of each pathlib module.
# The goal isn't really to test pathlib.Path or utility.path, the goal is to determine if there was a breaking change in a python patch release.
from __future__ import annotations

import os
import pathlib
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
from utility.path import Path as CustomPath
from utility.path import PosixPath as CustomPosixPath
from utility.path import PurePath as CustomPurePath
from utility.path import PurePosixPath as CustomPurePosixPath
from utility.path import PureWindowsPath as CustomPureWindowsPath
from utility.path import WindowsPath as CustomWindowsPath


class TestPathlibMixedSlashes(unittest.TestCase):

    def test_nt_case_hashing(self):
        test_classes: tuple[type, ...] = (
            (CustomPureWindowsPath)
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
