from unittest import TestCase

from pykotor.extract.capsule import Capsule
from pykotor.resource.type import ResourceType

TEST_FILE_ERF = "tests/files/capsule.mod"
TEST_FILE_RIM = "tests/files/capsule.rim"


class TestCapsule(TestCase):
    def test_erf_capsule(self):
        erf_capsule = Capsule(TEST_FILE_ERF)

        self.assertEqual(3, len(erf_capsule))

        self.assertTrue(erf_capsule.exists("001ebo", ResourceType.ARE))
        self.assertEqual(4865, len(erf_capsule.resource("001ebo", ResourceType.ARE)))
        self.assertEqual(
            "ARE ", erf_capsule.resource("001ebo", ResourceType.ARE)[:4].decode()
        )

        self.assertTrue(erf_capsule.exists("001ebo", ResourceType.GIT))
        self.assertEqual(42565, len(erf_capsule.resource("001ebo", ResourceType.GIT)))
        self.assertEqual(
            "GIT ", erf_capsule.resource("001ebo", ResourceType.GIT)[:4].decode()
        )

        self.assertTrue(erf_capsule.exists("001ebo", ResourceType.PTH))
        self.assertEqual(19788, len(erf_capsule.resource("001ebo", ResourceType.PTH)))
        self.assertEqual(
            "PTH ", erf_capsule.resource("001ebo", ResourceType.PTH)[:4].decode()
        )

    def test_rim_capsule(self):
        rim_capsule = Capsule(TEST_FILE_RIM)

        self.assertEqual(3, len(rim_capsule))

        self.assertTrue(rim_capsule.exists("m13aa", ResourceType.ARE))
        self.assertEqual(4096, len(rim_capsule.resource("m13aa", ResourceType.ARE)))
        self.assertEqual(
            "ARE ", rim_capsule.resource("m13aa", ResourceType.ARE)[:4].decode()
        )

        self.assertTrue(rim_capsule.exists("m13aa", ResourceType.GIT))
        self.assertEqual(51747, len(rim_capsule.resource("m13aa", ResourceType.GIT)))
        self.assertEqual(
            "GIT ", rim_capsule.resource("m13aa", ResourceType.GIT)[:4].decode()
        )

        self.assertTrue(rim_capsule.exists("module", ResourceType.IFO))
        self.assertEqual(1655, len(rim_capsule.resource("module", ResourceType.IFO)))
        self.assertEqual(
            "IFO ", rim_capsule.resource("module", ResourceType.IFO)[:4].decode()
        )
