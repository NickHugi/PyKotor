from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

import numpy as np

from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]


class BeyondDialogProcessor:
    """Dynamic dialog context understanding without predefined patterns."""

    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
    ):
        self.embedding_model: SentenceTransformer = SentenceTransformer(model_name)
        self.dialog_embeddings: dict[str, np.ndarray] = {}
        self.context_embeddings: dict[str, np.ndarray] = {}
        self.temporal_memory: list[tuple[str, np.ndarray]] = []
        self.max_memory_size: int = 1000

    def process_dialog(
        self,
        dialog_text: str,
        surrounding_context: list[str],
    ) -> None:
        """Process a dialog entry with its surrounding context."""
        # Generate embeddings for the dialog and its context
        dialog_embedding: np.ndarray = self.embedding_model.encode(dialog_text)
        context_embeddings: list[np.ndarray] = [self.embedding_model.encode(ctx) for ctx in surrounding_context]

        # Store embeddings
        self.dialog_embeddings[dialog_text] = dialog_embedding

        # Create a combined context embedding through weighted average
        if context_embeddings:
            combined_context: np.ndarray = np.mean(context_embeddings, axis=0)
            self.context_embeddings[dialog_text] = combined_context

        # Update temporal memory
        self.temporal_memory.append((dialog_text, dialog_embedding))
        if len(self.temporal_memory) > self.max_memory_size:
            self.temporal_memory.pop(0)

    def find_similar_contexts(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Find similar dialog contexts based on semantic similarity."""
        query_embedding: np.ndarray = self.embedding_model.encode(query_text)

        similarities: list[tuple[str, float]] = []
        for text, embedding in self.dialog_embeddings.items():
            similarity: float = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            similarities.append((text, float(similarity)))

        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

    def get_contextual_understanding(
        self,
        dialog_text: str,
    ) -> dict[str, np.ndarray]:
        """Get dynamic contextual understanding for a dialog."""
        if dialog_text not in self.dialog_embeddings:
            return {}

        dialog_embedding: np.ndarray = self.dialog_embeddings[dialog_text]
        context_embedding: np.ndarray | None = self.context_embeddings.get(dialog_text)

        return {"dialog_embedding": dialog_embedding, "context_embedding": context_embedding if context_embedding is not None else np.zeros_like(dialog_embedding)}

    def get_temporal_context(
        self,
        window_size: int = 5,
    ) -> list[np.ndarray]:
        """Get recent temporal context embeddings."""
        return [emb for _, emb in self.temporal_memory[-window_size:]]

    def compute_contextual_coherence(
        self,
        dialog_text: str,
    ) -> float:
        """Compute how well a dialog aligns with its stored context."""
        if dialog_text not in self.dialog_embeddings or dialog_text not in self.context_embeddings:
            return 0.0

        dialog_embedding: np.ndarray = self.dialog_embeddings[dialog_text]
        context_embedding: np.ndarray = self.context_embeddings[dialog_text]

        return float(np.dot(dialog_embedding, context_embedding) / (np.linalg.norm(dialog_embedding) * np.linalg.norm(context_embedding)))

    def save_state(
        self,
        save_path: Path,
    ) -> None:
        """Save the current state to disk."""
        save_path.mkdir(parents=True, exist_ok=True)

        state: dict[str, Any] = {
            "dialog_embeddings": {k: v.tolist() for k, v in self.dialog_embeddings.items()},
            "context_embeddings": {k: v.tolist() for k, v in self.context_embeddings.items()},
            "temporal_memory": [(text, emb.tolist()) for text, emb in self.temporal_memory],
        }

        with save_path.joinpath("beyond_dialog_state.json").open("w") as f:
            json.dump(state, f)

    @classmethod
    def load_state(cls, save_path: Path) -> Self:
        """Load state from disk."""
        instance: Self = cls()

        with save_path.joinpath("beyond_dialog_state.json").open() as f:
            state: dict[str, Any] = json.load(f)

        instance.dialog_embeddings = {k: np.array(v) for k, v in state["dialog_embeddings"].items()}
        instance.context_embeddings = {k: np.array(v) for k, v in state["context_embeddings"].items()}
        instance.temporal_memory = [(text, np.array(emb)) for text, emb in state["temporal_memory"]]

        return instance
