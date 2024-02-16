from __future__ import annotations

from PyQt5.QtWidgets import QDialog

from pykotor.common.misc import ResRef
from pykotor.resource.generics.dlg import DLGStunt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class CutsceneModelDialog(QDialog):
    def __init__(self, parent: QWidget, stunt: DLGStunt = DLGStunt()):
        super().__init__(parent)

        from toolset.uic.dialogs.edit_model import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.participantEdit.setText(stunt.participant)
        self.ui.stuntEdit.setText(str(stunt.stunt_model))

    def stunt(self) -> DLGStunt:
        stunt = DLGStunt()
        stunt.participant = self.ui.participantEdit.text()
        stunt.stunt_model = ResRef(self.ui.stuntEdit.text())
        return stunt
