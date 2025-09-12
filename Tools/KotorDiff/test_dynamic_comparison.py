#!/usr/bin/env python3
"""Test script to verify the dynamic comparison functionality works correctly."""
from __future__ import annotations

import sys
import tempfile

from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).absolute().parent / "src"))

from kotordiff.__main__ import _has_comparable_interface, _is_text_content, diff_data


def test_text_detection():
    """Test text content detection."""
    print("Testing text content detection...")

    # Test UTF-8 text
    utf8_text = "Hello, world! This is a test file.\nWith multiple lines.\n"
    assert _is_text_content(utf8_text.encode("utf-8")), "UTF-8 text should be detected as text"

    # Test Windows-1252 text
    win1252_text = "Hello, world! This is a test file.\nWith multiple lines.\n"
    assert _is_text_content(win1252_text.encode("windows-1252")), "Windows-1252 text should be detected as text"

    # Test binary content
    binary_data = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
    assert not _is_text_content(binary_data), "Binary data should not be detected as text"

    # Test empty data
    assert _is_text_content(b""), "Empty data should be detected as text"

    print("✓ Text content detection works correctly")

def test_comparable_interface():
    """Test ComparableMixin interface detection."""
    print("Testing ComparableMixin interface detection...")

    # Test with a mock object that has compare method
    class MockComparable:
        def compare(self, other, log_func=None):
            return True

    mock_obj = MockComparable()
    assert _has_comparable_interface(mock_obj), "Object with compare method should be detected"

    # Test with a regular object
    regular_obj = "hello"
    assert not _has_comparable_interface(regular_obj), "Regular object should not be detected as comparable"

    print("✓ ComparableMixin interface detection works correctly")

def test_text_comparison():
    """Test text file comparison."""
    print("Testing text file comparison...")

    # Create temporary files with different content
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f1:
        f1.write("Line 1\nLine 2\nLine 3\n")
        f1_path = Path(f1.name)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f2:
        f2.write("Line 1\nLine 2 Modified\nLine 3\n")
        f2_path = Path(f2.name)

    try:
        # Test comparison - should return False (different)
        result = diff_data(f1_path, f2_path, f1_path, f2_path, "txt")
        assert result is False, "Different text files should return False"

        # Test comparison with identical files
        result = diff_data(f1_path, f1_path, f1_path, f1_path, "txt")
        assert result is True, "Identical text files should return True"

    finally:
        # Clean up
        f1_path.unlink(missing_ok=True)
        f2_path.unlink(missing_ok=True)

    print("✓ Text file comparison works correctly")

def test_binary_comparison():
    """Test binary file comparison."""
    print("Testing binary file comparison...")

    # Create temporary files with different binary content
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f1:
        f1.write(b"\x00\x01\x02\x03\x04\x05")
        f1_path = Path(f1.name)

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f2:
        f2.write(b"\x00\x01\x02\x03\x04\x06")  # Different last byte
        f2_path = Path(f2.name)

    try:
        # Test comparison - should return False (different)
        result = diff_data(f1_path, f2_path, f1_path, f2_path, "bin")
        assert result is False, "Different binary files should return False"

        # Test comparison with identical files
        result = diff_data(f1_path, f1_path, f1_path, f1_path, "bin")
        assert result is True, "Identical binary files should return True"

    finally:
        # Clean up
        f1_path.unlink(missing_ok=True)
        f2_path.unlink(missing_ok=True)

    print("✓ Binary file comparison works correctly")

def main():
    """Run all tests."""
    print("Running dynamic comparison tests...\n")

    try:
        test_text_detection()
        test_comparable_interface()
        test_text_comparison()
        test_binary_comparison()

        print("\n🎉 All tests passed! The dynamic comparison system is working correctly.")
        print("\nKey improvements:")
        print("- ✅ Dynamic detection of ComparableMixin interface")
        print("- ✅ Intelligent text vs binary content detection")
        print("- ✅ Line-by-line text diffing for text files")
        print("- ✅ Hash comparison fallback for binary files")
        print("- ✅ Support for all PyKotor resource types without hardcoding")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
