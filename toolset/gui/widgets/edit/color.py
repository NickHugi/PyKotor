from PyQt5.QtGui import QColor, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QColorDialog
from pykotor.common.misc import Color


class ColorEdit(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._color: Color = Color(255, 255, 255)
        self.allowAlpha: bool = False

        from toolset.uic.widgets.color_edit import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.editButton.clicked.connect(self.openColorDialog)
        self.ui.colorSpin.valueChanged.connect(self._onColorChange)

    def openColorDialog(self) -> None:
        initColor = Color.from_rgba_integer(self.ui.colorSpin.value())
        initQColor = QColor(int(initColor.r*255), int(initColor.g*255), int(initColor.b*255), int(initColor.a*255))

        dialog = QColorDialog(QColor(initQColor.red(), initQColor.green(), initQColor.blue(), initQColor.alpha()))
        dialog.setOption(QColorDialog.ShowAlphaChannel, on=self.allowAlpha)

        if dialog.exec_():
            qcolor = dialog.selectedColor()
            if self.allowAlpha:
                color = Color(qcolor.redF(), qcolor.greenF(), qcolor.blueF())
                self.ui.colorSpin.setValue(color.rgb_integer() + (qcolor.alpha() << 24))
            else:
                color = Color(qcolor.redF(), qcolor.greenF(), qcolor.blueF())
                self.ui.colorSpin.setValue(color.rgb_integer())

    def _onColorChange(self, value: int) -> None:
        color = Color.from_rgba_integer(value)
        self._color.r, self._color.g, self._color.b, self._color.a = color.r, color.g, color.b, color.a
        if not self.allowAlpha:
            self._color.a = 0.0
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([b, g, r] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_BGR888))
        self.ui.colorLabel.setPixmap(pixmap)

    def setColor(self, color: Color) -> None:
        self._color: Color = color
        self.ui.colorSpin.setValue(color.rgba_integer() if self.allowAlpha else color.rgb_integer())

    def color(self) -> Color:
        return self._color