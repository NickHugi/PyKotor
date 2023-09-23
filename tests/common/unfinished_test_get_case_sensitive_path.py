import os
from unittest import TestCase
import tempfile

from pathlib import Path
from pykotor.tools.path import CaseAwarePath


class TestCaseAwarePath(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_join_with_nonexistent_path(self):
        non_existent_path = CaseAwarePath("nonExistentDir")
        existent_path = self.temp_path
        joined_path = existent_path.joinpath(non_existent_path)
        self.assertFalse(joined_path.exists(), f"joined_path is '{joined_path}'")

    def test_truediv_equivalent_to_joinpath(self):
        case_aware_path1 = CaseAwarePath("someDir")
        case_aware_path2 = CaseAwarePath("someFile.txt")
        self.assertEqual(case_aware_path1 / case_aware_path2, case_aware_path1.joinpath(case_aware_path2))

    def test_rtruediv(self):
        case_aware_file_path = CaseAwarePath(self.temp_dir.name) / "soMeDir" / CaseAwarePath("someFile.TXT")
        expected_path = self.temp_dir.name / CaseAwarePath("SOmeDir") / "SOMEFile.txT"
        expected_path.mkdir(exist_ok=True, parents=True)
        expected_path.touch()
        self.assertTrue(case_aware_file_path.exists(), f"expected_path: {expected_path} actual_path: {case_aware_file_path}")
        self.assertEqual(str(case_aware_file_path), str(expected_path))

    def test_case_change_after_creation(self):
        initial_path = self.temp_path / "TestFile.txt"
        case_aware_path = CaseAwarePath(f"{str(self.temp_path)}/testfile.TXT")
        initial_path.touch()

        # Ensure existence is detected despite case difference
        self.assertTrue(case_aware_path.exists())

        # Rename the file with different case
        os.rename(initial_path, self.temp_path / "testFILE.txt")

        # Should still exist from case_aware_path perspective
        self.assertTrue(case_aware_path.exists())

    def test_complex_case_changes(self):
        path = self.temp_path / "Dir1"
        path.mkdir()

        # Changing directory case
        os.rename(path, self.temp_path / "dir1")
        path_changed = self.temp_path / "dir1"
        case_aware_path = CaseAwarePath(f"{str(self.temp_path)}/DIR1/someFile.txt")

        self.assertFalse(case_aware_path.exists())
        (path_changed / "someFile.txt").touch()
        self.assertTrue(case_aware_path.exists())

    def test_mixed_case_creation_and_deletion(self):
        case_aware_path = CaseAwarePath(f"{str(self.temp_path)}/MixEDCase/File.TXT")
        regular_path = self.temp_path / "mixedcase" / "file.txt"

        case_aware_path.parent.mkdir()
        case_aware_path.touch()

        self.assertTrue(regular_path.exists())

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
        case_aware_path = self.temp_path
        for part in case_insensitive_chain:
            case_aware_path = case_aware_path / part

        self.assertTrue(case_aware_path.exists())

    def test_deep_directory_truediv(self):
        base_path = self.temp_path
        deep_path = base_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True)

        case_aware_deep_path = CaseAwarePath(f"{str(self.temp_path)}/A/B/C/D/E")
        self.assertTrue(case_aware_deep_path.exists())

    def test_recursive_directory_creation(self):
        recursive_path = CaseAwarePath(f"{str(self.temp_path)}/X/Y/Z")
        recursive_path.mkdir(parents=True)

        actual_path = self.temp_path / "x" / "y" / "z"
        self.assertTrue(actual_path.exists())

    def test_cascading_file_creation(self):
        cascading_file = self.temp_path / "dir" / "subdir" / "file.txt"
        case_aware_cascading_file = CaseAwarePath(f"{str(self.temp_path)}/DIR/SUBDIR/FILE.TXT")

        cascading_file.parent.mkdir(parents=True)
        cascading_file.touch()

        self.assertTrue(case_aware_cascading_file.exists())

    def test_relative_to(self):
        dir_path = self.temp_path / "someDir"
        file_path = dir_path / "someFile.txt"
        case_aware_file_path = CaseAwarePath(f"{str(dir_path)}/SOMEfile.TXT")

        file_path.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        relative = case_aware_file_path.relative_to(self.temp_path)

        self.assertEqual(relative, Path("someDir/someFile.txt"))

    def test_chmod(self):
        file_path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{str(self.temp_path)}/FILE.txt")

        file_path.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        original_permissions = file_path.stat().st_mode
        case_aware_file_path.chmod(original_permissions | 0o111)  # adding execute permissions

        modified_permissions = file_path.stat().st_mode
        self.assertNotEqual(original_permissions, modified_permissions)

    def test_open_read_write(self):
        file_path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{str(self.temp_path)}/FILE.txt")

        with case_aware_file_path.open("w") as f:
            f.write("Hello, world!")

        with case_aware_file_path.open("r") as f:
            content = f.read()

        self.assertEqual(content, "Hello, world!")

    def test_touch(self):
        case_aware_file_path = CaseAwarePath(f"{str(self.temp_path)}/someFile.txt")
        case_aware_file_path.touch()

        self.assertTrue(self.temp_path.joinpath("someFile.txt").exists())

    def test_samefile(self):
        file_path = self.temp_path / "file.txt"
        case_aware_file_path = CaseAwarePath(f"{str(self.temp_path)}/FILE.TXT")

        file_path.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        self.assertTrue(case_aware_file_path.samefile(file_path))

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

    def test_rename(self):
        original_file = self.temp_path / "original.txt"
        renamed_file = self.temp_path / "renamed.txt"
        case_aware_original_file = CaseAwarePath(f"{str(self.temp_path)}/ORIGINAL.txt")

        original_file.touch()
        case_aware_original_file.rename(renamed_file)

        self.assertFalse(original_file.exists())
        self.assertTrue(renamed_file.exists())

    def test_symlink_to(self):
        source_file = self.temp_path / "source.txt"
        link_file = self.temp_path / "link.txt"
        case_aware_link_file = CaseAwarePath(f"{str(self.temp_path)}/LINK.txt")

        source_file.touch()
        case_aware_link_file.symlink_to(source_file)

        self.assertTrue(link_file.is_symlink())
        self.assertTrue(link_file.resolve().samefile(source_file))

    def test_hardlink_to(self):
        source_file = self.temp_path / "source.txt"
        hardlink_file = self.temp_path / "hardlink.txt"
        case_aware_hardlink_file = CaseAwarePath(f"{str(self.temp_path)}/HARDLINK.txt")

        source_file.touch()
        case_aware_hardlink_file.link_to(source_file)

        self.assertTrue(hardlink_file.exists())
        self.assertTrue(os.path.samefile(str(hardlink_file), str(source_file)))
