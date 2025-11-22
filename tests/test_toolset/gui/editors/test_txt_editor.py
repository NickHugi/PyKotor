from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
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
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class TXTEditorTest(TestCase):
    def setUp(self):
        from toolset.gui.editors.txt import TXTEditor

        self.app = QApplication([])
        self.ui = TXTEditor(None, None)

    def tearDown(self):
        self.app.deleteLater()

    def test_placeholder(self): ...


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Additional UI tests (merged from test_ui_other_editors.py and test_ui_editors.py)
# ============================================================================

import pytest
from toolset.gui.editors.txt import TXTEditor
from toolset.data.installation import HTInstallation

def test_txt_editor(qtbot, installation: HTInstallation):
    """Test TXT Editor."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert editor.isVisible()
    assert hasattr(editor.ui, "textEdit")
    
    editor.ui.textEdit.setPlainText("Hello World")
    data, _ = editor.build()
    assert b"Hello World" in data