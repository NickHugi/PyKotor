from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QTimer, Qt
from qtpy.QtWidgets import QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class SetDefaultColumnsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Set Default Columns")
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout(self)

        # Folder type selection
        folder_type_layout = QHBoxLayout()
        folder_type_layout.addWidget(QLabel("Folder type:"))
        self.folder_type_combo: QComboBox = QComboBox()
        self.folder_type_combo.addItem("General")
        folder_type_layout.addWidget(self.folder_type_combo)
        layout.addLayout(folder_type_layout)

        # Columns list
        self.columns_list: QListWidget = QListWidget()
        self.columns_list.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.columns_list.setAcceptDrops(True)
        self.columns_list.setDragEnabled(True)
        self.columns_list.setDropIndicatorShown(True)
        self.columns_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.populate_columns()
        layout.addWidget(self.columns_list)

        # Description
        self.description_label: QLabel = QLabel("Description: File name")
        layout.addWidget(self.description_label)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Connect signals
        self.columns_list.itemClicked.connect(self.update_description)

    def populate_columns(self):
        columns = [
            "Name", "Type", "Size", "Date Modified", "Attributes", "Size On Disk",
            "8.3 Name", "Owner", "Product Name", "Company", "Description", "File Version",
            "Product Version", "Shortcut to", "Hard links", "Extension", "Date Created",
            "Date Accessed", "Title", "Subject", "Authors", "Keywords", "Comment",
            "Camera Model", "Date Taken", "Width", "Height", "Bit rate", "Copyright",
            "Duration", "Protected", "Rating", "Album artist", "Album", "Beats-per-minute",
            "Composer", "Conductor", "Director", "Genre", "Language", "Broadcast date",
            "Channel", "Station name", "Mood", "Parental rating", "Parental rating reason",
            "Period", "Producer"
        ]
        for column in columns:
            item = QListWidgetItem(column, self.columns_list, QListWidgetItem.ItemType.UserType)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsDragEnabled)
            self.columns_list.addItem(item)

    def update_description(self, item: QListWidgetItem):
        self.description_label.setText(f"Description: {item.text()}")

    def get_selected_columns(self) -> list[str]:
        selected_columns: list[str] = []
        for i in range(self.columns_list.count()):
            item: QListWidgetItem | None = self.columns_list.item(i)
            if (
                item is not None
                and item.checkState() == Qt.CheckState.Checked
            ):
                selected_columns.append(item.text())
        return selected_columns

if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = SetDefaultColumnsDialog()
    def on_accepted(*args, **kwargs):
        selected_columns = dialog.get_selected_columns()
        print("Selected columns:", selected_columns)
        QTimer.singleShot(0, app.quit)
    dialog.accepted.connect(on_accepted)
    dialog.show()
    sys.exit(app.exec())
