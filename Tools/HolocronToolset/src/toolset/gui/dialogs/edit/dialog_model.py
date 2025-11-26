from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

from pykotor.common.misc import ResRef
from pykotor.resource.generics.dlg import DLGStunt

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class CutsceneModelDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        stunt: DLGStunt | None = None,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinimizeButtonHint
        )

        from toolset.uic.qtpy.dialogs.edit_model import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        stunt = DLGStunt() if stunt is None else stunt
        self.ui.participantEdit.setText(stunt.participant)
        self.ui.stuntEdit.setText(str(stunt.stunt_model))

    def stunt(self) -> DLGStunt:
        stunt = DLGStunt()
        stunt.participant = self.ui.participantEdit.text()
        stunt.stunt_model = ResRef(self.ui.stuntEdit.text())
        return stunt
