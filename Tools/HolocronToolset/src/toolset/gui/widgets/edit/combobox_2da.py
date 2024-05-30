from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtWidgets import QAction, QComboBox, QMenu, QMessageBox

from toolset.gui.dialogs.edit.combo_2da import ModdedValueSpinboxDialog
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from toolset.data.installation import HTInstallation

_REAL_2DA_TEXT_ROLE = QtCore.Qt.UserRole + 5

class ComboBox2DA(QComboBox):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)

        self._sortAlphabetically: bool = False
        self._this2DA: TwoDA | None = None
        self._installation: HTInstallation | None = None
        self._resname: str | None = None

    def setContext(self, data: TwoDA, install: HTInstallation, resname: str):
        self._this2DA = data
        self._installation = install
        self._resname = resname

    def addItem(
        self,
        text: str,
        row: int | None = None,
    ):
        """Adds the 2DA row into the combobox. If the row index is not specified, then the value will be set to the number of items in the combobox.

        Args:
        ----
            text: Text to display.
            row: The row index into the 2DA table.
        """
        if row is None:
            row = self.count()
        assert isinstance(text, str), f"text '{text}' ({text.__class__.__name__}) is not a str"
        assert isinstance(row, int), f"row '{row}' ({row.__class__.__name__}) is not an int"
        display_text = f"{text} [{row}]"
        super().addItem(display_text, row)
        self.setItemData(row, text, _REAL_2DA_TEXT_ROLE)

    def setItems(
        self,
        values: list[str],
        *,
        sortAlphabetically: bool = True,
        cleanupStrings: bool = True,
        ignoreBlanks: bool = False,
    ):
        self._sortAlphabetically = sortAlphabetically
        self.clear()

        for index, text in enumerate(values):
            assert isinstance(text, str), f"text '{text}' ({text.__class__.__name__}) is not a str"
            assert isinstance(index, int), f"index '{index}' ({index.__class__.__name__}) is not an int"
            new_text: str = text
            if cleanupStrings:
                new_text = text.replace("TRAP_", "")
                new_text = text.replace("GENDER_", "")
                new_text = text.replace("_", " ")
            if not ignoreBlanks or new_text and new_text.strip():
                self.addItem(new_text, index)

        self.enableSort() if self._sortAlphabetically else self.disableSort()

    def toggleSort(self):
        self.disableSort() if self._sortAlphabetically else self.enableSort()

    def enableSort(self):
        # FIXME: sorting is broken. Causes wrong internal value to be applied. Should create a proper sort model here.
        return
        self._sortAlphabetically = True
        self.model().sort(0)

    def disableSort(self):
        self._sortAlphabetically = False
        selected: int = self.currentData()

        items: list[tuple[int, str]] = [
            (self.itemData(index), self.itemData(index, _REAL_2DA_TEXT_ROLE))
            for index in range(self.count())
        ]
        self.clear()

        for index, text in sorted(items, key=lambda x: x[0]):
            assert isinstance(text, str), f"text '{text}' ({text.__class__.__name__}) is not a str"
            assert isinstance(index, int), f"index '{index}' ({index.__class__.__name__}) is not an int"
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

        Returns:
        -------
            Row index into the 2DA file.
        """
        return 0 if self.currentData() is None else self.currentData()

    def onContextMenu(self, point: QPoint):
        menu = QMenu(self)
        if (
            self._installation is not None
            and self._resname is not None
            and self._this2DA is not None
        ):
            menu.addAction(f"Open '{self._resname}.2da' in 2DAEditor").triggered.connect(self.openIn2DAEditor)
        menu.addAction("Set Modded Value").triggered.connect(self.openModdedValueDialog)
        toggleSortAction = QAction("Toggle Sorting", self)
        toggleSortAction.setCheckable(True)
        toggleSortAction.setChecked(self._sortAlphabetically)
        toggleSortAction.triggered.connect(self.toggleSort)
        menu.addAction(toggleSortAction)
        menu.popup(self.mapToGlobal(point))

    def openIn2DAEditor(self):
        if (
            self._installation is None
            or self._resname is None
            or self._this2DA is None
        ):
            return
        from pykotor.resource.formats.twoda.twoda_auto import bytes_2da
        from toolset.gui.editors.twoda import TwoDAEditor
        from toolset.utils.window import addWindow
        editor = TwoDAEditor(None, self._installation)
        editor.new()
        try:
            bytes_data = bytes_2da(self._this2DA)
            editor._load_main(bytes_data)  # noqa: SLF001
        except ValueError as e:
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            QMessageBox(QMessageBox.Icon.Critical, "Failed to load file.", f"Failed to open or load file data.<br>{error_msg}").exec_()
            editor.proxyModel.setSourceModel(editor.model)
            editor.new()
        else:
            editor.jumpToRow(self.currentIndex())
        editor.setWindowTitle(f"{self._resname}.2da - 2DAEditor({self._installation.name})")
        addWindow(editor)

    def openModdedValueDialog(self):
        """Opens a dialog where the player can manually set the index into the 2DA file."""
        dialog = ModdedValueSpinboxDialog(self)
        if dialog.exec_():
            self.setCurrentIndex(dialog.value())
