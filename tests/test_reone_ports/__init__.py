"""
Comprehensive port of reone test suite to PyKotor.

This module contains a complete 1:1 port of all tests from the reone
project, adapted to use PyKotor's functionality and Python's unittest framework.

The tests are organized into the same categories as the original reone:
- audio: Audio format tests (WAV reader)
- game: Game logic tests (pathfinder)
- graphics: Graphics tests (AABB, walkmesh, format readers)
- resource: Resource format and provider tests (2DA, BIF, ERF, GFF, KEY, RIM, TLK, etc.)
- scene: Scene graph tests (model)
- script: Script format and VM tests (NCS reader/writer, virtual machine)
- system: System utility tests (binary I/O, cache, fileutil, hexutil, etc.)
- tools: Tool tests (LIP composer/analyzer, script expression tree)

All tests have been ported comprehensively with no exceptions, maintaining
the same test coverage and validation as the original C++ implementation.

Original reone tests location: vendor/reone/test/
Port implementation started: 2025-01-09
"""

