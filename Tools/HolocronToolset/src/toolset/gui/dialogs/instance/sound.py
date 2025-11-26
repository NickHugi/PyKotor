from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QDialog

from pykotor.common.misc import ResRef

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.generics.git import GITSound


class SoundDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        sound: GITSound,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint
            & ~QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )

        from toolset.uic.qtpy.dialogs.instance.sound import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.setWindowTitle("Edit Sound")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/sound.png")))

        self.ui.resrefEdit.setText(str(sound.resref))
        self.ui.xPosSpin.setValue(sound.position.x)
        self.ui.yPosSpin.setValue(sound.position.y)
        self.ui.zPosSpin.setValue(sound.position.z)

        self.sound: GITSound = sound

    def accept(self):
        super().accept()
        self.sound.resref = ResRef(self.ui.resrefEdit.text())
        self.sound.position.x = self.ui.xPosSpin.value()
        self.sound.position.y = self.ui.yPosSpin.value()
        self.sound.position.z = self.ui.zPosSpin.value()
