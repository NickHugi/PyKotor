from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget


class HelpDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("How to Play HoloPazaak")
        self.resize(500, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        title = QLabel("HoloPazaak Rules")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        content_layout.addWidget(title)
        
        rules = """
        <h2>Objective</h2>
        <p>The goal is to have the sum of your cards be as close to 20 as possible without exceeding it.</p>
        <p>To win a match, you must win 3 sets.</p>
        
        <h2>Gameplay</h2>
        <ol>
            <li>Each turn, a card from the Main Deck (1-10) is automatically played to your board.</li>
            <li>You then have four options:
                <ul>
                    <li><b>Play a Side Card:</b> Play one card from your hand to modify your score.</li>
                    <li><b>Stand:</b> End your turn for the round. Your score is locked.</li>
                    <li><b>End Turn:</b> Pass the turn to the opponent without standing.</li>
                </ul>
            </li>
            <li>You can only play <b>one</b> side card per turn.</li>
            <li>If your score exceeds 20 at the end of your turn, you <b>BUST</b> and lose the set (unless the opponent also busts or ties).</li>
            <li>If you fill your board (9 cards) without busting, you automatically win the set.</li>
        </ol>
        
        <h2>Card Types</h2>
        <ul>
            <li><b>Main Cards (Green):</b> Values +1 to +10. Drawn automatically.</li>
            <li><b>Plus Cards (Blue):</b> Add to your score.</li>
            <li><b>Minus Cards (Red):</b> Subtract from your score.</li>
            <li><b>Flip Cards (Yellow):</b> Can be positive or negative. They flip the sign of their value.</li>
        </ul>
        
        <h2>Controls</h2>
        <ul>
            <li><b>Space:</b> End Turn</li>
            <li><b>S:</b> Stand</li>
            <li><b>1-4:</b> Play Hand Card</li>
        </ul>
        """
        
        lbl_rules = QLabel(rules)
        lbl_rules.setWordWrap(True)
        lbl_rules.setTextFormat(Qt.RichText)
        content_layout.addWidget(lbl_rules)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

