import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
        os.chdir(PYKOTOR_PATH.parent)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

from pykotor.extract.chitin import Chitin


NWN_BASE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Neverwinter Nights"
NWN_KEY_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Neverwinter Nights\data\nwn_base.key"

class TestCapsule(TestCase):
    def test_nwn_chitin(self):
        chitin = Chitin(NWN_KEY_PATH, NWN_BASE_PATH)


if __name__ == "__main__":
    unittest.main()
