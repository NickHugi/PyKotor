from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QDialog

from pykotor.common.misc import ResRef
from pykotor.resource.generics.dlg import DLGStunt

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class CutsceneModelDialog(QDialog):
    def __init__(self, parent: QWidget, stunt: DLGStunt = DLGStunt()):
        super().__init__(parent)

        from toolset.uic.pyqt5.dialogs.edit_model import Ui_Dialog  # pylint: disable=C0415  # noqa: PLC0415

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.participantEdit.setText(stunt.participant)
        self.ui.stuntEdit.setText(str(stunt.stunt_model))

    def stunt(self) -> DLGStunt:
        stunt = DLGStunt()
        stunt.participant = self.ui.participantEdit.text()
        stunt.stunt_model = ResRef(self.ui.stuntEdit.text())
        return stunt
