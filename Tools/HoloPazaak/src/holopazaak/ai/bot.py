from __future__ import annotations

from holopazaak.data.opponents import OpponentProfile
from holopazaak.game.card import Card, CardType
from holopazaak.game.engine import PazaakGame
from holopazaak.game.player import Player


class AIPlayer(Player):
    def __init__(self, profile: OpponentProfile):
        super().__init__(profile.name, is_ai=True)
        self.profile: OpponentProfile = profile
        self.sideboard: list[Card] = []
        self.setup_deck()

    def setup_deck(self):
        self.sideboard.clear()
        for val, ctype in self.profile.sideboard:
            # Ensure correct value sign based on type
            actual_val = val
            if ctype == CardType.MINUS:
                actual_val = -abs(val)
            elif ctype == CardType.PLUS:
                actual_val = abs(val)
            # For FLIP, we keep absolute value as magnitude, 
            # display_value logic handles sign based on flip state.
            
            self.sideboard.append(Card(f"{val}", actual_val, ctype))
        
        # Ensure we have enough cards (10)
        while len(self.sideboard) < 10:
            self.sideboard.append(Card("+1", 1, CardType.PLUS))

    def decide_move(self, game: PazaakGame) -> tuple[str, int | None]:
        """
        Returns ('play_card', index), ('stand', None), or ('end_turn', None)
        """
        current_score = self.score
        opponent_score = game.player.score
        opponent_standing = game.player.is_standing
        
        # Check if busted
        if current_score > 20:
            # Try to save with minus card
            best_card_idx = -1
            best_score = current_score
            
            for i, card in enumerate(self.hand):
                if card.card_type in (CardType.MINUS, CardType.FLIP):
                    # For FLIP cards, ensure we use the negative value when busted
                    if card.card_type == CardType.FLIP:
                        # If not already flipped to negative, calculate negative value
                        if not card.is_flipped:
                            val = -abs(card.value)
                        else:
                            val = card.display_value
                    else:
                        # MINUS cards are already negative
                        val = card.display_value
                    
                    new_score = current_score + val
                    
                    # If using FLIP as positive would work better, try that
                    if card.card_type == CardType.FLIP and card.is_flipped:
                        # Card is currently negative, check if positive would be better
                        positive_score = current_score + abs(card.value)
                        if positive_score <= 20 and positive_score < new_score:
                            # Positive would still be under 20 but gets us closer
                            # However, we're busted, so negative is required
                            pass  # Keep using negative
                    
                    if new_score <= 20:
                        if new_score > best_score or best_score > 20:
                            best_score = new_score
                            best_card_idx = i
            
            if best_card_idx != -1:
                return ("play_card", best_card_idx)
            else:
                return ("stand", None) # Bust, so forced stand/loss

        # If score is exactly 20, Stand
        if current_score == 20:
            return ("stand", None)

        # Check winning hand cards
        # If playing a card gets us to 20, do it
        for i, card in enumerate(self.hand):
            val = card.display_value
            if card.card_type == CardType.FLIP:
                # Check both + and -
                if current_score + abs(card.value) == 20:
                     if card.is_flipped:
                         card.flip() # Ensure +
                     return ("play_card", i)
                if current_score - abs(card.value) == 20:
                     if not card.is_flipped:
                         card.flip() # Ensure -
                     return ("play_card", i)
            else:
                if current_score + val == 20:
                    return ("play_card", i)

        # Strategy when Opponent is Standing
        if opponent_standing:
            if current_score > opponent_score:
                return ("stand", None)  # Win
            elif current_score == opponent_score:
                # Tie logic
                if current_score >= 19:  # Tie at 19/20 is acceptable
                    return ("stand", None)
                # Try to beat the tie by playing a card
                for i, card in enumerate(self.hand):
                    val = card.display_value
                    if card.card_type == CardType.FLIP:
                        # Check if positive value beats opponent
                        if current_score + abs(card.value) > opponent_score and current_score + abs(card.value) <= 20:
                            if card.is_flipped:
                                card.flip()  # Ensure positive
                            return ("play_card", i)
                        # Check if negative value still beats (shouldn't happen but handle it)
                        if current_score + val > opponent_score and current_score + val <= 20:
                            return ("play_card", i)
                    else:
                        new_score = current_score + val
                        if new_score > opponent_score and new_score <= 20:
                            return ("play_card", i)
                # Cannot beat the tie, stand and accept tie
                return ("stand", None)
            
            # Try to find card to beat opponent
            for i, card in enumerate(self.hand):
                val = card.display_value
                # Simplified: Just check if playing card beats opponent and <= 20
                # (Need robust FLIP handling here too)
                new_score = current_score + val
                if new_score > opponent_score and new_score <= 20:
                    return ("play_card", i)
            
            # If we can't beat them with hand, and score is low, End Turn (Hit)
            # If score is high but losing, might be forced to hit anyway
            return ("end_turn", None)

        # Strategy when Opponent is NOT Standing
        if current_score >= self.profile.stand_at:
             return ("stand", None)
        
        # Check if playing a card reaches stand threshold?
        # Usually AI saves cards until necessary. 
        # "pazaak-eggborne" suggests holding unless it makes 20 or beats standing opponent
        
        return ("end_turn", None)
