from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from qtpy.QtWidgets import QApplication, QPushButton, QTableWidget, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu


class RobustTableWidget(QTableWidget, RobustTableView):
    """A table widget that supports common features and settings."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        QTableWidget.__init__(self, parent)
        RobustTableView.__init__(self, parent)

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = super().build_context_menu(parent)

        # Table-specific actions
        table_widget_menu = menu.addMenu("TableWidget")

        # Table-specific advanced actions
        advanced_menu = table_widget_menu.addMenu("Advanced")

        # Item manipulation actions
        item_menu = table_widget_menu.addMenu("Item Actions")

        return menu


if __name__ == "__main__":

    class SimpleTableModel(QAbstractTableModel):
        def __init__(self, data: list[list[str]]):
            super().__init__()
            self._data: list[list[str]] = data

        def rowCount(self, parent: QModelIndex | None = None) -> int:
            return len(self._data)

        def columnCount(self, parent: QModelIndex | None = None) -> int:
            return len(self._data[0]) if self._data else 0

        def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> str | None:
            if role == Qt.ItemDataRole.DisplayRole:
                return self._data[index.row()][index.column()]
            return None

        def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> str | None:
            if role == Qt.ItemDataRole.DisplayRole:
                if orientation == Qt.Orientation.Horizontal:
                    return f"Column {section + 1}"
                return f"Row {section + 1}"
            return None

        def add_row(self, row_data: list[str]):
            self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
            self._data.append(row_data)
            self.endInsertRows()

        def remove_last_row(self):
            if self._data:
                self.beginRemoveRows(QModelIndex(), len(self._data) - 1, len(self._data) - 1)
                self._data.pop()
                self.endRemoveRows()

    app = QApplication([])

    # Create the main window
    main_window = QWidget()
    layout = QVBoxLayout(main_window)

    # Create and set up the RobustTableView
    table_view = RobustTableView()
    layout.addWidget(table_view)

    # Create a simple model with some example data
    data = [
        ["Apple", "Red", "Sweet"],
        ["Banana", "Yellow", "Sweet"],
        ["Lemon", "Yellow", "Sour"],
    ]
    model = SimpleTableModel(data)
    table_view.setModel(model)

    # Ensure the header is visible
    table_view.horizontalHeader().setVisible(True)
    table_view.verticalHeader().setVisible(True)

    # Add buttons to add and remove rows
    add_button = QPushButton("Add Row")
    remove_button = QPushButton("Remove Last Row")
    layout.addWidget(add_button)
    layout.addWidget(remove_button)

    def add_row():
        model.add_row(["New Item", "Color", "Taste"])
        table_view.update_columns_after_text_size_change()

    def remove_row():
        model.remove_last_row()
        table_view.update_columns_after_text_size_change()

    add_button.clicked.connect(add_row)
    remove_button.clicked.connect(remove_row)

    # Show the main window
    main_window.resize(400, 300)
    main_window.show()

    app.exec_()
