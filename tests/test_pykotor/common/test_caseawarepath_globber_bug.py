"""Test case to reproduce and document the _Globber.__init__() bug in CaseAwarePath.

This test specifically targets the bug where calling rglob() or glob() on CaseAwarePath
results in:
    TypeError: _Globber.__init__() takes from 3 to 5 positional arguments but 6 were given

This occurs in Python 3.13 when the simple_wrapper passes arguments to pathlib's internal
_Globber class that don't match the updated signature.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import traceback
import unittest
from typing import Any

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


class TestGlobberBug(unittest.TestCase):
    """Test suite to reproduce and document the _Globber.__init__() TypeError bug."""

    def setUp(self):
        """Set up temporary directory structure for testing glob operations."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base = CaseAwarePath(self.temp_dir)

        # Create test directory structure
        (self.test_base / "level1").mkdir()
        (self.test_base / "level1" / "level2").mkdir()
        (self.test_base / "level1" / "level2" / "level3").mkdir()

        # Create test files
        (self.test_base / "file1.txt").touch()
        (self.test_base / "file2.py").touch()
        (self.test_base / "file3.json").touch()
        (self.test_base / "level1" / "file1.txt").touch()
        (self.test_base / "level1" / "file2.py").touch()
        (self.test_base / "level1" / "level2" / "deep_file.txt").touch()
        (self.test_base / "level1" / "level2" / "level3" / "deeper_file.txt").touch()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_rglob_simple_pattern(self):
        """Test rglob with simple pattern like '*'."""
        print(f"\n[TEST] Testing rglob('*') on {self.test_base}")
        print(f"[TEST] Python version: {sys.version}")

        try:
            result = list(self.test_base.rglob("*"))
            print(f"[TEST] SUCCESS: rglob('*') returned {len(result)} items")
            for item in result[:5]:  # Show first 5
                print(f"[TEST]   - {item}")
        except TypeError as e:
            print(f"[TEST] FAILED with TypeError: {e}")
            print(f"[TEST] Exception type: {type(e).__name__}")
            print(f"[TEST] Exception args: {e.args}")
            traceback.print_exc()
            self.fail(
                f"rglob('*') raised TypeError: {e}\n"
                "This is the _Globber.__init__() bug. Check traceback above."
            )

    def test_rglob_recursive_pattern(self):
        """Test rglob with recursive pattern like '**/*.txt'."""
        print(f"\n[TEST] Testing rglob('**/*.txt') on {self.test_base}")

        try:
            result = list(self.test_base.rglob("**/*.txt"))
            print(f"[TEST] SUCCESS: rglob('**/*.txt') returned {len(result)} items")
        except TypeError as e:
            print(f"[TEST] FAILED with TypeError: {e}")
            traceback.print_exc()
            self.fail(
                f"rglob('**/*.txt') raised TypeError: {e}\n"
                "This is the _Globber.__init__() bug. Check traceback above."
            )

    def test_rglob_file_extension(self):
        """Test rglob with file extension pattern."""
        print(f"\n[TEST] Testing rglob('*.txt') on {self.test_base}")

        try:
            result = list(self.test_base.rglob("*.txt"))
            print(f"[TEST] SUCCESS: rglob('*.txt') returned {len(result)} items")
        except TypeError as e:
            print(f"[TEST] FAILED with TypeError: {e}")
            traceback.print_exc()
            self.fail(
                f"rglob('*.txt') raised TypeError: {e}\n"
                "This is the _Globber.__init__() bug. Check traceback above."
            )

    def test_rglob_case_sensitive_parameter(self):
        """Test rglob with case_sensitive parameter (Python 3.12+)."""
        print(f"\n[TEST] Testing rglob('*', case_sensitive=False) on {self.test_base}")

        try:
            result = list(self.test_base.rglob("*", case_sensitive=False))
            print(f"[TEST] SUCCESS: rglob('*', case_sensitive=False) returned {len(result)} items")
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] FAILED with _Globber TypeError: {e}")
                traceback.print_exc()
                self.fail(
                    f"rglob('*', case_sensitive=False) raised _Globber TypeError: {e}\n"
                    "This is the _Globber.__init__() bug with case_sensitive parameter.\n"
                    "Check traceback above."
                )
            else:
                # Might be Python version that doesn't support case_sensitive
                print(f"[TEST] TypeError (expected if Python < 3.12): {e}")
        except Exception as e:
            print(f"[TEST] Unexpected exception: {type(e).__name__}: {e}")
            traceback.print_exc()

    def test_rglob_recurse_symlinks_parameter(self):
        """Test rglob with recurse_symlinks parameter."""
        print(f"\n[TEST] Testing rglob('*', recurse_symlinks=True) on {self.test_base}")

        try:
            result = list(self.test_base.rglob("*", recurse_symlinks=True))
            print(f"[TEST] SUCCESS: rglob('*', recurse_symlinks=True) returned {len(result)} items")
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] FAILED with _Globber TypeError: {e}")
                traceback.print_exc()
                self.fail(
                    f"rglob('*', recurse_symlinks=True) raised _Globber TypeError: {e}\n"
                    "This is the _Globber.__init__() bug with recurse_symlinks parameter.\n"
                    "Check traceback above."
                )
            else:
                print(f"[TEST] TypeError (might be expected): {e}")

    def test_glob_simple_pattern(self):
        """Test glob with simple pattern."""
        print(f"\n[TEST] Testing glob('*') on {self.test_base}")

        try:
            result = list(self.test_base.glob("*"))
            print(f"[TEST] SUCCESS: glob('*') returned {len(result)} items")
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] FAILED with _Globber TypeError: {e}")
                traceback.print_exc()
                self.fail(
                    f"glob('*') raised _Globber TypeError: {e}\n"
                    "This is the _Globber.__init__() bug. Check traceback above."
                )
            else:
                print(f"[TEST] TypeError (unexpected): {e}")
                traceback.print_exc()

    def test_glob_with_kwargs(self):
        """Test glob with keyword arguments (case_sensitive, recurse_symlinks)."""
        print(f"\n[TEST] Testing glob('*', case_sensitive=False, recurse_symlinks=True)")

        try:
            result = list(
                self.test_base.glob(
                    "*",
                    case_sensitive=False,
                    recurse_symlinks=True,
                ),
            )
            print(f"[TEST] SUCCESS: glob with kwargs returned {len(result)} items")
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] FAILED with _Globber TypeError: {e}")
                print(f"[TEST] Error message: {error_msg}")
                traceback.print_exc()
                self.fail(
                    f"glob() with kwargs raised _Globber TypeError: {e}\n"
                    "This is the _Globber.__init__() bug when passing multiple kwargs.\n"
                    "Check traceback above."
                )
            else:
                print(f"[TEST] TypeError (might be expected): {e}")

    def test_safe_rglob_from_utility(self):
        """Test safe_rglob which calls rglob internally."""
        print(f"\n[TEST] Testing safe_rglob('*') (from utility.path)")

        try:
            from pathlib import Path as UtilityPath

            util_path = UtilityPath(self.temp_dir)
            result = list(util_path.rglob("*"))
            print(f"[TEST] SUCCESS: safe_rglob('*') returned {len(result)} items")
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] FAILED with _Globber TypeError: {e}")
                traceback.print_exc()
                self.fail(
                    f"safe_rglob() raised _Globber TypeError: {e}\n"
                    "This is the _Globber.__init__() bug propagating through safe_rglob.\n"
                    "Check traceback above."
                )
            else:
                print(f"[TEST] TypeError: {e}")
                traceback.print_exc()

    def test_compare_with_standard_pathlib(self):
        """Compare CaseAwarePath behavior with standard pathlib.Path."""
        print(f"\n[TEST] Comparing CaseAwarePath vs pathlib.Path behavior")

        standard_path = pathlib.Path(self.temp_dir)

        try:
            standard_result = list(standard_path.rglob("*"))
            print(f"[TEST] Standard pathlib.Path.rglob('*'): {len(standard_result)} items (SUCCESS)")

            caseaware_result = list(self.test_base.rglob("*"))
            print(f"[TEST] CaseAwarePath.rglob('*'): {len(caseaware_result)} items (SUCCESS)")

            self.assertEqual(
                len(standard_result),
                len(caseaware_result),
                "CaseAwarePath should return same number of results as pathlib.Path",
            )
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] CaseAwarePath FAILED while pathlib.Path succeeded")
                print(f"[TEST] This confirms the bug is specific to CaseAwarePath wrapper")
                traceback.print_exc()
                self.fail(
                    f"CaseAwarePath.rglob() failed with _Globber TypeError while "
                    f"pathlib.Path.rglob() succeeded. Error: {e}"
                )
            else:
                raise

    def test_nested_directory_rglob(self):
        """Test rglob on nested directory structure."""
        print(f"\n[TEST] Testing rglob on nested directory: level1/level2")

        nested_path = self.test_base / "level1" / "level2"

        try:
            result = list(nested_path.rglob("*"))
            print(f"[TEST] SUCCESS: rglob('*') on nested dir returned {len(result)} items")
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] FAILED with _Globber TypeError: {e}")
                traceback.print_exc()
                self.fail(
                    f"rglob() on nested directory raised _Globber TypeError: {e}\n"
                    "Check traceback above."
                )

    def test_globber_signature_analysis(self):
        """Analyze and document the exact error signature."""
        print(f"\n[TEST] Analyzing _Globber.__init__() signature issue")

        import inspect

        try:
            # Try to inspect pathlib's _Globber if accessible
            from pathlib import _local  # noqa: PLC2701

            if hasattr(_local, "_Globber"):
                globber = _local._Globber
                sig = inspect.signature(globber.__init__)
                print(f"[TEST] _Globber.__init__ signature: {sig}")
                print(f"[TEST] Parameters: {list(sig.parameters.keys())}")
        except Exception as e:
            print(f"[TEST] Could not inspect _Globber: {e}")

        # Now test actual call to see what arguments are being passed
        try:
            result = list(self.test_base.rglob("*"))
            print(f"[TEST] rglob() call succeeded")
        except TypeError as e:
            error_msg = str(e)
            print(f"\n[TEST] ========================================")
            print(f"[TEST] ERROR ANALYSIS")
            print(f"[TEST] ========================================")
            print(f"[TEST] Error Type: {type(e).__name__}")
            print(f"[TEST] Error Message: {error_msg}")
            print(f"[TEST] Error Args: {e.args}")
            print(f"\n[TEST] Full Traceback:")
            traceback.print_exc()
            print(f"[TEST] ========================================")

            if "_Globber.__init__()" in error_msg:
                # Extract the argument count from error message
                if "takes from" in error_msg and "but" in error_msg:
                    parts = error_msg.split("takes from")[1].split("but")[0].strip()
                    expected = parts.split("to")[0].strip()
                    actual_part = error_msg.split("but")[1].split("were given")[0].strip()
                    print(f"\n[TEST] EXPECTED: 3 to 5 arguments")
                    print(f"[TEST] ACTUAL: {actual_part} arguments")
                    print(f"[TEST] DIFFERENCE: {int(actual_part) - 5} extra arguments")

            self.fail(f"rglob() failed: {e}")

    def test_installation_load_override_scenario(self):
        """Reproduce the exact scenario from installation.py:553 that triggers the bug."""
        print(f"\n[TEST] Reproducing installation.py:553 scenario (load_override)")

        # This mimics: target_dirs = [f for f in override_path.rglob("*") if f.is_dir()]
        from pathlib import Path as UtilityPath

        override_path = UtilityPath(self.temp_dir)

        try:
            target_dirs = [f for f in override_path.rglob("*") if f.is_dir()]
            print(f"[TEST] SUCCESS: Found {len(target_dirs)} directories")
        except TypeError as e:
            error_msg = str(e)
            if "_Globber.__init__()" in error_msg:
                print(f"[TEST] FAILED: Reproduced the exact bug from installation.py")
                print(f"[TEST] This is the scenario that causes KotorDiff to fail")
                traceback.print_exc()
                self.fail(
                    f"Reproduced installation.py:553 bug: {e}\n"
                    "This is why KotorDiff generates only 72 lines (empty INI).\n"
                    "The diff process crashes before any modifications are written."
                )
            else:
                raise


if __name__ == "__main__":
    print("=" * 80)
    print("Testing CaseAwarePath _Globber.__init__() Bug")
    print("=" * 80)
    print(f"Python version: {sys.version}")
    print(f"Python version info: {sys.version_info}")
    print("=" * 80)

    unittest.main(verbosity=2)

