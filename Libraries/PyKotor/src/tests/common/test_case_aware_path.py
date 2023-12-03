import os
import pathlib
import sys
import unittest
from unittest.mock import patch

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

if __name__ == "__main__" and not __package__:
    this_script_file_path = pathlib.Path(__file__)
    sys.path.insert(0, str(this_script_file_path.parents[1]))
    __init__ = __import__(str(this_script_file_path.parent.name)).__init__  # type: ignore[misc]

from pykotor.tools.path import CaseAwarePath


class TestCaseAwarePath(unittest.TestCase):
    def test_new_valid_str_argument(self):
        try:
            CaseAwarePath("C:\\path\\to\\dir")
            CaseAwarePath("/path/to/dir")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

    def test_hashing(self):
        path1 = CaseAwarePath("test\\path\\to\\nothing")
        path2 = CaseAwarePath("tesT\\PATH\\to\\noTHinG")

        test_set = {path1, path2}
        self.assertEqual(path1, path2)
        self.assertEqual(hash(path1), hash(path2))
        self.assertSetEqual(test_set, {CaseAwarePath("TEST\\path\\to\\nothing")})

    def test_valid_name_property(self):
        self.assertEqual((CaseAwarePath("test", "data\\something.test")).name, "something.test")
        self.assertEqual((CaseAwarePath("test") / "data/something.test").name, "something.test")
        self.assertEqual((CaseAwarePath("test").joinpath("data\\something.test")).name, "something.test")
        self.assertEqual((CaseAwarePath("test").joinpath("data/something.test")).name, "something.test")

    def test_valid_name_property_on_pathlib_path(self):
        self.assertEqual(CaseAwarePath(pathlib.Path("data\\something.test")).name, "something.test")
        self.assertEqual(CaseAwarePath(pathlib.Path("data/something.test")).name, "something.test")
        self.assertEqual((CaseAwarePath("test", pathlib.Path("data\\something.test"))).name, "something.test")
        self.assertEqual((CaseAwarePath("test") / pathlib.Path("data/something.test")).name, "something.test")

    def test_new_invalid_argument(self):
        with self.assertRaises(TypeError):
            CaseAwarePath(123)  # type: ignore[test raise]
            CaseAwarePath("path", "to", pathlib.Path("nothing"), 123)  # type: ignore[test raise]

    def test_endswith(self):
        path = CaseAwarePath("C:\\path\\to\\file.txt")
        self.assertTrue(path.endswith(".TXT"))
        self.assertFalse(path.endswith(".doc"))

    @unittest.skipIf(os.name == "nt", "see the HACK in pykotor\\tools\\path.py")
    def test_find_closest_match(self):
        items = [CaseAwarePath("test"), CaseAwarePath("TEST"), CaseAwarePath("TesT"), CaseAwarePath("teSt")]
        self.assertEqual(str(CaseAwarePath.find_closest_match("teST", items)), "teSt")  # type: ignore[generator vs list]

    @unittest.skipIf(os.name == "nt", "see the HACK in pykotor\\tools\\path.py")
    def test_get_matching_characters_count(self):
        self.assertEqual(CaseAwarePath.get_matching_characters_count("test", "tesT"), 3)
        self.assertEqual(CaseAwarePath.get_matching_characters_count("test", "teat"), -1)

    @unittest.skipIf(os.name == "nt", "see the HACK in pykotor\\tools\\path.py")
    def test_relative_to_case_sensitive(self):
        file_path = CaseAwarePath("TEST\\path\\to\\something.test")
        folder_path = CaseAwarePath("TesT\\Path\\")
        self.assertTrue(folder_path in file_path)
        self.assertTrue(file_path.is_relative_to(folder_path))

    def test_relative_to_base(self):
        file_path = CaseAwarePath("TEST\\path\\to\\something.test")
        folder_path = CaseAwarePath("TEST\\path\\")
        self.assertTrue(folder_path in file_path)
        self.assertTrue(file_path.is_relative_to(folder_path))

    def test_fix_path_formatting(self):
        self.assertEqual(CaseAwarePath._fix_path_formatting("C:/path//to/dir/", "\\"), "C:\\path\\to\\dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("C:/path//to/dir/", "/"), "C:/path/to/dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("\\path//to/dir/", "\\"), "\\path\\to\\dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("\\path//to/dir/", "/"), "/path/to/dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("/path//to/dir/", "\\"), "\\path\\to\\dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("/path//to/dir/", "/"), "/path/to/dir")

    @unittest.skipIf(os.name == "nt", "Test not available on Windows.")
    @patch.object(pathlib.Path, "exists", autospec=True)
    def test_should_resolve_case(self, mock_exists):
        mock_exists.side_effect = lambda x: str(x) != "/path/to/dir"
        self.assertTrue(CaseAwarePath.should_resolve_case("/path/to/dir"))
        self.assertTrue(CaseAwarePath.should_resolve_case(CaseAwarePath("/path/to/dir")))
        self.assertFalse(CaseAwarePath.should_resolve_case("path/to/dir"))

class TestSplitFilename(unittest.TestCase):
    def test_normal(self):
        path = CaseAwarePath('file.txt')
        stem, ext = path.split_filename()
        self.assertEqual(stem, 'file')
        self.assertEqual(ext, 'txt')

    def test_multiple_dots(self):
        path = CaseAwarePath('file.with.dots.txt')
        stem, ext = path.split_filename(dots=2)
        self.assertEqual(stem, 'file.with')
        self.assertEqual(ext, 'dots.txt')
        path = CaseAwarePath('test.asdf.qwerty.tlk.xml')
        stem, ext = path.split_filename(dots=2)
        self.assertEqual(stem, 'test.asdf.qwerty')
        self.assertEqual(ext, 'tlk.xml')

    def test_no_dots(self):
        path = CaseAwarePath('filename')
        stem, ext = path.split_filename()
        self.assertEqual(stem, 'filename')
        self.assertEqual(ext, '')

    def test_negative_dots(self):
        path = CaseAwarePath('left.right.txt')
        stem, ext = path.split_filename(dots=-1)
        self.assertEqual(stem, 'right.txt')
        self.assertEqual(ext, 'left')

    def test_more_dots_than_parts(self):
        path = CaseAwarePath('file.txt')
        stem, ext = path.split_filename(dots=3)
        self.assertEqual(stem, 'file')
        self.assertEqual(ext, 'txt')
        stem, ext = path.split_filename(dots=-3)
        self.assertEqual(stem, 'file')
        self.assertEqual(ext, 'txt')

    def test_invalid_dots(self):
        path = CaseAwarePath('file.txt')
        with self.assertRaises(ValueError):
            path.split_filename(dots=0)

class TestIsRelativeTo(unittest.TestCase):

    def test_basic(self):  # sourcery skip: class-extract-method
        p1 = CaseAwarePath('/usr/local/bin')
        p2 = CaseAwarePath('/usr/local')
        self.assertTrue(p1.is_relative_to(p2))

    def test_different_paths(self):
        p1 = CaseAwarePath('/usr/local/bin') 
        p2 = CaseAwarePath('/etc')
        self.assertFalse(p1.is_relative_to(p2))

    def test_relative_paths(self):
        p1 = CaseAwarePath('docs/file.txt')
        p2 = CaseAwarePath('docs')
        self.assertTrue(p1.is_relative_to(p2))

    def test_case_insensitive(self):
        p1 = CaseAwarePath('/User/Docs')
        p2 = CaseAwarePath('/user/docs')
        self.assertTrue(p1.is_relative_to(p2))

    def test_not_path(self):
        p1 = CaseAwarePath('/home')
        p2 = '/home'
        self.assertTrue(p1.is_relative_to(p2))

    def test_same_path(self):
        p1 = CaseAwarePath('/home/user')
        p2 = CaseAwarePath('/home/user')
        self.assertTrue(p1.is_relative_to(p2))

if __name__ == '__main__':
    unittest.main()