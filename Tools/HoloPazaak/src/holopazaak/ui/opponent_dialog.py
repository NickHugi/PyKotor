from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from holopazaak.data.opponents import OPPONENTS, OpponentProfile


class OpponentSelectionDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Select Opponent")
        self.setMinimumSize(400, 300)
        self.selected_opponent: OpponentProfile | None = None
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        label = QLabel("Choose your opponent:")
        layout.addWidget(label)
        
        self.list_widget = QListWidget()
        for opp in OPPONENTS:
            item = QListWidgetItem(f"{opp.name}")
            item.setData(Qt.UserRole, opp.id)
            item.setToolTip(opp.description)
            self.list_widget.addItem(item)
            
        self.list_widget.currentItemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)
        
        self.description_label = QLabel("Description will appear here.")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("font-style: italic; color: #AAA;")
        layout.addWidget(self.description_label)
        
        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("Select")
        self.btn_select.setEnabled(False)
        self.btn_select.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_select)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # Select first by default
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            
    def on_selection_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None):
        if current:
            opp_id = current.data(Qt.UserRole)
            # Find profile
            for opp in OPPONENTS:
                if opp.id == opp_id:
                    self.description_label.setText(opp.description)
                    self.selected_opponent = opp
                    self.btn_select.setEnabled(True)
                    break
        else:
            self.description_label.setText("")
            self.selected_opponent = None
            self.btn_select.setEnabled(False)

    def get_selected_opponent(self) -> OpponentProfile | None:
        return self.selected_opponent

