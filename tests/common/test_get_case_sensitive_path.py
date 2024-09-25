from __future__ import annotations

import os
import pathlib
import platform
import sys
import tempfile
import unittest
from unittest import TestCase

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


@unittest.skipIf(os.name == "nt", "Test not available on Windows")
class TestCaseAwarePath(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = pathlib.Path(str(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_join_with_nonexistent_path(self):
        non_existent_path = CaseAwarePath("nonExistentDir")
        existent_path = self.temp_path
        joined_path = existent_path.joinpath(non_existent_path)
        assert not joined_path.exists(), f"joined_path is '{joined_path}'"

    def test_truediv_equivalent_to_joinpath(self):
        case_aware_path1 = CaseAwarePath("someDir")
        case_aware_path2 = CaseAwarePath("someFile.txt")
        assert case_aware_path1 / case_aware_path2 == case_aware_path1.joinpath(case_aware_path2)

    def test_rtruediv(self):
        case_aware_file_path = str(self.temp_path) / CaseAwarePath("soMeDir", "someFile.TXT")
        expected_path: pathlib.Path = self.temp_path / "SOmeDir" / "SOMEFile.txT"
        expected_path.mkdir(exist_ok=True, parents=True)
        expected_path.touch()
        assert expected_path.exists(), f"expected_path: '{expected_path}' should always exist on disk in this test."
        assert case_aware_file_path.exists(), f"expected_path: '{expected_path}' actual_path: '{case_aware_file_path}'"
        assert str(case_aware_file_path) == str(expected_path) or platform.system() == "Darwin", f"Path case mismatch on a case-sensitive filesystem. Case-aware path: {case_aware_file_path}, expected path: {expected_path}"

    def test_make_and_parse_uri(self):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = CaseAwarePath(temp_dir)

            # Create a sample file within the temporary directory
            sample_file = temp_dir_path / "sample.txt"

            # uppercase whole path and create sample.txt
            CaseAwarePath(str(sample_file).upper()).touch()

            # Convert the uppercase'd path to a URI
            uri = sample_file.as_uri()

            # Ensure that the URI is in the expected format
            expected_uri = f'file://{temp_dir.replace(os.sep, "/")}/SAMPLE.TXT'
            assert uri == expected_uri or platform.system() == "Darwin", f"Path case mismatch on a case-sensitive filesystem. Case-aware path: {uri}, expected path: {expected_uri}"

            # Parse the URI back into a path
            assert uri.startswith("file:///"), f"Unsupported URI format: '{uri}'"

            from urllib.parse import unquote

            # Remove the "file:///" prefix and unquote the URI
            path = unquote(uri[7:])

            # Convert the URI to the platform-specific path separator
            path = path.replace("/", os.sep).replace("\\", os.sep)

            # Ensure that the parsed path matches the original path
            assert path == str(sample_file)

    def test_case_change_after_creation(self):
        initial_path: pathlib.Path = self.temp_path / "TestFile.txt"
        case_aware_path = CaseAwarePath(f"{self.temp_path!s}/testfile.TXT")
        initial_path.touch()

        # Ensure existence is detected despite case difference
        assert case_aware_path.exists()

        # Rename the file with different case
        os.rename(initial_path, self.temp_path / "testFILE.txt")

        # Should still exist from case_aware_path perspective
        assert case_aware_path.exists()

    def test_complex_case_changes(self):
        path: pathlib.Path = self.temp_path / "Dir1"
        path.mkdir()

        # Changing directory case
        os.rename(path, self.temp_path / "dir1")
        path_changed = self.temp_path / "dir1"
        case_aware_path = CaseAwarePath(f"{self.temp_path!s}/DIR1/someFile.txt")

        assert not case_aware_path.exists()
        (path_changed / "SOMEfile.TXT").touch()
        assert case_aware_path.exists()

    def test_mixed_case_creation_and_deletion(self):
        case_aware_path = CaseAwarePath(f"{self.temp_path!s}/MixEDCase/File.TXT")
        regular_path: pathlib.Path = self.temp_path / "mixedcase" / "file.txt"

        regular_path.parent.mkdir()
        regular_path.touch()

        assert case_aware_path.exists()

        regular_path.unlink()

        assert not case_aware_path.exists()

    def test_joinpath_chain(self):
        path_chain: list[str] = ["dirA", "dirB", "dirC", "file.txt"]
        case_insensitive_chain: list[str] = ["DIRa", "DirB", "dirc", "FILE.txt"]

        # Create actual path chain
        current_path = self.temp_path
        for part in path_chain:
            current_path /= part
            if part.endswith(".txt"):
                current_path.touch()
            else:
                current_path.mkdir()

        # Construct CaseAwarePath and verify existence
        case_aware_path = CaseAwarePath(self.temp_path)
        for part in case_insensitive_chain:
            case_aware_path = case_aware_path / part

        assert case_aware_path.exists()

    def test_deep_directory_truediv(self):
        base_path = self.temp_path
        deep_path: pathlib.Path = base_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True)

        case_aware_deep_path = CaseAwarePath(f"{self.temp_path!s}/A/B/C/D/E")
        assert case_aware_deep_path.exists()
        case_aware_deep_path = CaseAwarePath(self.temp_path) / "A" / "B" / "C" / "D" / "E"
        assert case_aware_deep_path.exists()

    def test_recursive_directory_creation(self):
        recursive_path: pathlib.Path = self.temp_path / "x" / "y" / "z"
        recursive_path.mkdir(parents=True)
        assert recursive_path.exists()

        actual_path = CaseAwarePath(f"{self.temp_path!s}/X/Y/Z")
        assert actual_path.exists()

    def test_cascading_file_creation(self):
        cascading_file: pathlib.Path = self.temp_path / "dir" / "subdir" / "file.txt"
        case_aware_cascading_file = CaseAwarePath(f"{self.temp_path!s}/DIR/SUBDIR/FILE.TXT")

        cascading_file.parent.mkdir(parents=True)
        cascading_file.touch()

        assert case_aware_cascading_file.exists()

    def test_relative_to(self):
        dir_path = self.temp_path / "someDir"
        file_path: pathlib.Path = dir_path / "someFile.txt"
        case_aware_file_path = CaseAwarePath(dir_path, "SOMEfile.TXT")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        relative = case_aware_file_path.relative_to(self.temp_path)
        assert case_aware_file_path.exists(), f"{relative} does not exist on disk"
        expected_relpath = "someDir/someFile.txt"
        if os.name == "posix":
            assert str(relative) == expected_relpath or platform.system() == "Darwin", f"Path case mismatch on a case-sensitive filesystem. Case-aware path: {relative}, expected path: {expected_relpath}"
        if os.name == "nt":
            assert str(relative).lower() == "somedir\\somefile.txt"

    @unittest.skip("unfinished")
    def test_chmod(self):
        file_path: pathlib.Path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{self.temp_path!s}/FILE.txt")

        file_path.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        original_permissions = file_path.stat().st_mode
        case_aware_file_path.chmod(original_permissions | 0o777)

        modified_permissions = file_path.stat().st_mode
        assert original_permissions != modified_permissions

    def test_open_read_write(self):
        file_path: pathlib.Path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{self.temp_path!s}/FILE.txt")

        with file_path.open("w", encoding="utf-8") as f:
            f.write("Hello, world!")

        with case_aware_file_path.open("r", encoding="utf-8") as f:
            content = f.read()

        assert content == "Hello, world!"

    def test_touch(self):
        self.temp_path.joinpath("SOMEfile.TXT").touch()
        assert CaseAwarePath(f"{self.temp_path!s}/someFile.txt").exists()

    def test_samefile(self):
        file_path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{self.temp_path!s}/FILE.TXT")

        file_path.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        assert case_aware_file_path.samefile(file_path)

    @unittest.skipIf(os.name == "nt", "method has issues on Windows - todo")
    def test_replace(self):
        file_path1 = self.temp_path / "file1.txt"
        file_path2 = self.temp_path / "file2.txt"
        case_aware_file_path1 = CaseAwarePath(f"{self.temp_path!s}/FILE1.txt")
        case_aware_file_path2 = CaseAwarePath(f"{self.temp_path!s}/FILE2.txt")

        file_path1.mkdir(parents=True, exist_ok=True)
        file_path1.touch()
        file_path2.mkdir(parents=True, exist_ok=True)
        file_path2.touch()

        case_aware_file_path1.replace(case_aware_file_path2)

        assert not file_path1.exists()
        assert file_path2.exists()

    @unittest.skipIf(os.name == "nt", "Test not available on Windows")
    def test_rename(self):
        original_file = self.temp_path / "original.txt"
        renamed_file = self.temp_path / "renamed.txt"
        case_aware_original_file = CaseAwarePath(f"{self.temp_path!s}/ORIGINAL.txt")

        original_file.touch()
        case_aware_original_file.rename(renamed_file)

        assert not original_file.exists()
        assert renamed_file.exists()

    @unittest.skip("unfinished")
    def test_symlink_to(self):
        source_file = self.temp_path / "source.txt"
        link_file = self.temp_path / "link.txt"
        case_aware_link_file = CaseAwarePath(f"{self.temp_path!s}/LINK.txt")

        source_file.touch()
        case_aware_link_file.symlink_to(source_file)

        assert link_file.is_symlink()
        assert link_file.resolve().samefile(source_file)

    @unittest.skip("unfinished")
    def test_hardlink_to(self):
        source_file = self.temp_path / "source.txt"
        hardlink_file = self.temp_path / "hardlink.txt"
        case_aware_hardlink_file = CaseAwarePath(f"{self.temp_path!s}/HARDLINK.txt")

        source_file.touch()
        case_aware_hardlink_file.hardlink_to(source_file)

        assert hardlink_file.exists()
        assert os.path.samefile(str(hardlink_file), str(source_file))


if __name__ == "__main__":
    unittest.main()
