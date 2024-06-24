from __future__ import annotations

import sys

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, Sequence

from qtpy.QtCore import (
    QEvent,
    QSize,
    QSortFilterProxyModel,
    QStringListModel,
    QTimer,
    Qt,
)
from qtpy.QtGui import (
    QFontMetrics,
)
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QListView,
    QMainWindow,
    QPushButton,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from toolset.utils.misc import getQtKeyString

if TYPE_CHECKING:
    from qtpy.QtCore import (
        QModelIndex,
        QObject,
    )
    from qtpy.QtGui import (
        QKeyEvent,
        QPainter,
    )


class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject | None = None, combo_box: FilterComboBox = None):
        super().__init__(parent)
        self.filter_text: str = ""
        self.filter_timer: QTimer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.invalidateFilter)
        self.debounce_delay: int = 300  # Milliseconds
        self.combo_box: FilterComboBox = combo_box

    def setFilterText(self, text: str):
        self.filter_text = text.lower()
        self.filter_timer.stop()
        self.filter_timer.start(self.debounce_delay)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        index = self.sourceModel().index(source_row, 0, source_parent)
        item_text: str | None = index.data(Qt.ItemDataRole.DisplayRole)
        current_text = self.combo_box.lineEdit().text().lower()

        if item_text is None:
            return False

        item_text_lower = item_text.lower()
        if self.filter_text in item_text_lower:
            return True
        return current_text == item_text_lower  # prevents annoying selection changes.


class ButtonDelegate(QStyledItemDelegate):
    def __init__(
        self,
        button_text: str,
        button_callback: Callable[[str], Any],
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.button_text: str = button_text
        self.button_callback: Callable[[str], Any] = button_callback
        self.buttons: dict[int, QPushButton] = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        if index.row() not in self.buttons:
            button = QPushButton(self.button_text, parent=option.widget)
            button.clicked.connect(lambda _checked, idx=index: self.button_callback(self.get_item_text(idx)))
            self.buttons[index.row()] = button

        button = self.buttons[index.row()]
        fm = QFontMetrics(button.font())
        button_width = fm.width(self.button_text) + 10
        button_height = fm.height() + 10
        button_size = QSize(button_width, button_height)
        button.move(option.rect.right() - button_size.width(), option.rect.top())
        button.resize(button_size)
        button.show()

    def get_item_text(self, index: QModelIndex) -> str:
        return index.model().data(index, Qt.DisplayRole) if index.isValid() else ""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        fm = QFontMetrics(option.font)
        text_width = fm.width(index.model().data(index, Qt.DisplayRole))
        text_height = fm.height()
        button_width = fm.width(self.button_text) + 10
        total_width = text_width + button_width + 5
        button_height = fm.height()+10
        return QSize(total_width, max(text_height, button_height))

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)


def filterLineEditKeyPressEvent(self: QLineEdit, event: QKeyEvent, parentComboBox: FilterComboBox):
    print("filterLineEditKeyPressEvent, curText of main lineEdit: ", parentComboBox.lineEdit().text(), "key:", getQtKeyString(event.key()))
    if event.key() in (Qt.Key_Enter, Qt.Key_Return):
        QLineEdit.keyPressEvent(self, event)
        return
    if event.key() in (Qt.Key_Escape,):
        QLineEdit.keyPressEvent(self, event)
    elif event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
        self.clear()
    else:
        QLineEdit.keyPressEvent(self, event)


class FilterComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setEditable(True)
        self.setCompleter(None)  # type: ignore[arg-type]
        self.lineEdit().setValidator(None)  # type: ignore[arg-type]
        self.original_model: QStringListModel = QStringListModel(self)
        self.items: list[str] = []
        self.proxy_model: FilterProxyModel = FilterProxyModel(self, self)
        self.itemsLoaded: bool = False
        self.popUpState = False
        self.origText: str = ""

        self.setView(QListView(self))
        self.proxy_model.setSourceModel(self.original_model)
        self.setModel(self.proxy_model)
        self.original_model.setStringList(self.items)
        self.createFilterLineEdit()
        line_edit_height = self.filterLineEdit.height()
        margins = self.view().viewportMargins()
        self.view().setViewportMargins(margins.left(), margins.top()+line_edit_height, margins.right(), margins.bottom())
        self.view().update()

    def setComboBoxText(
        self,
        text: str,
        *,
        alwaysOnTop: bool = True,  # recommended
    ):
        index = self.findText(text, Qt.MatchFlag.MatchCaseSensitive)
        if alwaysOnTop:
            if index != -1:  # Text found
                self.removeItem(index)
            newIndex = 1 if isinstance(self, FilterComboBox) else 0
            self.insertItem(newIndex, text)  # Insert at the top
            self.setCurrentIndex(newIndex)  # Set the current index to the top item
        else:
            if index == -1:  # Text not found
                self.addItem(text)
                index = self.findText(text)
            self.setCurrentIndex(index)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.FocusIn and source is not self.filterLineEdit:
            with suppress(RuntimeError):
                self.filterLineEdit.setFocus()
                return True
        return super().eventFilter(source, event)

    def createFilterLineEdit(self):
        self.filterLineEdit = QLineEdit(self)
        self.filterLineEdit.setPlaceholderText("Type to filter...")
        self.filterLineEdit.setClearButtonEnabled(True)
        self.filterLineEdit.textChanged.connect(self.filter_items)
        self.filterLineEdit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.view().keyPressEvent = self.filterLineEdit.keyPressEvent  # type: ignore[method-assign, assignment]
        self.filterLineEdit.hide()  # Initially hidden, shown in showPopup()
        self.filterLineEdit.keyPressEvent = lambda event: filterLineEditKeyPressEvent(self.filterLineEdit, event, self)  # type: ignore[method-assign, assignment]

    def showPopup(self):
        self.popUpState = True
        self.origText = self.currentText()
        if not self.itemsLoaded:
            self.original_model.setStringList(self.items)
            self.setComboBoxText(self.origText)
            self.itemsLoaded = True

        max_width = self.width()
        delegate = self.itemDelegate()
        max_items_to_measure = 20
        extra_padding = 25
        for i in range(min(self.model().rowCount(), max_items_to_measure)):
            item_width = delegate.sizeHint(QStyleOptionViewItem(), self.model().index(i, 0)).width()
            if item_width > max_width:
                max_width = item_width
        adjusted_width = extra_padding + max_width
        self.filterLineEdit.setFixedWidth(adjusted_width)
        self.filterLineEdit.adjustSize()
        self.filterLineEdit.setParent(self.view())
        self.filterLineEdit.move(0, 0)
        self.filterLineEdit.show()
        self.filterLineEdit.setFocus()
        super().showPopup()

    def hidePopup(self):
        self.popUpState = False
        super().hidePopup()

    def populateComboBox(self, items: Sequence[str]):
        self.items = list(items)
        self.itemsLoaded = False

    def filter_items(self, text):
        self.proxy_model.setFilterText(text)

    def set_button_delegate(self, button_text: str, button_callback: Callable[[str], Any]):
        button_delegate = ButtonDelegate(button_text, button_callback, self.view())
        self.view().setItemDelegate(button_delegate)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FilterComboBox Test")
        self.setGeometry(100, 100, 300, 200)

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a layout for the central widget
        layout = QVBoxLayout(central_widget)

        # Create and populate the FilterComboBox
        self.comboBox = FilterComboBox()
        self.comboBox.populateComboBox([f"Item {i}" for i in range(10)])
        layout.addWidget(self.comboBox)

        # Set the layout for the central widget
        central_widget.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
