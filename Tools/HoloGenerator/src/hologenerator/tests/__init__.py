"""
Test suite for HoloGenerator.

This module contains all unit tests for the HoloGenerator package.
HoloGenerator is a GUI-only tool for KOTOR configuration generation.
"""

import unittest
import sys
import os

# Add the src directory to path for testing
test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(test_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import test modules
from .test_core import *

# Conditionally import GUI tests
try:
    from .test_gui import *
except ImportError:
    print("Skipping GUI tests - tkinter not available")


def run_all_tests():
    """Run all tests in the test suite."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test modules
    suite.addTests(loader.loadTestsFromModule(sys.modules[__name__]))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)