from __future__ import annotations

from qtpy import QtCore
from qtpy.QtWidgets import QFormLayout, QSpinBox


class GFFFieldSpinBox(QSpinBox):
    applyFinalValue = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.specialValueTextMapping = {0: "0", -1: "-1"}
        self.setMinimum(-2147483647)
        self.setMaximum(2147483647)
        self.setSpecialValueText(self.specialValueTextMapping.get(self.value(), ""))

        self.lastOperation = None
        self.cachedValue = None

        # Connect the custom signal
        self.applyFinalValue.connect(self._apply_final_value)

    def stepBy(self, steps: int):
        self.lastOperation = "stepBy"
        current_value = self.value()
        if steps > 0:
            # Determine the step up logic
            self.cachedValue = current_value + 1  # Customize this as needed
        elif steps < 0:
            # Determine the step down logic
            self.cachedValue = current_value - 1  # Customize this as needed

        # Emit to handle in valueChanged or final application
        self.applyFinalValue.emit(self.cachedValue)

    def textChanged(self, text: str):
        self.lastOperation = "textChanged"
        # Parse the text and set the cached value accordingly
        try:
            self.cachedValue = int(text)
        except ValueError:
            self.cachedValue = self.value()  # fallback to current if invalid

    def _apply_final_value(self, value):
        # Apply the final value calculated from either stepBy or textChanged
        if value < self.minimum():
            value = self.minimum()
        elif value > self.maximum():
            value = self.maximum()
        super().setValue(value)  # Use super to avoid recursion with valueChanged signal
        self.valueChanged.emit(value)

    def onValueChanged(self, value):
        if self.lastOperation in ("stepBy", "textChanged"):
            print("GFFFieldSpinBox: Confirm and finalize value application")
            self.applyFinalValue.emit(self.cachedValue)
        self.lastOperation = None  # Reset after handling

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
