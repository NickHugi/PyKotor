from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QWidget, QComboBox, QMenu

from gui.dialogs.modded_value_spinbox import ModdedValueSpinboxDialog


class ComboBox2DA(QComboBox):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)

        self._sortAlphabetically = False

    def addItem(self, text: str, row: int = None) -> None:
        """
        Adds the 2DA row into the combobox. If the row index is not specified, then the value will be set to the number
        of items in the combobox.

        Args:
            text: Text to display.
            row: The row index into the 2DA table.
        """
        if row is None:
            row = self.count()
        super().addItem(text, row)

    def setItems(self, values: List[str], sortAlphabetically: bool = True) -> None:
        self._sortAlphabetically = sortAlphabetically

        for index, text in enumerate(values):
            super().addItem(text, index)

        if sortAlphabetically:
            self.model().sort(0)

    def toggleSort(self) -> None:
        self.disableSort() if self._sortAlphabetically else self.enableSort()

    def enableSort(self) -> None:
        self._sortAlphabetically = True
        self.model().sort(0)

    def disableSort(self) -> None:
        self._sortAlphabetically = False
        items = []
        selected = self.currentData()

        for index in range(self.count()):
            items.append((self.itemData(index), self.itemText(index)))
        self.clear()

        for index, text in sorted(items, key=lambda x: x[0]):
            self.addItem(text, index)
        self.setCurrentIndex(selected)

    def setCurrentIndex(self, rowIn2DA: int) -> None:
        """
        Selects the item with the specified row index: This is NOT the index into the combobox like it would be with a
        normal QCombobox. If the index cannot be found, it will create an item with the matching index.

        Args:
            rowIn2DA: The row index to select.
        """
        index = None
        for i in range(self.count()):
            if self.itemData(i) == rowIn2DA:
                index = i

        if index is None:
            self.addItem("[Modded Entry #{}]".format(rowIn2DA), rowIn2DA)
            index = self.count() - 1

        super().setCurrentIndex(index)

    def currentIndex(self) -> int:
        """
        Returns the row index from the currently selected item.

        Returns:
            Row index into the 2DA file.
        """
        return 0 if self.currentData() is None else self.currentData()

    def onContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction("Set Modded Value").triggered.connect(self.openModdedValueDialog)
        menu.addAction("Toggle Sorting").triggered.connect(self.toggleSort)
        menu.popup(self.mapToGlobal(point))

    def openModdedValueDialog(self) -> None:
        """
        Opens a dialog where the player can manually set the index into the 2DA file.
        """
        dialog = ModdedValueSpinboxDialog(self)
        if dialog.exec_():
            self.setCurrentIndex(dialog.value())
