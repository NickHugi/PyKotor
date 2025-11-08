"""Dialog node classes for entries and replies."""

from __future__ import annotations

import uuid

from typing import Any


class DLGAnimation:
    """Represents a unit of animation executed during a node."""

    def __init__(
        self,
    ):
        self._hash_cache: int = hash(uuid.uuid4().hex)
        self.animation_id: int = 6
        self.participant: str = ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(animation_id={self.animation_id}, participant={self.participant})"

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return self._hash_cache

    def to_dict(self) -> dict[str, Any]:
        return {"animation_id": self.animation_id, "participant": self.participant, "_hash_cache": self._hash_cache}

    @classmethod
    def from_dict(cls, data: dict) -> DLGAnimation:
        animation: DLGAnimation = cls()
        animation.animation_id = data.get("animation_id", 6)
        animation.participant = data.get("participant", "")
        animation._hash_cache = data.get("_hash_cache", animation._hash_cache)  # noqa: SLF001
        return animation