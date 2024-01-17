import os
import pathlib
import sys
import unittest
from unittest import TestCase

from pykotor.tools.path import CaseAwarePath

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.chitin import Chitin

NWN_BASE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Neverwinter Nights"
NWN_KEY_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Neverwinter Nights\data\nwn_base.key"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")

class TestChitin(TestCase):
    def test_nwn_chitin(self):
        chitin = Chitin(NWN_KEY_PATH, NWN_BASE_PATH)
    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_chitin(self):
        chitin = Chitin(CaseAwarePath(K1_PATH, "chitin.key"))
    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_chitin(self):
        chitin = Chitin(CaseAwarePath(K2_PATH, "chitin.key"))


if __name__ == "__main__":
    unittest.main()
