# Rigorously test the string result of each pathlib module.
# The goal isn't really to test pathlib.Path or pykotor\tools\path, the goal is to determine if there was a breaking change in a patch release.
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
        test_classes = [PosixPath, PurePosixPath] if os.name == "posix" else [PurePosixPath]
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
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                    "\\\\wsl.localhost\\path\\to\\file with space",
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
        test_classes = [WindowsPath, PureWindowsPath] if os.name == "nt" else [PureWindowsPath]
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
                self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\server\\folder")
                self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\server\\folder")
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
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("//")), "\\")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("///")), "\\")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_pathlib_path_edge_cases_os_specific(self):
        for PathType in [Path, PurePath]:
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
                    str(PathType("\\\\wsl.localhost\\path\\to\\file with space")),
                    "\\\\wsl.localhost\\path\\to\\file with space",
                )
                if os.name == "posix":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
                elif os.name == "nt":
                    self.assertEqual(str(PathType("\\\\server\\folder")), "\\\\server\\folder\\")
                    self.assertEqual(str(PathType("\\\\\\\\server\\folder/")), "\\server\\folder")
                    self.assertEqual(str(PathType("\\\\\\server\\\\folder")), "\\server\\folder")

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
                else:
                    self.assertEqual(str(PathType("//")), "\\")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("///")), "/".replace("/", os.sep))
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
                self.assertEqual(str(PathType("")), ".")
                self.assertEqual(str(PathType("//")), ".")
                self.assertEqual(str(PathType("///")), ".")
                self.assertEqual(str(PathType("C:")), "C:")
                self.assertEqual(str(PathType("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(PathType("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_os_specific(self):
        # sourcery skip: extract-duplicate-method
        for PathType in [CaseAwarePath, CustomPath, CustomPurePath]:
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
