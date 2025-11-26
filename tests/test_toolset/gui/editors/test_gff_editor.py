from __future__ import annotations

import os
import pathlib
import sys
import unittest
from typing import TYPE_CHECKING, TextIO
from unittest import TestCase

from utility.error_handling import format_exception_with_variables

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication as qapp
except (ImportError, ModuleNotFoundError):
    QTest, qapp = None, None  # type: ignore[misc, assignment]

absolute_file_path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_toolset/test_files"

if (
    __name__ == "__main__"
    and getattr(sys, "frozen", False) is False
):
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


K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    import types

    from qtpy.QtWidgets import QApplication
    from toolset.data.installation import HTInstallation


class CustomTextTestRunner(unittest.TextTestRunner):
    def __init__(
        self,
        stream: TextIO | None = None,
        descriptions: bool = True,
        verbosity: int = 1,
        failfast: bool = False,
        buffer: bool = False,
        resultclass: type[unittest.TestResult] | None = None,
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
        filepath = TESTS_FILES_PATH / "../test_toolset/files/zio001.git"
        editor = self.Editor(None, self.get_installation_k1())

        data = filepath.read_bytes()
        old = read_gff(data)
        editor.load(filepath, "zio001", ResourceType.GFF, data)

        data, _ = editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        assert diff, os.linesep.join(self.log_messages)

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
            assert diff, os.linesep.join(self.log_messages)

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
            assert diff, os.linesep.join(self.log_messages)

    def test_placeholder(self): ...


if __name__ == "__main__":
    unittest.main(testRunner=CustomTextTestRunner)


# ============================================================================
# Pytest-based headless UI tests
# ============================================================================

import pytest
from toolset.gui.editors.gff import GFFEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.type import ResourceType

def test_gff_editor_headless_ui_load_build(qtbot, installation: HTInstallation, test_files_dir: pathlib.Path):
    """Test GFF Editor in headless UI - loads real file and builds data."""
    editor = GFFEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a GFF file
    gff_file = test_files_dir / "zio001.git"  # GIT files are GFF format
    if not gff_file.exists():
        # Try to get one from installation
        gff_resources = [r for r in installation.resources(ResourceType.GIT)][:1]
        if not gff_resources:
            # Try any GFF-based resource
            gff_resources = [r for r in installation.resources(ResourceType.ARE)][:1]
        if not gff_resources:
            pytest.skip("No GFF files available for testing")
        gff_resource = gff_resources[0]
        gff_data = installation.resource(gff_resource.identifier)
        if not gff_data:
            pytest.skip(f"Could not load GFF data for {gff_resource.identifier}")
        editor.load(
            gff_resource.filepath if hasattr(gff_resource, 'filepath') else pathlib.Path("module.gff"),
            gff_resource.resname,
            gff_resource.restype,
            gff_data
        )
    else:
        original_data = gff_file.read_bytes()
        editor.load(gff_file, "zio001", ResourceType.GIT, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    loaded_gff = read_gff(data)
    assert loaded_gff is not None