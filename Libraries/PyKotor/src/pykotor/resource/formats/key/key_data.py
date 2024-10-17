from __future__ import annotations

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType


class KEY:
    BINARY_TYPE = ResourceType.KEY

    def __init__(self):
        self.file_type: str = ""
        self.file_version: str = ""
        self.bif_count: int = 0
        self.key_count: int = 0
        self.offset_to_file_table: int = 0
        self.offset_to_key_table: int = 0
        self.build_year: int = 0
        self.build_day: int = 0
        self.bif_entries: list[BifEntry] = []
        self.key_entries: list[KeyEntry] = []

class BifEntry:
    def __init__(self):
        self.filesize: int = 0
        self.filename_offset: int = 0
        self.filename_size: int = 0
        self.drives: int = 0
        self.filename: str = ""

class KeyEntry:
    def __init__(self):
        self.resref: ResRef = ResRef("")
        self.type: ResourceType = ResourceType.INVALID
        self.resource_id: int = 0
