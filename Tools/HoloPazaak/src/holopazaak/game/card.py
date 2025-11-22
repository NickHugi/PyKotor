from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    MAIN = "main"
    PLUS = "plus"
    MINUS = "minus"
    FLIP = "flip" # +/- card
    DOUBLE = "double" # Special card (optional, maybe later)
    TIEBREAKER = "tiebreaker" # Special card (optional)

@dataclass
class Card:
    name: str
    value: int
    card_type: CardType
    is_flipped: bool = False # For FLIP cards, if they are currently negative

    @property
    def display_value(self) -> int:
        if self.card_type == CardType.FLIP:
            return -abs(self.value) if self.is_flipped else abs(self.value)
        return self.value

    def flip(self):
        if self.card_type == CardType.FLIP:
            self.is_flipped = not self.is_flipped

    def __str__(self):
        val_str = str(abs(self.value))
        if self.card_type == CardType.PLUS:
            return f"+{val_str}"
        elif self.card_type == CardType.MINUS:
            return f"-{val_str}"
        elif self.card_type == CardType.FLIP:
            return f"±{val_str}"
        return val_str

