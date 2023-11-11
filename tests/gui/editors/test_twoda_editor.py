import os
import pathlib
import sys
import unittest
from unittest import TestCase

from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if pykotor_path.exists() or toolset_path.exists():
        sys.path.insert(0, str(pykotor_path.parent))

from toolset.data.installation import HTInstallation
from toolset.gui.editors.twoda import TwoDAEditor

K1_PATH = os.environ.get("K1_PATH")


@unittest.skipIf(
    not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
    "K1_PATH environment variable is not set or not found on disk.",
)
class TwoDAEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        cls.INSTALLATION = HTInstallation(K1_PATH, "", False, None)

    def setUp(self) -> None:
        self.app = QApplication([])
        self.ui = TwoDAEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_placeholder(self):
        ...


if __name__ == "__main__":
    unittest.main()
