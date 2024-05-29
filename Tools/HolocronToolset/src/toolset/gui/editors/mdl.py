from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtWidgets import QMessageBox

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.mdl import MDL, read_mdl, write_mdl
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class MDLEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initialize the Model Viewer window.

        Args:
        ----
            parent: {QWidget}: The parent widget of this window
            installation: {HTInstallation}: The installation context

        Processing Logic:
        ----------------
            - Initialize the base class with the given parameters
            - Create an MDL model object
            - Load the UI from the designer file
            - Set up menus and connect signals
            - Set the installation on the model renderer
            - Call new() to start with a blank state.
        """
        supported: list[ResourceType] = [ResourceType.MDL]
        super().__init__(parent, "Model Viewer", "none", supported, supported, installation)

        self._mdl: MDL = MDL()
        self._installation = installation

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.mdl import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.mdl import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.mdl import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.mdl import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ui.modelRenderer.installation = installation

        self.new()

    def _setupSignals(self): ...

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Loads a model resource and its associated data.

        Args:
        ----
            filepath: {Path to the resource file}
            resref: {Resource reference string}
            restype: {Resource type (MDL or MDX)}
            data: {Binary data of the resource}

        Loads associated MDL/MDX data:
            - Checks file extension and loads associated data from file
            - Loads associated data from Erf, Rim or Bif files if present
            - Sets model data on renderer if both MDL and MDX found
            - Displays error if unable to find associated data.
        """
        c_filepath: CaseAwarePath = CaseAwarePath.pathify(filepath)
        super().load(c_filepath, resref, restype, data)

        mdl_data: bytes | None = None
        mdx_data: bytes | None = None

        if restype is ResourceType.MDL:
            mdl_data = data
            if c_filepath.suffix.lower() == ".mdl":
                mdx_data = BinaryReader.load_file(c_filepath.with_suffix(".mdx"))
            elif is_any_erf_type_file(c_filepath.name):
                erf = read_erf(filepath)
                mdx_data = erf.get(resref, ResourceType.MDX)
            elif is_rim_file(c_filepath.name):
                rim = read_rim(filepath)
                mdx_data = rim.get(resref, ResourceType.MDX)
            elif is_bif_file(c_filepath.name):
                mdx_data = self._installation.resource(resref, ResourceType.MDX, [SearchLocation.CHITIN]).data
        elif restype is ResourceType.MDX:
            mdx_data = data
            if c_filepath.suffix.lower() == ".mdx":
                mdl_data = BinaryReader.load_file(c_filepath.with_suffix(".mdl"))
            elif is_any_erf_type_file(c_filepath.name):
                erf = read_erf(filepath)
                mdl_data = erf.get(resref, ResourceType.MDL)
            elif is_rim_file(c_filepath.name):
                rim = read_rim(filepath)
                mdl_data = rim.get(resref, ResourceType.MDL)
            elif is_bif_file(c_filepath.name):
                mdl_data = self._installation.resource(resref, ResourceType.MDL, [SearchLocation.CHITIN]).data

        if mdl_data is None or mdx_data is None:
            QMessageBox(QMessageBox.Icon.Critical, f"Could not find the '{c_filepath.stem}' MDL/MDX", "").exec_()
            return

        self.ui.modelRenderer.setModel(mdl_data, mdx_data)
        self._mdl = read_mdl(mdl_data, 0, 0, mdx_data, 0, 0)

    def _loadMDL(self, mdl: MDL):
        self._mdl = mdl

    def build(self) -> tuple[bytes, bytes]:
        data = bytearray()
        data_ext = bytearray()
        write_mdl(self._mdl, data, ResourceType.MDL, data_ext)
        return data, data_ext

    def new(self):
        super().new()
        self._mdl = MDL()
        self.ui.modelRenderer.clearModel()
