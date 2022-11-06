from typing import List


class PatchLogger:
    def __init__(self):
        self.notes: List[PatchLog] = []
        self.warnings: List[PatchLog] = []
        self.errors: List[PatchLog] = []

    def add_note(self, file: str, message: str) -> None:
        self.notes.append(PatchLog(file, message))

    def add_warning(self, file: str, message: str) -> None:
        self.warnings.append(PatchLog(file, message))

    def add_error(self, file: str, message: str) -> None:
        self.errors.append(PatchLog(file, message))


class PatchLog:
    def __init__(self, file: str, message: str):
        self.file: str = file
        self.message: str = message
