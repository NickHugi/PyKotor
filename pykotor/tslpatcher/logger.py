from __future__ import annotations

from pykotor.common.event import Observable


class PatchLogger:
    def __init__(self):
        self.verbose_logs: list[PatchLog] = []
        self.notes: list[PatchLog] = []
        self.warnings: list[PatchLog] = []
        self.errors: list[PatchLog] = []
        self.all_logs: list[PatchLog] = []  # used so logging is done in order of operations

        self.verbose_observable: Observable = Observable()
        self.note_observable: Observable = Observable()
        self.warning_observable: Observable = Observable()
        self.error_observable: Observable = Observable()

        self.patches_completed: int = 0

    def complete_patch(self) -> None:
        self.patches_completed += 1

    def add_verbose(self, message: str) -> None:
        message = f"[Verbose] {message}"
        print(message)
        self.verbose_logs.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))
        self.verbose_observable.fire(message)

    def add_note(self, message: str) -> None:
        message = f"[Note] {message}"
        print(message)
        self.notes.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))
        self.note_observable.fire(message)

    def add_warning(self, message: str) -> None:
        message = f"[Warning] {message}"
        print(message)
        self.warnings.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))
        self.warning_observable.fire(message)

    def add_error(self, message: str) -> None:
        message = f"[Error] {message}"
        print(message)
        self.errors.append(PatchLog(message))
        self.all_logs.append(PatchLog(message))
        self.error_observable.fire(message)


class PatchLog:
    def __init__(self, message: str):
        self.message: str = message
