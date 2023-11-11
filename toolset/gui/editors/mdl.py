from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt5.QtWidgets import QMessageBox, QWidget

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import SearchLocation
from pykotor.helpers.path import Path
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.mdl import MDL, read_mdl, write_mdl
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_erf_or_mod_file, is_rim_file
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from toolset.data.installation import HTInstallation


class MDLEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.MDL]
        super().__init__(parent, "Model Viewer", "none", supported, supported, installation)

        self._mdl: MDL = MDL()
        self._installation = installation

        from toolset.uic.editors.mdl import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ui.modelRenderer.installation = installation

        self.new()

    def _setupSignals(self) -> None:
        ...

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        c_filepath = Path(filepath)

        mdl_data = None
        mdx_data = None

        if restype == ResourceType.MDL:
            mdl_data = data
            if c_filepath.endswith(".mdl"):
                mdx_data = BinaryReader.load_file(str(c_filepath.with_suffix(".mdx")))
            elif is_erf_or_mod_file(c_filepath.name):
                erf = read_erf(filepath)
                mdx_data = erf.get(resref, ResourceType.MDX)
            elif is_rim_file(c_filepath.name):
                rim = read_rim(filepath)
                mdx_data = rim.get(resref, ResourceType.MDX)
            elif is_bif_file(c_filepath.name):
                mdx_data = self._installation.resource(resref, ResourceType.MDX, [SearchLocation.CHITIN]).data
        elif restype == ResourceType.MDX:
            mdx_data = data
            if c_filepath.endswith(".mdx"):
                mdl_data = BinaryReader.load_file(
                    str(c_filepath.with_suffix(c_filepath.suffix.lower().replace(".mdl", ".mdx"))),
                )
            elif is_erf_or_mod_file(c_filepath.name):
                erf = read_erf(filepath)
                mdl_data = erf.get(resref, ResourceType.MDX)
            elif is_rim_file(c_filepath.name):
                rim = read_rim(filepath)
                mdl_data = rim.get(resref, ResourceType.MDX)
            elif is_bif_file(c_filepath.name):
                mdl_data = self._installation.resource(resref, ResourceType.MDL, [SearchLocation.CHITIN]).data

        if mdl_data and mdx_data:
            self.ui.modelRenderer.setModel(mdl_data, mdx_data)
        else:
            QMessageBox(QMessageBox.Critical, "Could not find MDL/MDX", "").exec_()

        self._mdl = read_mdl(mdl_data, 0, 0, mdx_data, 0, 0)

    def _loadMDL(self, mdl: MDL) -> None:
        self._mdl = mdl

    def build(self) -> tuple[bytes, bytes]:
        data = bytearray()
        data_ext = bytearray()
        write_mdl(self._mdl, data, ResourceType.MDL, data_ext)
        return data, data_ext

    def new(self) -> None:
        super().new()
        self._mdl = MDL()
        self.ui.modelRenderer.clearModel()
