from __future__ import annotations

import importlib
import os
import pathlib
import sys
from typing import TYPE_CHECKING
import unittest
from unittest import TestCase


if TYPE_CHECKING:
    from pykotor.resource.formats.ssf import SSF
    from toolset.data.installation import HTInstallation
    from toolset.gui.editors.ssf import SSFEditor

absolute_file_path: pathlib.Path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH: pathlib.Path = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_toolset/test_files"

if __name__ == "__main__" and getattr(sys, "frozen", False) is False:

    def add_sys_path(p):
        working_dir = str(p)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = absolute_file_path.parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        add_sys_path(pykotor_path.parent)
    gl_path = absolute_file_path.parents[4] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        add_sys_path(gl_path.parent)
    utility_path = absolute_file_path.parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        add_sys_path(utility_path.parent)
    toolset_path = absolute_file_path.parents[4] / "Tools" / "HolocronToolset" / "src" / "toolset"
    if toolset_path.exists():
        add_sys_path(toolset_path.parent)

if importlib.util.find_spec("qtpy.QtWidgets") is None:  # pyright: ignore[reportAttributeAccessIssue]
    raise ImportError("qtpy.QtWidgets is required for this test. Install PyQt/PySide with qtpy before running this test.")

from loggerplus import Any
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QApplication


K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.ssf.ssf_auto import read_ssf
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K1_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class SSFEditorTest(TestCase):
    INSTALLATION: HTInstallation
    SSFEditor: type[SSFEditor]

    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        assert K2_PATH is not None, "K2_PATH environment variable is not set."
        from toolset.gui.editors.ssf import SSFEditor
        from toolset.data.installation import HTInstallation

        cls.SSFEditor = SSFEditor
        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=False)

    def setUp(self):
        self.app: QApplication = QApplication(sys.argv)
        self.editor: SSFEditor = self.SSFEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath: pathlib.Path = TESTS_FILES_PATH / "../test_toolset/files/n_ithorian.ssf"

        data: bytes = filepath.read_bytes()
        old: SSF = read_ssf(data)
        self.editor.load(filepath, "n_ithorian", ResourceType.SSF, data)

        data, _ = self.editor.build()
        new: SSF = read_ssf(data)

        self.assertDeepEqual(old, new)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_ssf_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for ssf_resource in (resource for resource in self.installation if resource.restype() is ResourceType.SSF):
            old: SSF = read_ssf(ssf_resource.data())
            self.editor.load(ssf_resource.filepath(), ssf_resource.resname(), ssf_resource.restype(), ssf_resource.data())

            data, _ = self.editor.build()
            new: SSF = read_ssf(data)

            self.assertDeepEqual(old, new)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_ssf_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for bwm_resource in (resource for resource in self.installation if resource.restype() is ResourceType.SSF):
            old: SSF = read_ssf(bwm_resource.data())
            self.editor.load(bwm_resource.filepath(), bwm_resource.resname(), bwm_resource.restype(), bwm_resource.data())

            data, _ = self.editor.build()
            new: SSF = read_ssf(data)

            self.assertDeepEqual(old, new)

    def assertDeepEqual(
        self,
        obj1: Any,
        obj2: Any,
        context: str = "",
    ) -> None:
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            assert set(obj1.keys()) == set(obj2.keys()), context
            for key in obj1:
                new_context = f"{context}.{key}" if context else str(key)
                self.assertDeepEqual(obj1[key], obj2[key], new_context)

        elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
            assert len(obj1) == len(obj2), context
            for index, (item1, item2) in enumerate(zip(obj1, obj2)):
                new_context = f"{context}[{index}]" if context else f"[{index}]"
                self.assertDeepEqual(item1, item2, new_context)

        elif hasattr(obj1, "__dict__") and hasattr(obj2, "__dict__"):
            self.assertDeepEqual(obj1.__dict__, obj2.__dict__, context)

        else:
            assert obj1 == obj2, context

    def test_placeholder(self): ...


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Additional UI tests (merged from test_ui_other_editors.py)
# ============================================================================

import pytest
from toolset.gui.editors.ssf import SSFEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.type import ResourceType

def test_ssf_editor(qtbot, installation: HTInstallation, test_files_dir):
    """Test SSF Editor."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert editor.isVisible()
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if ssf_file.exists():
        editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
        # Check widgets
        # Likely combo boxes for sound refs