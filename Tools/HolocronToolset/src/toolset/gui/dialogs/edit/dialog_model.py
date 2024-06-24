from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
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
        if stunt is None:
            stunt = DLGStunt()
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.edit_model import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.edit_model import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.edit_model import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.edit_model import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.participantEdit.setText(stunt.participant)
        self.ui.stuntEdit.setText(str(stunt.stunt_model))

    def stunt(self) -> DLGStunt:
        stunt = DLGStunt()
        stunt.participant = self.ui.participantEdit.text()
        stunt.stunt_model = ResRef(self.ui.stuntEdit.text())
        return stunt
