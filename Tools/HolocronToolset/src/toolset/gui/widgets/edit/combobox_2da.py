from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtWidgets import QComboBox, QMenu, QWidget
from toolset.gui.dialogs.edit.combo_2da import ModdedValueSpinboxDialog

if TYPE_CHECKING:
    from PyQt5.QtCore import QPoint


class ComboBox2DA(QComboBox):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)

        self._sortAlphabetically = False

    def addItem(self, text: str, row: int | None = None):
        """Adds the 2DA row into the combobox. If the row index is not specified, then the value will be set to the number of items in the combobox.

        Args:
        ----
            text: Text to display.
            row: The row index into the 2DA table.
        """
        if row is None:
            row = self.count()
        super().addItem(text, row)

    def setItems(self, values: list[str], sortAlphabetically: bool = True, cleanupStrings: bool = True,
                 ignoreBlanks: bool = False):
        self._sortAlphabetically = sortAlphabetically
        self.clear()

        for index, text in enumerate(values):
            new_text = text
            if cleanupStrings:
                new_text = text.replace("TRAP_", "")
                new_text = text.replace("GENDER_", "")
                new_text = text.replace("_", " ")
            if ignoreBlanks and new_text == "":
                continue
            super().addItem(new_text, index)

        self.enableSort() if self._sortAlphabetically else self.disableSort()

    def toggleSort(self):
        self.disableSort() if self._sortAlphabetically else self.enableSort()

    def enableSort(self):
        self._sortAlphabetically = True
        self.model().sort(0)

    def disableSort(self):
        self._sortAlphabetically = False
        selected = self.currentData()

        items = [
            (self.itemData(index), self.itemText(index))
            for index in range(self.count())
        ]
        self.clear()

        for index, text in sorted(items, key=lambda x: x[0]):
            self.addItem(text, index)
        self.setCurrentIndex(selected)

    def setCurrentIndex(self, rowIn2DA: int):
        """Selects the item with the specified row index: This is NOT the index into the combobox like it would be with a
        normal QCombobox. If the index cannot be found, it will create an item with the matching index.

        Args:
        ----
            rowIn2DA: The row index to select.
        """
        index = None
        for i in range(self.count()):
            if self.itemData(i) == rowIn2DA:
                index = i

        if index is None:
            self.addItem(f"[Modded Entry #{rowIn2DA}]", rowIn2DA)
            index = self.count() - 1

        super().setCurrentIndex(index)

    def currentIndex(self) -> int:
        """Returns the row index from the currently selected item.

        Returns
        -------
            Row index into the 2DA file.
        """
        return 0 if self.currentData() is None else self.currentData()

    def onContextMenu(self, point: QPoint):
        menu = QMenu(self)
        menu.addAction("Set Modded Value").triggered.connect(self.openModdedValueDialog)
        menu.addAction("Toggle Sorting").triggered.connect(self.toggleSort)
        menu.popup(self.mapToGlobal(point))

    def openModdedValueDialog(self):
        """Opens a dialog where the player can manually set the index into the 2DA file."""
        dialog = ModdedValueSpinboxDialog(self)
        if dialog.exec_():
            self.setCurrentIndex(dialog.value())
