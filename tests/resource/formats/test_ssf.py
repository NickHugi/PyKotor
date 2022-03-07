from unittest import TestCase

from pykotor.resource.formats.ssf import SSF, SSFSound, SSFBinaryReader, detect_ssf, SSFXMLReader, write_ssf
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "../../files/test.ssf"
XML_TEST_FILE = "../../files/test.ssf.xml"


class TestSSF(TestCase):
    def test_binary_io(self):
        self.assertEqual(detect_ssf(BINARY_TEST_FILE), ResourceType.SSF)

        ssf = SSFBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(ssf)

        data = bytearray()
        write_ssf(ssf, data, ResourceType.SSF)
        ssf = SSFBinaryReader(data).load()
        self.validate_io(ssf)

    def test_xml_io(self):
        self.assertEqual(detect_ssf(XML_TEST_FILE), ResourceType.SSF_XML)

        ssf = SSFXMLReader(XML_TEST_FILE).load()
        self.validate_io(ssf)

        data = bytearray()
        write_ssf(ssf, data, ResourceType.SSF_XML)
        ssf = SSFXMLReader(data).load()
        self.validate_io(ssf)

    def validate_io(self, ssf: SSF):
        self.assertEqual(ssf.get(SSFSound.BATTLE_CRY_1), 123075)
        self.assertEqual(ssf.get(SSFSound.BATTLE_CRY_2), 123074)
        self.assertEqual(ssf.get(SSFSound.BATTLE_CRY_3), 123073)
        self.assertEqual(ssf.get(SSFSound.BATTLE_CRY_4), 123072)
        self.assertEqual(ssf.get(SSFSound.BATTLE_CRY_5), 123071)
        self.assertEqual(ssf.get(SSFSound.BATTLE_CRY_6), 123070)
        self.assertEqual(ssf.get(SSFSound.SELECT_1), 123069)
        self.assertEqual(ssf.get(SSFSound.SELECT_2), 123068)
        self.assertEqual(ssf.get(SSFSound.SELECT_3), 123067)
        self.assertEqual(ssf.get(SSFSound.ATTACK_GRUNT_1), 123066)
        self.assertEqual(ssf.get(SSFSound.ATTACK_GRUNT_2), 123065)
        self.assertEqual(ssf.get(SSFSound.ATTACK_GRUNT_3), 123064)
        self.assertEqual(ssf.get(SSFSound.PAIN_GRUNT_1), 123063)
        self.assertEqual(ssf.get(SSFSound.PAIN_GRUNT_2), 123062)
        self.assertEqual(ssf.get(SSFSound.LOW_HEALTH), 123061)
        self.assertEqual(ssf.get(SSFSound.DEAD), 123060)
        self.assertEqual(ssf.get(SSFSound.CRITICAL_HIT), 123059)
        self.assertEqual(ssf.get(SSFSound.TARGET_IMMUNE), 123058)
        self.assertEqual(ssf.get(SSFSound.LAY_MINE), 123057)
        self.assertEqual(ssf.get(SSFSound.DISARM_MINE), 123056)
        self.assertEqual(ssf.get(SSFSound.BEGIN_STEALTH), 123055)
        self.assertEqual(ssf.get(SSFSound.BEGIN_SEARCH), 123054)
        self.assertEqual(ssf.get(SSFSound.BEGIN_UNLOCK), 123053)
        self.assertEqual(ssf.get(SSFSound.UNLOCK_FAILED), 123052)
        self.assertEqual(ssf.get(SSFSound.UNLOCK_SUCCESS), 123051)
        self.assertEqual(ssf.get(SSFSound.SEPARATED_FROM_PARTY), 123050)
        self.assertEqual(ssf.get(SSFSound.REJOINED_PARTY), 123049)
        self.assertEqual(ssf.get(SSFSound.POISONED), 123048)
