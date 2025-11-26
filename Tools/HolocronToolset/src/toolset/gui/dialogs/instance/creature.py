from __future__ import annotations

import math

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QDialog

from pykotor.common.misc import ResRef

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.generics.git import GITCreature


class CreatureDialog(QDialog):
    def __init__(self, parent: QWidget, creature: GITCreature):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint
            & ~QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )

        from toolset.uic.qtpy.dialogs.instance.creature import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.setWindowTitle("Edit Creature")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/creature.png")))

        self.ui.resrefEdit.setText(str(creature.resref))
        self.ui.xPosSpin.setValue(creature.position.x)
        self.ui.yPosSpin.setValue(creature.position.y)
        self.ui.zPosSpin.setValue(creature.position.z)
        self.ui.bearingSpin.setValue(math.degrees(creature.bearing))

        self.creature: GITCreature = creature

    def accept(self):
        super().accept()
        self.creature.resref = ResRef(self.ui.resrefEdit.text())
        self.creature.position.x = self.ui.xPosSpin.value()
        self.creature.position.y = self.ui.yPosSpin.value()
        self.creature.position.z = self.ui.zPosSpin.value()
        self.creature.bearing = math.radians(self.ui.bearingSpin.value())
