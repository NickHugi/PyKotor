from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable

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
    QComboBox,
    QLineEdit,
    QListView,
    QPushButton,
    QStyleOptionViewItem,
    QStyledItemDelegate,
)

if TYPE_CHECKING:
    from qtpy.QtCore import (
        QModelIndex,
        QObject,
    )
    from qtpy.QtGui import (
        QKeyEvent,
        QPainter,
    )
    from qtpy.QtWidgets import (
        QWidget,
    )


class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.filter_text: str = ""
        self.filter_timer: QTimer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.invalidateFilter)
        self.debounce_delay = 300  # Milliseconds

    def setFilterText(self, text: str):
        self.filter_text = text.lower()
        self.filter_timer.stop()
        self.filter_timer.start(self.debounce_delay)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row == 0:
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)
        item_text = index.data(Qt.DisplayRole)
        return False if item_text is None else self.filter_text in item_text.lower()


class ButtonDelegate(QStyledItemDelegate):
    def __init__(
        self,
        button_text: str,
        button_callback: Callable[[int], Any],
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.button_text: str = button_text
        self.button_callback: Callable[[int], Any] = button_callback
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


def lineEditKeyPressEvent(self: QLineEdit, event: QKeyEvent):
    if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
        self.clear()
    else:
        QLineEdit.keyPressEvent(self, event)

class FilterComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setEditable(True)
        self.original_model: QStringListModel = QStringListModel(self)
        self.items: list[str] = [""]
        self.proxy_model: FilterProxyModel = FilterProxyModel(self)
        self.itemsLoaded: bool = False

        self.setView(QListView(self))
        self.proxy_model.setSourceModel(self.original_model)
        self.setModel(self.proxy_model)
        self.original_model.setStringList(self.items)
        self.create_line_edit()
        self.lineEdit().editingFinished.connect(lambda *args: self.setComboBoxText(self.currentText()))

    def setComboBoxText(
        self,
        text: str,
        *,
        alwaysOnTop: bool = True,
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
        if event.type() == QEvent.FocusIn and source is not self.line_edit:
            with suppress(RuntimeError):
                self.line_edit.setFocus()
                return True
        return super().eventFilter(source, event)

    def create_line_edit(self):
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Type to filter...")
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.textChanged.connect(self.filter_items)
        self.line_edit.hide()
        self.line_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.line_edit.installEventFilter(self)
        self.line_edit.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)  # probably does nothing.
        self.line_edit.keyPressEvent = lineEditKeyPressEvent

    def showPopup(self):
        if not self.itemsLoaded:
            curText = self.currentText()
            self.original_model.setStringList(self.items)
            self.setComboBoxText(curText)
            self.itemsLoaded = True
        try:  # noqa: SIM105
            self.view().setIndexWidget(self.proxy_model.index(0, 0), self.line_edit)
        except RuntimeError: ...  # wrapped C/C++ object of type QLineEdit has been deleted
            # mostly works, but sometimes crashes whole app.
            #self.create_line_edit()
            #self.view().setIndexWidget(self.proxy_model.index(0, 0), self.line_edit)
            #self.line_edit.show()
            #self.line_edit.setFocus()
        else:
            self.line_edit.show()
            self.line_edit.setFocus()

        max_width = self.width()
        delegate = self.itemDelegate()
        max_items_to_measure = 20
        for i in range(min(self.model().rowCount(), max_items_to_measure)):
            item_width = delegate.sizeHint(QStyleOptionViewItem(), self.model().index(i, 0)).width()
            if item_width > max_width:
                max_width = item_width

        # Set the width of the dropdown list
        self.view().setFixedWidth(max_width+25)
        super().showPopup()

    def populate_items(self, items):
        self.items = ["", *items]
        self.itemsLoaded = False

    def filter_items(self, text):
        self.proxy_model.setFilterText(text)

    def set_button_delegate(self, button_text: str, button_callback: Callable[[int], Any]):
        button_delegate = ButtonDelegate(button_text, button_callback, self.view())
        self.view().setItemDelegate(button_delegate)
