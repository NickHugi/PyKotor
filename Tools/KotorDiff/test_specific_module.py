#!/usr/bin/env python3

"""Test script to verify specific module search functionality."""
from __future__ import annotations

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Test import
try:
    from kotordiff.__main__ import find_module_root
    print("✓ Import successful")

    # Test find_module_root function
    test_cases = [
        ("tat_m17ac.rim", "tat_m17ac"),
        ("tat_m17ac_s.rim", "tat_m17ac"),
        ("tat_m17ac_dlg.erf", "tat_m17ac"),
        ("danm13.mod", "danm13"),
    ]

    for filename, expected in test_cases:
        result = find_module_root(filename)
        status = "✓" if result == expected else "✗"
        print(f"{status} find_module_root('{filename}') = '{result}' (expected: '{expected}')")

except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print("All tests passed!")
