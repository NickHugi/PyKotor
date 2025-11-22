from __future__ import annotations

import random

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from holopazaak.game.card import Card, CardType


class SideDeckCardWidget(QFrame):
    clicked = Signal(int)
    
    def __init__(
        self,
        card: Card,
        index: int,
        is_selected: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.card: Card = card
        self.index: int = index
        self.is_selected: bool = is_selected
        self.setFixedSize(80, 120)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        
        layout = QVBoxLayout()
        self.label: QLabel = QLabel(str(card))
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 16, QFont.Bold)
        self.label.setFont(font)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.update_style()
    
    def update_style(self):
        color = "#FFFFFF"
        if self.card.card_type == CardType.PLUS:
            color = "#AAAAFF"  # Blueish
        elif self.card.card_type == CardType.MINUS:
            color = "#FFAAAA"  # Redish
        elif self.card.card_type == CardType.FLIP:
            color = "#FFFFAA"  # Yellowish
        
        if self.is_selected:
            self.setStyleSheet(f"background-color: {color}; border: 3px solid #00FF00; border-radius: 5px;")
        else:
            self.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()
    
    def mousePressEvent(self, event):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.clicked.emit(self.index)


class SideDeckSelectionDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.selected_cards: list[Card] = []
        self.all_cards: list[Card] = []
        self.selected_indices: set[int] = set()
        self.setWindowTitle("Select Your Side Deck")
        self.setMinimumSize(900, 700)
        self.setup_ui()
        self.generate_available_cards()
    
    def generate_available_cards(self):
        """Generate all available side deck cards based on playpazaak.py logic"""
        self.all_cards = []
        
        # Flip cards (1-6)
        for val in range(1, 7):
            self.all_cards.append(Card(f"±{val}", val, CardType.FLIP))
        
        # Plus cards (1-6)
        for val in range(1, 7):
            self.all_cards.append(Card(f"+{val}", val, CardType.PLUS))
        
        # Minus cards (1-6)
        for val in range(1, 7):
            self.all_cards.append(Card(f"-{val}", val, CardType.MINUS))
        
        # Shuffle for variety
        random.shuffle(self.all_cards)
        self.update_card_display()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Select 10 cards for your side deck. Click cards to select/deselect.")
        instructions.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(instructions)
        
        # Selected count
        self.selected_label = QLabel("Selected: 0 / 10")
        self.selected_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.selected_label)
        
        # Card grid container with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.card_container_widget = QWidget()
        self.grid_layout = QGridLayout(self.card_container_widget)
        self.card_widgets: list[SideDeckCardWidget] = []
        
        scroll_area.setWidget(self.card_container_widget)
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_random = QPushButton("Random Deck")
        self.btn_random.clicked.connect(self.random_deck)
        button_layout.addWidget(self.btn_random)
        
        self.btn_clear = QPushButton("Clear Selection")
        self.btn_clear.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.btn_clear)
        
        button_layout.addStretch()
        
        self.btn_confirm = QPushButton("Confirm (10 cards required)")
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_confirm)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def update_card_display(self):
        # Clear existing widgets
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
        
        self.card_widgets.clear()
        
        # Add all cards
        for idx, card in enumerate(self.all_cards):
            is_selected = idx in self.selected_indices
            widget = SideDeckCardWidget(card, idx, is_selected)
            widget.clicked.connect(self.toggle_card_selection)
            self.card_widgets.append(widget)
            
            row = idx // 10  # 10 cards per row
            col = idx % 10
            self.grid_layout.addWidget(widget, row, col)
        
        self.update_selected_count()
    
    def toggle_card_selection(self, index: int):
        if index in self.selected_indices:
            self.selected_indices.remove(index)
        else:
            if len(self.selected_indices) >= 10:
                return  # Already at max
            self.selected_indices.add(index)
        
        # Update widget
        if 0 <= index < len(self.card_widgets):
            self.card_widgets[index].set_selected(index in self.selected_indices)
        
        self.update_selected_count()
    
    def update_selected_count(self):
        count = len(self.selected_indices)
        self.selected_label.setText(f"Selected: {count} / 10")
        self.btn_confirm.setEnabled(count == 10)
        self.btn_confirm.setText(f"Confirm ({count}/10)" if count < 10 else "Confirm and Start Game")
    
    def random_deck(self):
        """Select 10 random cards"""
        self.selected_indices = set(random.sample(range(len(self.all_cards)), 10))
        self.update_card_display()
    
    def clear_selection(self):
        """Clear all selections"""
        self.selected_indices.clear()
        self.update_card_display()
    
    def get_selected_deck(self) -> list[Card]:
        """Return the selected cards as a list"""
        return [self.all_cards[idx] for idx in sorted(self.selected_indices)]

