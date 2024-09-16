from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

class CardType:
    POSITIVE = "+"
    NEGATIVE = "-"
    POS_OR_NEG = "+/-"
    YELLOW_SPECIAL = "Yellow"

@dataclass
class PazaakSideCard:
    value: int | List[int]
    card_type: CardType

    def __str__(self) -> str:
        if self.card_type == CardType.YELLOW_SPECIAL:
            return f"Yellow {self.value}"
        return f"{self.card_type.value.replace('+', f'+{self.value}').replace('-', f'-{self.value}')}"

    def get_value(self, choice: Optional[str] = None) -> int:
        if self.card_type == CardType.POSITIVE:
            return self.value
        elif self.card_type == CardType.NEGATIVE:
            return -self.value
        elif self.card_type == CardType.POS_OR_NEG:
            return self.value if choice == "+" else -self.value
        elif self.card_type == CardType.YELLOW_SPECIAL:
            return self.value[0]  # Return the first value for yellow cards
        else:
            raise ValueError(f"Unknown card_type {self.card_type!r}")

@dataclass
class Player:
    name: str
    hand: List[int | PazaakSideCard] = field(default_factory=list)
    side_deck: List[PazaakSideCard] = field(default_factory=list)
    active_side_hand: List[PazaakSideCard] = field(default_factory=list)
    score: int = 0
    stands: bool = False

    def calculate_hand_value(self) -> int:
        return sum(card.get_value() if isinstance(card, PazaakSideCard) else card for card in self.hand)

    def is_bust(self) -> bool:
        return self.calculate_hand_value() > 20

    def reset_hand(self):
        self.hand.clear()
        self.stands = False

