from __future__ import annotations

import importlib
import os
import pathlib
import sys
from typing import TYPE_CHECKING
import unittest
from unittest import TestCase


absolute_file_path: pathlib.Path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH: pathlib.Path = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_toolset/test_files"

if TYPE_CHECKING:
    from toolset.data.installation import HTInstallation
    from toolset.gui.editors.tlk import TLKEditor
    from pykotor.resource.formats.tlk.tlk_data import TLK

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

from pykotor.resource.formats.tlk.tlk_auto import read_tlk
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class TLKEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        assert K2_PATH is not None, "K2_PATH environment variable is not set."
        from toolset.gui.editors.tlk import TLKEditor

        cls.TLKEditor = TLKEditor
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app = QApplication([])
        self.editor = self.TLKEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath: pathlib.Path = TESTS_FILES_PATH / "dialog.tlk"

        data1: bytes = filepath.read_bytes()
        old: TLK = read_tlk(data1)
        self.editor.load(filepath, "dialog", ResourceType.TLK, data1)

        data2, _ = self.editor.build()
        assert data2 is not None, "Failed to build TLK"
        new: TLK = read_tlk(data2)

        diff: bool = old.compare(new, self.log_func)
        assert diff
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
                new_context: str = f"{context}.{key}" if context else str(key)
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


if __name__ == "__main__":
    unittest.main()
