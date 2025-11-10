from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)


from pykotor.extract.chitin import Chitin
from pykotor.tools.path import CaseAwarePath

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestChitin(TestCase):
    @unittest.skipIf(
        not K1_PATH or not CaseAwarePath(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_chitin(self):
        chitin = Chitin(CaseAwarePath(K1_PATH, "chitin.key"))

    @unittest.skipIf(
        not K2_PATH or not CaseAwarePath(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_chitin(self):
        chitin = Chitin(CaseAwarePath(K2_PATH, "chitin.key"))


if __name__ == "__main__":
    unittest.main()
