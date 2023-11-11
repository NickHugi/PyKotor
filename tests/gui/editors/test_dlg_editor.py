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

K1_PATH = os.environ.get("K1_PATH")


@unittest.skipIf(
    not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
    "K1_PATH environment variable is not set or not found on disk.",
)
class DLGEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        cls.INSTALLATION = HTInstallation(K1_PATH, "", False, None)  # type: ignore[reportGeneralTypeIssues]

    def setUp(self) -> None:
        from toolset.gui.editors.dlg import DLGEditor
        self.app = QApplication([])
        self.ui = DLGEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_placeholder(self):
        ...


if __name__ == "__main__":
    unittest.main()
