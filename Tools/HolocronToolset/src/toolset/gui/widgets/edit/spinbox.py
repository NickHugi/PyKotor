from __future__ import annotations

from qtpy import QtCore
from qtpy.QtWidgets import QFormLayout, QSpinBox


class GFFFieldSpinBox(QSpinBox):
    applyFinalValue = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.specialValueTextMapping = {0: "0", -1: "-1"}
        self.min_value = self.minimum()
        self.setMinimum(-2147483647+1)
        self.setMaximum(2147483647)
        self.setSpecialValueText(self.specialValueTextMapping.get(self.value(), ""))

        self.lastOperation = None
        self.cachedValue = None
        self.applyFinalValue.connect(self._apply_final_value)

    def true_minimum(self) -> int:
        special_min = min(self.specialValueTextMapping.keys(), default=self.minimum())
        return min(self.minimum(), special_min, self.min_value)

    def true_maximum(self) -> int:
        special_max = max(self.specialValueTextMapping.keys(), default=self.maximum())
        return max(self.maximum(), special_max)

    def stepBy(self, steps: int):
        self.lastOperation = "stepBy"
        current_value = self.value()
        if steps > 0:
            self.cachedValue = self._next_value(current_value, steps)
        elif steps < 0:
            self.cachedValue = self._next_value(current_value, steps)
        self.applyFinalValue.emit(self.cachedValue)

    def _next_value(self, current_value: int, steps: int) -> int:
        tentative_next_value = current_value + steps
        true_min = self.true_minimum()
        if tentative_next_value < true_min:
            return true_min
        max_val = self.maximum()
        if tentative_next_value > max_val:
            return max_val

        special_values: list[int] = sorted(self.specialValueTextMapping.keys())
        if steps > 0:
            for sv in special_values:
                if sv > current_value and sv <= tentative_next_value:
                    return sv
            if self.min_value > tentative_next_value:
                return self.min_value
            return min(tentative_next_value, max_val)
        if self.min_value <= tentative_next_value:
            return tentative_next_value
        sv = -1
        for sv in reversed(special_values):
            if sv <= tentative_next_value:
                return sv
        return sv

    def textChanged(self, text: str):
        self.lastOperation = "textChanged"
        try:
            self.cachedValue = int(text)
        except ValueError:
            self.cachedValue = self.value()

    def _apply_final_value(self, value):
        if value < self.true_minimum():
            value = self.true_minimum()
        elif value > self.true_maximum():
            value = self.true_maximum()
        super().setValue(value)
        self.valueChanged.emit(value)

    def setMinimum(self, value: int):
        self.min_value = value
        super().setMinimum(min(-2, value))

    def onValueChanged(self, value):
        if self.lastOperation in ("stepBy", "textChanged"):
            self.applyFinalValue.emit(self.cachedValue)
        self.lastOperation = None

    @classmethod
    def from_spinbox(
        cls,
        originalSpin: QSpinBox,
        min_value: int = 0,
        max_value: int = 100,
    ) -> GFFFieldSpinBox:
        """Is not perfect at realigning, but attempts to initialize a GFFFieldSpinBox from a pre-existing QSpinBox."""
        if not isinstance(originalSpin, QSpinBox):
            raise TypeError("The provided widget is not a QSpinBox.")

        layout = originalSpin.parentWidget().layout()
        row, role = None, None

        if isinstance(layout, QFormLayout):
            for r in range(layout.rowCount()):
                if layout.itemAt(r, QFormLayout.ItemRole.FieldRole) and layout.itemAt(r, QFormLayout.ItemRole.FieldRole).widget() == originalSpin:
                    row, role = r, QFormLayout.ItemRole.FieldRole

                    break
                if layout.itemAt(r, QFormLayout.ItemRole.LabelRole) and layout.itemAt(r, QFormLayout.ItemRole.LabelRole).widget() == originalSpin:
                    row, role = r, QFormLayout.ItemRole.LabelRole

                    break

        parent = originalSpin.parent()
        customSpin = cls(parent, min_value=min_value, max_value=max_value)

        for i in range(originalSpin.metaObject().propertyCount()):
            prop = originalSpin.metaObject().property(i)

            if prop.isReadable() and prop.isWritable():
                value = originalSpin.property(prop.name())
                customSpin.setProperty(prop.name(), value)

        if row is not None and role is not None:
            layout.setWidget(row, role, customSpin)

        originalSpin.deleteLater()

        return customSpin
