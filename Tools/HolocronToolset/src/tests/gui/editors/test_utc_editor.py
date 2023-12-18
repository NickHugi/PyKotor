import os
import pathlib
import sys
import unittest
from unittest import TestCase

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import read_gff

from pykotor.resource.type import ResourceType

from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication


K2_PATH = os.environ.get("K2_PATH")

PYKOTOR_PATH = next(f for f in pathlib.Path(__file__).parents if f.name == "Tools").parent / "Libraries" / "PyKotor" / "src" / "pykotor"
sys.path.insert(0, str(PYKOTOR_PATH))

HOLOCRON_TOOLSET_PATH = next(f for f in pathlib.Path(__file__).parents if f.name == "Tools") / "toolset"
sys.path.insert(0, str(HOLOCRON_TOOLSET_PATH))

TESTS_FILES_PATH = next(f for f in pathlib.Path(__file__).parents if f.name == "tests") / "files"


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K1_PATH environment variable is not set or not found on disk.",
)
class UTCEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        from toolset.data.installation import HTInstallation
        cls.INSTALLATION = HTInstallation(K2_PATH, "", True, None)

    def setUp(self) -> None:
        from toolset.gui.editors.utc import UTCEditor
        self.app = QApplication([])
        self.editor = UTCEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "p_hk47.utc"

        data = BinaryReader.load_file(filepath)
        old = read_gff(data)
        self.editor.load(filepath, "p_hk47", ResourceType.UTC, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new)
        self.assertTrue(diff)


if __name__ == "__main__":
    unittest.main()
