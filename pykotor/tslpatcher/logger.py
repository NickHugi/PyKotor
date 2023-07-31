from typing import List


class PatchLogger:
    def __init__(self):
        self.notes: List[PatchLog] = []
        self.warnings: List[PatchLog] = []
        self.errors: List[PatchLog] = []
        self.verbose_logs: List[PatchLog] = []
        self.all_logs: List[PatchLog] = [] # used so logging is done in order of operations

        self.patches_completed: int = 0

    def complete_patch(self) -> None:
        self.patches_completed += 1

    def add_verbose(self, message: str) -> None:
        message = f"[Verbose] {message}"
        print(message)
        self.verbose_logs.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))

    def add_note(self, message: str) -> None:
        message = f"[Note] {message}"
        print(message)
        self.notes.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))

    def add_warning(self, message: str) -> None:
        message = f"[Warning] {message}"
        print(message)
        self.warnings.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))

    def add_error(self, message: str) -> None:
        message = f"[Error] {message}"
        print(message)
        self.errors.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))


class PatchLog:
    def __init__(self, message: str):
        self.message: str = message
