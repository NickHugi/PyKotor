#!/usr/bin/env python3
"""
Validation script for case-sensitive filesystem testing.

This script checks if the current system can support case-sensitive testing
and provides diagnostic information.

Usage:
    python tests/common/validate_case_sensitivity.py
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def check_windows_version() -> tuple[bool, str]:
    """Check Windows version and build number."""
    if os.name != "nt":
        return True, "Not Windows"
    
    try:
        # Get Windows version
        result = subprocess.run(
            ["cmd", "/c", "ver"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_str = result.stdout.strip()
        print(f"Windows Version: {version_str}")
        
        # Check build number (needs 17134+ for case sensitivity)
        result = subprocess.run(
            ["wmic", "os", "get", "BuildNumber"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split("\n")
        build_number = int(lines[-1].strip()) if len(lines) > 1 else 0
        print(f"Build Number: {build_number}")
        
        if build_number >= 17134:
            return True, f"Windows 10 Build {build_number} (>= 17134) [OK]"
        else:
            return False, f"Windows Build {build_number} is too old (need >= 17134)"
    except Exception as e:
        return False, f"Failed to check Windows version: {e}"


def check_fsutil_available() -> tuple[bool, str]:
    """Check if fsutil command is available."""
    if os.name != "nt":
        return True, "Not needed on Unix"
    
    try:
        result = subprocess.run(
            ["fsutil", "file"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "fsutil.exe is available [OK]"
        else:
            return False, f"fsutil.exe returned error code {result.returncode}"
    except FileNotFoundError:
        return False, "fsutil.exe not found in PATH"
    except Exception as e:
        return False, f"Failed to check fsutil: {e}"


def check_filesystem_type() -> tuple[bool, str]:
    """Check if the filesystem type supports case sensitivity."""
    if os.name != "nt":
        return True, "Unix filesystems typically support case sensitivity"
    
    try:
        # Get current drive
        current_drive = os.path.splitdrive(os.getcwd())[0]
        if not current_drive:
            current_drive = "C:"
        
        result = subprocess.run(
            ["fsutil", "fsinfo", "volumeinfo", current_drive],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout
        print(f"Volume info for {current_drive}:")
        print(output[:500])  # First 500 chars
        
        if "NTFS" in output:
            return True, f"Filesystem is NTFS [OK]"
        else:
            return False, f"Filesystem might not be NTFS"
    except Exception as e:
        return False, f"Failed to check filesystem: {e}"


def test_case_sensitivity_enable() -> tuple[bool, str]:
    """Test if we can actually enable case sensitivity on a temp directory."""
    print("Creating temporary directory to test case sensitivity...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        print(f"Test directory: {temp_path}")
        
        if os.name == "nt":
            # Test Windows case sensitivity enablement
            try:
                # Try to enable case sensitivity
                result = subprocess.run(
                    ["fsutil", "file", "setCaseSensitiveInfo", str(temp_path), "enable"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                print(f"Enable returncode: {result.returncode}")
                print(f"Enable stdout: {result.stdout}")
                if result.stderr:
                    print(f"Enable stderr: {result.stderr}")
                
                if result.returncode != 0:
                    return False, f"Failed to enable case sensitivity: {result.stderr}"
                
                # Query to verify
                result = subprocess.run(
                    ["fsutil", "file", "queryCaseSensitiveInfo", str(temp_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                print(f"Query stdout: {result.stdout}")
                
                if "enabled" in result.stdout.lower():
                    # Test with actual files
                    test_lower = temp_path / "test.txt"
                    test_upper = temp_path / "TEST.txt"
                    
                    test_lower.write_text("lowercase")
                    
                    if not test_upper.exists():
                        test_upper.write_text("uppercase")
                        if test_lower.exists() and test_upper.exists():
                            content_lower = test_lower.read_text()
                            content_upper = test_upper.read_text()
                            if content_lower != content_upper:
                                return True, "Case sensitivity works! Created separate 'test.txt' and 'TEST.txt' [OK]"
                    
                    return False, "Case sensitivity enabled but files not treated as different"
                else:
                    return False, "Case sensitivity not enabled after command"
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                return False, f"Exception during test: {e}"
        else:
            # Test Unix case sensitivity
            try:
                test_lower = temp_path / "test.txt"
                test_upper = temp_path / "TEST.txt"
                
                test_lower.write_text("lowercase")
                
                if not test_upper.exists():
                    test_upper.write_text("uppercase")
                    if test_lower.exists() and test_upper.exists():
                        content_lower = test_lower.read_text()
                        content_upper = test_upper.read_text()
                        if content_lower != content_upper:
                            return True, "Filesystem is case-sensitive [OK]"
                
                return False, "Filesystem appears to be case-insensitive"
            except Exception as e:
                return False, f"Exception during test: {e}"


def check_permissions() -> tuple[bool, str]:
    """Check if we have necessary permissions."""
    if os.name != "nt":
        return True, "Permission check not needed on Unix"
    
    try:
        # Try to run a simple fsutil command
        result = subprocess.run(
            ["fsutil", "file"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "denied" in result.stderr.lower() or "access" in result.stderr.lower():
            return False, "Insufficient permissions - may need Administrator rights"
        
        return True, "Permissions appear sufficient [OK]"
    except Exception as e:
        return False, f"Failed to check permissions: {e}"


def main():
    """Run all validation checks."""
    # Set console encoding to UTF-8 for proper symbol display
    if os.name == "nt":
        try:
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
        except Exception:
            pass  # Fall back to default encoding
    
    print("="*60)
    print("  Case-Sensitive Filesystem Testing Validator")
    print("="*60)
    print(f"\nPlatform: {sys.platform}")
    print(f"OS Name: {os.name}")
    print(f"Python Version: {sys.version}")
    
    checks = [
        ("Windows Version Check", check_windows_version),
        ("fsutil Availability", check_fsutil_available),
        ("Filesystem Type", check_filesystem_type),
        ("Permissions Check", check_permissions),
        ("Case Sensitivity Test", test_case_sensitivity_enable),
    ]
    
    results = []
    for check_name, check_func in checks:
        print_section(check_name)
        try:
            success, message = check_func()
            results.append((check_name, success, message))
            status = "[PASS]" if success else "[FAIL]"
            print(f"\n{status}: {message}")
        except Exception as e:
            results.append((check_name, False, str(e)))
            print(f"\n[ERROR]: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print_section("Summary")
    all_passed = True
    for check_name, success, message in results:
        status = "[+]" if success else "[-]"
        print(f"{status} {check_name}: {message}")
        if not success:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("[+] All checks passed! Your system supports case-sensitive testing.")
        print("\nYou can now run the tests:")
        print("  uv run python tests/common/test_get_case_sensitive_path.py")
        return 0
    else:
        print("[-] Some checks failed. Review the issues above.")
        print("\nCommon solutions:")
        print("  1. Run as Administrator (Windows)")
        print("  2. Ensure Windows 10 version 1803+ or Windows 11")
        print("  3. Verify NTFS filesystem")
        print("  4. Check if fsutil.exe is available")
        return 1


if __name__ == "__main__":
    sys.exit(main())

