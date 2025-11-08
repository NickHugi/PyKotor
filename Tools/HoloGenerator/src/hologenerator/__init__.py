#!/usr/bin/env python3
"""
HoloGenerator - KOTOR Configuration Generator for HoloPatcher

This module provides functionality to generate changes.ini files for HoloPatcher
based on the differences between two KOTOR installations or individual files.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "th3w1zard1"
__description__ = "KOTOR Configuration Generator for HoloPatcher"

from hologenerator.core.generator import ConfigurationGenerator
from hologenerator.core.differ import KotorDiffer

__all__ = [
    "ConfigurationGenerator",
    "KotorDiffer",
]