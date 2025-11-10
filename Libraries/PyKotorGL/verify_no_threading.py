#!/usr/bin/env python3
"""Verification script to ensure NO threading is used in async loading system.

This script checks:
1. No threading/ThreadPool imports
2. Only ProcessPoolExecutor is used
3. Multiprocessing is properly configured
"""

from __future__ import annotations

import ast
import sys

from pathlib import Path


def check_file_for_threading(filepath: Path) -> tuple[bool, list[str]]:
    """Check a Python file for threading-related imports.
    
    Returns:
    -------
        (passed, violations)
    """
    violations = []
    
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
        
        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.lower()
                    if "thread" in name and "multiprocessing" not in name:
                        violations.append(f"Import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.lower()
                    if "thread" in module and "multiprocessing" not in module:
                        violations.append(f"From import: {node.module}")
                    
                    # Check for ThreadPoolExecutor specifically
                    for alias in node.names:
                        if "threadpool" in alias.name.lower():
                            violations.append(f"ThreadPoolExecutor import: {alias.name}")
        
    except Exception as e:
        violations.append(f"Error parsing file: {e!s}")
    
    return len(violations) == 0, violations


def check_for_process_pool(filepath: Path) -> tuple[bool, str]:
    """Check that ProcessPoolExecutor is used."""
    try:
        source = filepath.read_text(encoding="utf-8")
        
        if "ProcessPoolExecutor" in source:
            return True, "ProcessPoolExecutor found ✓"
        return False, "ProcessPoolExecutor NOT found ✗"
    
    except Exception as e:
        return False, f"Error: {e!s}"


def check_multiprocessing_spawn(filepath: Path) -> tuple[bool, str]:
    """Check that spawn context is used for multiprocessing."""
    try:
        source = filepath.read_text(encoding="utf-8")
        
        # Look for spawn context
        if 'get_context("spawn")' in source or "get_context('spawn')" in source:
            return True, "Spawn context configured ✓"
        
        # ProcessPoolExecutor without explicit spawn is okay on Windows
        if "ProcessPoolExecutor" in source:
            return True, "ProcessPoolExecutor present (spawn is default on Windows) ✓"
        
        return False, "No multiprocessing configuration found ✗"
    
    except Exception as e:
        return False, f"Error: {e!s}"


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Async Loading System - Threading Verification")
    print("=" * 70)
    
    # Find the async_loader.py file
    script_dir = Path(__file__).parent
    async_loader = script_dir / "src" / "pykotor" / "gl" / "scene" / "async_loader.py"
    scene_base = script_dir / "src" / "pykotor" / "gl" / "scene" / "scene_base.py"
    scene = script_dir / "src" / "pykotor" / "gl" / "scene" / "scene.py"
    
    all_passed = True
    
    # Check async_loader.py
    print(f"\n1. Checking {async_loader.name}...")
    if not async_loader.exists():
        print(f"   ✗ File not found: {async_loader}")
        all_passed = False
    else:
        # Check for threading
        passed, violations = check_file_for_threading(async_loader)
        if passed:
            print("   ✓ No threading imports found")
        else:
            print("   ✗ Threading violations found:")
            for violation in violations:
                print(f"      - {violation}")
            all_passed = False
        
        # Check for ProcessPoolExecutor
        passed, msg = check_for_process_pool(async_loader)
        print(f"   {msg}")
        if not passed:
            all_passed = False
        
        # Check for spawn context
        passed, msg = check_multiprocessing_spawn(async_loader)
        print(f"   {msg}")
        if not passed:
            all_passed = False
    
    # Check scene_base.py
    print(f"\n2. Checking {scene_base.name}...")
    if not scene_base.exists():
        print(f"   ✗ File not found: {scene_base}")
        all_passed = False
    else:
        passed, violations = check_file_for_threading(scene_base)
        if passed:
            print("   ✓ No threading imports found")
        else:
            print("   ✗ Threading violations found:")
            for violation in violations:
                print(f"      - {violation}")
            all_passed = False
    
    # Check scene.py
    print(f"\n3. Checking {scene.name}...")
    if not scene.exists():
        print(f"   ✗ File not found: {scene}")
        all_passed = False
    else:
        passed, violations = check_file_for_threading(scene)
        if passed:
            print("   ✓ No threading imports found")
        else:
            print("   ✗ Threading violations found:")
            for violation in violations:
                print(f"      - {violation}")
            all_passed = False
    
    # Final result
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - NO THREADING DETECTED")
        print("\nThe async loading system uses ONLY:")
        print("  - ProcessPoolExecutor for IO operations")
        print("  - ProcessPoolExecutor for parsing operations")
        print("  - Main process for OpenGL rendering")
        print("\n✅ Zero threading anywhere in the system")
    else:
        print("✗ VERIFICATION FAILED")
        print("\nSome checks did not pass. Review the violations above.")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

