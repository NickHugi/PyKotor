"""Linux helpers for creating case-insensitive directories.

This module provides functionality similar to Windows' `fsutil file setCaseSensitiveInfo`
but for creating case-insensitive directories on Linux.

Linux doesn't support per-directory case-insensitivity like Windows NTFS.
Instead, we use filesystem-level solutions:
1. ciopfs (FUSE-based overlay - closest to Windows per-directory behavior)
2. Loop device with FAT32 filesystem
3. ext4 with casefold feature (kernel 5.2+)

Usage:
    from tests.common.linux_case_insensitive_helpers import create_case_insensitive_dir

    # Method 1: Using ciopfs (recommended)
    mount_point = create_case_insensitive_dir(
        "/tmp/test_ci",
        method="ciopfs"
    )

    # Method 2: Using loop device with FAT32
    mount_point = create_case_insensitive_dir(
        "/tmp/test_fat32",
        method="loop_fat32",
        size_mb=100
    )
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
from typing import Literal


def check_ciopfs_available() -> bool:
    """Check if ciopfs is installed and available."""
    try:
        result = subprocess.run(
            ["which", "ciopfs"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True

        # Also check if it's available but not in PATH
        result = subprocess.run(
            ["ciopfs", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_fusermount_available() -> bool:
    """Check if fusermount (for unmounting FUSE) is available."""
    try:
        result = subprocess.run(
            ["which", "fusermount"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def create_case_insensitive_dir_ciopfs(
    base_path: pathlib.Path | str,
    cleanup_on_error: bool = True,
) -> pathlib.Path | None:
    """
    Create a case-insensitive directory using ciopfs (FUSE overlay).

    Args:
        base_path: Base directory path where the case-insensitive mount will be created
        cleanup_on_error: If True, clean up on error

    Returns:
        Path to the case-insensitive mount point, or None if failed

    Example:
        mount_point = create_case_insensitive_dir_ciopfs("/tmp/test")
        # Files accessed via mount_point will be case-insensitive
        (mount_point / "File.txt").touch()
        assert (mount_point / "file.txt").exists()  # True (case-insensitive)
    """
    if not check_ciopfs_available():
        print("ciopfs is not available. Install with: sudo apt-get install ciopfs")
        return None

    if not check_fusermount_available():
        print("fusermount is not available. Install fuse package.")
        return None

    base_path = pathlib.Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)

    # Create actual data directory and mount point
    data_dir = base_path / ".data"
    mount_point = base_path / "case_insensitive"

    try:
        data_dir.mkdir(exist_ok=True)
        mount_point.mkdir(exist_ok=True)

        # Mount with ciopfs
        # ciopfs <source_dir> <mount_point>
        result = subprocess.run(
            ["ciopfs", str(data_dir), str(mount_point)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            print(f"Failed to mount ciopfs: {result.stderr}")
            if cleanup_on_error:
                mount_point.rmdir()
                data_dir.rmdir()
            return None

        print(f"Case-insensitive directory created using ciopfs: {mount_point}")
        print(f"  Data directory: {data_dir}")
        print(f"  Mount point: {mount_point}")
        return mount_point

    except subprocess.TimeoutExpired:
        print("ciopfs mount command timed out")
        if cleanup_on_error:
            mount_point.rmdir()
            data_dir.rmdir()
        return None
    except Exception as e:
        print(f"Error creating ciopfs mount: {e}")
        if cleanup_on_error:
            mount_point.rmdir()
            data_dir.rmdir()
        return None


def unmount_case_insensitive_dir_ciopfs(mount_point: pathlib.Path | str) -> bool:
    """Unmount a ciopfs case-insensitive directory."""
    mount_point = pathlib.Path(mount_point)

    if not mount_point.exists():
        print(f"Mount point {mount_point} does not exist")
        return False

    try:
        result = subprocess.run(
            ["fusermount", "-u", str(mount_point)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(f"Unmounted ciopfs from {mount_point}")
            return True
        else:
            print(f"Failed to unmount: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error unmounting ciopfs: {e}")
        return False


def create_case_insensitive_dir_loop_fat32(
    base_path: pathlib.Path | str,
    size_mb: int = 100,
    cleanup_on_error: bool = True,
) -> pathlib.Path | None:
    """
    Create a case-insensitive directory using a loop device with FAT32 filesystem.

    Args:
        base_path: Base directory path
        size_mb: Size of FAT32 image in megabytes
        cleanup_on_error: If True, clean up on error

    Returns:
        Path to the mounted FAT32 directory, or None if failed

    Note:
        Requires root/sudo privileges for loop device mounting.
    """
    base_path = pathlib.Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)

    image_file = base_path / "case_insensitive.img"
    mount_point = base_path / "case_insensitive"

    try:
        # Check if we can use sudo
        sudo_check = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=5,
        )
        has_sudo = sudo_check.returncode == 0
        if not has_sudo:
            print("FAT32 loop device mounting requires sudo privileges")
            print("Run with sudo or configure passwordless sudo for mount/umount")
            return None

        # Create FAT32 image
        print(f"Creating {size_mb}MB FAT32 image...")
        subprocess.run(
            ["dd", "if=/dev/zero", f"of={image_file}", f"bs=1M", f"count={size_mb}"],
            capture_output=True,
            check=True,
            timeout=60,
        )

        # Format as FAT32
        print("Formatting as FAT32...")
        subprocess.run(
            ["mkfs.vfat", str(image_file)],
            capture_output=True,
            check=True,
            timeout=30,
        )

        # Create mount point
        mount_point.mkdir(exist_ok=True)

        # Mount as loop device
        print(f"Mounting loop device to {mount_point}...")
        result = subprocess.run(
            ["sudo", "mount", "-o", "loop", str(image_file), str(mount_point)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            print(f"Failed to mount loop device: {result.stderr}")
            if cleanup_on_error:
                image_file.unlink(missing_ok=True)
                mount_point.rmdir()
            return None

        print(f"Case-insensitive directory created using FAT32 loop device: {mount_point}")
        return mount_point

    except subprocess.CalledProcessError as e:
        print(f"Error creating FAT32 loop device: {e}")
        if cleanup_on_error:
            image_file.unlink(missing_ok=True)
            mount_point.rmdir()
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        if cleanup_on_error:
            image_file.unlink(missing_ok=True)
            mount_point.rmdir()
        return None


def unmount_case_insensitive_dir_loop_fat32(mount_point: pathlib.Path | str) -> bool:
    """Unmount a FAT32 loop device case-insensitive directory."""
    mount_point = pathlib.Path(mount_point)

    if not mount_point.exists():
        print(f"Mount point {mount_point} does not exist")
        return False

    try:
        result = subprocess.run(
            ["sudo", "umount", str(mount_point)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(f"Unmounted FAT32 loop device from {mount_point}")
            return True
        else:
            print(f"Failed to unmount: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error unmounting loop device: {e}")
        return False


def create_case_insensitive_dir(
    base_path: pathlib.Path | str,
    method: Literal["ciopfs", "loop_fat32"] = "ciopfs",
    **kwargs,
) -> pathlib.Path | None:
    """
    Create a case-insensitive directory using the specified method.

    Args:
        base_path: Base directory path
        method: Method to use ("ciopfs" or "loop_fat32")
        **kwargs: Additional arguments for specific methods
                 - For loop_fat32: size_mb (default: 100)

    Returns:
        Path to case-insensitive mount point, or None if failed

    Example:
        # Using ciopfs (recommended - no sudo needed)
        mount = create_case_insensitive_dir("/tmp/test", method="ciopfs")

        # Using FAT32 loop device (requires sudo)
        mount = create_case_insensitive_dir("/tmp/test", method="loop_fat32", size_mb=200)
    """
    if method == "ciopfs":
        return create_case_insensitive_dir_ciopfs(base_path, **kwargs)
    elif method == "loop_fat32":
        return create_case_insensitive_dir_loop_fat32(base_path, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'ciopfs' or 'loop_fat32'")


def is_case_insensitive_directory(path: pathlib.Path | str) -> bool:
    """
    Check if a directory is case-insensitive.

    Args:
        path: Directory path to check

    Returns:
        True if case-insensitive, False otherwise
    """
    path = pathlib.Path(path)

    if not path.exists() or not path.is_dir():
        return False

    # Test by creating files with different cases
    test_file1 = path / "test_case_sensitivity.TMP"
    test_file2 = path / "TEST_CASE_SENSITIVITY.tmp"

    try:
        test_file1.touch()
        is_insensitive = test_file2.exists()
        test_file1.unlink()
        return is_insensitive
    except Exception:
        return False


if __name__ == "__main__":
    # Example usage
    import tempfile

    temp_base = pathlib.Path(tempfile.mkdtemp())
    print(f"Testing case-insensitive directory creation in {temp_base}")

    # Test ciopfs method
    print("\n=== Testing ciopfs method ===")
    mount_point = create_case_insensitive_dir(temp_base / "ciopfs_test", method="ciopfs")
    if mount_point:
        print(f"✓ ciopfs mount created at {mount_point}")

        # Test case-insensitivity
        test_file = mount_point / "TestFile.txt"
        test_file.write_text("test content")
        assert (mount_point / "testfile.txt").exists(), "Case-insensitive check failed"
        print("✓ Case-insensitivity verified")

        # Cleanup
        unmount_case_insensitive_dir_ciopfs(mount_point)
        shutil.rmtree(temp_base / "ciopfs_test")

    print("\n=== Installation instructions ===")
    print("To install ciopfs:")
    print("  Debian/Ubuntu: sudo apt-get install ciopfs")
    print("  Fedora/RHEL:   sudo dnf install ciopfs")
    print("  Arch:          sudo pacman -S ciopfs")

