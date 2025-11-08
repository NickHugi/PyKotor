# Case-Sensitive Testing on Windows

## Overview

This document explains how the case-sensitive filesystem tests work on Windows and how to run them.

## Requirements

### Windows Requirements

- **Operating System**: Windows 10 (version 1803 or later) or Windows 11
- **File System**: NTFS
- **Privileges**: The tests will attempt to enable case sensitivity using `fsutil.exe`
  - On some systems, this may require administrator privileges
  - The script will gracefully skip tests if case sensitivity cannot be enabled
- **Tools**: `fsutil.exe` must be available (standard on Windows)

### Unix/Linux Requirements

- A case-sensitive filesystem (most Linux filesystems are case-sensitive by default)
- The tests will automatically detect if the filesystem is case-insensitive and skip if necessary

## How It Works

### On Windows

The solution leverages Windows 10's per-directory case sensitivity feature:

1. **Detection**: The test suite checks if `fsutil.exe` is available and working
2. **Setup**: For each test run, a temporary directory is created
3. **Enable Case Sensitivity**: Using `fsutil file setCaseSensitiveInfo <path> enable`, case sensitivity is enabled for that specific directory
4. **Testing**: All tests run within this case-sensitive directory
5. **Cleanup**: After tests complete, case sensitivity is disabled and the directory is removed

### On Unix/Linux

1. **Detection**: The test suite verifies the filesystem is case-sensitive
2. **Testing**: Tests run in a standard temporary directory
3. **Cleanup**: The temporary directory is removed after tests

## Running the Tests

### Standard Test Run

```powershell
# Run all tests in the file
uv run python -m pytest tests/common/test_get_case_sensitive_path.py -v

# Or using unittest directly
uv run python tests/common/test_get_case_sensitive_path.py
```

### Run with Verbose Output

```powershell
# See detailed case sensitivity setup information
uv run python tests/common/test_get_case_sensitive_path.py -v
```

### Run Specific Test

```powershell
uv run python -m pytest tests/common/test_get_case_sensitive_path.py::TestCaseAwarePath::test_rtruediv -v
```

## Verifying Case Sensitivity Support

You can manually test if your Windows system supports case sensitivity:

```powershell
# Create a test directory
mkdir C:\test_case_sensitivity

# Enable case sensitivity
fsutil file setCaseSensitiveInfo C:\test_case_sensitivity enable

# Query status
fsutil file queryCaseSensitiveInfo C:\test_case_sensitivity

# Should output: "Case sensitive attribute on directory: Enabled"

# Test it works
cd C:\test_case_sensitivity
echo "test" > file.txt
echo "TEST" > FILE.txt
dir

# Should show TWO files: file.txt and FILE.txt

# Cleanup
cd ..
fsutil file setCaseSensitiveInfo C:\test_case_sensitivity disable
rmdir /S C:\test_case_sensitivity
```

## Troubleshooting

### Tests Are Skipped on Windows

**Symptom**: All tests show as "skipped" with message about case sensitivity not supported

**Possible Causes**:

1. Windows version too old (need 1803+)
2. Not using NTFS filesystem
3. `fsutil.exe` not available or not in PATH

**Solutions**:

1. Check Windows version: Run `winver` and ensure build 17134 or higher
2. Verify NTFS: Run `fsutil fsinfo volumeinfo C:` and look for file system type
3. Verify fsutil: Run `fsutil file` in PowerShell/CMD

### Tests Fail with Permission Errors

**Symptom**: Tests fail with access denied or permission errors

**Possible Causes**:

1. Insufficient privileges to enable case sensitivity
2. Antivirus or security software blocking the operation
3. Directory in use by another process

**Solutions**:

1. Run PowerShell/Terminal as Administrator
2. Temporarily disable antivirus (if safe to do so)
3. Ensure no other processes are accessing the temp directory

### Cleanup Failures

**Symptom**: Warnings about failed cleanup during test teardown

**Impact**: Usually low - temp directories are in the system temp location and will be cleaned up eventually

**Solution**:

- The code uses multiple fallback cleanup strategies
- If persistent, manually clean up: `del /S %TEMP%\tmp*` (but be careful!)

