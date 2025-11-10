from __future__ import annotations

import pathlib
import sys
import unittest

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

if __name__ == "__main__" and not __package__:
    this_script_file_path = pathlib.Path(__file__).resolve()
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
        assert path1 == path2
        assert hash(path1) == hash(path2)
        self.assertSetEqual(test_set, {CaseAwarePath("TEST\\path\\to\\nothing")})

    def test_valid_name_property(self):
        assert CaseAwarePath("test", "data\\something.test").name == "something.test"
        assert (CaseAwarePath("test") / "data/something.test").name == "something.test"
        assert CaseAwarePath("test").joinpath("data\\something.test").name == "something.test"
        assert CaseAwarePath("test").joinpath("data/something.test").name == "something.test"

    def test_valid_name_property_on_pathlib_path(self):
        assert CaseAwarePath(pathlib.Path("data\\something.test")).name == "something.test"
        assert CaseAwarePath(pathlib.Path("data/something.test")).name == "something.test"
        assert CaseAwarePath("test", pathlib.Path("data\\something.test")).name == "something.test"
        assert (CaseAwarePath("test") / pathlib.Path("data/something.test")).name == "something.test"

    def test_new_invalid_argument(self):
        with self.assertRaises(TypeError):
            CaseAwarePath(123)  # type: ignore[test raise]
            CaseAwarePath("path", "to", pathlib.Path("nothing"), 123)  # type: ignore[test raise]

    def test_endswith(self):
        path = CaseAwarePath("C:\\path\\to\\file.txt")
        assert path.endswith(".txt")
        assert path.endswith(".TXT")
        assert not path.endswith(".doc")

    def test_find_closest_match(self):
        items = [CaseAwarePath("test"), CaseAwarePath("TEST"), CaseAwarePath("TesT"), CaseAwarePath("teSt")]
        assert str(CaseAwarePath.find_closest_match("teST", items)) == "teSt"  # type: ignore[generator vs list]

    def test_get_matching_characters_count(self):
        assert CaseAwarePath.get_matching_characters_count("test", "tesT") == 3
        assert CaseAwarePath.get_matching_characters_count("test", "teat") == -1

    def test_relative_to_relpath(self):
        file_path = CaseAwarePath("TEST\\path\\to\\something.test")
        folder_path = CaseAwarePath("TesT\\Path\\")
        assert file_path.is_relative_to(folder_path)
        relative_path = file_path.relative_to(folder_path)
        assert isinstance(relative_path, pathlib.Path)
        assert relative_path == "to\\something.test"

    def test_relative_to_relpath_case_sensitive(self):
        file_path = CaseAwarePath("TEST\\path\\to\\something.test")
        folder_path = CaseAwarePath("TEST\\path\\")
        assert file_path.is_relative_to(folder_path)

    def test_relative_to_abspath(self):
        file_path = CaseAwarePath("C:\\TEST\\path\\to\\something.test")
        folder_path = CaseAwarePath("C:\\TesT\\Path\\")
        assert file_path.is_relative_to(folder_path)
        relative_path = file_path.relative_to(folder_path)
        assert isinstance(relative_path, pathlib.Path)
        assert relative_path == "to\\something.test"

    def test_relative_to_abspath_case_sensitive(self):
        file_path = CaseAwarePath("C:\\TEST\\path\\to\\something.test")
        folder_path = CaseAwarePath("C:\\TEST\\path\\")
        assert file_path.is_relative_to(folder_path)

    def test_fix_path_formatting(self):
        assert CaseAwarePath.str_norm("C:/path//to/dir/", slash="\\") == "C:\\path\\to\\dir"
        assert CaseAwarePath.str_norm("C:/path//to/dir/", slash="/") == "C:/path/to/dir"
        assert CaseAwarePath.str_norm("\\path//to/dir/", slash="\\") == "\\path\\to\\dir"
        assert CaseAwarePath.str_norm("\\path//to/dir/", slash="/") == "/path/to/dir"
        assert CaseAwarePath.str_norm("/path//to/dir/", slash="\\") == "\\path\\to\\dir"
        assert CaseAwarePath.str_norm("/path//to/dir/", slash="/") == "/path/to/dir"


class TestSplitFilename(unittest.TestCase):
    def test_normal(self):
        path = CaseAwarePath("file.txt")
        stem, ext = path.split_filename()
        assert stem == "file"
        assert ext == "txt"

    def test_multiple_dots(self):
        path = CaseAwarePath("file.with.dots.txt")
        stem, ext = path.split_filename(dots=2)
        assert stem == "file.with"
        assert ext == "dots.txt"
        path = CaseAwarePath("test.asdf.qwerty.tlk.xml")
        stem, ext = path.split_filename(dots=2)
        assert stem == "test.asdf.qwerty"
        assert ext == "tlk.xml"

    def test_no_dots(self):
        path = CaseAwarePath("filename")
        stem, ext = path.split_filename()
        assert stem == "filename"
        assert ext == ""

    def test_negative_dots(self):
        path = CaseAwarePath("left.right.txt")
        stem, ext = path.split_filename(dots=-1)
        assert stem == "right.txt"
        assert ext == "left"

    def test_more_dots_than_parts(self):
        path = CaseAwarePath("file.txt")
        stem, ext = path.split_filename(dots=3)
        assert stem == "file"
        assert ext == "txt"
        stem, ext = path.split_filename(dots=-3)
        assert stem == "file"
        assert ext == "txt"

    def test_invalid_dots(self):
        path = CaseAwarePath("file.txt")
        with self.assertRaises(ValueError):
            path.split_filename(dots=0)


class TestIsRelativeTo(unittest.TestCase):
    def test_basic(self):  # sourcery skip: class-extract-method
        p1 = CaseAwarePath("/usr/local/bin")
        p2 = CaseAwarePath("/usr/local")
        assert p1.is_relative_to(p2)

    def test_different_paths(self):
        p1 = CaseAwarePath("/usr/local/bin")
        p2 = CaseAwarePath("/etc")
        assert not p1.is_relative_to(p2)

    def test_relative_paths(self):
        p1 = CaseAwarePath("docs/file.txt")
        p2 = CaseAwarePath("docs")
        assert p1.is_relative_to(p2)

    def test_case_insensitive(self):
        p1 = CaseAwarePath("/User/Docs")
        p2 = CaseAwarePath("/user/docs")
        assert p1.is_relative_to(p2)

    def test_not_path(self):
        p1 = CaseAwarePath("/home")
        p2 = "/home"
        assert p1.is_relative_to(p2)

    def test_same_path(self):
        p1 = CaseAwarePath("/home/user")
        p2 = CaseAwarePath("/home/user")
        assert p1.is_relative_to(p2)


if __name__ == "__main__":
    try:
        import pytest
    except ImportError: # pragma: no cover
        unittest.main()
    else:
        pytest.main(["-v", __file__])
