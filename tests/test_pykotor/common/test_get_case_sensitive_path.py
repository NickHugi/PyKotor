from __future__ import annotations

import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import TracebackType
from unittest import TestCase

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

from pykotor.tools.path import CaseAwarePath


def is_windows_case_sensitivity_supported() -> bool:
    """Check if Windows supports per-directory case sensitivity (Windows 10 1803+)."""
    if os.name != "nt":
        return False
    
    try:
        # Check Windows version
        version_output: str = subprocess.check_output(
            ["cmd", "/c", "ver"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        print(f"Windows version check output: {version_output}")
        
        # Check if fsutil command exists and works
        fsutil_check = subprocess.run(
            ["fsutil", "file"],
            capture_output=True,
            text=True,
            timeout=5
        )
        fsutil_available = fsutil_check.returncode == 0
        print(f"fsutil availability: {fsutil_available}, returncode: {fsutil_check.returncode}")
        
        return fsutil_available
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"Case sensitivity support check failed with error: {e}")
        return False


def get_case_sensitivity_status(directory_path: pathlib.Path) -> bool:
    """
    Check if a directory has case sensitivity enabled on Windows.
    
    Returns True if case-sensitive, False otherwise.
    """
    if os.name != "nt":
        # On Unix-like systems, check by trying to create files with different cases
        try:
            test_file_lower = directory_path / "test_case_check_file.tmp"
            test_file_upper = directory_path / "TEST_CASE_CHECK_FILE.TMP"
            
            # Clean up if they exist
            test_file_lower.unlink(missing_ok=True)
            test_file_upper.unlink(missing_ok=True)
            
            # Create lowercase version
            test_file_lower.touch()
            
            # Check if uppercase version is seen as different
            case_sensitive = not test_file_upper.exists()
            
            # Clean up
            test_file_lower.unlink(missing_ok=True)
            
            print(f"Unix case sensitivity test for {directory_path}: {case_sensitive}")
            return case_sensitive
        except Exception as e:
            print(f"Case sensitivity check failed with error: {e}")
            return False
    
    try:
        result = subprocess.run(
            ["fsutil", "file", "queryCaseSensitiveInfo", str(directory_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout.strip()
        print(f"Case sensitivity status for {directory_path}: {output}, returncode: {result.returncode}")
        
        if result.returncode != 0:
            print(f"fsutil stderr: {result.stderr}")
            return False
        
        # The output contains "Case sensitive attribute on directory: Enabled" or "Disabled"
        is_case_sensitive = "enabled" in output.lower()
        print(f"Directory {directory_path} case sensitivity: {is_case_sensitive}")
        return is_case_sensitive
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"Failed to query case sensitivity status with error: {e}")
        return False


def enable_case_sensitivity(directory_path: pathlib.Path) -> bool:
    """
    Enable case sensitivity on a directory (Windows 10 1803+ only).
    
    Returns True if successful, False otherwise.
    Idempotent: safe to call multiple times.
    """
    if os.name != "nt":
        print(f"Not on Windows, skipping case sensitivity enablement for {directory_path}")
        return True  # Unix systems are typically case-sensitive by default
    
    if not directory_path.exists():
        print(f"Directory {directory_path} does not exist, cannot enable case sensitivity")
        return False
    
    # Check if already enabled (idempotent)
    if get_case_sensitivity_status(directory_path):
        print(f"Case sensitivity already enabled for {directory_path}")
        return True
    
    try:
        result = subprocess.run(
            ["fsutil", "file", "setCaseSensitiveInfo", str(directory_path), "enable"],
            capture_output=True,
            text=True,
            timeout=10
        )
        success = result.returncode == 0
        print(f"Enabling case sensitivity for {directory_path}: returncode={result.returncode}")
        print(f"stdout: {result.stdout}")
        if not success:
            print(f"stderr: {result.stderr}")
        
        # Verify it was actually enabled
        if success:
            actual_status = get_case_sensitivity_status(directory_path)
            print(f"Verification after enabling: {actual_status}")
            return actual_status
        
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"Failed to enable case sensitivity with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def disable_case_sensitivity(directory_path: pathlib.Path) -> bool:
    """
    Disable case sensitivity on a directory (Windows only).
    
    Returns True if successful, False otherwise.
    Idempotent: safe to call multiple times.
    """
    if os.name != "nt":
        return True  # Not applicable on Unix
    
    if not directory_path.exists():
        print(f"Directory {directory_path} does not exist, cannot disable case sensitivity")
        return False
    
    # Check if already disabled (idempotent)
    if not get_case_sensitivity_status(directory_path):
        print(f"Case sensitivity already disabled for {directory_path}")
        return True
    
    try:
        result = subprocess.run(
            ["fsutil", "file", "setCaseSensitiveInfo", str(directory_path), "disable"],
            capture_output=True,
            text=True,
            timeout=10
        )
        success = result.returncode == 0
        print(f"Disabling case sensitivity for {directory_path}: returncode={result.returncode}")
        if not success:
            print(f"stderr: {result.stderr}")
        return success
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"Failed to disable case sensitivity with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def enable_case_sensitivity_recursive(directory_path: pathlib.Path) -> bool:
    """
    Recursively enable case sensitivity on a directory and all its subdirectories (Windows only).
    
    On Windows, case sensitivity must be explicitly enabled on each directory.
    This function walks the directory tree and enables it on all subdirectories.
    
    Returns True if successful, False otherwise.
    Idempotent: safe to call multiple times.
    """
    if os.name != "nt":
        return True  # Unix systems are case-sensitive by default
    
    if not directory_path.exists():
        print(f"Directory {directory_path} does not exist, cannot enable recursive case sensitivity")
        return False
    
    # Enable on the root directory first
    if not enable_case_sensitivity(directory_path):
        return False
    
    # Windows-specific: Recursively enable on all existing subdirectories
    # On Windows, each directory must have case sensitivity explicitly enabled
    try:
        for root, dirs, _ in os.walk(directory_path):
            for dir_name in dirs:
                subdir_path = pathlib.Path(root) / dir_name
                if subdir_path.exists() and subdir_path.is_dir():
                    if not enable_case_sensitivity(subdir_path):
                        print(f"Warning: Failed to enable case sensitivity on subdirectory {subdir_path}")
    except Exception as e:
        print(f"Warning: Error during recursive case sensitivity enablement: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail if we can't enable on subdirectories, root is what matters
    
    return True


class CaseSensitiveTempDirectory:
    """
    A temporary directory with case sensitivity enabled on Windows.
    
    This is a context manager and cleanup handler that ensures proper
    setup and teardown of case-sensitive test directories.
    """
    
    def __init__(self):
        self.temp_dir: tempfile.TemporaryDirectory | None = None
        self.path: pathlib.Path | None = None
        self._case_sensitivity_enabled: bool = False
    
    def __enter__(self) -> pathlib.Path:
        """Create and configure the temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.temp_dir.name)
        print(f"Created temporary directory: {self.path}")
        
        if os.name == "nt":
            # Windows-specific: Enable case sensitivity on root directory
            # On Windows, case sensitivity must be enabled on each directory explicitly
            # Newly created subdirectories should inherit it, but we'll enable recursively to be safe
            self._case_sensitivity_enabled = enable_case_sensitivity(self.path)
            if not self._case_sensitivity_enabled:
                print(f"WARNING: Failed to enable case sensitivity for {self.path}")
                raise unittest.SkipTest(
                    "Could not enable case sensitivity on Windows. "
                    "Requires Windows 10 (1803+) or Windows 11 and administrator privileges."
                )
            # Windows-specific: Ensure case sensitivity is enabled recursively on all subdirectories
            # This ensures any subdirectories that exist or will be created have case sensitivity
            enable_case_sensitivity_recursive(self.path)

        self._case_sensitivity_enabled = get_case_sensitivity_status(self.path)
        if not self._case_sensitivity_enabled:
            raise unittest.SkipTest(
                "File system is not case-sensitive. These tests require a case-sensitive filesystem."
            )
        
        print(f"Case-sensitive directory ready: {self.path}")
        return self.path
    
    
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Clean up the temporary directory."""
        if self.path and os.name == "nt" and self._case_sensitivity_enabled:
            try:
                # Disable case sensitivity before cleanup to avoid potential issues
                disable_case_sensitivity(self.path)
            except Exception as e:
                print(f"Warning: Failed to disable case sensitivity during cleanup: {e}")
        
        if self.temp_dir:
            try:
                self.temp_dir.cleanup()
                print(f"Cleaned up temporary directory")
            except Exception as e:
                print(f"Warning: Failed to cleanup temp directory: {e}")
                # If normal cleanup fails, try forceful removal
                if self.path and self.path.exists():
                    try:
                        shutil.rmtree(self.path, ignore_errors=True)
                    except Exception as e2:
                        print(f"Warning: Forceful cleanup also failed: {e2}")
        return True


def _determine_skip_reason() -> str | None:
    """
    Determine whether the entire test class should be skipped.

    Returns a string reason when skipping is required, otherwise None.
    """
    if os.name == "nt":
        windows_supported = is_windows_case_sensitivity_supported()
        print(f"Windows case sensitivity support check result: {windows_supported}")
        if not windows_supported:
            reason = (
                "Windows case sensitivity not supported. "
                "Requires Windows 10 (1803+) or Windows 11, NTFS filesystem, "
                "and fsutil.exe must be available."
            )
            print(f"Windows skip reason: {reason}")
            return reason
        return None
    if os.name == "posix":
        print(f"POSIX environment detected, skip reason: None")
        return None
    reason = f"Unsupported operating system: {os.name}"
    print(f"Non-Windows skip reason computed: {reason}")
    return reason


class TestCaseAwarePath(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        skip_reason = _determine_skip_reason()
        print(f"Evaluated skip reason in setUpClass: {skip_reason}")
        if skip_reason:
            raise unittest.SkipTest(skip_reason)

    def setUp(self):
        """Set up a case-sensitive temporary directory for testing."""
        self.case_sensitive_dir = CaseSensitiveTempDirectory()
        self.temp_path: pathlib.Path = self.case_sensitive_dir.__enter__()
        print(f"Test setup complete with temp_path: {self.temp_path}")

    def tearDown(self):
        """Clean up the case-sensitive temporary directory."""        
        try:
            self.case_sensitive_dir.__exit__(None, None, None)
            print(f"Test teardown complete")
        except Exception as e:
            print(f"Error during teardown: {e}")
            import traceback
            traceback.print_exc()

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
        assert (
            str(case_aware_file_path) == str(expected_path) or platform.system() == "Darwin"
        ), f"Path case mismatch on a case-sensitive filesystem. Case-aware path: {case_aware_file_path}, expected path: {expected_path}"

    def test_make_and_parse_uri(self):
        # Use the case-sensitive temp directory from setUp
        temp_dir_path = CaseAwarePath(self.temp_path)

        # Create a sample file within the temporary directory
        sample_file = temp_dir_path / "sample.txt"

        # uppercase whole path and create sample.txt
        CaseAwarePath(str(sample_file).upper()).touch()

        # Convert the uppercase'd path to a URI
        uri = sample_file.as_uri()

        # Ensure that the URI is in the expected format
        # pathlib.Path.as_uri() returns file:/// (three slashes) for absolute paths on all platforms
        temp_path_str = str(self.temp_path).replace(os.sep, "/")
        if os.name == "posix":
            # On Unix, paths start with /, so use file:// (2 slashes) + /path = file:///path (3 slashes total)
            expected_uri = f'file://{temp_path_str}/SAMPLE.TXT'
        else:
            # On Windows, paths are like C:/path, so use file:/// (3 slashes) + C:/path = file:///C:/path
            expected_uri = f'file:///{temp_path_str}/SAMPLE.TXT'
        self.assertTrue(
            uri == expected_uri or platform.system() == "Darwin",
            f"Path case mismatch on a case-sensitive filesystem. Case-aware path: {uri}, expected path: {expected_uri}",
        )

        # Parse the URI back into a path
        self.assertTrue(uri.startswith("file:///"), f"Unsupported URI format: '{uri}'")

        from urllib.parse import unquote

        # Remove the "file:///" prefix and unquote the URI
        path = unquote(uri[7:])  # Remove "file:///" (7 characters)

        # On Windows, file URIs have an extra leading slash before the drive letter
        # e.g., file:///C:/Users/... -> /C:/Users/... -> C:/Users/...
        if os.name == "nt" and path.startswith("/") and len(path) > 1 and path[1].isalpha() and path[2:4] == ":/":
            path = path[1:]  # Remove leading slash before drive letter

        # Convert forward slashes to platform-specific separator
        path = path.replace("/", os.sep)

        # Use pathlib to normalize the path to absolute
        parsed_path = pathlib.Path(path).resolve()
        path_str = str(parsed_path)

        # Get the actual case-sensitive path from the filesystem
        # The file was created with uppercase (SAMPLE.TXT), so we need the resolved case
        sample_file_resolved = CaseAwarePath.get_case_sensitive_path(sample_file)
        sample_file_normalized = str(pathlib.Path(sample_file_resolved).resolve())

        # Ensure that the parsed path matches the actual file path on disk
        self.assertEqual(path_str, sample_file_normalized)

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

        self.assertTrue(
            case_aware_file_path.exists(),
            f"{relative} does not exist on disk",
        )
        # On Windows, relative paths use backslashes (os.sep); on Unix/macOS, they use forward slashes
        if os.name == "nt":
            expected_relpath = "someDir/someFile.txt".replace("/", os.sep)
        else:
            expected_relpath = "someDir/someFile.txt"
        self.assertTrue(
            str(relative) == expected_relpath or platform.system() == "Darwin",
            f"Path case mismatch on a case-sensitive filesystem. Case-aware path: {relative}, expected path: {expected_relpath}",
        )

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
    try:
        import pytest
    except ImportError:  # pragma: no cover
        unittest.main()
    else:
        pytest.main(["-v", __file__])
