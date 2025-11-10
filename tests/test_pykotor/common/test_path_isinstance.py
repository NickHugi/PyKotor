from __future__ import annotations

import os
import pathlib
import sys
import unittest
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

from pathlib import (
    Path,
    PosixPath,
    PurePath,
    PurePosixPath,
    PureWindowsPath,
    WindowsPath,
)

from pykotor.tools.path import CaseAwarePath


class TestPathInheritance(unittest.TestCase):
    def test_nt_case_hashing(self):
        test_classes: tuple[type, ...] = (PureWindowsPath,) if os.name == "posix" else (WindowsPath, PureWindowsPath, Path)
        for PathType in test_classes:
            with self.subTest(PathType=PathType):
                path1 = PathType("test\\path\\to\\nothing")
                path2 = PathType("tesT\\PATH\\\\to\\noTHinG\\")

            with mock.patch("os.name", "nt"):
                test_set = {path1, path2}
                assert path1 == path2
                assert hash(path1) == hash(path2)
                self.assertSetEqual(test_set, {PathType("TEST\\path\\to\\\\nothing")})

    def test_path_attributes(self):
        assert PureWindowsPath("mypath").__class__ is PureWindowsPath
        assert PurePath("mypath").__class__ is (PurePosixPath if os.name == "posix" else PureWindowsPath)
        assert PurePosixPath("mypath").__class__ is PurePosixPath
        if os.name == "nt":
            assert WindowsPath("mypath").__class__ is WindowsPath
        else:
            assert PosixPath("mypath").__class__ is PosixPath

        assert Path("mypath").__class__ is (PosixPath if os.name == "posix" else WindowsPath)
        assert PureWindowsPath("mypath").__class__.__base__ is PurePath
        assert PurePath("mypath").__class__.__base__ is PurePath
        assert PurePosixPath("mypath").__class__.__base__ is PurePath
        if os.name == "nt":
            assert WindowsPath("mypath").__class__.__base__ is Path
        else:
            assert PosixPath("mypath").__class__.__base__ is Path
        assert Path("mypath").__class__.__base__ is Path

    def test_path_hashing(self):
        test_list = [Path("/mnt/c/Program Files (x86)/steam/steamapps/common/swkotor/saves")]
        if os.name == "posix":
            assert Path("/MNT/c/Program FileS (x86)/steam/steamapps/common/swkotor/saves") not in test_list
        assert Path("/mnt/c/Program Files (x86)/steam/steamapps/common/swkotor/saves") in test_list

    def test_pure_windows_path_isinstance(self):
        assert isinstance(PureWindowsPath("mypath"), PurePath)
        assert issubclass(PureWindowsPath, PurePath)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pure_posix_path_isinstance(self):
        assert isinstance(PurePosixPath("mypath"), PurePath)
        assert issubclass(PurePosixPath, PurePath)

    def test_path_isinstance(self):
        assert isinstance(Path("mypath"), PurePath)
        assert issubclass(Path, PurePath)

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_windows_path_isinstance(self):
        assert isinstance(WindowsPath("mypath"), PurePath)
        assert issubclass(WindowsPath, PurePath)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_posix_path_isinstance(self):
        assert isinstance(PosixPath("mypath"), PurePath)
        assert issubclass(PosixPath, PurePath)

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_windows_path_isinstance_path(self):
        assert isinstance(WindowsPath("mypath"), Path)
        assert issubclass(WindowsPath, Path)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_posix_path_isinstance_path(self):
        assert isinstance(PosixPath("mypath"), Path)
        assert issubclass(PosixPath, Path)

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_purepath_not_isinstance_windows_path(self):
        assert not isinstance(PurePath("mypath"), WindowsPath)
        assert not issubclass(PurePath, WindowsPath)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_purepath_not_isinstance_posix_path(self):
        assert not isinstance(PurePath("mypath"), PosixPath)
        assert not issubclass(PurePath, PosixPath)

    def test_purepath_not_isinstance_path(self):
        assert not isinstance(PurePath("mypath"), Path)
        assert not issubclass(PurePath, Path)

    def test_pathlib_pure_windows_path_isinstance(self):
        assert isinstance(PureWindowsPath("mypath"), pathlib.PurePath)
        assert issubclass(PureWindowsPath, pathlib.PurePath)
        assert isinstance(pathlib.PureWindowsPath("mypath"), PurePath)
        assert issubclass(pathlib.PureWindowsPath, PurePath)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_pure_posix_path_isinstance(self):
        assert isinstance(PurePosixPath("mypath"), pathlib.PurePath)
        assert issubclass(PurePosixPath, pathlib.PurePath)
        assert isinstance(pathlib.PurePosixPath("mypath"), PurePath)
        assert issubclass(pathlib.PurePosixPath, PurePath)

    def test_pathlib_path_isinstance(self):
        assert isinstance(Path("mypath"), pathlib.PurePath)
        assert issubclass(Path, pathlib.PurePath)
        assert isinstance(pathlib.Path("mypath"), PurePath)
        assert issubclass(pathlib.Path, PurePath)

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_pathlib_windows_path_isinstance(self):
        assert isinstance(WindowsPath("mypath"), pathlib.PurePath)
        assert issubclass(WindowsPath, pathlib.PurePath)
        assert isinstance(pathlib.WindowsPath("mypath"), PurePath)
        assert issubclass(pathlib.WindowsPath, PurePath)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_posix_path_isinstance(self):
        assert isinstance(PosixPath("mypath"), pathlib.PurePath)
        assert issubclass(PosixPath, pathlib.PurePath)
        assert isinstance(pathlib.PosixPath("mypath"), PurePath)
        assert issubclass(pathlib.PosixPath, PurePath)

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_pathlib_windows_path_isinstance_path(self):
        assert isinstance(WindowsPath("mypath"), pathlib.Path)
        assert issubclass(WindowsPath, pathlib.Path)
        assert isinstance(pathlib.WindowsPath("mypath"), Path)
        assert issubclass(pathlib.WindowsPath, Path)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_posix_path_isinstance_path(self):
        assert isinstance(PosixPath("mypath"), pathlib.Path)
        assert issubclass(PosixPath, pathlib.Path)
        assert isinstance(pathlib.PosixPath("mypath"), Path)
        assert issubclass(pathlib.PosixPath, Path)

    @unittest.skipIf(os.name != "nt", "Test must be run on Windows os")
    def test_pathlib_purepath_not_isinstance_windows_path(self):
        assert not isinstance(PurePath("mypath"), pathlib.WindowsPath)
        assert not issubclass(PurePath, pathlib.WindowsPath)
        assert not isinstance(pathlib.PurePath("mypath"), WindowsPath)
        assert not issubclass(pathlib.PurePath, WindowsPath)

    @unittest.skipIf(os.name != "posix", "Test must be run on Posix os")
    def test_pathlib_purepath_not_isinstance_posix_path(self):
        assert not isinstance(PurePath("mypath"), pathlib.PosixPath)
        assert not issubclass(PurePath, pathlib.PosixPath)
        assert not isinstance(pathlib.PurePath("mypath"), PosixPath)
        assert not issubclass(pathlib.PurePath, PosixPath)

    def test_pathlib_purepath_not_isinstance_path(self):
        assert not isinstance(PurePath("mypath"), pathlib.Path)
        assert not issubclass(PurePath, pathlib.Path)
        assert not isinstance(pathlib.PurePath("mypath"), Path)
        assert not issubclass(pathlib.PurePath, Path)


if __name__ == "__main__":
    unittest.main()
