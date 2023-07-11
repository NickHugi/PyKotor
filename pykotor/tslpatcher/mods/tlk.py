from abc import ABC
from typing import List

from pykotor.common.misc import ResRef

from pykotor.resource.formats.tlk import TLK
from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsTLK:
    def __init__(self):
        self.modifiers: List[ModifyTLK] = []

    def apply(self, dialog: TLK, memory: PatcherMemory) -> None:
        # do replacements first.
        for modifier in self.modifiers:
            modifier.apply_replacements(dialog, memory)
        for modifier in self.modifiers:
            modifier.apply(dialog, memory)


class ModifyTLK:
    def __init__(self, token_id, text: str, sound: ResRef):
        self.token_id: int = token_id
        self.text: str = text
        self.sound: ResRef = sound

    def apply(self, dialog: TLK, memory: PatcherMemory) -> None:
        dialog.add(self.text, self.sound.get())
        memory.memory_str[self.token_id] = len(dialog.entries) - 1

    def apply_replacements(self, dialog: TLK, memory: PatcherMemory) -> None:
        dialog.replace(self.token_id, self.text, self.sound.get())