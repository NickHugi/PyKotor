from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Any, Callable, Sequence, cast

import qtpy

from qtpy.QtCore import QRect, QSize, QSortFilterProxyModel, QStringListModel, QTimer, Qt
from qtpy.QtGui import QFontMetrics, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QComboBox, QLineEdit, QListView, QMainWindow, QSizePolicy, QStyleOptionViewItem, QStyledItemDelegate, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QMargins, QModelIndex, QObject, QPoint
    from qtpy.QtGui import QKeyEvent, QMouseEvent, QPainter
    from qtpy.QtWidgets import QAbstractItemDelegate, QAbstractItemView, QPushButton


class FilterProxyModel(QSortFilterProxyModel):
    def __init__(
        self,
        combo_box: FilterComboBox,
    ):
        super().__init__(combo_box)
        self.filter_text: str = ""
        self.filter_timer: QTimer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.invalidateFilter)
        self.debounce_delay: int = 300  # Milliseconds
        self.combo_box: FilterComboBox | None = combo_box

    def setFilterText(
        self,
        text: str,
    ):
        self.filter_text = text.lower()
        self.filter_timer.stop()
        self.filter_timer.start(self.debounce_delay)

    def filterAcceptsRow(  # noqa: PLR0911
        self,
        source_row: int,
        source_parent: QModelIndex,
    ) -> bool:
        source_model: QAbstractItemModel | None = self.sourceModel()
        if source_model is None:
            return False
        index: QModelIndex | None = source_model.index(source_row, 0, source_parent)
        if index is None:
            return False
        item_text: str | None = index.data(Qt.ItemDataRole.DisplayRole)
        if self.combo_box is None:
            return False
        line_edit: QLineEdit | None = self.combo_box.filter_line_edit
        if line_edit is None:
            return True
        current_text: str = line_edit.text().lower()

        if item_text is None:
            return False

        item_text_lower: str = item_text.lower()
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

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ):
        super().paint(painter, option, index)
        fm: QFontMetrics = QFontMetrics(option.font)
        button_width: int = fm.horizontalAdvance(self.button_text) + 20  # Adding padding
        button_height: int = fm.height() + 10
        button_rect: QRect = QRect(option.rect.right() - button_width, option.rect.top(), button_width, button_height)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Qt.GlobalColor.lightGray)
        painter.drawRect(button_rect)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(button_rect, Qt.AlignmentFlag.AlignCenter, self.button_text)
        painter.restore()

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QSize:
        size: QSize = super().sizeHint(option, index)
        fm: QFontMetrics = QFontMetrics(option.font)
        button_width: int = fm.horizontalAdvance(self.button_text) + 20
        button_height: int = fm.height() + 10
        return QSize(size.width() + button_width, max(size.height(), button_height))


def filterLineEditKeyPressEvent(
    self: QLineEdit,
    event: QKeyEvent,
    parentComboBox: FilterComboBox,
):
    # print("filterLineEditKeyPressEvent, curText of main lineEdit: ", parentComboBox.lineEdit().text(), "key:", get_qt_key_string(event.key()))
    if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
        self.clear()
    else:
        QLineEdit.keyPressEvent(self, event)
    view: QAbstractItemView | None = parentComboBox.view()
    if view is not None:
        view.repaint()


