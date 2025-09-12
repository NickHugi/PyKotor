#!/usr/bin/env python3
"""Test script for the new KotorDiff features."""
from __future__ import annotations

import pathlib
import sys

# Add PyKotor to path
if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = pathlib.Path(__file__).parents[2] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    utility_path = pathlib.Path(__file__).parents[2] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        update_sys_path(utility_path.parent)

from utility.system.path import Path


def test_logging_system():
    """Test the new logging system."""
    print("Testing logging system:")

    try:
        from kotordiff.logger import LogLevel, OutputMode, diff_output, error, info, setup_logger, warning  # noqa: PLC0415

        # Test setup
        setup_logger(LogLevel.INFO, OutputMode.FULL, use_colors=True)

        # Test different log levels
        info("This is an info message")
        warning("This is a warning message")
        error("This is an error message")
        diff_output("This is diff output")

        print("✓ Logging system test passed\n")
    except ImportError as e:
        print(f"✗ Logging system test failed: {e.__class__.__name__}\n")
        return False
    else:
        return True


def test_diff_objects():
    """Test the structured diff objects."""
    print("Testing diff objects:")

    try:
        from kotordiff.diff_objects import DiffEngine, DiffType  # noqa: PLC0415

        engine = DiffEngine()

        # Test simple byte comparison
        result = engine.compare_resources(
            b"hello world",
            b"hello world",
            "test1.txt",
            "test2.txt",
            "bytes"
        )

        assert result.diff_type == DiffType.IDENTICAL
        print("✓ Diff objects test passed\n")
    except ImportError as e:
        print(f"✗ Diff objects test failed: {e.__class__.__name__}\n")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"✗ Diff objects test failed: {e}\n")
        return False
    else:
        return True


def test_formatters():
    """Test the diff formatters."""
    print("Testing formatters:")

    try:
        from kotordiff.diff_objects import DiffType, ResourceDiffResult  # noqa: PLC0415
        from kotordiff.formatters import DiffFormat, FormatterFactory  # noqa: PLC0415

        # Create a simple diff result
        diff_result = ResourceDiffResult(
            diff_type=DiffType.MODIFIED,
            left_identifier="file1.txt",
            right_identifier="file2.txt",
            left_value=b"content1",
            right_value=b"content2",
            resource_type="txt"
        )

        # Test different formatters
        for format_type in [DiffFormat.DEFAULT, DiffFormat.UNIFIED]:
            formatter = FormatterFactory.create_formatter(format_type)
            formatted = formatter.format_diff(diff_result)
            print(f"  {format_type.value}: {formatted[:50]}...")

        print("✓ Formatters test passed\n")
    except ImportError as e:
        print(f"✗ Formatters test failed: {e.__class__.__name__}\n")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"✗ Formatters test failed: {e}\n")
        return False
    else:
        return True


# Test the new filtering functionality
def test_should_include_in_filtered_diff():
    """Test the filtering logic."""
    from kotordiff.__main__ import should_include_in_filtered_diff  # noqa: PLC0415

    # Test module filtering
    assert should_include_in_filtered_diff("modules/tat_m18ac.rim", ["tat_m18ac"])
    assert should_include_in_filtered_diff("modules/tat_m18ac_s.rim", ["tat_m18ac"])
    assert should_include_in_filtered_diff("modules/tat_m18ac_dlg.erf", ["tat_m18ac"])
    assert not should_include_in_filtered_diff("modules/dan_m13aa.rim", ["tat_m18ac"])

    # Test specific resource filtering
    assert should_include_in_filtered_diff("override/some_character.utc", ["some_character.utc"])
    assert should_include_in_filtered_diff("override/some_character.utc", ["some_character"])
    assert not should_include_in_filtered_diff("override/other_character.utc", ["some_character"])

    # Test no filters (should include everything)
    assert should_include_in_filtered_diff("anything.txt", None)
    assert should_include_in_filtered_diff("anything.txt", [])

    print("✓ All filtering tests passed!")


def test_resource_resolution():
    """Test resource resolution logic (mock test since we need actual installations)."""
    from kotordiff.__main__ import resolve_resource_in_installation  # noqa: PLC0415

    # This would need a real installation to test properly
    # For now, just test that the function exists and has the right signature
    fake_path = Path("fake_installation")
    result_data, result_info = resolve_resource_in_installation(fake_path, "test.utc")

    # Should return None and error message for non-existent installation
    assert result_data is None
    assert "Error resolving resource" in result_info or "Cannot determine resource type" in result_info

    print("✓ Resource resolution function exists and handles errors correctly!")


if __name__ == "__main__":
    print("Testing KotorDiff new features")
    print("=" * 40)

    tests_passed = 0
    total_tests = 5

    if test_logging_system():
        tests_passed += 1

    if test_diff_objects():
        tests_passed += 1

    if test_formatters():
        tests_passed += 1

    test_should_include_in_filtered_diff()
    tests_passed += 1

    test_resource_resolution()
    tests_passed += 1

    print(f"Tests completed: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
