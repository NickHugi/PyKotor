from __future__ import annotations

import random

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Literal


# Define card types
class CardType(Enum):
    POSITIVE = "+"
    NEGATIVE = "-"
    POS_OR_NEG = "+/-"
    YELLOW_SPECIAL = "Yellow"


# Define the Pazaak side card class
class PazaakSideCard:
    def __init__(
        self,
        value: int | list[int],
        card_type: CardType,
    ):
        if card_type == CardType.YELLOW_SPECIAL and not isinstance(value, list):
            raise ValueError("Yellow card value must be a list of numbers.")
        self.value: int | list[int] = value
        self.card_type: CardType = card_type

    def __str__(self) -> str:
        if self.card_type == CardType.YELLOW_SPECIAL:
            return f"Yellow {self.value}"
        return f"{self.card_type.value.replace('+', f'+{self.value}').replace('-', f'-{self.value}')}"

    def choose_value(self) -> int:
        if self.card_type == CardType.POS_OR_NEG:
            while True:
                choice = input(f"Do you want to use {self.value} as + or -? (+/-): ").strip()
                if choice == "+":
                    return self.value
                if choice == "-":
                    return -self.value
                print("Invalid choice. Please enter + or -.")
        elif self.card_type == CardType.POSITIVE:
            return self.value
        elif self.card_type == CardType.NEGATIVE:
            return -self.value
        raise ValueError(f"Unknown card_type {self.card_type!r}")


# Define the values of the cards
MAIN_DECK_VALUES: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

  # For this implementation, its assumed everyone has 10 of every single side card.
SIDE_DECK = [
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
    PazaakSideCard([3, 6], CardType.YELLOW_SPECIAL),  # TODO(th3w1zard1): add more yellow cards
]

MAX_HAND_VALUE: Literal[20] = 20


# Function to create a deck of cards
def create_deck() -> list[int]:
    deck: list[int] = []
    for card in MAIN_DECK_VALUES:
        deck.extend(card for _ in range(4))
    random.shuffle(deck)
    return deck


