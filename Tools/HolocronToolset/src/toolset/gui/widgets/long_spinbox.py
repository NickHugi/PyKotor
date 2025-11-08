from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtCore import Signal  # type: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import QAbstractSpinBox

if TYPE_CHECKING:
    from qtpy.QtWidgets import QLineEdit, QWidget


class LongSpinBox(QAbstractSpinBox):  # pyright: ignore[reportGeneralTypeIssues]
    """Implementation of QAbstractSpinBox that allows for values that exceed a signed 32-bit integer."""

    sig_value_changed = Signal(object)  # type: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._min: int = 0
        self._max: int = 0xFFFFFFFF

        line_edit: QLineEdit | None = self.lineEdit()
        if line_edit is None:
            raise RuntimeError("Line edit is None somehow? This should be impossible.")
        line_edit.editingFinished.connect(self.clamp_line_edit)
        line_edit.textEdited.connect(lambda: self.sig_value_changed.emit(self.value()))

    def stepUp(self):
        self.setValue(self.value() + 1)

    def stepDown(self):
        self.setValue(self.value() - 1)

    def stepBy(self, steps: int):
        self.setValue(self.value() + steps * 1)

    def text(self) -> str:
        line_edit: QLineEdit | None = self.lineEdit()
        if line_edit is None:
            raise RuntimeError("Line edit is None somehow? This should be impossible.")
        return str(line_edit.text())

    def setRange(self, min_value: int, max_value: int):
        self._min = min_value
        self._max = max_value

    def _within_range(self, value: int) -> bool:
        return self._min <= value <= self._max

    def clamp_line_edit(self):
        line_edit: QLineEdit | None = self.lineEdit()
        if line_edit is None:
            raise RuntimeError("Line edit is None somehow? This should be impossible.")
        try:
            value = int(line_edit.text())
            value = max(self._min, min(self._max, value))
            line_edit.setText(str(value))
        except ValueError:
            line_edit.setText("0")

    def setValue(self, value: int):
        line_edit: QLineEdit | None = self.lineEdit()
        if line_edit is None:
            raise RuntimeError("Line edit is None somehow? This should be impossible.")
        if not isinstance(value, int):
            line_edit.setText("0")
        else:
            value = max(self._min, min(self._max, value))
            line_edit.setText(str(value))
        self.sig_value_changed.emit(self.value())

    def value(self) -> int:
        line_edit: QLineEdit | None = self.lineEdit()
        if line_edit is None:
            raise RuntimeError("Line edit is None somehow? This should be impossible.")
        try:
            return int(line_edit.text())
        except ValueError:
            return 0

    def stepEnabled(self):
        if hasattr(QAbstractSpinBox, "StepEnabledFlag"):
            return (
                QAbstractSpinBox.StepEnabledFlag.StepUpEnabled
                | QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
            )
        if qtpy.API_NAME == "PyQt5":
            return self.StepUpEnabled | self.StepDownEnabled
        return QAbstractSpinBox.StepUpEnabled | QAbstractSpinBox.StepDownEnabled
