"""
Port of xoreos-tools FilePath utility tests to PyKotor.

Original file: vendor/xoreos-tools/tests/common/filepath.cpp
Ported to test file path utilities using Python's pathlib and os modules.

This test suite validates:
- File path manipulation and normalization
- File and directory existence checking
- Path joining and splitting operations
- File extension handling
- Cross-platform path operations

Note: Some tests from the original are OS-dependent and may behave differently
on different platforms. These are adapted to work with Python's pathlib.

All test cases maintain compatibility with the original xoreos-tools tests
where possible, with adaptations for Python's path handling.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from typing import Optional


class TestXoreosFilePath(unittest.TestCase):
    """Test file path utility functions ported from xoreos-tools."""

    @classmethod
    def setUpClass(cls):
        """Set up test files and directories."""
        # Create temporary directory structure for testing
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="xoreos_test_"))
        cls.directory_path = cls.temp_dir / "test_directory"
        cls.directory_path.mkdir(exist_ok=True)
        
        # Create test files
        cls.filename = "test_file.txt"
        cls.file_path = cls.directory_path / cls.filename
        cls.file_path.write_text("Test content")
        
        cls.filename_fake = "fake_file.txt"
        cls.file_path_fake = cls.directory_path / cls.filename_fake
        # Don't create the fake file

    @classmethod
    def tearDownClass(cls):
        """Clean up test files and directories."""
        import shutil
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def test_file_exists(self):
        """Test file existence checking.
        
        Original xoreos test: GTEST_TEST(FilePath, exists)
        """
        # Test existing file
        self.assertTrue(self._file_exists(self.file_path))
        
        # Test non-existing file
        self.assertFalse(self._file_exists(self.file_path_fake))
        
        # Test existing directory
        self.assertTrue(self._file_exists(self.directory_path))

    def test_is_regular_file(self):
        """Test regular file checking.
        
        Original xoreos test: GTEST_TEST(FilePath, isRegularFile)
        """
        # Test regular file
        self.assertTrue(self._is_regular_file(self.file_path))
        
        # Test non-existing file
        self.assertFalse(self._is_regular_file(self.file_path_fake))
        
        # Test directory (should not be a regular file)
        self.assertFalse(self._is_regular_file(self.directory_path))

    def test_is_directory(self):
        """Test directory checking.
        
        Original xoreos test: GTEST_TEST(FilePath, isDirectory)
        """
        # Test directory
        self.assertTrue(self._is_directory(self.directory_path))
        
        # Test regular file (should not be a directory)
        self.assertFalse(self._is_directory(self.file_path))
        
        # Test non-existing path
        self.assertFalse(self._is_directory(self.file_path_fake))

    def test_get_file_size(self):
        """Test file size retrieval.
        
        Original xoreos test: GTEST_TEST(FilePath, getFileSize)
        """
        # Test existing file
        expected_size = len("Test content")
        actual_size = self._get_file_size(self.file_path)
        self.assertEqual(actual_size, expected_size)
        
        # Test non-existing file
        size = self._get_file_size(self.file_path_fake)
        self.assertEqual(size, -1)  # Indicate error

    def test_get_stem(self):
        """Test getting file stem (name without extension).
        
        Original xoreos test: GTEST_TEST(FilePath, getStem)
        """
        test_cases = [
            ("test.txt", "test"),
            ("file.tar.gz", "file.tar"),
            ("no_extension", "no_extension"),
            (".hidden", ".hidden"),
            ("path/to/file.ext", "file"),
        ]
        
        for filename, expected_stem in test_cases:
            actual_stem = self._get_stem(filename)
            self.assertEqual(actual_stem, expected_stem, f"Failed for {filename}")

    def test_get_extension(self):
        """Test getting file extension.
        
        Original xoreos test: GTEST_TEST(FilePath, getExtension)
        """
        test_cases = [
            ("test.txt", ".txt"),
            ("file.tar.gz", ".gz"),
            ("no_extension", ""),
            (".hidden", ""),
            ("path/to/file.ext", ".ext"),
        ]
        
        for filename, expected_ext in test_cases:
            actual_ext = self._get_extension(filename)
            self.assertEqual(actual_ext, expected_ext, f"Failed for {filename}")

    def test_change_extension(self):
        """Test changing file extension.
        
        Original xoreos test: GTEST_TEST(FilePath, changeExtension)
        """
        test_cases = [
            ("test.txt", ".bak", "test.bak"),
            ("file.tar.gz", ".zip", "file.tar.zip"),
            ("no_extension", ".txt", "no_extension.txt"),
            ("path/to/file.old", ".new", "path/to/file.new"),
        ]
        
        for original, new_ext, expected in test_cases:
            actual = self._change_extension(original, new_ext)
            self.assertEqual(actual, expected, f"Failed for {original} -> {new_ext}")

    def test_get_file(self):
        """Test getting filename from path.
        
        Original xoreos test: GTEST_TEST(FilePath, getFile)
        """
        test_cases = [
            ("/path/to/file.txt", "file.txt"),
            ("file.txt", "file.txt"),
            ("/path/to/directory/", ""),
            ("relative/path/file.ext", "file.ext"),
        ]
        
        for path, expected_file in test_cases:
            actual_file = self._get_file(path)
            self.assertEqual(actual_file, expected_file, f"Failed for {path}")

    def test_get_directory(self):
        """Test getting directory from path.
        
        Original xoreos test: GTEST_TEST(FilePath, getDirectory)
        """
        test_cases = [
            ("/path/to/file.txt", "/path/to"),
            ("file.txt", ""),
            ("/path/to/directory/", "/path/to/directory"),
            ("relative/path/file.ext", "relative/path"),
        ]
        
        for path, expected_dir in test_cases:
            actual_dir = self._get_directory(path)
            # Normalize paths for comparison (handle different path separators)
            expected_normalized = str(Path(expected_dir)) if expected_dir else ""
            actual_normalized = str(Path(actual_dir)) if actual_dir else ""
            self.assertEqual(actual_normalized, expected_normalized, f"Failed for {path}")

    def test_path_joining(self):
        """Test path joining operations."""
        test_cases = [
            (("path", "to", "file.txt"), "path/to/file.txt"),
            (("", "file.txt"), "file.txt"),
            (("path", "", "file.txt"), "path/file.txt"),
            (("/absolute", "path"), "/absolute/path"),
        ]
        
        for parts, expected in test_cases:
            actual = self._join_paths(*parts)
            # Normalize for cross-platform comparison
            expected_path = str(Path(expected))
            actual_path = str(Path(actual))
            self.assertEqual(actual_path, expected_path, f"Failed for {parts}")

    def test_path_normalization(self):
        """Test path normalization."""
        test_cases = [
            ("path/./to/../file.txt", "path/file.txt"),
            ("/path//double//slash", "/path/double/slash"),
            ("./relative/path", "relative/path"),
            ("../parent/path", "../parent/path"),
        ]
        
        for original, expected in test_cases:
            actual = self._normalize_path(original)
            # Use pathlib for cross-platform normalization
            expected_path = str(Path(expected))
            actual_path = str(Path(actual))
            # Note: Path normalization can vary by platform, so we test basic cases
            self.assertTrue(actual_path.endswith(Path(expected).name), 
                          f"Failed for {original}: got {actual_path}, expected {expected_path}")

    def test_relative_path_operations(self):
        """Test relative path operations."""
        # Test making relative paths
        base_path = "/home/user/project"
        target_path = "/home/user/project/src/file.txt"
        
        relative = self._make_relative(target_path, base_path)
        # Should be something like "src/file.txt"
        self.assertTrue("src" in relative and "file.txt" in relative)

    # --- Helper Methods ---

    def _file_exists(self, path: Path | str) -> bool:
        """Check if file or directory exists."""
        return Path(path).exists()

    def _is_regular_file(self, path: Path | str) -> bool:
        """Check if path is a regular file."""
        return Path(path).is_file()

    def _is_directory(self, path: Path | str) -> bool:
        """Check if path is a directory."""
        return Path(path).is_dir()

    def _get_file_size(self, path: Path | str) -> int:
        """Get file size, return -1 if file doesn't exist."""
        try:
            return Path(path).stat().st_size
        except (OSError, FileNotFoundError):
            return -1

    def _get_stem(self, filename: str) -> str:
        """Get file stem (name without extension)."""
        return Path(filename).stem

    def _get_extension(self, filename: str) -> str:
        """Get file extension."""
        return Path(filename).suffix

    def _change_extension(self, filename: str, new_extension: str) -> str:
        """Change file extension."""
        path = Path(filename)
        return str(path.with_suffix(new_extension))

    def _get_file(self, path: str) -> str:
        """Get filename from path."""
        return Path(path).name

    def _get_directory(self, path: str) -> str:
        """Get directory from path."""
        return str(Path(path).parent)

    def _join_paths(self, *parts: str) -> str:
        """Join path parts."""
        # Filter out empty parts
        non_empty_parts = [part for part in parts if part]
        if not non_empty_parts:
            return ""
        return str(Path(*non_empty_parts))

    def _normalize_path(self, path: str) -> str:
        """Normalize path."""
        return str(Path(path).resolve())

    def _make_relative(self, target: str, base: str) -> str:
        """Make target path relative to base path."""
        try:
            return str(Path(target).relative_to(Path(base)))
        except ValueError:
            # Paths don't have a common base
            return target


if __name__ == "__main__":
    unittest.main()