# Function to choose side deck
def choose_side_deck() -> list[PazaakSideCard]:
    selected_cards: list[PazaakSideCard] = []
    available_cards: list[PazaakSideCard] = SIDE_DECK[:]  # Create a copy of SIDE_DECK to manage availability

    print("Please choose 10 side cards from the following list by entering their indices:")

    # Function to print the current selection and available cards
    def print_selections():
        print("\nAvailable cards:")
        for index, card in enumerate(available_cards, 1):
            print(f"{index}. {card}")
        print("\nCurrently selected cards:")
        for i, card in enumerate(selected_cards, 1):
            print(f"{i}. {card}")

    # Main loop to choose cards
    while len(selected_cards) < 10:
        print_selections()
        print(f"\nYou have {10 - len(selected_cards)} choices left.")

        try:
            choice = int(input("Enter the index of the card you want to add to your side deck: ")) - 1
            if 0 <= choice < len(available_cards):
                selected_cards.append(available_cards[choice])
            else:
                print("Invalid index. Please choose a valid number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    return selected_cards


# Function to get active side deck
def get_active_side_deck(full_side_deck: list[PazaakSideCard]) -> list[PazaakSideCard]:
    return random.sample(full_side_deck, 5)


# Function to calculate the value of a hand
def calculate_hand_value(hand: list[int | PazaakSideCard]) -> int:
    return sum((card.choose_value() if isinstance(card, PazaakSideCard) else card) for card in hand)


# Function to apply yellow card effect
def apply_yellow_card_effect(
    hand: list[int | PazaakSideCard],
    yellow_card: PazaakSideCard,
) -> list[PazaakSideCard | int]:
    for i, card in enumerate(hand):
        if isinstance(card, PazaakSideCard) and card.card_type is CardType.POSITIVE and card.value in yellow_card.value:
            hand[i] = PazaakSideCard(card.value, CardType.NEGATIVE)
        elif isinstance(card, int) and card in yellow_card.value:
            hand[i] = PazaakSideCard(card.value, CardType.NEGATIVE)
    return hand


# Function to print the hand
def print_hand(name: str, hand: list[int | PazaakSideCard]):
    hand_values = [str(card) for card in hand]
    print(f"{name}'s hand: {', '.join(hand_values)} (total: {calculate_hand_value(hand)})")


# Function to check if the hand is a bust
def is_bust(hand: list[int | PazaakSideCard]) -> bool:
    return calculate_hand_value(hand) > MAX_HAND_VALUE


# AI's strategy function
def ai_strategy(
    ai_hand: list[PazaakSideCard | int],
    player_hand: list[PazaakSideCard | int],
    ai_side_hand: list[PazaakSideCard],
) -> Literal["stand", "hit"]:
    ai_value = calculate_hand_value(ai_hand)
    player_value = calculate_hand_value(player_hand)
    best_choice = None
    min_value_diff = float("inf")

    for side_card in ai_side_hand:
        if side_card.card_type == CardType.YELLOW_SPECIAL:
            simulated_hand = apply_yellow_card_effect(ai_hand, side_card)
            simulated_value = calculate_hand_value(simulated_hand)
            value_diff = MAX_HAND_VALUE - simulated_value

            if simulated_value <= MAX_HAND_VALUE and value_diff < min_value_diff:
                best_choice = (side_card, simulated_value)
                min_value_diff = value_diff

        else:
            potential_values = [side_card.value] if side_card.card_type != CardType.POS_OR_NEG else [side_card.value, -side_card.value]
            for value in potential_values:
                simulated_value = ai_value + value
                value_diff = MAX_HAND_VALUE - simulated_value

                if simulated_value <= MAX_HAND_VALUE and value_diff < min_value_diff:
                    best_choice = (side_card, simulated_value)
                    min_value_diff = value_diff

    if best_choice is None:
        print("AI did not use a side card for this turn.")
    else:
        side_card, new_value = best_choice
        if new_value == MAX_HAND_VALUE or (ai_value < player_value and new_value > ai_value):
            ai_side_hand.remove(side_card)
            if side_card.card_type == CardType.YELLOW_SPECIAL:
                ai_hand[:] = apply_yellow_card_effect(ai_hand, side_card)  # Apply yellow effect
            else:
                ai_hand.append(side_card)
            print(f"AI uses {side_card} resulting in new hand value of {new_value}.")
            return "stand" if new_value == MAX_HAND_VALUE else "hit"

    stand_minimum = 17
    return "stand" if ai_value >= stand_minimum and ai_value >= player_value else "hit"


# Main game function
def play_pazaak():
    deck = create_deck()

    # Initial hands
    player_hand: list[int | PazaakSideCard] = []
    ai_hand: list[int | PazaakSideCard] = []

    player_side_deck: list[PazaakSideCard] = choose_side_deck()
    ai_side_deck: list[PazaakSideCard] = choose_side_deck()  # TODO(th3w1zard1): allow ai to auto-choose side deck.

    # for each player, randomly choose 5 out of the 10 chosen side cards
    player_active_side_hand: list[PazaakSideCard] = get_active_side_deck(player_side_deck)
    ai_active_side_hand: list[PazaakSideCard] = get_active_side_deck(ai_side_deck)

    player_stands = False
    ai_stands = False

    # Game loop
    while not player_stands or not ai_stands:
        print_hand("Player", player_hand)
        print_hand("AI", ai_hand)
        if not player_stands:
            # Player's turn
            while True:
                main_card_popped = deck.pop()
                player_hand.append(main_card_popped)
                print(f"Player: Card hit from main deck: {main_card_popped}, bringing their total to {calculate_hand_value(player_hand)}")
                print_hand("Player", player_hand)
                if is_bust(player_hand):
                    print("Player busts! AI wins!")
                    return
                action = input("Do you want to stand, or use a side card? (s/u): ").lower()
                if action == "s":
                    player_stands = True
                    break
                if action == "u":
                    if player_active_side_hand:
                        print("Your side cards: " + ", ".join(map(str, player_active_side_hand)))
                        side_card_index = int(input("Choose a side card to use (1-5): ")) - 1
                        if 0 <= side_card_index < len(player_active_side_hand):
                            chosen_card = player_active_side_hand.pop(side_card_index)
                            if chosen_card.card_type == CardType.YELLOW_SPECIAL:
                                player_hand = apply_yellow_card_effect(player_hand, chosen_card)
                            else:
                                player_hand.append(chosen_card)
                            print_hand("Player", player_hand)
                            if is_bust(player_hand):
                                print("Player busts! AI wins!")
                                return
                            break
                        print("Invalid choice. Choose a number between 1 and 5.")
                    else:
                        print("No side cards left.")
                    continue
                print("Invalid input, please enter 'h' for hit, 's' for stand, or 'u' for using a side card.")

        # AI Turn
        main_card_popped = deck.pop()
        ai_hand.append(main_card_popped)
        print(f"AI: Card hit from main deck: {main_card_popped}, bringing their total to {calculate_hand_value(ai_hand)}")
        print_hand("AI", ai_hand)
        ai_strategy(ai_hand, player_hand, ai_active_side_hand)
        if is_bust(ai_hand):
            print("AI busts! Player wins!")
            return
        if action == "stand":
            print("AI chose to Stand")

    # Final hands
    print_hand("Player", player_hand)
    print_hand("AI", ai_hand)

    # Determine the winner
    player_value = calculate_hand_value(player_hand)
    ai_value = calculate_hand_value(ai_hand)

    if player_value > ai_value:
        print("Player wins!")
    elif ai_value > player_value:
        print("AI wins!")
    else:
        print("It's a tie!")


# Start the game
if __name__ == "__main__":
    play_pazaak()
