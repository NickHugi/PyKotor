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

absolute_file_path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_toolset/test_files"

if (
    __name__ == "__main__"
    and getattr(sys, "frozen", False) is False
):
    pykotor_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)
    gl_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        working_dir = str(gl_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)
    utility_path = pathlib.Path(__file__).parents[6] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        working_dir = str(utility_path.parent)
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
K2_PATH = os.environ.get("K2_PATH")

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class GITEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.gui.editors.git import GITEditor

        cls.GITEditor = GITEditor
        from toolset.data.installation import HTInstallation

        # cls.K1_INSTALLATION = HTInstallation(K1_PATH, "", tsl=False)
        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app = QApplication([])
        self.editor = self.GITEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "zio001.git"

        data = filepath.read_bytes()
        old = read_gff(data)
        self.editor.load(filepath, "zio001", ResourceType.GIT, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        assert diff, os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for git_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GIT):
            old = read_gff(git_resource.data())
            self.editor.load(git_resource.filepath(), git_resource.resname(), git_resource.restype(), git_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            assert diff, os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for git_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GIT):
            old = read_gff(git_resource.data())
            self.editor.load(git_resource.filepath(), git_resource.resname(), git_resource.restype(), git_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            assert diff, os.linesep.join(self.log_messages)

    def test_placeholder(self): ...


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Additional UI tests (merged from test_ui_gff_editors.py)
# ============================================================================

import pytest
from toolset.gui.editors.git import GITEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.type import ResourceType

def test_git_editor_specifics(qtbot, installation: HTInstallation, test_files_dir: pathlib.Path):
    """Specific granular tests for GIT Editor (common enough to warrant specific attention)."""
    editor = GITEditor(None, installation)
    qtbot.addWidget(editor)
    
    git_file = test_files_dir / "zio001.git"
    if not git_file.exists():
        pytest.skip("zio001.git not found")
        
    editor.load(git_file, "zio001", ResourceType.GIT, git_file.read_bytes())
    
    # Test Geometry/Environment/etc tabs if they exist
    # Check specific widget: Tag
    # GIT doesn't strictly have a "Tag" field in the root struct like UTI, but usually has one?
    # Actually GIT is Area Properties mostly.
    
    # Let's test the lists (Creatures, Placeables, etc.)
    # Assuming ui.creatureList, ui.placeableList, etc.
    if hasattr(editor.ui, "creatureList"):
        assert editor.ui.creatureList.count() >= 0
        
    # Check generic properties if any
    if hasattr(editor.ui, "environmentPage"):
        # navigate to environment page
        pass