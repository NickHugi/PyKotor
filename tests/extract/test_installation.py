import os
from unittest import TestCase

from pykotor.extract.file import FileQuery

from pykotor.extract.capsule import Capsule

from pykotor.resource.type import ResourceType

from pykotor.extract.installation import Installation, SearchLocation


class TestInstallation(TestCase):
    def setUp(self) -> None:
        path = os.environ.get("K1_PATH")
        self.installation = Installation(path)

        if not os.path.exists(self.installation.override_path() + "nwscript.nss"):
            raise ValueError("Place nwscript.nss in override folder before testing.")

    def test_resource(self):
        installation = self.installation

        self.assertIsNone(installation.resource("c_bantha", ResourceType.UTC, []))
        self.assertIsNotNone(installation.resource("c_bantha", ResourceType.UTC))

        self.assertIsNotNone(installation.resource("c_bantha", ResourceType.UTC, [SearchLocation.CHITIN]))
        self.assertIsNone(installation.resource("xxx", ResourceType.UTC, [SearchLocation.CHITIN]))
        self.assertIsNotNone(installation.resource("m13aa", ResourceType.ARE, [SearchLocation.MODULES]))
        self.assertIsNone(installation.resource("xxx", ResourceType.ARE, [SearchLocation.MODULES]))
        self.assertIsNotNone(installation.resource("nwscript", ResourceType.NSS, [SearchLocation.OVERRIDE]))
        self.assertIsNone(installation.resource("xxx", ResourceType.NSS, [SearchLocation.OVERRIDE]))
        self.assertIsNotNone(installation.resource("NM03ABCITI06004_", ResourceType.WAV, [SearchLocation.VOICE]))
        self.assertIsNone(installation.resource("xxx", ResourceType.WAV, [SearchLocation.VOICE]))
        self.assertIsNotNone(installation.resource("P_hk47_POIS", ResourceType.WAV, [SearchLocation.SOUND]))
        self.assertIsNone(installation.resource("xxx", ResourceType.WAV, [SearchLocation.SOUND]))
        self.assertIsNotNone(installation.resource("mus_theme_carth", ResourceType.WAV, [SearchLocation.MUSIC]))
        self.assertIsNone(installation.resource("xxx", ResourceType.WAV, [SearchLocation.MUSIC]))
        self.assertIsNotNone(installation.resource("n_gendro_coms1", ResourceType.LIP, [SearchLocation.LIPS]))
        self.assertIsNone(installation.resource("xxx", ResourceType.LIP, [SearchLocation.LIPS]))
        self.assertIsNotNone(installation.resource("darkjedi", ResourceType.SSF, [SearchLocation.RIMS]))
        self.assertIsNone(installation.resource("xxx", ResourceType.SSF, [SearchLocation.RIMS]))
        self.assertIsNotNone(installation.resource("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPA]))
        self.assertIsNone(installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPA]))
        self.assertIsNotNone(installation.resource("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPB]))
        self.assertIsNone(installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPB]))
        self.assertIsNotNone(installation.resource("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPC]))
        self.assertIsNone(installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPC]))
        self.assertIsNotNone(installation.resource("PO_PCarth", ResourceType.TPC, [SearchLocation.TEXTURES_GUI]))
        self.assertIsNone(installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_GUI]))

        self.assertIsNotNone(installation.resource("nwscript", ResourceType.NSS, [SearchLocation.CUSTOM_FOLDERS], folders=[installation.override_path()]).data)
        self.assertIsNotNone(installation.resource("m13aa", ResourceType.ARE, [SearchLocation.CUSTOM_MODULES], capsules=[Capsule(installation.module_path() + "danm13.rim")]).data)

        self.assertTrue(installation.resource("nwscript", ResourceType.NSS, [SearchLocation.CHITIN, SearchLocation.OVERRIDE]).filepath.endswith(".bif"))
        self.assertTrue(installation.resource("nwscript", ResourceType.NSS, [SearchLocation.OVERRIDE, SearchLocation.CHITIN]).filepath.endswith(".nss"))

    def test_batch_resource(self):
        installation = self.installation

        self.assertFalse(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)], []))
        self.assertTrue(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)]))

        self.assertTrue(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)], [SearchLocation.MODULES]))

        self.assertTrue(installation.resource_batch([FileQuery("c_bantha", ResourceType.UTC)], [SearchLocation.CHITIN]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.UTC)], [SearchLocation.CHITIN]))
        self.assertTrue(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)], [SearchLocation.MODULES]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.ARE)], [SearchLocation.MODULES]))
        self.assertTrue(installation.resource_batch([FileQuery("nwscript", ResourceType.NSS)], [SearchLocation.OVERRIDE]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.NSS)], [SearchLocation.OVERRIDE]))
        self.assertTrue(installation.resource_batch([FileQuery("NM03ABCITI06004_", ResourceType.WAV)], [SearchLocation.VOICE]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.WAV)], [SearchLocation.VOICE]))
        self.assertTrue(installation.resource_batch([FileQuery("P_hk47_POIS", ResourceType.WAV)], [SearchLocation.SOUND]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.WAV)], [SearchLocation.SOUND]))
        self.assertTrue(installation.resource_batch([FileQuery("mus_theme_carth", ResourceType.WAV)], [SearchLocation.MUSIC]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.WAV)], [SearchLocation.MUSIC]))
        self.assertTrue(installation.resource_batch([FileQuery("n_gendro_coms1", ResourceType.LIP)], [SearchLocation.LIPS]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.LIP)], [SearchLocation.LIPS]))
        self.assertTrue(installation.resource_batch([FileQuery("darkjedi", ResourceType.SSF)], [SearchLocation.RIMS]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.SSF)], [SearchLocation.RIMS]))
        self.assertTrue(installation.resource_batch([FileQuery("blood", ResourceType.TPC)], [SearchLocation.TEXTURES_TPA]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_TPA]))
        self.assertTrue(installation.resource_batch([FileQuery("blood", ResourceType.TPC)], [SearchLocation.TEXTURES_TPB]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_TPB]))
        self.assertTrue(installation.resource_batch([FileQuery("blood", ResourceType.TPC)], [SearchLocation.TEXTURES_TPC]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_TPC]))
        self.assertTrue(installation.resource_batch([FileQuery("PO_PCarth", ResourceType.TPC)], [SearchLocation.TEXTURES_GUI]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_GUI]))

    def test_locate(self):
        installation = self.installation

        self.assertFalse(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)], []))
        self.assertTrue(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)]))

        self.assertTrue(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)], [SearchLocation.MODULES]))

        self.assertTrue(installation.resource_batch([FileQuery("c_bantha", ResourceType.UTC)], [SearchLocation.CHITIN]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.UTC)], [SearchLocation.CHITIN]))
        self.assertTrue(installation.resource_batch([FileQuery("m13aa", ResourceType.ARE)], [SearchLocation.MODULES]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.ARE)], [SearchLocation.MODULES]))
        self.assertTrue(installation.resource_batch([FileQuery("nwscript", ResourceType.NSS)], [SearchLocation.OVERRIDE]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.NSS)], [SearchLocation.OVERRIDE]))
        self.assertTrue(installation.resource_batch([FileQuery("NM03ABCITI06004_", ResourceType.WAV)], [SearchLocation.VOICE]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.WAV)], [SearchLocation.VOICE]))
        self.assertTrue(installation.resource_batch([FileQuery("P_hk47_POIS", ResourceType.WAV)], [SearchLocation.SOUND]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.WAV)], [SearchLocation.SOUND]))
        self.assertTrue(installation.resource_batch([FileQuery("mus_theme_carth", ResourceType.WAV)], [SearchLocation.MUSIC]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.WAV)], [SearchLocation.MUSIC]))
        self.assertTrue(installation.resource_batch([FileQuery("n_gendro_coms1", ResourceType.LIP)], [SearchLocation.LIPS]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.LIP)], [SearchLocation.LIPS]))
        self.assertTrue(installation.resource_batch([FileQuery("darkjedi", ResourceType.SSF)], [SearchLocation.RIMS]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.SSF)], [SearchLocation.RIMS]))
        self.assertTrue(installation.resource_batch([FileQuery("blood", ResourceType.TPC)], [SearchLocation.TEXTURES_TPA]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_TPA]))
        self.assertTrue(installation.resource_batch([FileQuery("blood", ResourceType.TPC)], [SearchLocation.TEXTURES_TPB]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_TPB]))
        self.assertTrue(installation.resource_batch([FileQuery("blood", ResourceType.TPC)], [SearchLocation.TEXTURES_TPC]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_TPC]))
        self.assertTrue(installation.resource_batch([FileQuery("PO_PCarth", ResourceType.TPC)], [SearchLocation.TEXTURES_GUI]))
        self.assertFalse(installation.resource_batch([FileQuery("xxx", ResourceType.TPC)], [SearchLocation.TEXTURES_GUI]))

