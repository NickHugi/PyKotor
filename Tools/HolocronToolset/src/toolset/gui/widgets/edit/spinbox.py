from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtWidgets import QFormLayout, QSpinBox

if TYPE_CHECKING:
    from qtpy.QtCore import QObject
    from qtpy.QtWidgets import QLayout


class GFFFieldSpinBox(QSpinBox):
    sig_final_value_applied = QtCore.Signal(int)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.special_value_text_mapping: dict[int, str] = {0: "0", -1: "-1"}
        self.min_value = self.minimum()
        self.setMinimum(-2147483647+1)
        self.setMaximum(2147483647)
        self.setSpecialValueText(self.special_value_text_mapping.get(self.value(), ""))

        self.last_operation: str | None = None
        self.cached_value: int | None = None
        self.sig_final_value_applied.connect(self._apply_final_value)

    def true_minimum(self) -> int:
        special_min = min(self.special_value_text_mapping.keys(), default=self.minimum())
        return min(self.minimum(), special_min, self.min_value)

    def true_maximum(self) -> int:
        special_max = max(self.special_value_text_mapping.keys(), default=self.maximum())
        return max(self.maximum(), special_max)

    def stepBy(self, steps: int):
        self.last_operation = "stepBy"
        current_value: int = self.value()
        if steps > 0:
            self.cached_value = self._next_value(current_value, steps)
        elif steps < 0:
            self.cached_value = self._next_value(current_value, steps)
        self.sig_final_value_applied.emit(self.cached_value)

    def _next_value(
        self,
        current_value: int,
        steps: int,
    ) -> int:
        tentative_next_value: int = current_value + steps
        true_min: int = self.true_minimum()
        if tentative_next_value < true_min:
            return true_min
        max_val = self.maximum()
        if tentative_next_value > max_val:
            return max_val

        special_values: list[int] = sorted(self.special_value_text_mapping.keys())
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

    def text_changed(self, text: str):
        self.last_operation = "textChanged"
        try:
            self.cached_value = int(text)
        except ValueError:
            self.cached_value = self.value()

    def _apply_final_value(self, value: int):
        if value < self.true_minimum():
            value = self.true_minimum()
        elif value > self.true_maximum():
            value = self.true_maximum()
        super().setValue(value)
        self.valueChanged.emit(value)

    def setMinimum(self, value: int):
        self.min_value = value
        super().setMinimum(min(-2, value))

    def on_value_changed(self, value):
        if self.last_operation in ("stepBy", "textChanged"):
            self.sig_final_value_applied.emit(self.cached_value)
        self.last_operation = None

    @classmethod
    def from_spinbox(
        cls,
        original_spin: QSpinBox,
        min_value: int = 0,
        max_value: int = 100,
    ) -> GFFFieldSpinBox:
        """Is not perfect at realigning, but attempts to initialize a GFFFieldSpinBox from a pre-existing QSpinBox."""
        if not isinstance(original_spin, QSpinBox):
            raise TypeError("The provided widget is not a QSpinBox.")

        layout: QLayout | None = original_spin.parentWidget().layout()
        row: int | None = None
        role: int | None = None

        if isinstance(layout, QFormLayout):
            for r in range(layout.rowCount()):
                if layout.itemAt(r, QFormLayout.ItemRole.FieldRole) and layout.itemAt(r, QFormLayout.ItemRole.FieldRole).widget() == original_spin:
                    row, role = r, QFormLayout.ItemRole.FieldRole

                    break
                if layout.itemAt(r, QFormLayout.ItemRole.LabelRole) and layout.itemAt(r, QFormLayout.ItemRole.LabelRole).widget() == original_spin:
                    row, role = r, QFormLayout.ItemRole.LabelRole

                    break

        parent: QObject | None = original_spin.parent()
        if parent is None:
            raise RuntimeError("The provided widget has no parent.")

        custom_spin: GFFFieldSpinBox = cls(parent, min_value=min_value, max_value=max_value)

        meta_obj: QtCore.QMetaObject | None = original_spin.metaObject()
        if meta_obj is None:
            raise RuntimeError("The provided widget is not a QSpinBox.")

        for i in range(meta_obj.propertyCount()):
            prop: QtCore.QMetaProperty = meta_obj.property(i)

            if prop.isReadable() and prop.isWritable():
                value = original_spin.property(prop.name())
                custom_spin.setProperty(prop.name(), value)

        if row is not None and role is not None:
            layout.setWidget(row, role, custom_spin)

        original_spin.deleteLater()

        return custom_spin
