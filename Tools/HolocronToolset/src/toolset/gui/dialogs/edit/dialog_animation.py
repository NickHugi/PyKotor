from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtWidgets import QDialog

from pykotor.resource.generics.dlg import DLGAnimation
from toolset.data.installation import HTInstallation

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class EditAnimationDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, animation: DLGAnimation = DLGAnimation()):
        super().__init__(parent)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.edit_animation import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.edit_animation import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.edit_animation import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.edit_animation import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        animations_list = installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
        self.ui.animationSelect.setItems(animations_list.get_column("name"), sortAlphabetically=True, cleanupStrings=True, ignoreBlanks=True)

        self.ui.animationSelect.setCurrentIndex(animation.animation_id)
        self.ui.participantEdit.setText(animation.participant)

    def animation(self) -> DLGAnimation:
        animation = DLGAnimation()
        animation.animation_id = self.ui.animationSelect.currentIndex()
        animation.participant = self.ui.participantEdit.text()
        return animation
