from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

import numpy as np

from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]


class SelfAlignmentProcessor:
    """Dynamic self-alignment processor without hardcoded patterns."""

    def __init__(self):
        self.embedding_model: SentenceTransformer = SentenceTransformer("all-mpnet-base-v2")
        self.dialog_memory: list[tuple[str, np.ndarray]] = []
        self.context_memory: list[tuple[str, np.ndarray]] = []
        self.alignment_threshold: float = 0.75

    def process_dialog_sequence(
        self,
        dialogs: list[str],
        window_size: int = 5,
    ) -> list[np.ndarray]:
        """Process a sequence of dialogs to build contextual understanding."""
        embeddings: list[np.ndarray] = []

        for i, dialog in enumerate(dialogs):
            # Get surrounding context
            start_idx: int = max(0, i - window_size)
            end_idx: int = min(len(dialogs), i + window_size + 1)
            context: list[str] = dialogs[start_idx:i] + dialogs[i + 1 : end_idx]

            # Generate embeddings
            dialog_embedding: np.ndarray = self.embedding_model.encode(dialog)
            if context:
                context_embeddings: list[np.ndarray] = [self.embedding_model.encode(ctx) for ctx in context]
                context_embedding: np.ndarray = np.mean(context_embeddings, axis=0)
                # Dynamic weighting based on context relevance
                context_similarity: float = np.dot(dialog_embedding, context_embedding) / (np.linalg.norm(dialog_embedding) * np.linalg.norm(context_embedding))
                # Adjust weighting based on contextual relevance
                dialog_weight: float = 0.5 + (0.5 * (1 - context_similarity))
                combined_embedding: np.ndarray = dialog_weight * dialog_embedding + (1 - dialog_weight) * context_embedding
            else:
                combined_embedding = dialog_embedding

            embeddings.append(combined_embedding)
            self.dialog_memory.append((dialog, combined_embedding))

        return embeddings

    def find_aligned_response(
        self,
        query: str,
        recent_context: list[str],
    ) -> tuple[str | None, float]:
        """Find a self-aligned response based on query and context."""
        if not self.dialog_memory:
            return None, 0.0

        # Generate query embedding with context influence
        query_embedding: np.ndarray = self.embedding_model.encode(query)
        if recent_context:
            context_embeddings: list[np.ndarray] = [self.embedding_model.encode(ctx) for ctx in recent_context]
            context_embedding: np.ndarray = np.mean(context_embeddings, axis=0)

            # Dynamic context integration
            context_coherence: float = np.dot(query_embedding, context_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(context_embedding))

            # Adjust query embedding based on context coherence
            query_embedding = ((1 + context_coherence) * query_embedding + context_coherence * context_embedding) / (2 + context_coherence)

        # Find most aligned response
        best_response: str | None = None
        best_alignment: float = 0.0

        for text, embedding in self.dialog_memory:
            alignment: float = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))

            if alignment > best_alignment:
                best_alignment = alignment
                best_response = text

        return (best_response, best_alignment) if best_alignment > self.alignment_threshold else (None, 0.0)

    def save_state(
        self,
        save_path: Path,
    ) -> None:
        """Save alignment state to disk."""
        save_path.mkdir(parents=True, exist_ok=True)

        state: dict[str, Any] = {
            "dialog_memory": [(text, emb.tolist()) for text, emb in self.dialog_memory],
            "context_memory": [(text, emb.tolist()) for text, emb in self.context_memory],
            "alignment_threshold": self.alignment_threshold,
        }

        with save_path.joinpath("alignment_state.json").open("w") as f:
            json.dump(state, f)

    @classmethod
    def load_state(
        cls,
        save_path: Path,
    ) -> Self:
        """Load alignment state from disk."""
        instance: Self = cls()

        state: dict[str, Any] = json.loads(save_path.joinpath("alignment_state.json").read_bytes())

        instance.dialog_memory = [(text, np.array(emb)) for text, emb in state["dialog_memory"]]
        instance.context_memory = [(text, np.array(emb)) for text, emb in state["context_memory"]]
        instance.alignment_threshold = state["alignment_threshold"]

        return instance