class PazaakGame:
    MAIN_DECK_VALUES: List[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    MAX_HAND_VALUE: int = 20
    SETS_TO_WIN: int = 3

    def __init__(self):
        self.deck = self.create_deck()
        self.player = Player("Player")
        self.ai = Player("AI")
        self.current_player = self.player
        self.winner = None

    def create_deck(self) -> List[int]:
        deck: List[int] = []
        for card in self.MAIN_DECK_VALUES:
            deck.extend(card for _ in range(4))
        random.shuffle(deck)
        return deck

    def setup_game(self):
        self.player.side_deck = self.choose_side_deck()
        self.ai.side_deck = self.auto_choose_side_deck()
        self.reset_round()

    def reset_round(self):
        self.deck = self.create_deck()
        self.player.reset_hand()
        self.ai.reset_hand()
        self.player.active_side_hand = random.sample(self.player.side_deck, 4)
        self.ai.active_side_hand = random.sample(self.ai.side_deck, 4)
        self.current_player = self.player
        self.winner = None

    def choose_side_deck(self) -> List[PazaakSideCard]:
        side_deck = [
            PazaakSideCard(1, CardType.POS_OR_NEG),
            PazaakSideCard(2, CardType.POS_OR_NEG),
            PazaakSideCard(3, CardType.POS_OR_NEG),
            PazaakSideCard(4, CardType.POS_OR_NEG),
            PazaakSideCard(5, CardType.POS_OR_NEG),
            PazaakSideCard(6, CardType.POS_OR_NEG),
            PazaakSideCard(1, CardType.POSITIVE),
            PazaakSideCard(2, CardType.POSITIVE),
            PazaakSideCard(3, CardType.POSITIVE),
            PazaakSideCard(4, CardType.POSITIVE),
            PazaakSideCard(5, CardType.POSITIVE),
            PazaakSideCard(6, CardType.POSITIVE),
            PazaakSideCard(1, CardType.NEGATIVE),
            PazaakSideCard(2, CardType.NEGATIVE),
            PazaakSideCard(3, CardType.NEGATIVE),
            PazaakSideCard(4, CardType.NEGATIVE),
            PazaakSideCard(5, CardType.NEGATIVE),
            PazaakSideCard(6, CardType.NEGATIVE),
            PazaakSideCard([3, 6], CardType.YELLOW_SPECIAL),
        ]
        return random.sample(side_deck, 10)

    def auto_choose_side_deck(self) -> List[PazaakSideCard]:
        return self.choose_side_deck()

    def draw_card(self) -> int:
        return self.deck.pop()

    def play_card(self, player: Player, card: int | PazaakSideCard):
        player.hand.append(card)

    def apply_yellow_card_effect(self, player: Player, yellow_card: PazaakSideCard):
        for i, card in enumerate(player.hand):
            if isinstance(card, PazaakSideCard) and card.card_type == CardType.POSITIVE and card.value in yellow_card.value:
                player.hand[i] = PazaakSideCard(card.value, CardType.NEGATIVE)
            elif isinstance(card, int) and card in yellow_card.value:
                player.hand[i] = PazaakSideCard(card.value, CardType.NEGATIVE)

    def switch_player(self):
        self.current_player = self.ai if self.current_player == self.player else self.player

    def check_winner(self) -> Optional[Player]:
        if self.player.is_bust():
            return self.ai
        elif self.ai.is_bust():
            return self.player
        elif self.player.stands and self.ai.stands:
            player_value = self.player.calculate_hand_value()
            ai_value = self.ai.calculate_hand_value()
            if player_value > ai_value:
                return self.player
            elif ai_value > player_value:
                return self.ai
            else:
                return None  # Tie
        return None

    def update_score(self, winner: Optional[Player]):
        if winner:
            winner.score += 1
        if winner and winner.score >= self.SETS_TO_WIN:
            self.winner = winner

    def ai_strategy(self) -> Tuple[str, Optional[PazaakSideCard]]:
        ai_value = self.ai.calculate_hand_value()
        player_value = self.player.calculate_hand_value()
        best_choice = None
        min_value_diff = float("inf")

        for side_card in self.ai.active_side_hand:
            if side_card.card_type == CardType.YELLOW_SPECIAL:
                simulated_hand = self.ai.hand.copy()
                self.apply_yellow_card_effect(Player("Simulated", simulated_hand), side_card)
                simulated_value = sum(card.get_value() if isinstance(card, PazaakSideCard) else card for card in simulated_hand)
            else:
                simulated_value = ai_value + side_card.get_value()

            value_diff = self.MAX_HAND_VALUE - simulated_value
            if 0 <= value_diff < min_value_diff:
                best_choice = (side_card, simulated_value)
                min_value_diff = value_diff

        if best_choice:
            side_card, new_value = best_choice
            if new_value == self.MAX_HAND_VALUE or (ai_value < player_value and new_value > ai_value):
                return "use_side_card", side_card

        if ai_value >= 17 and ai_value >= player_value:
            return "stand", None
        return "hit", None

class PazaakInterface(ABC):
    @abstractmethod
    def setup_game(self):
        pass

    @abstractmethod
    def play_turn(self, player: Player):
        pass

    @abstractmethod
    def end_round(self, winner: Optional[Player]):
        pass

    @abstractmethod
    def end_game(self, winner: Player):
        pass

class ConsolePazaak(PazaakInterface):
    def __init__(self):
        self.game = PazaakGame()

    def setup_game(self):
        self.game.setup_game()
        print("Game setup complete. Let's begin!")
        self.print_scores()

    def play_turn(self, player: Player):
        print(f"\n{player.name}'s turn:")
        self.print_hand(player)

        if player == self.game.player:
            self.player_turn()
        else:
            self.ai_turn()

    def player_turn(self):
        main_card = self.game.draw_card()
        self.game.play_card(self.game.player, main_card)
        print(f"You drew a {main_card} from the main deck.")
        self.print_hand(self.game.player)

        if self.game.player.is_bust():
            print("You went bust!")
            return

        while True:
            action = input("Do you want to hit (h), stand (s), end turn (e), or use a side card (u)? ").lower()
            if action == 's':
                self.game.player.stands = True
                print("You chose to stand.")
                break
            elif action == 'h':
                print("You chose to hit.")
                break
            elif action == 'e':
                print("You chose to end your turn.")
                break
            elif action == 'u':
                if self.game.player.active_side_hand:
                    self.use_side_card(self.game.player)
                    if self.game.player.is_bust():
                        print("You went bust!")
                        return
                else:
                    print("No side cards left.")
            else:
                print("Invalid input. Please enter 'h' for hit, 's' for stand, 'e' for end turn, or 'u' for using a side card.")

    def ai_turn(self):
        main_card = self.game.draw_card()
        self.game.play_card(self.game.ai, main_card)
        print(f"AI drew a {main_card} from the main deck.")
        self.print_hand(self.game.ai)

        if self.game.ai.is_bust():
            print("AI went bust!")
            return

        action, side_card = self.game.ai_strategy()
        if action == "stand":
            self.game.ai.stands = True
            print("AI chose to stand.")
        elif action == "hit":
            print("AI chose to hit.")
        elif action == "use_side_card":
            self.game.ai.active_side_hand.remove(side_card)
            if side_card.card_type == CardType.YELLOW_SPECIAL:
                self.game.apply_yellow_card_effect(self.game.ai, side_card)
                print(f"AI used yellow card: {side_card}")
            else:
                self.game.play_card(self.game.ai, side_card)
                print(f"AI used side card: {side_card}")
            self.print_hand(self.game.ai)
        else:
            print("AI ended its turn.")

    def use_side_card(self, player: Player):
        print("Your side cards:")
        for i, card in enumerate(player.active_side_hand, 1):
            print(f"{i}. {card}")

        try:
            choice = int(input("Choose a side card to use (1-4): ")) - 1
            if 0 <= choice < len(player.active_side_hand):
                chosen_card = player.active_side_hand.pop(choice)
                if chosen_card.card_type == CardType.YELLOW_SPECIAL:
                    self.game.apply_yellow_card_effect(player, chosen_card)
                    print(f"You used yellow card: {chosen_card}")
                else:
                    self.game.play_card(player, chosen_card)
                    print(f"You used: {chosen_card}")
                self.print_hand(player)
            else:
                print("Invalid choice. Please choose a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def print_hand(self, player: Player):
        hand_str = ", ".join(str(card) for card in player.hand)
        print(f"{player.name}'s hand: {hand_str} (Total: {player.calculate_hand_value()})")

    def print_scores(self):
        print(f"Current score - Player: {self.game.player.score}, AI: {self.game.ai.score}")

    def end_round(self, winner: Optional[Player]):
        if winner:
            print(f"\n{winner.name} wins this round!")
        else:
            print("\nThis round is a tie!")
        self.print_scores()

    def end_game(self, winner: Player):
        print(f"\nGame over! {winner.name} wins the game!")
        self.print_scores()

    def play_game(self):
        self.setup_game()
        while not self.game.winner:
            round_winner = None
            while round_winner is None:
                self.play_turn(self.game.current_player)
                round_winner = self.game.check_winner()
                if round_winner is None:
                    self.game.switch_player()

            self.game.update_score(round_winner)
            self.end_round(round_winner)

            if not self.game.winner:
                input("Press Enter to start the next round...")
                self.game.reset_round()
                print("\nNew round started!")

        self.end_game(self.game.winner)

def print_game_rules():
    print("""
Pazaak Game Rules:
1. The goal is to reach exactly 20 points or get as close as possible without going over.
2. Players take turns drawing cards from the main deck and optionally playing cards from their side deck.
3. Main deck cards are always positive values from 1 to 10.
4. Side deck cards can be positive, negative, or special cards.
5. Players can choose to "stand" (keep their current score) or continue playing.
6. If a player's score goes over 20, they "bust" and lose the round.
7. The first player to win 3 rounds wins the game.

Special Cards:
- +/- cards: Can be played as either positive or negative.
- Yellow cards: Can flip the sign of a card already on the table.

Good luck and have fun!
""")

if __name__ == "__main__":
    print("Welcome to Pazaak!")
    print_game_rules()
    play_again = True
    console_game = ConsolePazaak()
    while play_again:
        console_game.play_game()
        choice = input("Do you want to play again? (y/n): ").lower()
        if choice != 'y':
            play_again = False
        else:
            console_game = ConsolePazaak()
    print("Thanks for playing Pazaak!")
