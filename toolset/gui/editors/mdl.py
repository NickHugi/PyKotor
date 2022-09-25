from typing import Optional, Tuple

from PyQt5.QtGui import QPixmap, QColor, QImage
from PyQt5.QtWidgets import QWidget, QColorDialog, QLabel, QMessageBox

from gui.dialogs.locstring import LocalizedStringDialog
from pykotor.common.geometry import Vector2
from pykotor.common.misc import Color, ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.formats.mdl import MDL, read_mdl, write_mdl
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.generics.are import ARE, dismantle_are, ARENorthAxis, AREWindPower, read_are
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.editor import Editor
from gui.widgets.long_spinbox import LongSpinBox


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

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        mdl_data = None
        mdx_data = None

        if restype == ResourceType.MDL:
            mdl_data = data
            if filepath.endswith(".mdl"):
                mdx_data = BinaryReader.load_file(filepath.replace(".mdl", ".mdx"))
            elif filepath.endswith(".erf") or filepath.endswith(".mod"):
                erf = read_erf(filepath)
                mdx_data = erf.get(resref, ResourceType.MDX)
            elif filepath.endswith(".rim"):
                rim = read_rim(filepath)
                mdx_data = rim.get(resref, ResourceType.MDX)
            elif filepath.endswith(".bif"):
                mdx_data = self._installation.resource(resref, ResourceType.MDX, [SearchLocation.CHITIN]).data
        elif restype == ResourceType.MDX:
            mdx_data = data
            if filepath.endswith(".mdx"):
                mdl_data = BinaryReader.load_file(filepath.replace(".mdl", ".mdx"))
            elif filepath.endswith(".erf") or filepath.endswith(".mod"):
                erf = read_erf(filepath)
                mdl_data = erf.get(resref, ResourceType.MDX)
            elif filepath.endswith(".rim"):
                rim = read_rim(filepath)
                mdl_data = rim.get(resref, ResourceType.MDX)
            elif filepath.endswith(".bif"):
                mdl_data = self._installation.resource(resref, ResourceType.MDL, [SearchLocation.CHITIN]).data

        if mdl_data and mdx_data:
            self.ui.modelRenderer.setModel(mdl_data, mdx_data)
        else:
            QMessageBox(QMessageBox.Critical, "Could not find MDL/MDX").exec_()

        self._mdl = read_mdl(mdl_data, 0, 0, mdx_data, 0, 0)

    def _loadMDL(self, mdl: MDL) -> None:
        self._mdl = mdl

    def build(self) -> Tuple[bytes, bytes]:
        data = bytearray()
        data_ext = bytearray()
        write_mdl(self._mdl, data, ResourceType.MDL, data_ext)
        return data, data_ext

    def new(self) -> None:
        super().new()
        self._mdl = MDL()
        self.ui.modelRenderer.clearModel()
