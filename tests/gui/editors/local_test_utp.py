import os
import pathlib
import sys
from unittest import TestCase
import unittest

from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if pykotor_path.exists() or toolset_path.exists():
        sys.path.append(str(pykotor_path.parent))

from toolset.data.installation import HTInstallation
from toolset.gui.editors.utp import UTPEditor


class UTPEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        cls.INSTALLATION = HTInstallation(os.environ.get("K1_PATH"), "", False, None)

    def setUp(self) -> None:
        self.app = QApplication([])
        self.ui = UTPEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_open_and_save(self):
        editor = UTPEditor(None, self.INSTALLATION)


if __name__ == "__main__":
    unittest.main()
