from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ssf import SSF, SSFSound
    from pykotor.tslpatcher.memory import PatcherMemory, TokenUsage


class ModifySSF:
    def __init__(self, sound: SSFSound, stringref: TokenUsage):
        self.sound: SSFSound = sound
        self.stringref: TokenUsage = stringref

    def apply(self, ssf: SSF, memory: PatcherMemory) -> None:
        ssf.set(self.sound, int(self.stringref.value(memory)))


class ModificationsSSF:
    def __init__(
        self,
        filename: str,
        replace_file: bool,
        modifiers: list[ModifySSF] | None = None,
    ):
        self.filename: str = filename
        self.replace_file: bool = replace_file
        self.modifiers: list[ModifySSF] = modifiers if modifiers is not None else []

    def apply(self, ssf: SSF, memory: PatcherMemory) -> None:
        for modifier in self.modifiers:
            modifier.apply(ssf, memory)
