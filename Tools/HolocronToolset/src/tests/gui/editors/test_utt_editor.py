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


TESTS_FILES_PATH = next(f for f in pathlib.Path(__file__).parents if f.name == "tests") / "files"

if getattr(sys, "frozen", False) is False:
    def add_sys_path(p):
        working_dir = str(p)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)
    pykotor_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        add_sys_path(pykotor_path.parent)
    gl_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        add_sys_path(gl_path.parent)
    utility_path = pathlib.Path(__file__).parents[6] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        add_sys_path(utility_path.parent)
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if toolset_path.exists():
        add_sys_path(toolset_path.parent)

K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "PyQt5 is required, please run pip install -r requirements.txt before running this test.",
)
class UTTEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        from toolset.data.installation import HTInstallation
        from toolset.gui.editors.utt import UTTEditor
        cls.UTTEditor = UTTEditor
        #cls.K1_INSTALLATION = HTInstallation(K1_PATH, "", tsl=False, mainWindow=None)
        cls.K2_INSTALLATION = HTInstallation(K2_PATH, "", tsl=False, mainWindow=None)

    def setUp(self) -> None:
        from toolset.gui.editors.utt import UTTEditor
        self.app = QApplication([])
        self.editor = UTTEditor(None, self.K2_INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self) -> None:
        self.app.deleteLater()

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "newtransition9.utt"

        data = BinaryReader.load_file(filepath)
        old = read_gff(data)
        self.editor.load(filepath, "newtransition9", ResourceType.UTT, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        self.assertTrue(diff, os.linesep.join(self.log_messages))

    def test_editor_init(self):
        self.UTTEditor(None, self.K2_INSTALLATION)


if __name__ == "__main__":
    unittest.main()
