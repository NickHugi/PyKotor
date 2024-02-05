import os
import pathlib
import sys
import unittest

from utility.system.path import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath

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


class TestPathInheritance(unittest.TestCase):

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
        self.assertIsInstance(pathlib.PureWindowsPath("mypath"), PurePath)
        self.assertTrue(issubclass(pathlib.PureWindowsPath, PurePath))
        self.assertIsInstance(PureWindowsPath("mypath"), pathlib.PurePath)
        self.assertTrue(issubclass(PureWindowsPath, pathlib.PurePath))

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