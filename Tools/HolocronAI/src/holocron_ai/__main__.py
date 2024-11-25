from __future__ import annotations

import sys

from pathlib import Path
from typing import TYPE_CHECKING, Any

from holocron_ai.character_system import CharacterSystem

if TYPE_CHECKING:
    from typing import NoReturn


def display_metrics(
    metrics: dict[str, float],
) -> None:
    """Display evaluation metrics in a readable format."""
    print("\nResponse Metrics:")
    print("-" * 40)
    for metric, value in metrics.items():
        print(f"{metric.title()}: {value:.2f}")
    print("-" * 40)


def main() -> NoReturn:
    """Main entry point for HolocronAI character system."""
    print("Initializing HolocronAI Character System...")

    # Initialize system
    data_dir = Path("data")
    save_dir = Path("save")
    system = CharacterSystem(data_dir)

    try:
        # Try to load existing state
        if save_dir.exists():
            loaded_system: CharacterSystem | None = CharacterSystem.load_state(data_dir, save_dir)
            if loaded_system is not None:
                system: CharacterSystem = loaded_system
                print("Loaded existing state.")
            else:
                system.initialize()
                print("Failed to load state, initialized new system.")
        else:
            system.initialize()
            print("Initialized new system.")

        # Get available characters
        characters: list[str] = system.get_available_characters()
        if not characters:
            print("No characters available.")
            sys.exit(1)

        # Display character selection
        print("\nAvailable Characters:")
        for i, char in enumerate(characters, 1):
            print(f"{i}. {char}")

        # Select character
        while True:
            try:
                choice = int(input("\nSelect a character (number): "))
                if 1 <= choice <= len(characters):
                    selected: str = characters[choice - 1]
                    if system.set_character(selected):
                        print(f"\nSelected character: {selected}")
                        break
                print("Invalid selection, please try again.")
            except ValueError:
                print("Please enter a valid number.")

        # Main interaction loop
        context: list[dict[str, Any]] = []
        print("\nStart chatting with your character! (type 'quit' to exit)")

        while True:
            try:
                # Get user input
                user_input: str = input("\nYou: ").strip()
                if user_input.lower() in ("quit", "exit"):
                    break

                # Generate response
                response, metrics = system.generate_response(user_input, context)

                if response:
                    print(f"\nCharacter: {response}")
                    if metrics:
                        display_metrics(metrics)

                    # Update context
                    context.append({"role": "user", "content": user_input})
                    context.append({"role": "assistant", "content": response})

                    # Keep context window manageable
                    if len(context) > 10:  # noqa: PLR2004
                        context = context[-10:]
                else:
                    print("\nNo appropriate response generated.")

            except KeyboardInterrupt:
                break
            except Exception as e:  # noqa: BLE001
                print(f"\nError: {e}")

        # Save final state
        print("\nSaving state...")
        save_dir.mkdir(exist_ok=True)
        system.save_state(save_dir)
        print("Done. Thank you for using HolocronAI!")

    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
