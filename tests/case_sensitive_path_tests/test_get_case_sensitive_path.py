import os
from pathlib import Path, PureWindowsPath, PurePosixPath
import unittest
from unittest.mock import patch

from pykotor.tools.path import CaseAwarePath


class MockedPath(CaseAwarePath):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all
    _forced_parts = None

    @property
    def parts(self):
        if MockedPath._forced_parts is not None:
            return MockedPath._forced_parts
        return super().parts


class TestCaseAwarePath(unittest.TestCase):
    @patch.object(MockedPath, "iterdir", autospec=True)
    @patch.object(MockedPath, "exists", autospec=True)
    @patch.object(MockedPath, "is_dir", autospec=True)
    def test_get_case_sensitive_path(self, mock_iterdir, mock_exists, mock_is_dir):
        # Setting up the mock filesystem behavior
        MockedPath._forced_parts = ("/", "path", "to", "dir")

        # For Unix: root ("/") is always a directory
        mock_is_dir.side_effect = lambda x: x in [MockedPath("/"), MockedPath("/path")]

        # For the purpose of this test, let's assume "/path/to" exists but "/path/to/dir" does not.
        mock_exists.side_effect = lambda x: x in [
            MockedPath("/"),
            MockedPath("/path"),
            MockedPath("/path/to"),
        ]

        # Simulate directory listing for "/path/"
        dir_items = [MockedPath("/path/to")]
        mock_iterdir.side_effect = (
            lambda x: iter(dir_items) if x == MockedPath("/path") else iter([])
        )

        path = MockedPath("/path/to/DiR")
        result = path._get_case_sensitive_path(path)
        expected_result = "/path/to/dir"

        self.assertEqual(str(result), expected_result)

        # Let's also test for a directory which has multiple similar named items.
        MockedPath._forced_parts = ("/", "path", "to", "directory")
        dir_items = [
            MockedPath("/path/to/directory1"),
            MockedPath("/path/to/direCtory"),
            MockedPath("/path/to/DIRECTORY"),
        ]

        path = MockedPath("/path/to/DiReCtOrY")
        result = path._get_case_sensitive_path(path)
        expected_result = "/path/to/direCtory"
        self.assertEqual(str(result), expected_result)

        path = MockedPath("/path/to/DIRECTOrY")
        result = path._get_case_sensitive_path(path)
        expected_result = "/path/to/DIRECTORY"
        self.assertEqual(str(result), expected_result)

        path = MockedPath("/path/to/DIRECTOrY1")
        result = path._get_case_sensitive_path(path)
        expected_result = "/path/to/directory1"
        self.assertEqual(str(result), expected_result)
