from PyQt5.QtWidgets import QAbstractSpinBox


class LongSpinBox(QAbstractSpinBox):
    """
    Abstract spin box that can handle integers larger than 32 bits which Qt's inbuilt QSpinBox does not support.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._min = 0
        self._max = 0

        self.lineEdit().editingFinished.connect(self.clampLineEdit)

    def stepUp(self) -> None:
        self.setValue(self.value() + 1)

    def stepDown(self) -> None:
        self.setValue(self.value() - 1)

    def stepBy(self, steps: int) -> None:
        self.setValue(self.value() + steps * 1)

    def text(self) -> str:
        return str(self._value)

    def setRange(self, min: int, max: int) -> None:
        self._min = min
        self._max = max

    def _withinRange(self, value: int):
        return self._min <= value <= self._max

    def clampLineEdit(self):
        try:
            value = int(self.lineEdit().text())
            value = max(self._min, min(self._max, value))
            self.lineEdit().setText(str(value))
        except ValueError:
            self.lineEdit().setText("0")

    def setValue(self, value: int) -> None:
        if not isinstance(value, int):
            self.lineEdit().setText("0")
        else:
            value = max(self._min, min(self._max, value))
            self.lineEdit().setText(str(value))

    def value(self) -> int:
        try:
            return int(self.lineEdit().text())
        except ValueError:
            return 0

    def stepEnabled(self):
        return self.StepUpEnabled | self.StepDownEnabled
