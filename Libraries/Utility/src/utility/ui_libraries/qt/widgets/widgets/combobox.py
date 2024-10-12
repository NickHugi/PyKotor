from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Any, Callable, Sequence

from qtpy.QtCore import QRect, QSize, QSortFilterProxyModel, QStringListModel, QTimer, Qt
from qtpy.QtGui import QFontMetrics, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QComboBox, QLineEdit, QListView, QMainWindow, QSizePolicy, QStyleOptionViewItem, QStyledItemDelegate, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject
    from qtpy.QtGui import QKeyEvent, QMouseEvent
    from qtpy.QtWidgets import QPushButton


class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, combo_box: FilterComboBox):
        super().__init__(combo_box)
        self.filter_text: str = ""
        self.filter_timer: QTimer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.invalidateFilter)
        self.debounce_delay: int = 300  # Milliseconds
        self.combo_box: FilterComboBox | None = combo_box

    def set_filter_text(self, text: str):
        self.filter_text = text.lower()
        self.filter_timer.stop()
        self.filter_timer.start(self.debounce_delay)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        index = self.sourceModel().index(source_row, 0, source_parent)
        item_text: str | None = index.data(Qt.ItemDataRole.DisplayRole)
        line_edit = self.combo_box.filter_line_edit
        if line_edit is None:
            return True
        current_text = line_edit.text().lower()

        if item_text is None:
            return False

        item_text_lower = item_text.lower()
        if self.filter_text in item_text_lower:
            return True
        return current_text == item_text_lower  # Prevents annoying selection changes.


class ButtonDelegate(QStyledItemDelegate):
    def __init__(
        self,
        combobox: FilterComboBox,
        button_text: str,
        button_callback: Callable[[str], Any],
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.combobox: FilterComboBox = combobox
        self.button_text: str = button_text
        self.button_callback: Callable[[str], Any] = button_callback
        self.buttons: dict[str, QPushButton] = {}

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        fm = QFontMetrics(option.font)
        button_width = fm.horizontalAdvance(self.button_text) + 20  # Adding padding
        button_height = fm.height() + 10
        button_rect = QRect(option.rect.right() - button_width, option.rect.top(), button_width, button_height)
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.lightGray)
        painter.drawRect(button_rect)
        painter.setPen(Qt.black)
        painter.drawText(button_rect, Qt.AlignCenter, self.button_text)
        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        size = super().sizeHint(option, index)
        fm = QFontMetrics(option.font)
        button_width = fm.horizontalAdvance(self.button_text) + 20
        button_height = fm.height() + 10
        return QSize(size.width() + button_width, max(size.height(), button_height))


def filter_line_edit_key_press_event(self: QLineEdit, event: QKeyEvent, parent_combo_box: FilterComboBox):
    #print("filterLineEditKeyPressEvent, curText of main lineEdit: ", parentComboBox.lineEdit().text(), "key:", get_qt_key_string(event.key()))
    if event.key() in (
        Qt.Key.Key_Backspace,
        Qt.Key.Key_Delete,
    ):
        self.clear()
    else:
        QLineEdit.keyPressEvent(self, event)
    parent_combo_box.view().repaint()


class CustomListView(QListView):
    def __init__(self, parent: FilterComboBox):
        self.combobox: FilterComboBox = parent
        super().__init__(parent)
        self.button_text: str = ""
        self.button_callback: Callable[[str], Any]

    def keyPressEvent(self, event: QKeyEvent):
        if self.combobox.isPoppedUp:
            self.combobox.filter_line_edit.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if not self.button_text:
            super().mousePressEvent(event)
            return
        viewport_pos = self.viewport().mapFromGlobal(event.globalPos())
        index = self.indexAt(viewport_pos)
        if index.isValid():
            option = self.viewOptions()
            option.rect = self.visualRect(index)
            button_width = QFontMetrics(option.font).horizontalAdvance(self.button_text) + 20
            left_limit = min(option.rect.right() - button_width, self.parent().width() - button_width)

            #print(f"Clicked item '{index.data(Qt.DisplayRole)}', row {index.row()}, mouse position: ({viewport_pos.x()}, {viewport_pos.y()})")
            #print(f"Item rect: ({option.rect.x()}, {option.rect.y()}, {option.rect.width()}, {option.rect.height()})")
            #print(f"Check range: {left_limit} to {option.rect.right()}")

            if left_limit <= viewport_pos.x() <= option.rect.right():
                #print("Click inside button range")
                self.combobox.force_stay_popped_up = True
                self.button_callback(index.data(Qt.ItemDataRole.DisplayRole))
        super().mousePressEvent(event)


class FilterComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None, *, init: bool = True):
        if init:
            super().__init__(parent)
            self._editable = True
        else:
            self._editable = self.isEditable()
        if self._editable:
            self.setEditable(True)
            self.setCompleter(None)  # type: ignore[arg-type]
            self.lineEdit().setValidator(None)  # type: ignore[arg-type]
        self.proxy_model: FilterProxyModel = FilterProxyModel(self)
        self.source_model: QStringListModel | QStandardItemModel | QAbstractItemModel = QStringListModel(self) if init else self.model()
        assert isinstance(self.source_model, (QStringListModel, QStandardItemModel)), f"Invalid source model type: {type(self.source_model).__name__}"
        self.setModel(self.source_model)
        super().setModel(self.proxy_model)

        self.items: list[str] = []
        self.itemsLoaded: bool = False
        self.isPoppedUp: bool = False
        self.orig_text: str = ""
        self.force_stay_popped_up: bool = False
        self.old_width = self.width()

        self.filter_line_edit = QLineEdit(self)
        self.filter_line_edit.setPlaceholderText("Type to filter...")
        self.filter_line_edit.setClearButtonEnabled(True)
        self.filter_line_edit.textChanged.connect(self.filter_items)
        self.filter_line_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.filter_line_edit.hide()
        self.filter_line_edit.keyPressEvent = lambda event: filter_line_edit_key_press_event(self.filter_line_edit, event, self)  # type: ignore[method-assign, assignment]
        main_view = CustomListView(self)
        main_view.combobox = self
        self.setView(main_view)
        # Make room for the filterbox
        margins = self.view().viewportMargins()
        self.view().setViewportMargins(margins.left(), margins.top() + self.filter_line_edit.height(), margins.right(), margins.bottom())
        self.old_width = self.width()
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)

    def setEditable(self, state: bool):  # noqa: FBT001
        self._editable = state
        super().setEditable(state)

    def lineEdit(self) -> QLineEdit:
        line_edit = super().lineEdit()
        if line_edit is None:
            line_edit = QLineEdit(self)
            self.setLineEdit(line_edit)
        line_edit.setReadOnly(not self._editable)
        if not self._editable:
            line_edit.mousePressEvent = lambda *args: self.hidePopup() if self.isPoppedUp else self.showPopup()  # type: ignore[attr-value]
        else:
            line_edit.mousePressEvent = lambda *args: QLineEdit.mousePressEvent(line_edit, *args)  # type: ignore[attr-value]
        line_edit.home(False)  # noqa: FBT003
        return line_edit

    def setModel(self, model: QStringListModel | QStandardItemModel):
        assert isinstance(model, (QStringListModel, QStandardItemModel))
        self.proxy_model.setSourceModel(model)
        self.source_model = model

    def keyPressEvent(self, event: QKeyEvent):
        if self.isPoppedUp:
            self.filter_line_edit.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def set_combo_box_text(
        self,
        text: str,
        *,
        always_on_top: bool = True,  # Recommended
    ):
        index = self.findText(text, Qt.MatchFlag.MatchCaseSensitive)
        if always_on_top:
            if index != -1:  # Text found
                self.removeItem(index)
            newIndex = 0
            self.insertItem(newIndex, text)
        elif index == -1:  # Text not found
            self.addItem(text)
            newIndex = self.findText(text)
        self.setCurrentIndex(newIndex)
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setText(text)
        else:
            self.setCurrentText(text)

    def showPopup(self):
        self.orig_text = self.currentText()
        if not self.itemsLoaded and self.items:
            if isinstance(self.source_model, QStringListModel):
                self.source_model.setStringList(self.items)
            elif isinstance(self.source_model, QStandardItemModel):
                self.source_model.clear()
                for item in self.items:
                    self.source_model.appendRow(QStandardItem(item))
            self.set_combo_box_text(self.orig_text)
            self.itemsLoaded = True

        self.old_width = self.width()
        max_width = self.old_width
        delegate = self.itemDelegate()
        max_items_to_measure = 1000
        for i in range(min(self.model().rowCount(), max_items_to_measure)):
            item_width = delegate.sizeHint(QStyleOptionViewItem(), self.model().index(i, 0)).width()
            max_width = max(item_width, max_width)
        adjusted_width = max_width
        self.resize(adjusted_width, self.height())
        self.filter_line_edit.setFixedWidth(adjusted_width)
        self.filter_line_edit.adjustSize()
        self.filter_line_edit.setParent(self.view())
        self.filter_line_edit.move(0, 0)
        self.filter_line_edit.show()
        self.filter_line_edit.setFocus()
        super().showPopup()
        self.resize(self.old_width, self.height())
        self.isPoppedUp = True
        self.filter_line_edit.setFocus()
        self.view().repaint()

    def hidePopup(self):
        if self.force_stay_popped_up:
            self.force_stay_popped_up = False
            return
        super().hidePopup()
        self.isPoppedUp = False
        self.resize(self.old_width, self.height())

    def populate_combo_box(self, items: Sequence[str]):
        self.items = list(items)
        self.itemsLoaded = False

    def filter_items(self, text):
        self.proxy_model.set_filter_text(text)

    def set_button_delegate(self, button_text: str, button_callback: Callable[[str], Any]):
        listview = self.view()
        assert isinstance(listview, CustomListView)
        listview.button_text = button_text
        listview.button_callback = button_callback
        listview.setItemDelegate(ButtonDelegate(self, button_text, button_callback, listview))


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
        self.comboBox.populate_combo_box([f"Item {i}" for i in range(10)])
        layout.addWidget(self.comboBox)

        # Set the layout for the central widget
        central_widget.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
