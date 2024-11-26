from __future__ import annotations

import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.resource.formats.ssf import (
    SSF,
    SSFBinaryReader,
    SSFSound,
    SSFXMLReader,
    read_ssf,
    write_ssf,
)
from pykotor.resource.formats.ssf.ssf_auto import detect_ssf
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "tests/test_pykotor/test_files/test.ssf"
XML_TEST_FILE = "tests/test_pykotor/test_files/test.ssf.xml"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "tests/test_pykotor/test_files/test_corrupted.ssf"
CORRUPT_XML_TEST_FILE = "tests/test_pykotor/test_files/test_corrupted.ssf.xml"


class TestSSF(unittest.TestCase):
    def test_binary_io(self):
        assert detect_ssf(BINARY_TEST_FILE) == ResourceType.SSF

        ssf = SSFBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(ssf)

        data = bytearray()
        write_ssf(ssf, data, ResourceType.SSF)
        ssf = SSFBinaryReader(data).load()
        self.validate_io(ssf)

    def test_xml_io(self):
        assert detect_ssf(XML_TEST_FILE) == ResourceType.SSF_XML

        ssf = SSFXMLReader(XML_TEST_FILE).load()
        self.validate_io(ssf)

        data = bytearray()
        write_ssf(ssf, data, ResourceType.SSF_XML)
        ssf = SSFXMLReader(data).load()
        self.validate_io(ssf)

    def validate_io(self, ssf: SSF):
        assert ssf.get(SSFSound.BATTLE_CRY_1) == 123075
        assert ssf.get(SSFSound.BATTLE_CRY_2) == 123074
        assert ssf.get(SSFSound.BATTLE_CRY_3) == 123073
        assert ssf.get(SSFSound.BATTLE_CRY_4) == 123072
        assert ssf.get(SSFSound.BATTLE_CRY_5) == 123071
        assert ssf.get(SSFSound.BATTLE_CRY_6) == 123070
        assert ssf.get(SSFSound.SELECT_1) == 123069
        assert ssf.get(SSFSound.SELECT_2) == 123068
        assert ssf.get(SSFSound.SELECT_3) == 123067
        assert ssf.get(SSFSound.ATTACK_GRUNT_1) == 123066
        assert ssf.get(SSFSound.ATTACK_GRUNT_2) == 123065
        assert ssf.get(SSFSound.ATTACK_GRUNT_3) == 123064
        assert ssf.get(SSFSound.PAIN_GRUNT_1) == 123063
        assert ssf.get(SSFSound.PAIN_GRUNT_2) == 123062
        assert ssf.get(SSFSound.LOW_HEALTH) == 123061
        assert ssf.get(SSFSound.DEAD) == 123060
        assert ssf.get(SSFSound.CRITICAL_HIT) == 123059
        assert ssf.get(SSFSound.TARGET_IMMUNE) == 123058
        assert ssf.get(SSFSound.LAY_MINE) == 123057
        assert ssf.get(SSFSound.DISARM_MINE) == 123056
        assert ssf.get(SSFSound.BEGIN_STEALTH) == 123055
        assert ssf.get(SSFSound.BEGIN_SEARCH) == 123054
        assert ssf.get(SSFSound.BEGIN_UNLOCK) == 123053
        assert ssf.get(SSFSound.UNLOCK_FAILED) == 123052
        assert ssf.get(SSFSound.UNLOCK_SUCCESS) == 123051
        assert ssf.get(SSFSound.SEPARATED_FROM_PARTY) == 123050
        assert ssf.get(SSFSound.REJOINED_PARTY) == 123049
        assert ssf.get(SSFSound.POISONED) == 123048

    # sourcery skip: no-conditionals-in-tests
    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_ssf, ".")
        else:
            self.assertRaises(IsADirectoryError, read_ssf, ".")
        self.assertRaises(FileNotFoundError, read_ssf, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_ssf, CORRUPT_BINARY_TEST_FILE)
        self.assertRaises(ValueError, read_ssf, CORRUPT_XML_TEST_FILE)

    # sourcery skip: no-conditionals-in-tests
    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_ssf, SSF(), ".", ResourceType.SSF)
        else:
            self.assertRaises(IsADirectoryError, write_ssf, SSF(), ".", ResourceType.SSF)
        self.assertRaises(ValueError, write_ssf, SSF(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
