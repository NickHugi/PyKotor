import os
from unittest import TestCase

from PyQt5.QtWidgets import QApplication

from data.installation import HTInstallation
from gui.editors.utt import UTTEditor


class UTTEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        cls.INSTALLATION = HTInstallation(os.environ.get("K1_PATH"), "", False, None)

    def setUp(self) -> None:
        self.app = QApplication([])
        self.ui = UTTEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_placeholder(self):
        ...
