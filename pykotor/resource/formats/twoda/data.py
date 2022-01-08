"""
This module handles classes relating to editing 2DA files.
"""
from __future__ import annotations

from pykotor.resource.formats.twoda_io import *
from pykotor.resource.ops import BinaryOps, CSVOps


class TwoDA(BinaryOps, CSVOps):
    """
    Represents the data of a 2DA file.
    """
    BINARY_READER = TwoDABinaryReader

    def __init__(self):
        ...
