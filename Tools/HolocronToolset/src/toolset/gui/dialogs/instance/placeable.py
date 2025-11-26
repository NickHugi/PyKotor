from __future__ import annotations

import math

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtGui import QColor, QIcon, QImage, QPixmap
from qtpy.QtWidgets import QColorDialog, QDialog, QDoubleSpinBox

from pykotor.common.misc import Color, ResRef

if TYPE_CHECKING:
    from qtpy.QtWidgets import QLabel, QWidget

    from pykotor.resource.generics.git import GITPlaceable
    from toolset.gui.widgets.long_spinbox import LongSpinBox


class PlaceableDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        placeable: GITPlaceable,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint & ~QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )

        from toolset.uic.qtpy.dialogs.instance.placeable import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.setWindowTitle("Edit Placeable")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/placeable.png")))

        self.ui.colorButton.clicked.connect(lambda: self.changeColor(self.ui.colorSpin))
        self.ui.colorSpin.valueChanged.connect(lambda value: self.redoColorImage(value, self.ui.color))

        self.ui.resrefEdit.setText(str(placeable.resref))
        self.ui.xPosSpin.setValue(placeable.position.x)
        self.ui.yPosSpin.setValue(placeable.position.y)
        self.ui.zPosSpin.setValue(placeable.position.z)
        self.ui.bearingSpin.setValue(math.degrees(placeable.bearing))
        self.ui.colorSpin.setValue(0 if placeable.tweak_color is None else placeable.tweak_color.rgb_integer())

        self.placeable: GITPlaceable = placeable

        for widget in (getattr(self.ui, attr) for attr in dir(self.ui)):
            if isinstance(widget, QDoubleSpinBox):
                widget.setDecimals(8)

    def accept(self):
        super().accept()
        self.placeable.resref = ResRef(self.ui.resrefEdit.text())
        self.placeable.position.x = self.ui.xPosSpin.value()
        self.placeable.position.y = self.ui.yPosSpin.value()
        self.placeable.position.z = self.ui.zPosSpin.value()
        self.placeable.bearing = math.radians(self.ui.bearingSpin.value())
        self.placeable.tweak_color = Color.from_rgb_integer(self.ui.colorSpin.value()) if self.ui.colorSpin.value() != 0 else None

    def changeColor(
        self,
        colorSpin: LongSpinBox,
    ):
        qcolor: QColor = QColorDialog.getColor(QColor(colorSpin.value()))
        color: Color = Color.from_rgb_integer(qcolor.rgb())
        colorSpin.setValue(color.rgb_integer())

    def redoColorImage(
        self,
        value: int,
        colorLabel: QLabel,
    ):
        color: Color = Color.from_bgr_integer(value)
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([r, g, b] * 16 * 16)
        pixmap: QPixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_RGB888))
        colorLabel.setPixmap(pixmap)
