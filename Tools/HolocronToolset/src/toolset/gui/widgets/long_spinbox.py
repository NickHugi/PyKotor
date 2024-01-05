from PyQt5 import QtCore
from PyQt5.QtWidgets import QAbstractSpinBox


class LongSpinBox(QAbstractSpinBox):
    """Implementation of QAbstractSpinBox that allows for values that exceed a signed 32-bit integer."""

    valueChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self._min = 0
        self._max = 4294967295

        self.lineEdit().editingFinished.connect(self.clampLineEdit)
        self.lineEdit().textEdited.connect(lambda: self.valueChanged.emit(self.value()))

    def stepUp(self):
        self.setValue(self.value() + 1)

    def stepDown(self):
        self.setValue(self.value() - 1)

    def stepBy(self, steps: int):
        self.setValue(self.value() + steps * 1)

    def text(self) -> str:
        return str(self._value)

    def setRange(self, min_value: int, max_value: int):
        self._min = min_value
        self._max = max_value

    def _withinRange(self, value: int):
        return self._min <= value <= self._max

    def clampLineEdit(self):
        try:
            value = int(self.lineEdit().text())
            value = max(self._min, min(self._max, value))
            self.lineEdit().setText(str(value))
        except ValueError:
            self.lineEdit().setText("0")

    def setValue(self, value: int):
        if not isinstance(value, int):
            self.lineEdit().setText("0")
        else:
            value = max(self._min, min(self._max, value))
            self.lineEdit().setText(str(value))
        self.valueChanged.emit(self.value())

    def value(self) -> int:
        try:
            return int(self.lineEdit().text())
        except ValueError:
            return 0

    def stepEnabled(self):
        return self.StepUpEnabled | self.StepDownEnabled
