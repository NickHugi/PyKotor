import os
import unittest
from unittest.mock import patch
from pykotor.tools.path import PurePosixPath as CustomPurePosixPath
from pykotor.tools.path import PureWindowsPath as CustomPureWindowsPath
from pykotor.tools.path import WindowsPath as CustomWindowsPath
from pykotor.tools.path import PosixPath as CustomPosixPath

from pykotor.tools.path import PurePath as CustomPurePath
from pykotor.tools.path import Path as CustomPath
from pykotor.tools.path import CaseAwarePath
from pathlib import PurePath, Path, PurePosixPath, PureWindowsPath, WindowsPath, PosixPath


class TestPathlibMixedSlashes(unittest.TestCase):
    def test_pathlib_path_edge_cases_posix(self):
        if os.name == "nt":
            print("Test isn't possible on windows")
            return
        for PathType in [PosixPath, PurePosixPath]:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/test")), "C:/Users/test")
                self.assertEqual(str(PathType("C://Users///test")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:/Users/TEST")

                # Network Paths
                self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                self.assertNotEqual(str(PathType("\\\\\\\\server\\folder/")), "/server/folder")
                self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "/server/folder")
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                    "/wsl.localhost/path/to/file with space",
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
                self.assertNotEqual(str(PathType("")), "")
                self.assertEqual(str(PathType("//")), ".")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("///")), ".")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test")
                self.assertEqual(str(PathType("~/folder/")), "~/folder")

    def test_pathlib_path_edge_cases_windows(self):
        for PathType in [Path, WindowsPath, PurePath, PureWindowsPath]:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertNotEqual(str(PathType("C:/")), "C:")
                self.assertNotEqual(str(PathType("C:\\")), "C:")
                self.assertNotEqual(str(PathType("C:/")), "C:")
                self.assertNotEqual(str(PathType("C:\\")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/test")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C://Users///test")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                self.assertNotEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                self.assertNotEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                self.assertNotEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\server\\folder")
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                    "\\\\wsl.localhost\\path\\to\\file with space",
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
                self.assertNotEqual(str(PathType("")), "")
                self.assertNotEqual(str(PathType("//")), ".")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertNotEqual(str(PathType("///")), ".")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_pathlib_path_edge_cases_os_specific(self):
        for PathType in [Path, PurePath]:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                if os.name == "posix":
                    self.assertEqual(str(PathType("C:/")), "C:")
                    self.assertNotEqual(str(PathType("C:\\")), "C:")
                    self.assertNotEqual(str(PathType("C:/Users/test/")), "C:\\Users\\test")
                    self.assertNotEqual(str(PathType("C:/Users/test")), "C:\\Users\\test")
                    self.assertNotEqual(str(PathType("C://Users///test")), "C:\\Users\\test")
                    self.assertNotEqual(str(PathType("C:/Users/TEST/")), "C:\\Users\\TEST")
                elif os.name == "nt":
                    self.assertNotEqual(str(PathType("C:/")), "C:")
                    self.assertNotEqual(str(PathType("C:\\")), "C:")
                    self.assertEqual(str(PathType("C:/Users/test/")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users/test")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C://Users///test")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                if os.name == "posix":
                    self.assertNotEqual(str(PathType("\\\\server\\folder")), "/server/folder")
                    self.assertNotEqual(str(PathType("\\\\\\\\server\\folder/")), "/server/folder")
                    self.assertNotEqual(str(PathType("\\\\\\server\\\\folder")), "/server/folder")
                    self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                    self.assertEqual(
                        str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                        "/wsl.localhost/path/to/file with space",
                    )
                elif os.name == "nt":
                    self.assertNotEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertNotEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                    self.assertNotEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                    self.assertEqual(
                        str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                        "\\\\wsl.localhost\\path\\to\\file with space",
                    )

                # Special Characters
                if os.name == "posix":
                    self.assertEqual(str(PathType("C:/Users/test folder/")), "C:/Users/test folder")
                    self.assertNotEqual(str(PathType("C:/Users/üser/")), "C:/Users/üser")
                    self.assertNotEqual(str(PathType("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("C:/Users/test folder/")), "C:\\Users\\test folder")
                    self.assertEqual(str(PathType("C:/Users/üser/")), "C:\\Users\\üser")
                    self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")

                # Joinpath, rtruediv, truediv
                if os.name == "posix":
                    self.assertNotEqual(str(PathType("C:/Users").joinpath("test/")), "C:/Users/test")
                    self.assertNotEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test")
                    self.assertNotEqual(str(PathType("C:/Users").__truediv__("test/")), "C:/Users/test")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users") / "test/"), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:\\Users\\test")

                # Bizarre Scenarios
                if os.name == "posix":
                    self.assertNotEqual(str(PathType("")), "")
                    self.assertNotEqual(str(PathType("//")), ".")
                    self.assertNotEqual(str(PathType("C:")), "C:")
                    self.assertNotEqual(str(PathType("///")), ".")
                    self.assertNotEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test")
                    self.assertNotEqual(str(PathType("~/folder/")), "~/folder")
                elif os.name == "nt":
                    self.assertNotEqual(str(PathType("")), "")
                    self.assertNotEqual(str(PathType("//")), ".")
                    self.assertEqual(str(PathType("C:")), "C:")
                    self.assertNotEqual(str(PathType("///")), ".")
                    self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                    self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_windows(self):
        for PathType in [CustomWindowsPath, CustomPureWindowsPath]:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/test")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C://Users///test")), "C:\\Users\\test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                if os.name == "nt":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                else:
                    self.assertNotEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertNotEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                    self.assertNotEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\server\\folder")
                    self.assertNotEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")

                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                    "\\\\wsl.localhost\\path\\to\\file with space",
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
                self.assertNotEqual(str(PathType("")), "")
                self.assertEqual(str(PathType("//")), ".")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("///")), ".")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_posix(self):
        for PathType in [CustomPosixPath, CustomPurePosixPath]:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                self.assertEqual(str(PathType("C:/Users/test/")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/test")), "C:/Users/test")
                self.assertEqual(str(PathType("C://Users///test")), "C:/Users/test")
                self.assertEqual(str(PathType("C:/Users/TEST/")), "C:/Users/TEST")

                # Network Paths
                self.assertEqual(str(PathType("\\\\server\\folder")), "/server/folder")
                self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "/server/folder")
                self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "/server/folder")
                self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                self.assertEqual(
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                    "/wsl.localhost/path/to/file with space",
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
                self.assertNotEqual(str(PathType("")), "")
                self.assertEqual(str(PathType("//")), ".")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("///")), ".")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test")
                self.assertEqual(str(PathType("~/folder/")), "~/folder")

    def test_custom_path_edge_cases_os_specific(self):
        for PathType in [CaseAwarePath, CustomPath, CustomPurePath]:
            with self.subTest(PathType=PathType):
                # Absolute vs Relative Paths
                self.assertEqual(str(PathType("C:/")), "C:")
                if os.name == "posix":
                    self.assertEqual(str(PathType("C:/")), "C:")
                    self.assertEqual(str(PathType("C:/Users/test/")), "C:/Users/test")
                    self.assertEqual(str(PathType("C:/Users/test")), "C:/Users/test")
                    self.assertEqual(str(PathType("C://Users///test")), "C:/Users/test")
                    self.assertEqual(str(PathType("C:/Users/TEST/")), "C:/Users/TEST")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("C:/Users/test/")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users/test")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C://Users///test")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                if os.name == "posix":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "/server/folder")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "/server/folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "/server/folder")
                    self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                    self.assertEqual(
                        str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                        "/wsl.localhost/path/to/file with space",
                    )
                elif os.name == "nt":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                    self.assertEqual(
                        str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                        "\\\\wsl.localhost\\path\\to\\file with space",
                    )

                # Special Characters
                if os.name == "posix":
                    self.assertEqual(str(PathType("C:/Users/test folder/")), "C:/Users/test folder")
                    self.assertEqual(str(PathType("C:/Users/üser/")), "C:/Users/üser")
                    self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("C:/Users/test folder/")), "C:\\Users\\test folder")
                    self.assertEqual(str(PathType("C:/Users/üser/")), "C:\\Users\\üser")
                    self.assertEqual(str(PathType("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")

                # Joinpath, rtruediv, truediv
                if os.name == "posix":
                    self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:/Users/test")
                    self.assertEqual(str(PathType("C:/Users") / "test/"), "C:/Users/test")
                    self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:/Users/test")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("C:/Users").joinpath("test/")), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users") / "test/"), "C:\\Users\\test")
                    self.assertEqual(str(PathType("C:/Users").__truediv__("test/")), "C:\\Users\\test")

                # Bizarre Scenarios
                if os.name == "posix":
                    self.assertNotEqual(str(PathType("")), "")
                    self.assertEqual(str(PathType("//")), ".")
                    self.assertEqual(str(PathType("C:")), "C:")
                    self.assertEqual(str(PathType("///")), ".")
                    self.assertEqual(str(PathType("C:/./Users/../test/")), "C:/Users/../test")
                    self.assertEqual(str(PathType("~/folder/")), "~/folder")
                elif os.name == "nt":
                    self.assertNotEqual(str(PathType("")), "")
                    self.assertEqual(str(PathType("//")), ".")
                    self.assertEqual(str(PathType("C:")), "C:")
                    self.assertEqual(str(PathType("///")), ".")
                    self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                    self.assertEqual(str(PathType("~/folder/")), "~\\folder")


if __name__ == "__main__":
    unittest.main()
