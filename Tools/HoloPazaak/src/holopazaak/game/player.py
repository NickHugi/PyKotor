from __future__ import annotations

import random

from typing import List

from holopazaak.game.card import Card


class Player:
    def __init__(self, name: str, is_ai: bool = False):
        self.name = name
        self.is_ai = is_ai
        self.hand: List[Card] = []
        self.board: List[Card] = []
        self.sideboard: List[Card] = [] # The 10 cards selected for the match
        self.sets_won: int = 0
        self.is_standing: bool = False
        
    @property
    def score(self) -> int:
        return sum(c.display_value for c in self.board)

    @property
    def is_bust(self) -> bool:
        return self.score > 20

    @property
    def is_full(self) -> bool:
        return len(self.board) >= 9

    def reset_round(self):
        self.board = []
        self.is_standing = False
        # Redraw hand from sideboard for new round
        if self.sideboard:
            self.draw_hand_from_sideboard()

    def reset_game(self):
        self.sets_won = 0
        self.hand = []
        self.reset_round()  # This will draw the initial hand

    def draw_hand_from_sideboard(self):
        if len(self.sideboard) >= 4:
            self.hand = random.sample(self.sideboard, min(4, len(self.sideboard)))
        else:
            self.hand = list(self.sideboard)  # Use all if less than 4

    def add_card_to_board(self, card: Card):
        self.board.append(card)

    def play_card_from_hand(self, index: int):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            self.add_card_to_board(card)
            return card
        return None

