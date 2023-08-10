from abc import ABC
from typing import List

from pykotor.common.misc import ResRef

from pykotor.resource.formats.tlk import TLK
from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsTLK:
    def __init__(self):
        self.modifiers: List[ModifyTLK] = []

    def apply(self, dialog: TLK, memory: PatcherMemory) -> None:
        for modifier in self.modifiers:
            if modifier.is_replacement:
                modifier.replace(dialog)
            else:
                modifier.insert(dialog, memory)


class ModifyTLK:
    def __init__(self, token_id: int, text: str, sound: ResRef, is_replacement: bool):
        self.token_id: int = token_id
        self.text: str = text
        self.sound: ResRef = sound
        self.is_replacement: bool = is_replacement

    def insert(self, dialog: TLK, memory: PatcherMemory) -> None:
        dialog.add(self.text, self.sound.get())
        memory.memory_str[self.token_id] = len(dialog.entries) - 1

    def replace(self, dialog: TLK) -> None:
        dialog.replace(self.token_id, self.text, self.sound.get())
