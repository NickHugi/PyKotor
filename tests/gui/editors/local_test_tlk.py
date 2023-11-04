import os
from unittest import TestCase

from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
import sys
from pathlib import Path

toolset_path = Path("./toolset").resolve()
if toolset_path.exists() and getattr(sys, "frozen", False) is False:
    sys.path.append(str(toolset_path))
    toolset_parent_path = toolset_path.parent.resolve()
    sys.path.append(str(toolset_parent_path))
    os.chdir(toolset_parent_path)
from toolset.data.installation import HTInstallation
from toolset.gui.editors.tlk import TLKEditor


class TLKEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        cls.INSTALLATION = HTInstallation(os.environ.get("K1_PATH"), "", False, None)

    def setUp(self) -> None:
        self.app = QApplication([])
        self.ui = TLKEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_placeholder(self):
        ...
