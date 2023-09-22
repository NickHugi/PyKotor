import os
from pathlib import Path
import unittest
from unittest.mock import patch
from pykotor.tools.path import CaseAwarePath


class TestCaseAwarePath(unittest.TestCase):
    def test_new_valid_str_argument(self):
        try:
            CaseAwarePath("C:\\path\\to\\dir")
            CaseAwarePath("/path/to/dir")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

    def test_valid_name_property(self):
        self.assertTrue((CaseAwarePath("test") / "data\\something.test").name == "something.test")
        self.assertTrue((CaseAwarePath("test") / "data/something.test").name == "something.test")
        self.assertTrue((CaseAwarePath("test").joinpath("data\\something.test")).name == "something.test")
        self.assertTrue((CaseAwarePath("test").joinpath("data/something.test")).name == "something.test")

    def test_valid_name_property_on_pathlib_path(self):
        self.assertTrue(CaseAwarePath(Path("data\\something.test")).name == "something.test")
        self.assertTrue(CaseAwarePath(Path("data/something.test")).name == "something.test")
        self.assertTrue((CaseAwarePath("test") / Path("data\\something.test")).name == "something.test")
        self.assertTrue((CaseAwarePath("test") / Path("data/something.test")).name == "something.test")

    def test_new_invalid_argument(self):
        with self.assertRaises(TypeError):
            CaseAwarePath(123)
            CaseAwarePath("path", "to", Path("nothing"), 123)

    def test_endswith(self):
        path = CaseAwarePath("C:\\path\\to\\file.txt")
        self.assertTrue(path.endswith(".txt"))
        self.assertFalse(path.endswith(".doc"))

    def test_find_closest_match(self):
        items = [CaseAwarePath("test"), CaseAwarePath("TEST"), CaseAwarePath("TesT"), CaseAwarePath("teSt")]
        self.assertEqual(str(CaseAwarePath._find_closest_match("teST", items)), "teSt")

    def test_get_matching_characters_count(self):
        self.assertEqual(CaseAwarePath._get_matching_characters_count("test", "tesT"), 3)
        self.assertEqual(CaseAwarePath._get_matching_characters_count("test", "teat"), -1)

    def test_fix_path_formatting(self):
        self.assertEqual(CaseAwarePath._fix_path_formatting("C:/path//to/dir/", "\\"), "C:\\path\\to\\dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("C:/path//to/dir/", "/"), "C:/path/to/dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("\\path//to/dir/", "\\"), "\\path\\to\\dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("\\path//to/dir/", "/"), "/path/to/dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("/path//to/dir/", "\\"), "\\path\\to\\dir")
        self.assertEqual(CaseAwarePath._fix_path_formatting("/path//to/dir/", "/"), "/path/to/dir")

    @patch.object(Path, "exists", autospec=True)
    def test_should_resolve_case(self, mock_exists):
        if os.name == "nt":
            self.assertFalse(CaseAwarePath.should_resolve_case("C:\\path\\to\\dir"))
            self.assertFalse(CaseAwarePath.should_resolve_case(CaseAwarePath("C:\\path\\to\\dir")))
        else:
            mock_exists.side_effect = lambda x: str(x) != "/path/to/dir"
            self.assertTrue(CaseAwarePath.should_resolve_case("/path/to/dir"))
            self.assertTrue(CaseAwarePath.should_resolve_case(CaseAwarePath("/path/to/dir")))
            self.assertFalse(CaseAwarePath.should_resolve_case("path/to/dir"))


if __name__ == "__main__":
    unittest.main()
