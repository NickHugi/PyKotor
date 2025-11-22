from __future__ import annotations

import random

from typing import List

from holopazaak.game.card import Card, CardType
from holopazaak.game.player import Player


class PazaakGame:
    WIN_SCORE = 20
    MAX_BOARD_SIZE = 9
    SETS_TO_WIN = 3

    def __init__(self, player: Player, opponent: Player):
        self.player = player
        self.opponent = opponent
        self.current_turn: Player = self.player # Randomize or set later
        self.winner: Player | None = None
        self.round_winner: Player | None = None
        self.is_round_over: bool = False
        self.is_game_over: bool = False
        self.turn_phase: str = "start" # start, action, end
        self.main_deck: List[Card] = []

    def draw_main_deck_card(self) -> Card:
        # Standard Pazaak main deck is random 1-10
        val = random.randint(1, 10)
        return Card(f"Main {val}", val, CardType.MAIN)

    def start_game(self):
        self.player.reset_game()
        self.opponent.reset_game()
        self.start_round()

    def start_round(self):
        self.player.reset_round()
        self.opponent.reset_round()
        self.is_round_over = False
        self.round_winner = None
        # Winner of previous set goes first, or default to player
        self.current_turn = self.player 
        self.start_turn()

    def start_turn(self):
        if self.is_round_over:
            return

        active_player = self.current_turn
        
        # If active player is standing, they cannot take a turn.
        # Logic in end_turn should prevent switching TO a standing player unless both are standing (which ends round).
        if active_player.is_standing:
            self.resolve_round() # Should have been caught, but safety check
            return

        # Draw card automatically at start of turn
        card = self.draw_main_deck_card()
        active_player.add_card_to_board(card)
        
        # Check for immediate bust
        # In Pazaak, you draw, THEN you can play a card to fix it.
        # So we don't end immediately on 21+. We wait for action phase.
        
        # Auto-stand on natural 20? 
        # Usually not forced, but smart. We leave it to player/AI.
        
        self.turn_phase = "action"
        
        # If board is full (9 cards), usually forced to stand or auto-win?
        # KOTOR: If you fill the board without busting, you win the set automatically.
        if active_player.is_full and not active_player.is_bust:
            # Instant win condition
            self.round_winner = active_player
            self.resolve_round()

    def play_hand_card(self, player: Player, card_index: int):
        if self.turn_phase != "action" or self.current_turn != player:
            return False
        
        # One card per turn limit
        # We need to track if card played this turn.
        # Using turn_phase="end" to signify "Action taken, can now only Stand or End Turn" 
        # is slightly wrong because you can Play Card AND THEN Stand.
        # But you CANNOT Play Card AND THEN Play Another Card.
        
        card = player.play_card_from_hand(card_index)
        if card:
            self.turn_phase = "played_card" # State change to prevent second card
            return True
        return False

    def stand(self, player: Player):
        if self.current_turn != player:
            return
        player.is_standing = True
        self.end_turn()

    def end_turn(self):
        # Player chose to end turn (pass to opponent) OR Stood
        
        # Check Bust Condition now (after potential hand card played)
        if self.current_turn.is_bust:
            # If bust, you lose round immediately.
            # Opponent wins.
            self.round_winner = self.opponent if self.current_turn == self.player else self.player
            self.resolve_round()
            return

        # Check Full Board Condition (if not bust)
        if self.current_turn.is_full:
             self.round_winner = self.current_turn
             self.resolve_round()
             return

        # Switch Turn Logic
        next_player = self.opponent if self.current_turn == self.player else self.player
        
        if self.player.is_standing and self.opponent.is_standing:
            self.resolve_round()
            return

        # If current player stood, we switch to next.
        # If next player is standing, we stay on current player (if they didn't stand).
        # If current player stood AND next player is standing -> handled above.
        
        if self.current_turn.is_standing:
            self.current_turn = next_player
        elif next_player.is_standing:
            self.current_turn = self.current_turn # Stay on current
        else:
            self.current_turn = next_player # Standard switch

        self.turn_phase = "start"
        self.start_turn()

    def resolve_round(self):
        if self.is_round_over:
            return # Already resolved
        self.is_round_over = True
        
        # If round_winner already determined (by bust or full board), skip scoring
        if not self.round_winner:
            p_score = self.player.score
            o_score = self.opponent.score
            
            # Both standing.
            if p_score > o_score:
                self.round_winner = self.player
            elif o_score > p_score:
                self.round_winner = self.opponent
            else:
                self.round_winner = None # Tie
        
        if self.round_winner:
            self.round_winner.sets_won += 1
            
        # Check game over
        if self.player.sets_won >= self.SETS_TO_WIN:
            self.winner = self.player
            self.is_game_over = True
        elif self.opponent.sets_won >= self.SETS_TO_WIN:
            self.winner = self.opponent
            self.is_game_over = True

