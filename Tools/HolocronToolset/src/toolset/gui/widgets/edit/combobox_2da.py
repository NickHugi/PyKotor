from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from qtpy import QtCore
from qtpy.QtGui import QColor, QPainter, QPen
from qtpy.QtWidgets import QAction, QComboBox, QMenu, QMessageBox

from toolset.gui.dialogs.edit.combo_2da import ModdedValueSpinboxDialog
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QPaintEvent, QStandardItemModel
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from toolset.data.installation import HTInstallation


_ROW_INDEX_DATA_ROLE = QtCore.Qt.ItemDataRole.UserRole + 4
_REAL_2DA_TEXT_ROLE = QtCore.Qt.ItemDataRole.UserRole + 5


class ComboBox2DA(QComboBox):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)
        self.currentIndexChanged.connect(self.onCurrentIndexChanged)
        self.setToolTip("<i>Right click for more options</i>")

        self._sortAlphabetically: bool = False
        self._this2DA: TwoDA | None = None
        self._installation: HTInstallation | None = None
        self._resname: str | None = None

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        if super().currentIndex() == -1:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(0, 0, 0)))
            text_rect = self.rect().adjusted(2, 0, 0, 0)
            painter.drawText(text_rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, self.placeholderText())
            painter.end()

    def currentIndex(self) -> int:
        """Returns the row index from the currently selected item: This is NOT the index into the combobox like it would be with a normal QCombobox.

        Returns:
        -------
            Row index into the 2DA file.
        """
        current_index = super().currentIndex()
        if current_index == -1:
            return 0
        row_index = self.itemData(current_index, _ROW_INDEX_DATA_ROLE)
        return row_index or 0

    def setCurrentIndex(self, rowIn2DA: int):
        """Selects the item with the specified row index: This is NOT the index into the combobox like it would be with a normal QCombobox.

        If the index cannot be found, it will create an item with the matching index.

        Args:
        ----
            rowIn2DA: The Row index to select.
        """
        index = None
        for i in range(self.count()):
            if self.itemData(i, _ROW_INDEX_DATA_ROLE) == rowIn2DA:
                index = i

        if index is None:
            self.addItem(f"[Modded Entry #{rowIn2DA}]", rowIn2DA)
            index = self.count() - 1

        super().setCurrentIndex(index)

    def addItem(
        self,
        text: str,
        row: int | None = None,
    ):
        """Adds the 2DA row into the combobox.

        If the row index is not specified, then the value will be set to the number of items in the combobox (the last row + 1).

        Args:
        ----
            text: Text to display.
            row: The row index into the 2DA table.
        """
        if row is None:
            row = self.count()
        assert isinstance(text, str), f"text '{text}' ({text.__class__.__name__}) is not a str"
        assert isinstance(row, int), f"row '{row}' ({row.__class__.__name__}) is not an int"
        display_text = text if text.startswith("[Modded Entry #") else f"{text} [{row}]"
        super().addItem(display_text)

        self.setItemData(self.count() - 1, row, _ROW_INDEX_DATA_ROLE)
        self.setItemData(self.count() - 1, text, _REAL_2DA_TEXT_ROLE)

    def insertItem(self, index: int, text: str):
        """Raises NotImplementedError because inserting an item without specifying a row index is not supported."""
        msg = "Inserting an item using insertItem is not supported. Use addItem to add a new entry to the combobox."
        raise NotImplementedError(msg)

    def addItems(self, texts: list[str]):
        """Raises NotImplementedError because bulk adding items without specifying row indices is not supported."""
        msg = "Bulk adding items using addItems is not supported. Use setItems to add multiple items with proper row indices."
        raise NotImplementedError(msg)

    def insertItems(self, index: int, texts: list[str]):
        """Raises NotImplementedError because bulk inserting items without specifying row indices is not supported."""
        msg = "Bulk inserting items using insertItems is not supported. Use setItems to insert multiple items with proper row indices."
        raise NotImplementedError(msg)

    def onCurrentIndexChanged(self, index: int):
        self.updateToolTip()

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

    def setItems(
        self,
        values: Iterable[str],
        *,
        sortAlphabetically: bool = True,
        cleanupStrings: bool = True,
        ignoreBlanks: bool = False,
    ):
        self._sortAlphabetically = sortAlphabetically
        self.clear()

        for index, text in enumerate(values):
            assert isinstance(text, str), f"text '{text}' ({text.__class__.__name__}) is not a str"
            new_text: str = text
            if cleanupStrings:
                new_text = text.replace("TRAP_", "")
                new_text = text.replace("GENDER_", "")
                new_text = text.replace("_", " ")
            if not ignoreBlanks or new_text and new_text.strip():
                self.addItem(new_text, index)

        self.enableSort() if self._sortAlphabetically else self.disableSort()

    def updateToolTip(self):
        rowIndexDisplay = (f"<b>Row Index:</b> {self.currentIndex()}<br>" if self.currentIndex() != -1 else "")
        if self._resname and self._this2DA:
            tooltip_text = (
                f"<b>Filename:</b> {self._resname}.2da<br>"
                f"{rowIndexDisplay}<br><i>Right-click for more options.</i>"
            )
        else:
            tooltip_text = (
                f"{rowIndexDisplay}<br><i>Right-click for more options.</i>"
            )
        self.setToolTip(tooltip_text)

    def setContext(self, data: TwoDA, install: HTInstallation, resname: str):
        self._this2DA = data
        self._installation = install
        self._resname = resname

    def toggleSort(self):
        self.disableSort() if self._sortAlphabetically else self.enableSort()

    def enableSort(self):  # sourcery skip: class-extract-method
        """Sorts the combobox alphabetically. This is a custom method."""
        self._sortAlphabetically = True
        model: QStandardItemModel = self.model()
        model.setSortRole(_REAL_2DA_TEXT_ROLE)
        model.sort(0)

    def disableSort(self):
        """Sorts the combobox by row index. This is a custom method."""
        self._sortAlphabetically = False
        model: QStandardItemModel = self.model()
        model.setSortRole(_ROW_INDEX_DATA_ROLE)
        model.sort(0)

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
        except (ValueError, OSError) as e:
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
