from __future__ import annotations

import sys

from typing import TYPE_CHECKING

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget
from playpazaak import CardType, PazaakGame, PazaakInterface, PazaakSideCard

if TYPE_CHECKING:
    from playpazaak import Player


class CardWidget(QLabel):
    def __init__(self, card, parent=None):
        super().__init__(parent)
        self.card = card
        self.setFixedSize(80, 120)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent;")
        self.update_display()

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)

    def update_display(self):
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw card background with gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(240, 240, 240))
        gradient.setColorAt(1, QColor(220, 220, 220))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        # Draw card border
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 9, 9)

        # Draw card text
        if isinstance(self.card, PazaakSideCard):
            text = str(self.card)
            color = "blue" if self.card.card_type in [CardType.POSITIVE, CardType.POS_OR_NEG] else "red"
        else:
            text = str(self.card)
            color = "black"

        painter.setFont(QFont("Arial", 18, QFont.Bold))
        painter.setPen(QColor(color))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        self.setPixmap(pixmap)

class PlayerHandWidget(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.update_display()

    def update_display(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)
        
        for card in self.player.hand:
            self.layout.addWidget(CardWidget(card))

class SideDeckWidget(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.update_display()

    def update_display(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)
        
        for card in self.player.active_side_hand:
            self.layout.addWidget(CardWidget(card))

class GameBoardWidget(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.player_hand = PlayerHandWidget(self.game.player)
        self.ai_hand = PlayerHandWidget(self.game.ai)
        self.player_side_deck = SideDeckWidget(self.game.player)
        self.ai_side_deck = SideDeckWidget(self.game.ai)

        self.ai_score_label = QLabel("AI Score: 0")
        self.player_score_label = QLabel("Player Score: 0")
        self.game_log = QTextEdit()

        self.layout.addWidget(QLabel("AI Hand:"), 0, 0)
        self.layout.addWidget(self.ai_hand, 1, 0)
        self.layout.addWidget(QLabel("AI Side Deck:"), 2, 0)
        self.layout.addWidget(self.ai_side_deck, 3, 0)
        self.layout.addWidget(self.ai_score_label, 4, 0)

        self.layout.addWidget(self.game_log, 5, 0)

        self.layout.addWidget(self.player_score_label, 6, 0)
        self.layout.addWidget(QLabel("Player Side Deck:"), 7, 0)
        self.layout.addWidget(self.player_side_deck, 8, 0)
        self.layout.addWidget(QLabel("Player Hand:"), 9, 0)
        self.layout.addWidget(self.player_hand, 10, 0)

        self.game_log.setReadOnly(True)
        self.setStyleSheet("""
            QLabel { font-weight: bold; }
            QWidget { background-color: #f0f0f0; }
        """)

    def update_scores(self):
        self.ai_score_label.setText(f"AI Score: {self.game.ai.score}")
        self.player_score_label.setText(f"Player Score: {self.game.player.score}")

    def update_display(self):
        self.player_hand.update_display()
        self.ai_hand.update_display()
        self.player_side_deck.update_display()
        self.ai_side_deck.update_display()
        self.update_scores()

    def log_action(self, message):
        self.game_log.append(message)

class PazaakMainWindow(QMainWindow, PazaakInterface):
    def __init__(self):
        super().__init__()
        self.game = PazaakGame()
        self.sound_enabled = True
        self.setup_ui()
        self.setup_sounds()

    def setup_sounds(self):
        self.sounds = {
            "card_draw": QSound("path/to/card_draw.wav"),
            "round_end": QSound("path/to/round_end.wav"),
        }

    def setup_ui(self):
        self.setWindowTitle("Pazaak")
        self.setGeometry(100, 100, 800, 700)
        self.setStyleSheet("background-color: #e0e0e0;")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.game_board = GameBoardWidget(self.game)
        main_layout.addWidget(self.game_board)

        self.info_label = QLabel("Welcome to Pazaak!")
        self.info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_label, alignment=Qt.AlignCenter)

        button_layout = QHBoxLayout()
        self.hit_button = QPushButton("Hit")
        self.stand_button = QPushButton("Stand")
        self.end_turn_button = QPushButton("End Turn")
        self.use_side_card_button = QPushButton("Use Side Card")
        
        self.hit_button.setToolTip("Draw a card from the main deck")
        self.stand_button.setToolTip("End your turn and keep your current score")
        self.end_turn_button.setToolTip("End your turn without standing")
        self.use_side_card_button.setToolTip("Play a card from your side deck")

        button_layout.addWidget(self.hit_button)
        button_layout.addWidget(self.stand_button)
        button_layout.addWidget(self.end_turn_button)
        button_layout.addWidget(self.use_side_card_button)

        main_layout.addLayout(button_layout)

        self.hit_button.clicked.connect(self.hit)
        self.stand_button.clicked.connect(self.stand)
        self.end_turn_button.clicked.connect(self.end_turn)
        self.use_side_card_button.clicked.connect(self.use_side_card)

        # Add sound toggle button
        self.sound_toggle_button = QPushButton("🔊")
        self.sound_toggle_button.setToolTip("Toggle sound effects")
        self.sound_toggle_button.clicked.connect(self.toggle_sound)
        button_layout.addWidget(self.sound_toggle_button)

        self.setStyleSheet(self.styleSheet() + """
            QPushButton { background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
        """)
    def setup_game(self):
        self.game.setup_game()
        self.update_display()
        self.info_label.setText("Game setup complete. Player's turn.")

    def play_turn(self, player: Player):
        self.info_label.setText(f"{player.name}'s turn")
        self.update_display()

        if player == self.game.ai:
            QTimer.singleShot(1000, self.ai_turn)

    def play_sound(self, sound_type):
        if self.sound_enabled:
            if sound_type in self.sounds:
                self.sounds[sound_type].play()

    def hit(self):
        if self.game.current_player == self.game.player and not self.game.player.stands:
            main_card = self.game.draw_card()
            self.game.play_card(self.game.player, main_card)
            self.update_display()
            self.check_bust()
            self.play_sound("card_draw")
            self.game_board.log_action(f"Player drew {main_card}")
        else:
            self.show_error("You cannot hit at this time.")

    def stand(self):
        if self.game.current_player == self.game.player and not self.game.player.stands:
            self.game.player.stands = True
            self.info_label.setText("Player stands. AI's turn.")
            self.game.switch_player()
            self.play_turn(self.game.current_player)
            self.play_sound("stand")
            self.game_board.log_action("Player stands")
        else:
            self.show_error("You cannot stand at this time.")

    def end_turn(self):
        if self.game.current_player == self.game.player and not self.game.player.stands:
            self.game.switch_player()
            self.play_turn(self.game.current_player)
            self.game_board.log_action("Player ends turn")
        else:
            self.show_error("You cannot end your turn at this time.")
    def use_side_card(self):
        if self.game.current_player == self.game.player and self.game.player.active_side_hand:
            # For simplicity, we'll just use the first side card
            side_card = self.game.player.active_side_hand.pop(0)
            if side_card.card_type == CardType.YELLOW_SPECIAL:
                self.game.apply_yellow_card_effect(self.game.player, side_card)
            else:
                self.game.play_card(self.game.player, side_card)
            self.update_display()
            self.check_bust()
            self.play_sound("side_card")
            self.game_board.log_action(f"Player used side card: {side_card}")
        else:
            self.show_error("You cannot use a side card at this time.")


    def ai_turn(self):
        main_card = self.game.draw_card()
        self.game.play_card(self.game.ai, main_card)
        self.update_display()
        self.game_board.log_action(f"AI drew {main_card}")

        if self.game.ai.is_bust():
            self.end_round(self.game.player)
            self.play_sound("bust")
            return

        action, side_card = self.game.ai_strategy()
        if action == "stand":
            self.game.ai.stands = True
            self.info_label.setText("AI stands. Player's turn.")
            self.game.switch_player()
            self.game_board.log_action("AI stands")
        elif action == "use_side_card":
            self.game.ai.active_side_hand.remove(side_card)
            if side_card.card_type == CardType.YELLOW_SPECIAL:
                self.game.apply_yellow_card_effect(self.game.ai, side_card)
            else:
                self.game.play_card(self.game.ai, side_card)
            self.update_display()
            self.play_sound("side_card")
            self.game_board.log_action(f"AI used side card: {side_card}")
        else:
            self.info_label.setText("AI ends its turn. Player's turn.")
            self.game.switch_player()
            self.game_board.log_action("AI ends turn")

        self.play_turn(self.game.current_player)

    def check_bust(self):
        if self.game.current_player.is_bust():
            winner = self.game.ai if self.game.current_player == self.game.player else self.game.player
            self.end_round(winner)
            self.play_sound("bust")
        elif self.game.current_player.calculate_hand_value() == 20:
            self.stand()
            self.play_sound("perfect_score")

    def end_round(self, winner: Player):
        self.game.update_score(winner)
        if winner:
            self.info_label.setText(f"{winner.name} wins this round!")
        else:
            self.info_label.setText("This round is a tie!")
        self.play_sound("round_end")
        self.game_board.log_action(f"Round ended. {winner.name if winner else 'Tie'}")

        QTimer.singleShot(2000, self.start_new_round)

    def start_new_round(self):
        if not self.game.winner:
            self.game.reset_round()
            self.update_display()
            self.info_label.setText("New round started. Player's turn.")
            self.game_board.log_action("New round started")
        else:
            self.end_game(self.game.winner)

    def end_game(self, winner: Player):
        message = f"Game over! {winner.name} wins the game!\n\nFinal Score:\nPlayer: {self.game.player.score}\nAI: {self.game.ai.score}"
        QMessageBox.information(self, "Game Over", message)
        self.ask_play_again()
        self.play_sound("game_over")

    def ask_play_again(self):
        reply = QMessageBox.question(self, "Play Again", "Do you want to play another game?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.game = PazaakGame()
            self.setup_game()
        else:
            self.close()

    def update_display(self):
        self.game_board.update_display()
        self.info_label.setText(f"Player: {self.game.player.calculate_hand_value()} | AI: {self.game.ai.calculate_hand_value()}")

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.sound_toggle_button.setText("🔊")
        else:
            self.sound_toggle_button.setText("🔇")

def main():
    app = QApplication(sys.argv)
    window = PazaakMainWindow()
    window.show()
    window.setup_game()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()