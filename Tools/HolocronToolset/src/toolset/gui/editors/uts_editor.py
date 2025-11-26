from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QBuffer
from qtpy.QtMultimedia import QMediaPlayer

from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.uts import UTS, read_uts
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.editors.uts_data import UTSData
from toolset.gui.editors.uts_ui import UTSEditorUI

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.common.module import GFF
    from toolset.data.installation import HTInstallation


class UTSEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation = None,
    ):
        """Initialize the Sound Editor window."""
        supported: list[ResourceType] = [ResourceType.UTS]
        super().__init__(parent, "Sound Editor", "sound", supported, supported, installation)

        self._uts: UTS = UTS()
        self.player = QMediaPlayer(self)
        self.buffer = QBuffer(self)

        from toolset.uic.qtpy.editors.uts import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui_handler = UTSEditorUI(self)
        self.data_handler = UTSData(self)

        if installation is not None:
            self._setup_installation(installation)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.new()

    def _setup_installation(
        self,
        installation: HTInstallation,
    ):
        self._installation = installation
        self.ui.nameEdit.set_installation(installation)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)
        uts: UTS = read_uts(data)
        self.data_handler.load_uts(uts)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTS from UI fields."""
        uts: UTS = self.data_handler.build_uts()
        data = bytearray()
        gff: GFF = self.data_handler.dismantle_uts(uts)
        write_gff(gff, data)
        return data, b""

    def new(self):
        super().new()
        self.data_handler.load_uts(UTS())

    def closeEvent(
        self,
        e: QCloseEvent,
    ):
        self.player.stop()
