from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

from PyQt5.QtWidgets import QApplication

PYKOTOR_PATH = next(f for f in pathlib.Path(__file__).parents if f.name == "Tools").parent / "Libraries" / "PyKotor" / "src" / "pykotor"
sys.path.insert(0, str(PYKOTOR_PATH))

HOLOCRON_TOOLSET_PATH = next(f for f in pathlib.Path(__file__).parents if f.name == "Tools") / "toolset"
sys.path.insert(0, str(HOLOCRON_TOOLSET_PATH))

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
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
class UTCEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.data.installation import HTInstallation
        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True, mainWindow=None)

    def setUp(self):
        from toolset.gui.editors.utc import UTCEditor
        self.app = QApplication([])
        self.editor = UTCEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "p_hk47.utc"

        data = BinaryReader.load_file(filepath)
        old = read_gff(data)
        self.editor.load(filepath, "p_hk47", ResourceType.UTC, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        self.assertTrue(diff, os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for utc_resource in (resource for resource in self.installation if resource.restype() == ResourceType.UTC):
            old = read_gff(utc_resource.data())
            self.editor.load(utc_resource.filepath(), utc_resource.resname(), utc_resource.restype(), utc_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            self.assertTrue(diff, os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for utc_resource in (resource for resource in self.installation if resource.restype() == ResourceType.UTC):
            old = read_gff(utc_resource.data())
            self.editor.load(utc_resource.filepath(), utc_resource.resname(), utc_resource.restype(), utc_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            self.assertTrue(diff, os.linesep.join(self.log_messages))


if __name__ == "__main__":
    unittest.main()
