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
    pykotor_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)
    gl_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        working_dir = str(gl_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)
    utility_path = pathlib.Path(__file__).parents[6] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        working_dir = str(utility_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if toolset_path.exists():
        working_dir = str(toolset_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)


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
class GITEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Make sure to configure this environment path before testing!
        from toolset.gui.editors.git import GITEditor
        cls.GITEditor = GITEditor
        from toolset.data.installation import HTInstallation
        #cls.K1_INSTALLATION = HTInstallation(K1_PATH, "", tsl=False, mainWindow=None)
        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True, mainWindow=None)

    def setUp(self) -> None:
        self.app = QApplication([])
        self.editor = self.GITEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self) -> None:
        self.app.deleteLater()

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "zio001.git"

        data = BinaryReader.load_file(filepath)
        old = read_gff(data)
        self.editor.load(filepath, "zio001", ResourceType.GIT, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        self.assertTrue(diff, os.linesep.join(self.log_messages))

    def test_placeholder(self):
        ...


if __name__ == "__main__":
    unittest.main()
