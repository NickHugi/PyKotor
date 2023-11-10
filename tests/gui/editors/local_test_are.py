import os
import pathlib
import sys
import unittest
from unittest import TestCase

from PyQt5.QtWidgets import QApplication

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if pykotor_path.exists() or toolset_path.exists():
        sys.path.append(str(pykotor_path.parent))

from toolset.data.installation import HTInstallation
from toolset.gui.editors.are import AREEditor


class AREEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        cls.INSTALLATION = HTInstallation(os.environ.get("K1_PATH"), "", tsl=False, main_window=None)

    def setUp(self) -> None:
        self.app = QApplication([])
        self.ui = AREEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_placeholder(self):
        ...


if __name__ == "__main__":
    unittest.main()
