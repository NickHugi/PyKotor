from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class PatcherModifications(ABC):

    def __init__(self, sourcefile: str, destination: str | None = None, saveas: str | None = None) -> None:
        self.sourcefile: str = sourcefile
        self.saveas = saveas if saveas is not None else sourcefile
        self.destination: str = destination if destination is not None else "Override"
        self.action: str = "Patch" + " "

    @abstractmethod
    def apply(self, source: SOURCE_TYPES, memory: PatcherMemory, logger: PatchLogger, game: Game) -> bytes:
        ...
