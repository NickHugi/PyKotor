from __future__ import annotations

import os
import pathlib
import sys
import unittest
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
from utility.system.path import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath


class TestPathInheritance(unittest.TestCase):
    def test_nt_case_hashing(self):
        test_classes: tuple[type, ...] = (PureWindowsPath,) if os.name == "posix" else (WindowsPath, PureWindowsPath, Path)
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                path1 = PathType("test\\path\\to\\nothing")
                path2 = PathType("tesT\\PATH\\\\to\\noTHinG\\")

            with mock.patch("os.name", "nt"):
                test_set = {path1, path2}
                self.assertEqual(path1, path2)
                self.assertEqual(hash(path1), hash(path2))
                self.assertSetEqual(test_set, {PathType("TEST\\path\\to\\\\nothing")})

    def test_path_attributes(self):
        self.assertIs(PureWindowsPath("mypath").__class__, PureWindowsPath)
        self.assertIs(PurePath("mypath").__class__, PurePosixPath if os.name == "posix" else PureWindowsPath)
        self.assertIs(PurePosixPath("mypath").__class__, PurePosixPath)
        if os.name == "nt":
            self.assertIs(WindowsPath("mypath").__class__, WindowsPath)
        else:
            self.assertIs(PosixPath("mypath").__class__, PosixPath)

        self.assertIs(Path("mypath").__class__, PosixPath if os.name == "posix" else WindowsPath)
        self.assertIs(CaseAwarePath("mypath").__class__, CaseAwarePath)
        self.assertIs(PureWindowsPath("mypath").__class__.__base__, PurePath)
        self.assertIs(PurePath("mypath").__class__.__base__, PurePath)
        self.assertIs(PurePosixPath("mypath").__class__.__base__, PurePath)
        if os.name == "nt":
            self.assertIs(WindowsPath("mypath").__class__.__base__, Path)
        else:
            self.assertIs(PosixPath("mypath").__class__.__base__, Path)
        self.assertIs(Path("mypath").__class__.__base__, Path)
        self.assertIs(CaseAwarePath("mypath").__class__.__base__, WindowsPath if os.name == "nt" else PosixPath)

    def test_path_hashing(self):
        test_list = [Path("/mnt/c/Program Files (x86)/steam/steamapps/common/swkotor/saves")]
        if os.name == "posix":
            self.assertNotIn(Path("/MNT/c/Program FileS (x86)/steam/steamapps/common/swkotor/saves"), test_list)
        self.assertIn(Path("/mnt/c/Program Files (x86)/steam/steamapps/common/swkotor/saves"), test_list)

    def test_pure_windows_path_isinstance(self):
        self.assertIsInstance(PureWindowsPath("mypath"), PurePath)
        self.assertTrue(issubclass(PureWindowsPath, PurePath))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pure_posix_path_isinstance(self):
        self.assertIsInstance(PurePosixPath("mypath"), PurePath)
        self.assertTrue(issubclass(PurePosixPath, PurePath))

    def test_path_isinstance(self):
        self.assertIsInstance(Path("mypath"), PurePath)
        self.assertTrue(issubclass(Path, PurePath))

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_windows_path_isinstance(self):
        self.assertIsInstance(WindowsPath("mypath"), PurePath)
        self.assertTrue(issubclass(WindowsPath, PurePath))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_posix_path_isinstance(self):
        self.assertIsInstance(PosixPath("mypath"), PurePath)
        self.assertTrue(issubclass(PosixPath, PurePath))

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_windows_path_isinstance_path(self):
        self.assertIsInstance(WindowsPath("mypath"), Path)
        self.assertTrue(issubclass(WindowsPath, Path))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_posix_path_isinstance_path(self):
        self.assertIsInstance(PosixPath("mypath"), Path)
        self.assertTrue(issubclass(PosixPath, Path))

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_purepath_not_isinstance_windows_path(self):
        self.assertNotIsInstance(PurePath("mypath"), WindowsPath)
        self.assertFalse(issubclass(PurePath, WindowsPath))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_purepath_not_isinstance_posix_path(self):
        self.assertNotIsInstance(PurePath("mypath"), PosixPath)
        self.assertFalse(issubclass(PurePath, PosixPath))

    def test_purepath_not_isinstance_path(self):
        self.assertNotIsInstance(PurePath("mypath"), Path)
        self.assertFalse(issubclass(PurePath, Path))

    def test_pathlib_pure_windows_path_isinstance(self):
        self.assertIsInstance(PureWindowsPath("mypath"), pathlib.PurePath)
        self.assertTrue(issubclass(PureWindowsPath, pathlib.PurePath))
        self.assertIsInstance(pathlib.PureWindowsPath("mypath"), PurePath)
        self.assertTrue(issubclass(pathlib.PureWindowsPath, PurePath))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_pure_posix_path_isinstance(self):
        self.assertIsInstance(PurePosixPath("mypath"), pathlib.PurePath)
        self.assertTrue(issubclass(PurePosixPath, pathlib.PurePath))
        self.assertIsInstance(pathlib.PurePosixPath("mypath"), PurePath)
        self.assertTrue(issubclass(pathlib.PurePosixPath, PurePath))

    def test_pathlib_path_isinstance(self):
        self.assertIsInstance(Path("mypath"), pathlib.PurePath)
        self.assertTrue(issubclass(Path, pathlib.PurePath))
        self.assertIsInstance(pathlib.Path("mypath"), PurePath)
        self.assertTrue(issubclass(pathlib.Path, PurePath))

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_pathlib_windows_path_isinstance(self):
        self.assertIsInstance(WindowsPath("mypath"), pathlib.PurePath)
        self.assertTrue(issubclass(WindowsPath, pathlib.PurePath))
        self.assertIsInstance(pathlib.WindowsPath("mypath"), PurePath)
        self.assertTrue(issubclass(pathlib.WindowsPath, PurePath))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_posix_path_isinstance(self):
        self.assertIsInstance(PosixPath("mypath"), pathlib.PurePath)
        self.assertTrue(issubclass(PosixPath, pathlib.PurePath))
        self.assertIsInstance(pathlib.PosixPath("mypath"), PurePath)
        self.assertTrue(issubclass(pathlib.PosixPath, PurePath))

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_pathlib_windows_path_isinstance_path(self):
        self.assertIsInstance(WindowsPath("mypath"), pathlib.Path)
        self.assertTrue(issubclass(WindowsPath, pathlib.Path))
        self.assertIsInstance(pathlib.WindowsPath("mypath"), Path)
        self.assertTrue(issubclass(pathlib.WindowsPath, Path))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_posix_path_isinstance_path(self):
        self.assertIsInstance(PosixPath("mypath"), pathlib.Path)
        self.assertTrue(issubclass(PosixPath, pathlib.Path))
        self.assertIsInstance(pathlib.PosixPath("mypath"), Path)
        self.assertTrue(issubclass(pathlib.PosixPath, Path))

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_pathlib_purepath_not_isinstance_windows_path(self):
        self.assertNotIsInstance(PurePath("mypath"), pathlib.WindowsPath)
        self.assertFalse(issubclass(PurePath, pathlib.WindowsPath))
        self.assertNotIsInstance(pathlib.PurePath("mypath"), WindowsPath)
        self.assertFalse(issubclass(pathlib.PurePath, WindowsPath))

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_purepath_not_isinstance_posix_path(self):
        self.assertNotIsInstance(PurePath("mypath"), pathlib.PosixPath)
        self.assertFalse(issubclass(PurePath, pathlib.PosixPath))
        self.assertNotIsInstance(pathlib.PurePath("mypath"), PosixPath)
        self.assertFalse(issubclass(pathlib.PurePath, PosixPath))

    def test_pathlib_purepath_not_isinstance_path(self):
        self.assertNotIsInstance(PurePath("mypath"), pathlib.Path)
        self.assertFalse(issubclass(PurePath, pathlib.Path))
        self.assertNotIsInstance(pathlib.PurePath("mypath"), Path)
        self.assertFalse(issubclass(pathlib.PurePath, Path))


if __name__ == "__main__":
    unittest.main()
