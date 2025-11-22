from __future__ import annotations

from qtpy.QtCore import QSettings, QTimer, Qt, Signal
from qtpy.QtGui import QFont, QKeySequence
from qtpy.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QShortcut,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from holopazaak.ai.bot import AIPlayer
from holopazaak.data.opponents import get_opponent
from holopazaak.game.card import Card, CardType
from holopazaak.game.engine import PazaakGame
from holopazaak.game.player import Player
from holopazaak.ui.help_dialog import HelpDialog
from holopazaak.ui.opponent_dialog import OpponentSelectionDialog
from holopazaak.ui.sidedeck_dialog import SideDeckSelectionDialog
from holopazaak.ui.sound import SoundManager
from holopazaak.ui.styles import Theme, get_stylesheet


class CardWidget(QFrame):
    clicked: Signal = Signal(int)

    def __init__(
        self,
        card: Card,
        index: int,
        theme: dict[str, str],
        is_opponent: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.card: Card = card
        self.index: int = index
        self.theme = theme
        self.is_opponent: bool = is_opponent
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

    def set_theme(self, theme: dict[str, str]):
        self.theme = theme
        self.update_style()

    def update_style(self):
        color = "#FFFFFF"
        border_color = "#000000"
        
        if self.card.card_type == CardType.MAIN:
            color = self.theme.get("card_main", "#D0F0C0")
            border_color = "#2E8B57"
        elif self.card.card_type == CardType.PLUS:
            color = self.theme.get("card_plus", "#ADD8E6")
            border_color = "#00008B"
        elif self.card.card_type == CardType.MINUS:
            color = self.theme.get("card_minus", "#F08080")
            border_color = "#8B0000"
        elif self.card.card_type == CardType.FLIP:
            color = self.theme.get("card_flip", "#FFFFE0")
            border_color = "#DAA520"

        self.setStyleSheet(f"""
            background-color: {color}; 
            border: 2px solid {border_color}; 
            border-radius: 8px;
        """)
        
        # Update label color if needed
        if self.card.card_type == CardType.MINUS:
             self.label.setStyleSheet("color: #500000; font-weight: bold; border: none; background: transparent;")
        elif self.card.card_type == CardType.PLUS:
             self.label.setStyleSheet("color: #000050; font-weight: bold; border: none; background: transparent;")
        else:
             self.label.setStyleSheet("color: black; border: none; background: transparent;")

    def mousePressEvent(self, event):  # pyright: ignore[reportIncompatibleMethodOverride]
        if not self.is_opponent:
            self.clicked.emit(self.index)

class PazaakWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HoloPazaak")
        self.resize(1000, 800)
        
        self.settings = QSettings("PyKotor", "HoloPazaak")
        self.sound_manager = SoundManager()
        
        # Game Setup - will be initialized after side deck selection
        self.human: Player | None = None
        self.ai: AIPlayer | None = None
        self.game: PazaakGame | None = None
        self.ai_profile = get_opponent("standard")
        self.current_sideboard: list[Card] = []
        self.round_logged = False
        self.current_theme = Theme.REPUBLIC
        self.total_games = 0
        self.games_won = 0
        
        self.setup_ui()
        self.load_settings()
        self.show_side_deck_selection()

    def load_settings(self):
        auto_stand = self.settings.value("auto_stand", False, type=bool)
        self.auto_stand_checkbox.setChecked(auto_stand)
        
        # Load stats
        self.total_games = self.settings.value("total_games", 0, type=int)
        self.games_won = self.settings.value("games_won", 0, type=int)
        
        # Load theme
        theme_name = self.settings.value("theme", "Republic", type=str)
        if theme_name == "Sith":
            self.current_theme = Theme.SITH
        else:
            self.current_theme = Theme.REPUBLIC
        self.apply_theme()
        
    def save_settings(self):
        self.settings.setValue("auto_stand", self.auto_stand_checkbox.isChecked())
        self.settings.setValue("total_games", self.total_games)
        self.settings.setValue("games_won", self.games_won)
        self.settings.setValue("theme", self.current_theme["name"])

    def apply_theme(self):
        self.setStyleSheet(get_stylesheet(self.current_theme))
        # Update all existing card widgets
        self.update_ui()

    def toggle_theme(self):
        if self.current_theme["name"] == "Republic":
            self.current_theme = Theme.SITH
        else:
            self.current_theme = Theme.REPUBLIC
        self.apply_theme()
        self.log_message(f"Theme changed to {self.current_theme['name']}.")

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Opponent Area
        self.opp_info = QLabel("Opponent: ")
        main_layout.addWidget(self.opp_info)
        
        self.opp_hand_layout = QHBoxLayout()
        main_layout.addLayout(self.opp_hand_layout)
        
        self.opp_board_layout = QGridLayout()
        opp_board_frame = QFrame()
        opp_board_frame.setLayout(self.opp_board_layout)
        opp_board_frame.setStyleSheet("background-color: #333333; min-height: 200px;")
        main_layout.addWidget(opp_board_frame)

        self.opp_score_label = QLabel("Score: 0")
        main_layout.addWidget(self.opp_score_label)

        # Center Info
        self.center_label = QLabel("Select your side deck to begin")
        self.center_label.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 24, QFont.Bold)
        self.center_label.setFont(font)
        main_layout.addWidget(self.center_label)

        self.scoreboard_label = QLabel("Sets Won - You: 0 | Opponent: 0")
        self.scoreboard_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.scoreboard_label)

        # Player Area
        self.player_score_label = QLabel("Score: 0")
        main_layout.addWidget(self.player_score_label)

        self.player_board_layout = QGridLayout()
        player_board_frame = QFrame()
        player_board_frame.setLayout(self.player_board_layout)
        player_board_frame.setStyleSheet("background-color: #333333; min-height: 200px;")
        main_layout.addWidget(player_board_frame)

        self.player_hand_layout = QHBoxLayout()
        main_layout.addLayout(self.player_hand_layout)

        self.side_deck_label = QLabel("Side Deck: N/A")
        self.side_deck_label.setWordWrap(True)
        main_layout.addWidget(self.side_deck_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.document().setMaximumBlockCount(200)
        self.log_text.setFixedHeight(150)
        main_layout.addWidget(self.log_text)

        # Controls
        controls_layout = QHBoxLayout()
        self.btn_end_turn = QPushButton("End Turn (Space)")
        self.btn_end_turn.clicked.connect(self.on_end_turn)
        self.btn_end_turn.setEnabled(False)
        
        self.btn_stand = QPushButton("Stand (S)")
        self.btn_stand.clicked.connect(self.on_stand)
        self.btn_stand.setEnabled(False)
        
        controls_layout.addWidget(self.btn_end_turn)
        controls_layout.addWidget(self.btn_stand)

        self.auto_stand_checkbox = QCheckBox("Auto-stand at 20")
        controls_layout.addWidget(self.auto_stand_checkbox)

        self.btn_new_game = QPushButton("New Game")
        self.btn_new_game.clicked.connect(self.new_game_same_deck)
        controls_layout.addWidget(self.btn_new_game)

        self.btn_change_deck = QPushButton("Change Deck")
        self.btn_change_deck.clicked.connect(self.change_deck)
        controls_layout.addWidget(self.btn_change_deck)
        
        self.btn_change_opponent = QPushButton("Change Opponent")
        self.btn_change_opponent.clicked.connect(self.change_opponent)
        controls_layout.addWidget(self.btn_change_opponent)
        
        self.btn_theme = QPushButton("Theme")
        self.btn_theme.clicked.connect(self.toggle_theme)
        controls_layout.addWidget(self.btn_theme)
        
        self.btn_help = QPushButton("Help")
        self.btn_help.clicked.connect(self.show_help)
        controls_layout.addWidget(self.btn_help)

        main_layout.addLayout(controls_layout)
        
        # Shortcuts
        self.shortcut_end_turn = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.shortcut_end_turn.activated.connect(self.on_end_turn)
        
        self.shortcut_stand = QShortcut(QKeySequence(Qt.Key_S), self)
        self.shortcut_stand.activated.connect(self.on_stand)
        
        # Hand shortcuts 1-4
        for i in range(4):
            shortcut = QShortcut(QKeySequence(f"{i+1}"), self)
            shortcut.activated.connect(lambda i=i: self.on_hand_card_clicked(i))
    
    def keyPressEvent(self, event):
        # Fallback for simple keys if shortcuts don't catch
        if event.key() == Qt.Key_Space:
            if self.btn_end_turn.isEnabled():
                self.on_end_turn()
        elif event.key() == Qt.Key_S:
            if self.btn_stand.isEnabled():
                self.on_stand()
        elif Qt.Key_1 <= event.key() <= Qt.Key_4:
            idx = event.key() - Qt.Key_1
            self.on_hand_card_clicked(idx)
        else:
            super().keyPressEvent(event)
    
    def show_side_deck_selection(self, allow_cancel_exit: bool = True):
        """Show the side deck selection dialog"""
        dialog = SideDeckSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:  # type: ignore[attr-defined]
            selected_deck = dialog.get_selected_deck()
            self.start_game_with_deck(selected_deck)
        else:
            # User cancelled - could close app or show menu
            if allow_cancel_exit and not self.game:
                self.close()
    
    def start_game_with_deck(self, sideboard: list[Card]):
        """Initialize and start the game with the selected side deck"""
        self.current_sideboard = [Card(card.name, card.value, card.card_type) for card in sideboard]
        self.human = Player("Player")
        self.human.sideboard = [Card(card.name, card.value, card.card_type) for card in self.current_sideboard]
        
        self.ai = AIPlayer(self.ai_profile)
        
        self.game = PazaakGame(self.human, self.ai)
        self.round_logged = False
        
        # Update UI with opponent info
        self.opp_info.setText(f"Opponent: {self.ai.name}")
        self.side_deck_label.setText("Side Deck: " + ", ".join(str(card) for card in self.current_sideboard))
        self.log_text.clear()
        self.log_message("New game started! Good luck.")
        self.log_message(f"Opponent: {self.ai.name}")
        
        # Start the game (this will reset both players and draw hands)
        self.game.start_game()
        self.update_ui()

    def update_ui(self):
        if not self.game or not self.human or not self.ai:
            return
        
        # Update Opponent
        self.opp_score_label.setText(f"Score: {self.ai.score} {'(STANDING)' if self.ai.is_standing else ''}")
        self.clear_layout(self.opp_board_layout)
        for i, card in enumerate(self.ai.board):
            cw = CardWidget(card, i, self.current_theme, is_opponent=True)
            self.opp_board_layout.addWidget(cw, 0, i)
        
        # Opponent Hand (Hidden logic usually, but for debug/simplicity shown as backs or count)
        self.clear_layout(self.opp_hand_layout)
        for i in range(len(self.ai.hand)):
             lbl = QLabel("Card")
             lbl.setStyleSheet(f"background-color: gray; border: 1px solid black; padding: 5px; color: {self.current_theme['text']}")
             self.opp_hand_layout.addWidget(lbl)

        # Update Player
        self.player_score_label.setText(f"Score: {self.human.score} {'(STANDING)' if self.human.is_standing else ''}")
        self.clear_layout(self.player_board_layout)
        for i, card in enumerate(self.human.board):
            cw = CardWidget(card, i, self.current_theme, is_opponent=False)
            self.player_board_layout.addWidget(cw, 0, i)

        self.clear_layout(self.player_hand_layout)
        for i, card in enumerate(self.human.hand):
            cw = CardWidget(card, i, self.current_theme, is_opponent=False)
            cw.clicked.connect(self.on_hand_card_clicked)
            self.player_hand_layout.addWidget(cw)

        # Buttons
        can_act = (self.game.current_turn == self.human and 
                   not self.human.is_standing and 
                   not self.game.is_round_over)
        self.btn_end_turn.setEnabled(can_act)
        self.btn_stand.setEnabled(can_act)

        self.scoreboard_label.setText(f"Sets Won - You: {self.human.sets_won} | {self.ai.name}: {self.ai.sets_won}")

        if self.game.is_game_over and self.game.winner:
            self.center_label.setText(f"Game Over! Winner: {self.game.winner.name}")
            if not self.round_logged:
                self.total_games += 1
                if self.game.winner == self.human:
                    self.games_won += 1
                self.log_message(f"Match finished! {self.game.winner.name} won the game.")
                self.log_message(f"Lifetime Stats: Played {self.total_games}, Won {self.games_won}")
                self.round_logged = True
                self.sound_manager.play("game_over")
                self.save_settings()
        elif self.game.is_round_over:
            winner_name = self.game.round_winner.name if self.game.round_winner else "Draw"
            self.center_label.setText(f"Round Over! Winner: {winner_name}")
            if not self.round_logged:
                self.log_message(f"Round finished! Result: {winner_name}.")
                self.round_logged = True
                if self.game.round_winner == self.human:
                    self.sound_manager.play("win_round")
                elif self.game.round_winner == self.ai:
                    self.sound_manager.play("lose_round")
            QTimer.singleShot(2000, self.next_round)
        else:
            self.center_label.setText(f"Turn: {self.game.current_turn.name}")
            if self.game.current_turn == self.ai:
                QTimer.singleShot(1000, self.ai_turn)

        # Auto-stand check
        if (
            self.auto_stand_checkbox.isChecked()
            and self.game.current_turn == self.human
            and not self.human.is_standing
            and self.human.score >= self.game.WIN_SCORE
        ):
            self.log_message("Auto-stand activated at 20.")
            self.game.stand(self.human)
            self.sound_manager.play("stand")
            QTimer.singleShot(0, self.update_ui)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def on_end_turn(self):
        if self.game:
            if self.game.current_turn == self.human:
                self.log_message("You ended your turn.")
            self.game.end_turn()
            self.sound_manager.play("draw")
            self.update_ui()

    def on_stand(self):
        if self.game and self.human:
            self.log_message("You stand.")
            self.game.stand(self.human)
            self.sound_manager.play("stand")
            self.update_ui()

    def on_hand_card_clicked(self, index):
        if self.game and self.human:
            if 0 <= index < len(self.human.hand):
                card = self.human.hand[index]
            else:
                card = None
            if self.game.play_hand_card(self.human, index):
                if card:
                    self.log_message(f"You played side card {card}.")
                    self.sound_manager.play("play_card")
                self.update_ui()

    def ai_turn(self):
        if not self.game or not self.ai or self.game.is_round_over:
            return
        
        action, data = self.ai.decide_move(self.game)
        
        if action == "play_card" and data is not None:
            # Execute play card
            self.perform_ai_play_card(data)
            # Schedule next step (Check Stand/End) after delay
            QTimer.singleShot(1000, self.perform_ai_post_card_action)
        elif action == "stand":
            self.perform_ai_stand()
            self.update_ui()
        else:
            self.perform_ai_end_turn()
            self.update_ui()

    def perform_ai_play_card(self, data: int):
        if not self.game or not self.ai:
            return
        card_repr = None
        if 0 <= data < len(self.ai.hand):
            card_repr = str(self.ai.hand[data])
        self.game.play_hand_card(self.ai, data)
        if card_repr:
            self.log_message(f"{self.ai.name} played side card {card_repr}.")
            self.sound_manager.play("play_card")
        self.update_ui()

    def perform_ai_post_card_action(self):
        if not self.game or not self.ai:
            return
        # Re-evaluate? Usually play card -> check if 20 -> Stand.
        if self.ai.score == 20:
            self.perform_ai_stand()
        elif self.ai.score >= self.ai.profile.stand_at:
            self.perform_ai_stand()
        else:
            self.perform_ai_end_turn()
        self.update_ui()

    def perform_ai_stand(self):
        if not self.game or not self.ai:
            return
        self.log_message(f"{self.ai.name} stands.")
        self.game.stand(self.ai)
        self.sound_manager.play("stand")

    def perform_ai_end_turn(self):
        if not self.game or not self.ai:
            return
        self.log_message(f"{self.ai.name} ends their turn.")
        self.game.end_turn()
        self.sound_manager.play("draw")

    def next_round(self):
        if self.game and not self.game.is_game_over:
            self.game.start_round()
            self.round_logged = False
            self.log_message("Starting next round...")
            self.update_ui()

    def new_game_same_deck(self):
        if not self.current_sideboard:
            self.show_side_deck_selection()
            return
        # Fresh copy of the deck
        deck_copy = [Card(card.name, card.value, card.card_type) for card in self.current_sideboard]
        self.start_game_with_deck(deck_copy)

    def change_deck(self):
        self.show_side_deck_selection(allow_cancel_exit=False)

    def change_opponent(self):
        dialog = OpponentSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:  # type: ignore[attr-defined]
            profile = dialog.get_selected_opponent()
            if profile:
                self.ai_profile = profile
                self.log_message(f"Opponent changed to {self.ai_profile.name}. Starting new game...")
                self.new_game_same_deck()

    def log_message(self, message: str):
        self.log_text.append(message)

