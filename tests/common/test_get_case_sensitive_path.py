import os
from unittest import TestCase
import tempfile

from pathlib import Path
import unittest
from pykotor.tools.path import CaseAwarePath


class TestCaseAwarePath(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(str(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    @unittest.skipIf(os.name == "nt", "Test not available on Windows")
    def test_join_with_nonexistent_path(self):
        non_existent_path = CaseAwarePath("nonExistentDir")
        existent_path = self.temp_path
        joined_path = existent_path.joinpath(non_existent_path)
        self.assertFalse(joined_path.exists(), f"joined_path is '{joined_path}'")

    @unittest.skipIf(os.name == "nt", "Test not available on Windows")
    def test_truediv_equivalent_to_joinpath(self):
        case_aware_path1 = CaseAwarePath("someDir")
        case_aware_path2 = CaseAwarePath("someFile.txt")
        self.assertEqual(case_aware_path1 / case_aware_path2, case_aware_path1.joinpath(case_aware_path2))

    @unittest.skipIf(os.name == "nt", "Test not available on Windows")
    def test_rtruediv(self):
        case_aware_file_path = str(self.temp_path) / CaseAwarePath("soMeDir", "someFile.TXT")
        expected_path: Path = self.temp_path / "SOmeDir" / "SOMEFile.txT"
        expected_path.mkdir(exist_ok=True, parents=True)
        expected_path.touch()
        self.assertTrue(expected_path.exists(), f"expected_path: {expected_path} should always exist on disk in this test.")
        self.assertTrue(case_aware_file_path.exists(), f"expected_path: {expected_path} actual_path: {case_aware_file_path}")
        self.assertEqual(str(case_aware_file_path), str(expected_path))

    @unittest.skipIf(os.name == "nt", "Test not available on Windows")
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
            self.assertEqual(uri, expected_uri)

            # Parse the URI back into a path
            self.assertTrue(uri.startswith("file:///"), f"Unsupported URI format: '{uri}'")

            from urllib.parse import unquote

            # Remove the "file:///" prefix and unquote the URI
            path = unquote(uri[7:])

            # Convert the URI to the platform-specific path separator
            path = path.replace("/", os.sep).replace("\\", os.sep)

            # Ensure that the parsed path matches the original path
            self.assertEqual(path, str(sample_file))

    @unittest.skipIf(os.name == "nt", "Test not available on Windows")
    def test_case_change_after_creation(self):
        initial_path: Path = self.temp_path / "TestFile.txt"
        case_aware_path = CaseAwarePath(f"{str(self.temp_path)}/testfile.TXT")
        initial_path.touch()

        # Ensure existence is detected despite case difference
        self.assertTrue(case_aware_path.exists())

        # Rename the file with different case
        os.rename(initial_path, self.temp_path / "testFILE.txt")

        # Should still exist from case_aware_path perspective
        self.assertTrue(case_aware_path.exists())

    def test_complex_case_changes(self):
        path: Path = self.temp_path / "Dir1"
        path.mkdir()

        # Changing directory case
        os.rename(path, self.temp_path / "dir1")
        path_changed = self.temp_path / "dir1"
        case_aware_path = CaseAwarePath(f"{str(self.temp_path)}/DIR1/someFile.txt")

        self.assertFalse(case_aware_path.exists())
        (path_changed / "SOMEfile.TXT").touch()
        self.assertTrue(case_aware_path.exists())

    def test_mixed_case_creation_and_deletion(self):
        case_aware_path = CaseAwarePath(f"{str(self.temp_path)}/MixEDCase/File.TXT")
        regular_path: Path = self.temp_path / "mixedcase" / "file.txt"

        regular_path.parent.mkdir()
        regular_path.touch()

        self.assertTrue(case_aware_path.exists())

        regular_path.unlink()

        self.assertFalse(case_aware_path.exists())

    def test_joinpath_chain(self):
        path_chain = ["dirA", "dirB", "dirC", "file.txt"]
        case_insensitive_chain = ["DIRa", "DirB", "dirc", "FILE.txt"]

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

        self.assertTrue(case_aware_path.exists())

    def test_deep_directory_truediv(self):
        base_path = self.temp_path
        deep_path: Path = base_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True)

        case_aware_deep_path = CaseAwarePath(f"{str(self.temp_path)}/A/B/C/D/E")
        self.assertTrue(case_aware_deep_path.exists())
        case_aware_deep_path = CaseAwarePath(self.temp_path) / "A" / "B" / "C" / "D" / "E"
        self.assertTrue(case_aware_deep_path.exists())

    def test_recursive_directory_creation(self):
        recursive_path: Path = self.temp_path / "x" / "y" / "z"
        recursive_path.mkdir(parents=True)
        self.assertTrue(recursive_path.exists())

        actual_path = CaseAwarePath(f"{str(self.temp_path)}/X/Y/Z")
        self.assertTrue(actual_path.exists())

    def test_cascading_file_creation(self):
        cascading_file: Path = self.temp_path / "dir" / "subdir" / "file.txt"
        case_aware_cascading_file = CaseAwarePath(f"{str(self.temp_path)}/DIR/SUBDIR/FILE.TXT")

        cascading_file.parent.mkdir(parents=True)
        cascading_file.touch()

        self.assertTrue(case_aware_cascading_file.exists())

    @unittest.skip("unfinished")
    def test_relative_to(self):
        dir_path = self.temp_path / "someDir"
        file_path: Path = dir_path / "someFile.txt"
        case_aware_file_path = CaseAwarePath(dir_path, "SOMEfile.TXT")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        relative = case_aware_file_path.relative_to(self.temp_path)
        self.assertTrue(
            case_aware_file_path.exists(),
            f"{relative} does not exist on disk",
        )
        if os.name == "posix":
            self.assertEqual(str(relative), "someDir/someFile.txt")
        if os.name == "nt":
            self.assertEqual(str(relative).lower(), "somedir\\somefile.txt")

    @unittest.skip("unfinished")
    def test_chmod(self):
        file_path: Path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{str(self.temp_path)}/FILE.txt")

        file_path.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        original_permissions = file_path.stat().st_mode
        case_aware_file_path.chmod(original_permissions | 0o777)

        modified_permissions = file_path.stat().st_mode
        self.assertNotEqual(original_permissions, modified_permissions)

    def test_open_read_write(self):
        file_path: Path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{str(self.temp_path)}/FILE.txt")

        with file_path.open("w") as f:
            f.write("Hello, world!")

        with case_aware_file_path.open("r") as f:
            content = f.read()

        self.assertEqual(content, "Hello, world!")

    def test_touch(self):
        self.temp_path.joinpath("SOMEfile.TXT").touch()
        self.assertTrue(CaseAwarePath(f"{str(self.temp_path)}/someFile.txt").exists())

    def test_samefile(self):
        file_path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{str(self.temp_path)}/FILE.TXT")

        file_path.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        self.assertTrue(case_aware_file_path.samefile(file_path))

    @unittest.skipIf(os.name == "nt", "method has issues on Windows - todo")
    def test_replace(self):
        file_path1 = self.temp_path / "file1.txt"
        file_path2 = self.temp_path / "file2.txt"
        case_aware_file_path1 = CaseAwarePath(f"{str(self.temp_path)}/FILE1.txt")
        case_aware_file_path2 = CaseAwarePath(f"{str(self.temp_path)}/FILE2.txt")

        file_path1.mkdir(parents=True, exist_ok=True)
        file_path1.touch()
        file_path2.mkdir(parents=True, exist_ok=True)
        file_path2.touch()

        case_aware_file_path1.replace(case_aware_file_path2)

        self.assertFalse(file_path1.exists())
        self.assertTrue(file_path2.exists())

    @unittest.skipIf(os.name == "nt", "Test not available on Windows")
    def test_rename(self):
        original_file = self.temp_path / "original.txt"
        renamed_file = self.temp_path / "renamed.txt"
        case_aware_original_file = CaseAwarePath(f"{str(self.temp_path)}/ORIGINAL.txt")

        original_file.touch()
        case_aware_original_file.rename(renamed_file)

        self.assertFalse(original_file.exists())
        self.assertTrue(renamed_file.exists())

    @unittest.skip("unfinished")
    def test_symlink_to(self):
        source_file = self.temp_path / "source.txt"
        link_file = self.temp_path / "link.txt"
        case_aware_link_file = CaseAwarePath(f"{str(self.temp_path)}/LINK.txt")

        source_file.touch()
        case_aware_link_file.symlink_to(source_file)

        self.assertTrue(link_file.is_symlink())
        self.assertTrue(link_file.resolve().samefile(source_file))

    @unittest.skip("unfinished")
    def test_hardlink_to(self):
        source_file = self.temp_path / "source.txt"
        hardlink_file = self.temp_path / "hardlink.txt"
        case_aware_hardlink_file = CaseAwarePath(f"{str(self.temp_path)}/HARDLINK.txt")

        source_file.touch()
        case_aware_hardlink_file.link_to(source_file)

        self.assertTrue(hardlink_file.exists())
        self.assertTrue(os.path.samefile(str(hardlink_file), str(source_file)))
