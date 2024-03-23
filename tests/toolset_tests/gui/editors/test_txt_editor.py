from __future__ import annotations

import os
import pathlib
import sys
import unittest

from unittest import TestCase

try:
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    QTest, QApplication = None, None  # type: ignore[misc, assignment]


if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if toolset_path.exists():
        working_dir = str(toolset_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

K1_PATH = os.environ.get("K1_PATH")


@unittest.skipIf(
    not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
    "K1_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "PyQt5 is required, please run pip install -r requirements.txt before running this test.",
)
class TXTEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K1_PATH, "", False, None)

    def setUp(self):
        from toolset.gui.editors.txt import TXTEditor

        self.app = QApplication([])
        self.ui = TXTEditor(None, self.INSTALLATION)

    def tearDown(self):
        self.app.deleteLater()

    def test_placeholder(self): ...


if __name__ == "__main__":
    unittest.main()
