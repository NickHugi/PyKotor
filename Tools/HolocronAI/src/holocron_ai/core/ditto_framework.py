from __future__ import annotations

import json

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from pathlib import Path

    from torch import Tensor
    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]


@dataclass
class DialogContext:
    text: str
    speaker: str
    preceding_context: list[str]
    following_context: list[str]
    scene_description: str | None = None


class DITTOFramework:
    """Implementation of DITTO (Dialog Interactive Training Through Observation) framework."""

    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
    ) -> None:
        self.embedding_model: SentenceTransformer = SentenceTransformer(model_name)
        self.context_window_size: int = 3
        self.dialog_contexts: list[DialogContext] = []
        self.dialog_embeddings: dict[str, np.ndarray] = {}
        self.alignment_scores: dict[str, float] = {}

    def add_dialog_context(
        self,
        context: DialogContext,
    ) -> None:
        """Add a dialog context to the framework."""
        self.dialog_contexts.append(context)
        # Generate embedding for the main dialog text
        embedding: Tensor = self.embedding_model.encode(context.text)
        self.dialog_embeddings[context.text] = embedding

    def compute_contextual_alignment(
        self,
        dialog_text: str,
    ) -> float:
        """Compute how well a dialog aligns with its surrounding context."""
        if dialog_text not in self.dialog_embeddings:
            return 0.0

        # Find the context for this dialog
        context: DialogContext | None = next((ctx for ctx in self.dialog_contexts if ctx.text == dialog_text), None)
        if not context:
            return 0.0

        # Get embeddings for preceding and following context
        preceding_emb: list[Tensor] = [self.embedding_model.encode(txt) for txt in context.preceding_context]
        following_emb: list[Tensor] = [self.embedding_model.encode(txt) for txt in context.following_context]

        # Compute alignment scores
        dialog_emb: Tensor = self.dialog_embeddings[dialog_text]

        # Calculate average similarity with preceding context
        prec_scores: list[float] = [np.dot(dialog_emb, p_emb) / (np.linalg.norm(dialog_emb) * np.linalg.norm(p_emb)) for p_emb in preceding_emb]
        prec_alignment: float = float(np.mean(prec_scores)) if prec_scores else 0.0

        # Calculate average similarity with following context
        foll_scores: list[float] = [np.dot(dialog_emb, f_emb) / (np.linalg.norm(dialog_emb) * np.linalg.norm(f_emb)) for f_emb in following_emb]
        foll_alignment: float = float(np.mean(foll_scores)) if foll_scores else 0.0

        # Combine scores with weights favoring preceding context slightly more
        alignment_score: float = 0.6 * prec_alignment + 0.4 * foll_alignment
        self.alignment_scores[dialog_text] = alignment_score

        return alignment_score

    def get_self_aligned_dialogs(
        self,
        threshold: float = 0.7,
    ) -> list[tuple[str, float]]:
        """Get dialogs that show strong self-alignment with their context."""
        aligned_dialogs: list[tuple[str, float]] = []
        for dialog_text in self.dialog_embeddings:
            score: float = self.compute_contextual_alignment(dialog_text)
            if score < threshold:
                continue

            aligned_dialogs.append((dialog_text, score))

        return sorted(aligned_dialogs, key=lambda x: x[1], reverse=True)

    def save_framework_state(
        self,
        save_path: Path,
    ) -> None:
        """Save the framework state to disk."""
        save_path.mkdir(parents=True, exist_ok=True)

        # Save dialog contexts
        contexts_data: list[dict[str, Any]] = [
            {
                "text": ctx.text,
                "speaker": ctx.speaker,
                "preceding_context": ctx.preceding_context,
                "following_context": ctx.following_context,
                "scene_description": ctx.scene_description,
            }
            for ctx in self.dialog_contexts
        ]

        with save_path.joinpath("dialog_contexts.json").open("w") as f:
            json.dump(contexts_data, f)

        # Save embeddings
        embeddings_data: dict[str, list[float]] = {text: emb.tolist() for text, emb in self.dialog_embeddings.items()}
        with save_path.joinpath("dialog_embeddings.json").open("w") as f:
            json.dump(embeddings_data, f)

        # Save alignment scores
        with save_path.joinpath("alignment_scores.json").open("w") as f:
            json.dump(self.alignment_scores, f)

    @classmethod
    def load_framework_state(
        cls,
        save_path: Path,
    ) -> Self:
        """Load the framework state from disk."""
        instance: Self = cls()

        # Load dialog contexts
        with save_path.joinpath("dialog_contexts.json").open() as f:
            contexts_data: list[dict[str, Any]] = json.load(f)
            instance.dialog_contexts = [DialogContext(**ctx_data) for ctx_data in contexts_data]

        # Load embeddings
        with save_path.joinpath("dialog_embeddings.json").open() as f:
            embeddings_data: dict[str, list[float]] = json.load(f)
            instance.dialog_embeddings = {text: np.array(emb) for text, emb in embeddings_data.items()}

        # Load alignment scores
        with save_path.joinpath("alignment_scores.json").open() as f:
            instance.alignment_scores = json.load(f)

        return instance
