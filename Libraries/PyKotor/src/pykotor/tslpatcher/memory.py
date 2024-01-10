from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utility.path import PureWindowsPath


class PatcherMemory:
    def __init__(self):
        self.memory_2da: dict[int, str | PureWindowsPath] = {}  # 2DAMemory# (token) -> str
        self.memory_str: dict[int, int] = {}  # StrRef# (token) -> dialog.tlk index


class TokenUsage(ABC):
    @abstractmethod
    def value(self, memory: PatcherMemory) -> str:
        ...


class NoTokenUsage(TokenUsage):
    def __init__(self, stored: str | int):
        self.stored = str(stored)

    def value(self, memory: PatcherMemory) -> str:
        return self.stored


class TokenUsage2DA(TokenUsage):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def value(self, memory: PatcherMemory) -> str | PureWindowsPath:  # type: ignore[override]
        return memory.memory_2da[self.token_id]


class TokenUsageTLK(TokenUsage):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def value(self, memory: PatcherMemory) -> str:
        return str(memory.memory_str[self.token_id])
