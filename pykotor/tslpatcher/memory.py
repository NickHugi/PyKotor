from typing import List, Dict


class PatcherMemory:
    def __init__(self):
        self.memory_2da: Dict[int, str] = {}
        self.memory_str: Dict[int, int] = {}  # StrRef# -> dialog.tlk index
