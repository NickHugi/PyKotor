"""Tests for the texture loader process with Qt integration.

Note: Core serialization tests are in tests/test_pykotor_gl/test_texture_loader_core.py
This file tests the Qt integration which requires Qt bindings to be available.
"""

from __future__ import annotations

import pytest

# Skip entire module if Qt is not available
pytest.importorskip("qtpy")
