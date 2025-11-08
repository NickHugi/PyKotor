from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

from holocron_ai.core.dialog_processor import DialogProcessor
from holocron_ai.core.self_alignment import SelfAlignmentProcessor

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.extract.installation import Installation


class CharacterAgent:
    """Dynamic character response agent using self-alignment and dialog embeddings."""

    def __init__(
        self,
        installation: Installation,
        save_dir: Path | None = None,
    ):
        self.dialog_processor: DialogProcessor = DialogProcessor(installation)
        self.alignment_processor: SelfAlignmentProcessor = SelfAlignmentProcessor()
        self.conversation_history: list[tuple[str, str]] = []  # (speaker, text)
        self.context_window: int = 5

        # Load existing state if provided
        if save_dir:
            self.load_state(installation, save_dir)
        else:
            # Process installation dialogs
            self.dialog_processor.process_installation()
            # Initial self-alignment processing
            self._align_processed_dialogs()

    def _align_processed_dialogs(self) -> None:
        """Process all extracted dialogs through self-alignment."""
        dialog_sequence: list[str] = self.dialog_processor.dialog_sequence
        if not dialog_sequence:
            return

        self.alignment_processor.process_dialog_sequence(dialog_sequence)

    def _get_recent_context(self) -> list[str]:
        """Get recent conversation context."""
        return [text for _, text in self.conversation_history[-self.context_window :]]

    def generate_response(
        self,
        query: str,
    ) -> str | None:
        """Generate a contextually appropriate character response."""
        # Get recent context
        recent_context: list[str] = self._get_recent_context()

        # Find aligned response using both processors
        aligned_response, alignment_score = self.alignment_processor.find_aligned_response(query, recent_context)

        if aligned_response and alignment_score > 0.8:
            # High confidence in aligned response
            response = aligned_response
        else:
            # Fallback to contextual response
            response: str | None = self.dialog_processor.get_contextual_response(query, len(recent_context))

        if response:
            # Update conversation history
            self.conversation_history.append(("user", query))
            self.conversation_history.append(("character", response))

            # Keep history within context window
            if len(self.conversation_history) > self.context_window * 2:
                self.conversation_history = self.conversation_history[-self.context_window * 2 :]

        return response

    def save_state(
        self,
        save_dir: Path,
    ) -> None:
        """Save agent state to disk."""
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save processor states
        self.dialog_processor.save_state(save_dir)
        self.alignment_processor.save_state(save_dir)

        # Save conversation history
        state: dict[str, Any] = {"conversation_history": self.conversation_history, "context_window": self.context_window}

        with save_dir.joinpath("agent_state.json").open("w") as f:
            json.dump(state, f)

    @classmethod
    def load_state(
        cls,
        installation: Installation,
        save_dir: Path,
    ) -> Self:
        """Load agent state from disk."""
        instance: Self = cls(installation, None)  # Initialize without processing

        # Load processor states
        instance.dialog_processor = DialogProcessor.load_state(installation, save_dir)
        instance.alignment_processor = SelfAlignmentProcessor.load_state(save_dir)

        # Load conversation history
        state: dict[str, Any] = json.loads(save_dir.joinpath("agent_state.json").read_bytes())

        instance.conversation_history = state["conversation_history"]
        instance.context_window = state["context_window"]

        return instance

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation_history.clear()
