from __future__ import annotations

import os
import pathlib
import sys
from typing import TextIO, Type, TYPE_CHECKING
import unittest

from unittest import TestCase

from utility.error_handling import format_exception_with_variables

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication as qapp
except (ImportError, ModuleNotFoundError):
    QTest, qapp = None, None  # type: ignore[misc, assignment]


absolute_file_path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "files"

if getattr(sys, "frozen", False) is False:

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


K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    import types
    from toolset.data.installation import HTInstallation
    from PySide2.QtWidgets import QApplication


class CustomTextTestRunner(unittest.TextTestRunner):
    def __init__(
        self,
        stream: TextIO | None = None,
        descriptions: bool = True,
        verbosity: int = 1,
        failfast: bool = False,
        buffer: bool = False,
        resultclass: Type[unittest.TestResult] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(stream, descriptions, verbosity, failfast, buffer, resultclass, **kwargs)

    def run(self, test):
        # Create an instance of CustomTestResult
        result = CustomTestResult(self.stream, self.descriptions, self.verbosity)
        # Run the test case (or test suite) and return the result
        test(result)
        return result


class CustomTestResult(unittest.TextTestResult):
    def addError(
        self,
        test: unittest.TestCase,
        exc_tuple: tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None],
    ):
        exc_type, exc_value, tb = exc_tuple
        if exc_value is not None:
            print(format_exception_with_variables(exc_value, exc_type, tb), file=sys.stderr)
        super().addError(test, exc_tuple)

    def _exc_info_to_string(
        self,
        exc_tuple: tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None],
        test: unittest.TestCase,
    ):
        # err is a tuple of (exc_type, exc_value, tb)
        exctype, value, tb = exc_tuple
        if value is None:
            raise ValueError(f"exception object was unexpectedly None, got exc_tuple: {exc_tuple} and test: {test}")
        return format_exception_with_variables(value, exctype, tb)


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not qapp,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class GFFEditorTest(TestCase):
    K1_INSTALLATION = None
    TSL_INSTALLATION: HTInstallation | None = None
    app: QApplication

    @classmethod
    def setUpClass(cls):
        from toolset.gui.editors.gff import GFFEditor

        cls.Editor = GFFEditor
        cls.K1_INSTALLATION = None
        cls.TSL_INSTALLATION = None
        if qapp is None:
            raise RuntimeError("QApplication not defined.")
        cls.app = qapp([])

    @classmethod
    def tearDownClass(cls):
        cls.app.deleteLater()

    @classmethod
    def get_installation_k1(cls):
        if cls.K1_INSTALLATION is None:
            from toolset.data.installation import HTInstallation

            cls.K1_INSTALLATION = HTInstallation(K1_PATH, "", tsl=False)
        return cls.K1_INSTALLATION

    @classmethod
    def get_installation_tsl(cls):
        if cls.TSL_INSTALLATION is None:
            from toolset.data.installation import HTInstallation

            cls.TSL_INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)
        return cls.TSL_INSTALLATION

    def setUp(self):
        self.log_messages: list[str] = [os.linesep]
        self.app: QApplication

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "../toolset_tests/files/zio001.git"
        editor = self.Editor(None, self.get_installation_k1())

        data = BinaryReader.load_file(filepath)
        old = read_gff(data)
        editor.load(filepath, "zio001", ResourceType.GFF, data)

        data, _ = editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        self.assertTrue(diff, os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        editor = self.Editor(None, self.get_installation_k1())
        for gff_resource in (resource for resource in editor._installation if resource.restype().contents == "gff"):
            print("Load ", gff_resource.identifier())
            old = read_gff(gff_resource.data())
            editor.load(gff_resource.filepath(), gff_resource.resname(), gff_resource.restype(), gff_resource.data())

            data, _ = editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            self.assertTrue(diff, os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        editor = self.Editor(None, self.get_installation_tsl())
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for gff_resource in (resource for resource in editor._installation if resource.restype().contents == "gff"):
            old = read_gff(gff_resource.data())
            editor.load(gff_resource.filepath(), gff_resource.resname(), gff_resource.restype(), gff_resource.data())

            data, _ = editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            self.assertTrue(diff, os.linesep.join(self.log_messages))

    def test_placeholder(self): ...


if __name__ == "__main__":
    unittest.main(testRunner=CustomTextTestRunner)