class CustomListView(QListView):
    def __init__(
        self,
        parent: FilterComboBox,
    ):
        self.combobox: FilterComboBox = parent
        super().__init__(parent)
        self.button_text: str = ""
        self.button_callback: Callable[[str], Any]

    def keyPressEvent(
        self,
        event: QKeyEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.combobox.is_popped_up:
            self.combobox.filter_line_edit.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(
        self,
        event: QMouseEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        if not self.button_text:
            super().mousePressEvent(event)
            return
        viewport: QWidget | None = self.viewport()
        if viewport is None:
            return
        viewport_pos: QPoint = viewport.mapFromGlobal(
            event.globalPos()  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else event.globalPosition().toPoint()
        )
        index: QModelIndex | None = self.indexAt(viewport_pos)
        if index is not None and index.isValid():
            # In Qt6, viewOptions() was removed, so we create the style option directly
            if hasattr(self, "viewOptions"):
                option = self.viewOptions()  # type: ignore[attr-defined]
            else:
                from qtpy.QtWidgets import QStyleOptionViewItem
                option = QStyleOptionViewItem()
                option.initFrom(self)

            option.rect = self.visualRect(index)
            button_width: int = QFontMetrics(option.font).horizontalAdvance(self.button_text) + 20
            left_limit: int = min(option.rect.right() - button_width, cast(QWidget, self.parent()).width() - button_width)

            if left_limit <= viewport_pos.x() <= option.rect.right():
                self.combobox.force_stay_popped_up = True
                self.button_callback(index.data(Qt.ItemDataRole.DisplayRole))
        super().mousePressEvent(event)


class FilterComboBox(QComboBox):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        init: bool = True,
    ):
        if init:
            super().__init__(parent)
            self._editable = True
        else:
            self._editable: bool = self.isEditable()
        if self._editable:
            self.setEditable(True)
            self.setCompleter(None)  # type: ignore[arg-type]
            self.lineEdit().setValidator(None)  # type: ignore[arg-type]

        self.proxy_model: FilterProxyModel = FilterProxyModel(self)
        self.source_model: QStringListModel | QStandardItemModel = QStringListModel(self) if init else self.model()  # pyright: ignore[reportAttributeAccessIssue]
        self.setModel(self.source_model)
        super().setModel(self.proxy_model)

        self.items: list[str] = []
        self.items_loaded: bool = False
        self.is_popped_up: bool = False
        self.orig_text: str = ""
        self.force_stay_popped_up: bool = False
        self.old_width = self.width()

        self.filter_line_edit: QLineEdit = QLineEdit(self)
        self.filter_line_edit.setPlaceholderText("Type to filter...")
        self.filter_line_edit.setClearButtonEnabled(True)
        self.filter_line_edit.textChanged.connect(self.filter_items)
        self.filter_line_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.filter_line_edit.hide()
        self.filter_line_edit.keyPressEvent = lambda event: filterLineEditKeyPressEvent(self.filter_line_edit, event, self)  # type: ignore[method-assign, assignment]
        main_view = CustomListView(self)
        main_view.combobox = self
        self.setView(main_view)
        # Make room for the filterbox
        view: QAbstractItemView | None = self.view()
        if view is None:
            return
        margins: QMargins | None = view.viewportMargins()
        if margins is None:
            return
        view.setViewportMargins(margins.left(), margins.top() + self.filter_line_edit.height(), margins.right(), margins.bottom())
        view.update()
        self.old_width = self.width()
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)

    def setEditable(
        self,
        state: bool,  # noqa: FBT001
    ):  # noqa: FBT001  # pyright: ignore[reportIncompatibleMethodOverride]
        self._editable = state
        super().setEditable(state)

    def lineEdit(self) -> QLineEdit:
        line_edit: QLineEdit | None = super().lineEdit()
        if line_edit is None:
            line_edit = QLineEdit(self)
            self.setLineEdit(line_edit)
        line_edit.setReadOnly(not self._editable)
        if not self._editable:
            line_edit.mousePressEvent = lambda *args: self.hidePopup() if self.is_popped_up else self.showPopup()  # type: ignore[attr-value]
        else:
            line_edit.mousePressEvent = lambda *args: QLineEdit.mousePressEvent(line_edit, *args)  # type: ignore[attr-value]
        line_edit.home(False)
        return line_edit

    def setModel(
        self,
        model: QStringListModel | QStandardItemModel,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        assert isinstance(model, (QStringListModel, QStandardItemModel))
        self.proxy_model.setSourceModel(model)
        self.source_model: QStringListModel | QStandardItemModel = model

    def keyPressEvent(
        self,
        event: QKeyEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: ARG002
        if self.is_popped_up:
            self.filter_line_edit.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def set_combo_box_text(
        self,
        text: str,
        *,
        alwaysOnTop: bool = True,  # Recommended
    ):
        index = self.findText(text, Qt.MatchFlag.MatchCaseSensitive)
        if alwaysOnTop:
            if index != -1:  # Text found
                self.removeItem(index)
            new_index = 0
            self.insertItem(new_index, text)
        elif index == -1:  # Text not found
            self.addItem(text)
            new_index = self.findText(text)
        self.setCurrentIndex(new_index)
        line_edit: QLineEdit = self.lineEdit()
        if line_edit is not None:
            line_edit.setText(text)
        else:
            self.setCurrentText(text)

    def showPopup(self):
        self.orig_text = self.currentText()
        if not self.items_loaded and self.items:
            if isinstance(self.source_model, QStringListModel):
                self.source_model.setStringList(self.items)
            elif isinstance(self.source_model, QStandardItemModel):
                self.source_model.clear()
                for item in self.items:
                    self.source_model.appendRow(QStandardItem(item))
            self.set_combo_box_text(self.orig_text)
            self.items_loaded = True

        self.old_width: int = self.width()
        max_width: int = self.old_width
        delegate: QAbstractItemDelegate | None = self.itemDelegate()
        if delegate is None:
            return
        max_items_to_measure: int = 1000
        model: QAbstractItemModel | None = self.model()
        if model is None:
            return
        for i in range(min(model.rowCount(), max_items_to_measure)):
            item_width: int = delegate.sizeHint(QStyleOptionViewItem(), model.index(i, 0)).width()
            max_width = max(item_width, max_width)
        adjusted_width: int = max_width
        self.resize(adjusted_width, self.height())
        self.filter_line_edit.setFixedWidth(adjusted_width)
        self.filter_line_edit.adjustSize()
        self.filter_line_edit.setParent(self.view())
        self.filter_line_edit.move(0, 0)
        self.filter_line_edit.show()
        self.filter_line_edit.setFocus()
        super().showPopup()
        self.resize(self.old_width, self.height())
        self.is_popped_up = True
        self.filter_line_edit.setFocus()
        view: QAbstractItemView | None = self.view()
        if view is not None:
            view.repaint()

    def hidePopup(self):
        if self.force_stay_popped_up:
            self.force_stay_popped_up = False
            return
        super().hidePopup()
        self.is_popped_up = False
        self.resize(self.old_width, self.height())

    def populate_combo_box(
        self,
        items: Sequence[str],
    ):
        self.items = list(items)
        self.items_loaded = False

    def filter_items(
        self,
        text: str,
    ):
        self.proxy_model.setFilterText(text)

    def set_button_delegate(
        self,
        button_text: str,
        button_callback: Callable[[str], Any],
    ):
        listview: QAbstractItemView | None = self.view()
        if not isinstance(listview, CustomListView):
            return
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
        self.combo_box: FilterComboBox = FilterComboBox()
        self.combo_box.populate_combo_box([f"Item {i}" for i in range(10)])
        layout.addWidget(self.combo_box)

        # Set the layout for the central widget
        central_widget.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
