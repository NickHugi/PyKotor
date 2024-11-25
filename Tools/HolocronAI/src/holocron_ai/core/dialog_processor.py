from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

import numpy as np

from sentence_transformers import SentenceTransformer

from pykotor.resource.generics.dlg import read_dlg
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Self

    from pykotor.extract.file import FileResource
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.formats.tlk.tlk_data import TLKEntry
    from pykotor.resource.generics.dlg import DLG


class DialogProcessor:
    def __init__(
        self,
        installation: Installation,
    ):
        self.installation: Installation = installation
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        self.dialog_embeddings: dict[str, np.ndarray] = {}
        self.dialog_sequence: list[str] = []
        self.context_window: int = 5
        self.temporal_memory: list[tuple[str, np.ndarray]] = []
        self.max_memory_size: int = 1000
        self.tlk: TLK | None = self._load_talk_table()

    def _load_talk_table(self) -> TLK | None:
        """Load the game's talk table."""
        try:
            return self.installation.talktable()
        except Exception as e:  # noqa: BLE001
            print(f"Error loading talk table: {e}")
            return None

    def _resolve_text(
        self,
        strref: int,
    ) -> str | None:
        """Resolve string reference to actual text."""
        if self.tlk is None or strref < 0:
            return None

        try:
            string_entry: TLKEntry | None = self.tlk.get(strref)
        except Exception as e:  # noqa: BLE001
            print(f"Error resolving string {strref}: {e}")
            return None
        else:
            if string_entry and string_entry.text:
                return string_entry.text.strip()
            return None

    def _get_surrounding_context(
        self,
        current_idx: int,
    ) -> list[str]:
        """Get surrounding dialog context."""
        start_idx: int = max(0, current_idx - self.context_window)
        end_idx: int = min(len(self.dialog_sequence), current_idx + self.context_window + 1)

        context: list[str] = []
        if start_idx < current_idx:
            context.extend(self.dialog_sequence[start_idx:current_idx])

        if current_idx + 1 < end_idx:
            context.extend(self.dialog_sequence[current_idx + 1 : end_idx])

        return context

    def process_dialog(
        self,
        text: str,
        speaker: str | None = None,
    ) -> np.ndarray:
        """Process a dialog entry and generate its embedding."""
        # Generate embedding for the dialog
        dialog_embedding: np.ndarray = self.embedding_model.encode(text)

        # Store in sequence and get context
        self.dialog_sequence.append(text)
        current_idx: int = len(self.dialog_sequence) - 1
        context: list[str] = self._get_surrounding_context(current_idx)

        # Generate context embedding
        if context:
            context_embeddings: list[np.ndarray] = [self.embedding_model.encode(ctx) for ctx in context]
            context_embedding: np.ndarray = np.mean(context_embeddings, axis=0)
            # Combine dialog and context embeddings with attention-like weighting
            combined_embedding: np.ndarray = 0.7 * dialog_embedding + 0.3 * context_embedding
        else:
            combined_embedding = dialog_embedding

        # Store in temporal memory
        self.temporal_memory.append((f"{speaker}: {text}", combined_embedding))
        if len(self.temporal_memory) > self.max_memory_size:
            self.temporal_memory.pop(0)

        # Store final embedding
        self.dialog_embeddings[text] = combined_embedding

        return combined_embedding

    def process_dialog_file(
        self,
        dlg: DLG,
    ) -> list[np.ndarray]:
        return [self.process_dialog(node.text, node.speaker) for node in dlg.all_entries()]

    def process_installation(self):
        """Process all dialog files from the installation."""
        if not self.tlk:
            raise RuntimeError("Talk table not loaded")

        dialog_files: list[FileResource] = [res for res in self.installation if res.type == ResourceType.DLG]
        for dlg_file in dialog_files:
            try:
                dlg: DLG = read_dlg(dlg_file.data())
                self.process_dialog_file(dlg)
            except Exception as e:  # noqa: PERF203, BLE001
                print(f"Error processing dialog '{dlg_file.filepath()}': {e}")

    def find_similar_responses(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Find similar dialog responses based on semantic similarity."""
        query_embedding: np.ndarray = self.embedding_model.encode(query)

        similarities: list[tuple[str, float]] = []
        for text, embedding in self.dialog_embeddings.items():
            similarity: float = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            similarities.append((text, float(similarity)))

        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

    def get_contextual_response(
        self,
        query: str,
        context_window: int = 3,
    ) -> str | None:
        """Get a contextually appropriate response considering recent temporal context."""
        if not self.temporal_memory:
            return None

        # Get recent context embeddings
        recent_context: list[tuple[str, np.ndarray]] = self.temporal_memory[-context_window:]
        context_embeddings: list[np.ndarray] = [emb for _, emb in recent_context]

        # Generate query embedding with context influence
        query_embedding: np.ndarray = self.embedding_model.encode(query)
        if context_embeddings:
            context_embedding: np.ndarray = np.mean(context_embeddings, axis=0)
            query_embedding = 0.7 * query_embedding + 0.3 * context_embedding

        # Find most similar response
        best_response: str | None = None
        best_similarity: float = -1

        for text, embedding in self.dialog_embeddings.items():
            similarity: float = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            if similarity <= best_similarity:
                continue

            best_similarity = similarity
            best_response = text

        return best_response if best_similarity > 0.5 else None  # noqa: PLR2004

    def save_state(
        self,
        save_path: Path,
    ):
        """Save the current state to disk."""
        save_path.mkdir(parents=True, exist_ok=True)

        state: dict[str, Any] = {
            "dialog_embeddings": {k: v.tolist() for k, v in self.dialog_embeddings.items()},
            "dialog_sequence": self.dialog_sequence,
            "temporal_memory": [(text, emb.tolist()) for text, emb in self.temporal_memory],
        }

        with save_path.joinpath("dialog_state.json").open("w") as f:
            json.dump(state, f)

    @classmethod
    def load_state(
        cls,
        installation: Installation,
        save_path: Path,
    ) -> Self:
        """Load state from disk."""
        instance: Self = cls(installation)

        state: dict[str, Any] = json.loads(save_path.joinpath("dialog_state.json").read_bytes())

        instance.dialog_embeddings = {k: np.array(v) for k, v in state["dialog_embeddings"].items()}
        instance.dialog_sequence = state["dialog_sequence"]
        instance.temporal_memory = [(text, np.array(emb)) for text, emb in state["temporal_memory"]]

        return instance
