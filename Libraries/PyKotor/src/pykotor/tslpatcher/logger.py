from __future__ import annotations

from datetime import datetime, timezone
from enum import IntEnum

from utility.event import Observable


class LogType(IntEnum):
    VERBOSE = 0
    NOTE = 1
    WARNING = 2
    ERROR = 3

    def __str__(self):
        return self.name.title()


class PatchLogger:
    def __init__(self) -> None:
        self.all_logs: list[PatchLog] = []

        self.verbose_observable: Observable = Observable()
        self.note_observable: Observable = Observable()
        self.warning_observable: Observable = Observable()
        self.error_observable: Observable = Observable()

        self.patches_completed: int = 0

    @property
    def verbose_logs(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.NOTE]

    @property
    def notes(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.NOTE]

    @property
    def warnings(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.NOTE]

    @property
    def errors(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.NOTE]

    def complete_patch(self) -> None:
        self.patches_completed += 1

    def add_verbose(self, message: str) -> None:
        log_obj = PatchLog(message, LogType.VERBOSE)
        self.all_logs.append(log_obj)
        self.verbose_observable.fire(log_obj)

    def add_note(self, message: str) -> None:
        log_obj = PatchLog(message, LogType.NOTE)
        self.all_logs.append(log_obj)
        self.note_observable.fire(log_obj)

    def add_warning(self, message: str) -> None:
        log_obj = PatchLog(message, LogType.WARNING)
        self.all_logs.append(log_obj)
        self.warning_observable.fire(log_obj)

    def add_error(self, message: str) -> None:
        log_obj = PatchLog(message, LogType.ERROR)
        self.all_logs.append(log_obj)
        self.error_observable.fire(log_obj)


class PatchLog:
    def __init__(self, message: str, ltype: LogType):
        self.message: str = message
        self.log_type: LogType = ltype
        self.timestamp = datetime.now(tz=timezone.utc).astimezone().time()
        print(self.formatted_message)

    @property
    def formatted_message(self) -> str:
        return f"[{self.log_type}] [{self.timestamp.strftime('%H:%M:%S')}] {self.message}"
