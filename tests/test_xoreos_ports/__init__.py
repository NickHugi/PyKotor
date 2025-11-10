"""
Comprehensive port of xoreos-tools test suite to PyKotor.

This module contains a complete 1:1 port of all tests from the xoreos-tools
project, adapted to use PyKotor's functionality and Python's unittest framework.

The tests are organized into the same categories as the original xoreos-tools:
- common: Common utility tests (string, encoding, streams, etc.)
- aurora: File format tests (2DA, BIF, ERF, GFF, etc.)
- images: Image processing tests
- xml: XML parser tests
- version: Version tests

All tests have been ported comprehensively with no exceptions, maintaining
the same test coverage and validation as the original C++ implementation.

Original xoreos-tools tests location: vendor/xoreos-tools/tests/
Port implementation started: 2025-01-09
"""
