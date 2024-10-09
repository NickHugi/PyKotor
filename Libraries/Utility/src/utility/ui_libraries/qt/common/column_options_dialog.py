from __future__ import annotations

from loggerplus import RobustLogger
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout


class SetDefaultColumnsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Default Columns")
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout(self)

        # Folder type selection
        folder_type_layout = QHBoxLayout()
        folder_type_layout.addWidget(QLabel("Folder type:"))
        self.folder_type_combo = QComboBox()
        self.folder_type_combo.addItem("General")
        folder_type_layout.addWidget(self.folder_type_combo)
        layout.addLayout(folder_type_layout)

        # Columns list
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.populate_columns()
        layout.addWidget(self.columns_list)

        # Move buttons
        move_buttons_layout = QVBoxLayout()
        self.move_up_button = QPushButton("Move Up")
        self.move_down_button = QPushButton("Move Down")
        move_buttons_layout.addWidget(self.move_up_button)
        move_buttons_layout.addWidget(self.move_down_button)
        move_buttons_layout.addStretch()

        columns_layout = QHBoxLayout()
        columns_layout.addWidget(self.columns_list)
        columns_layout.addLayout(move_buttons_layout)
        layout.addLayout(columns_layout)

        # Description
        self.description_label = QLabel("Description: File name")
        layout.addWidget(self.description_label)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Connect signals
        self.move_up_button.clicked.connect(self.move_item_up)
        self.move_down_button.clicked.connect(self.move_item_down)
        self.columns_list.itemSelectionChanged.connect(self.update_description)

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
            item = QListWidgetItem(column, self.columns_list, Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.columns_list.addItem(item)

    def move_item_up(self):
        current_row = self.columns_list.currentRow()
        if current_row <= 0:
            RobustLogger().warning(f"Current row {current_row} is less than or equal to 0")
            return
        item: QListWidgetItem | None = self.columns_list.takeItem(current_row)
        if item is None:
            RobustLogger().warning(f"Item at row {current_row} is None")
            return
        self.columns_list.insertItem(current_row - 1, item)
        self.columns_list.setCurrentRow(current_row - 1)

    def move_item_down(self):
        current_row = self.columns_list.currentRow()
        if current_row >= self.columns_list.count() - 1:
            RobustLogger().warning(f"Current row {current_row} is greater than or equal to {self.columns_list.count() - 1}")
            return
        item: QListWidgetItem | None = self.columns_list.takeItem(current_row)
        if item is None:
            RobustLogger().warning(f"Item at row {current_row} is None")
            return
        self.columns_list.insertItem(current_row + 1, item)
        self.columns_list.setCurrentRow(current_row + 1)

    def update_description(self):
        selected_items = self.columns_list.selectedItems()
        if selected_items:
            self.description_label.setText(f"Description: {selected_items[0].text()}")
        else:
            self.description_label.setText("Description: ")

    def get_selected_columns(self) -> list[str]:
        return [
            item.text()
            for item in (
                self.columns_list.item(i)
                for i in range(self.columns_list.count())
            )
            if item is not None
            and item.checkState() == Qt.CheckState.Checked
        ]