## Implementation Details

### Key Functions

- `is_windows_case_sensitivity_supported()`: Checks if the system can enable case sensitivity
- `get_case_sensitivity_status(path)`: Queries if a directory is case-sensitive
- `enable_case_sensitivity(path)`: Enables case sensitivity (idempotent)
- `disable_case_sensitivity(path)`: Disables case sensitivity (idempotent)
- `CaseSensitiveTempDirectory`: Context manager for case-sensitive temp directories

### Idempotency

All operations are idempotent:

- Enabling case sensitivity on an already case-sensitive directory is a no-op
- Disabling case sensitivity on a case-insensitive directory is a no-op
- Status checks can be called repeatedly without side effects

### No Mocking

This implementation uses **zero** mocking or monkey-patching:

- Real temporary directories are created on disk
- Real case sensitivity is enabled using Windows APIs
- Real file operations test actual behavior
- Tests truly verify cross-platform case-sensitive behavior

## Testing the Solution

To verify the solution works correctly, run:

```powershell
# Run tests with verbose output
uv run python tests/common/test_get_case_sensitive_path.py -v 2>&1 | Tee-Object -FilePath test_output.log

# Check the output for:
# 1. "Case-sensitive directory ready" messages
# 2. No errors about case sensitivity enablement
# 3. All tests passing (or skipping gracefully)
```

## Platform Compatibility

| Platform | Support | Notes |
|----------|---------|-------|
| Windows 11 | ✅ Full | Native support |
| Windows 10 (1803+) | ✅ Full | Native support |
| Windows 10 (< 1803) | ⚠️ Skip | Tests skipped gracefully |
| Linux (ext4, btrfs, etc.) | ✅ Full | Native support |
| macOS (APFS) | ⚠️ Partial | APFS is case-insensitive by default, tests check dynamically |
| macOS (HFS+) | ⚠️ Partial | Usually case-insensitive |

## Developer Notes

### Adding New Tests

When adding new tests that require case sensitivity:

1. Use `self.temp_path` - it's automatically case-sensitive
2. Create files with different cases to test behavior
3. No need to manually enable/disable case sensitivity
4. Cleanup happens automatically in `tearDown()`

Example:

```python
def test_my_case_feature(self):
    # self.temp_path is already case-sensitive
    lower_file = self.temp_path / "file.txt"
    upper_file = self.temp_path / "FILE.TXT"
    
    lower_file.touch()
    # On case-sensitive filesystem, these are different files
    self.assertFalse(upper_file.exists())
```

### Modifying Case Sensitivity Logic

The case sensitivity logic is centralized in helper functions at the top of the test file. If you need to modify behavior:

1. Update the relevant function (`enable_case_sensitivity`, etc.)
2. Ensure idempotency is maintained
3. Update error messages to be informative
4. Test on both Windows and Unix systems

## Known Limitations

1. **Administrator Privileges**: On some Windows configurations, enabling case sensitivity requires admin rights
2. **Filesystem Support**: Only works on NTFS on Windows; other filesystems not supported
3. **Windows Subsystem for Linux (WSL)**: May behave differently in WSL environments
4. **Network Drives**: Case sensitivity cannot be enabled on network drives
5. **Cleanup**: In rare cases, if process is killed forcefully, temp directories may persist

## References

- [Windows Developer Docs - Per-directory case sensitivity](https://learn.microsoft.com/en-us/windows/wsl/case-sensitivity)
- [fsutil file documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil-file)
- [NTFS case sensitivity in Windows 10](https://devblogs.microsoft.com/commandline/per-directory-case-sensitivity-and-wsl/)

## Support

If you encounter issues not covered in this documentation:

1. Check Windows version and build number
2. Verify NTFS filesystem
3. Try running with administrator privileges
4. Check antivirus logs for blocked operations
5. Review test output logs for specific error messages

## Changelog

- **2025-11-02**: Initial implementation with full Windows and Unix support
  - Idempotent case sensitivity operations
  - Comprehensive error handling and cleanup
  - Graceful test skipping when not supported
  - Zero mocking/monkey-patching approach
