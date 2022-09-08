from PyQt5.QtGui import QColor, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QColorDialog
from pykotor.common.misc import Color


class ColorEdit(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.widgets.color_edit import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self._color: Color = Color(255, 255, 255)

        self.ui.editButton.clicked.connect(self.openColorDialog)
        self.ui.colorSpin.valueChanged.connect(self._onColorChange)

    def openColorDialog(self) -> None:
        qcolor = QColorDialog.getColor(QColor(self.ui.colorSpin.value()))
        color = Color(qcolor.red()/255, qcolor.green()/255, qcolor.blue()/255)
        self.ui.colorSpin.setValue(color.rgb_integer())

    def _onColorChange(self, value: int) -> None:
        color = Color.from_bgr_integer(value)
        self._color.r, self._color.g, self._color.b = color.r, color.g, color.b
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([b, g, r] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_RGB888))
        self.ui.colorLabel.setPixmap(pixmap)

    def setColor(self, color: Color) -> None:
        self._color: Color = color
        self.ui.colorSpin.setValue(color.rgb_integer())

    def color(self) -> Color:
        return self._color