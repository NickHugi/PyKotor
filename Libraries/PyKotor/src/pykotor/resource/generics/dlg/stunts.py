"""Dialog stunt class for handling stunt models."""

from __future__ import annotations

import uuid

from typing import Any

from pykotor.common.misc import ResRef


class DLGStunt:
    """Represents a stunt model in a dialog.

    Attributes:
    ----------
    participant: "Participant" field.
    stunt_model: "StuntModel" field.
    """

    def __init__(
        self,
    ):
        self._hash_cache: int = hash(uuid.uuid4().hex)
        self.participant: str = ""
        self.stunt_model: ResRef = ResRef.from_blank()

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return self._hash_cache

    def to_dict(self) -> dict[str, Any]:
        return {"participant": self.participant, "stunt_model": str(self.stunt_model), "_hash_cache": self._hash_cache}

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        node_map: dict[str | int, Any] | None = None,  # noqa: ARG003
    ) -> DLGStunt:
        stunt: DLGStunt = cls()
        stunt.participant = data.get("participant", "")
        stunt.stunt_model = ResRef(data.get("stunt_model", ""))
        stunt._hash_cache = data.get("_hash_cache", stunt._hash_cache)  # noqa: SLF001
        return stunt
