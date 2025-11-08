from __future__ import annotations

import sys

from datetime import datetime, timezone
from enum import IntEnum
from typing import TYPE_CHECKING

from utility.event_util import Observable

if TYPE_CHECKING:
    from datetime import time

    from typing_extensions import LiteralString  # pyright: ignore[reportMissingModuleSource]



class LogType(IntEnum):
    VERBOSE = 0
    NOTE = 1
    WARNING = 2
    ERROR = 3

    def __str__(self) -> LiteralString:
        return self.name.title()


class PatchLogger:
    def __init__(self):
        self.all_logs: list[PatchLog] = []

        self.verbose_observable: Observable = Observable()
        self.note_observable: Observable = Observable()
        self.warning_observable: Observable = Observable()
        self.error_observable: Observable = Observable()

        self.patches_completed: int = 0

    @property
    def verbose_logs(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.VERBOSE]

    @property
    def notes(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.NOTE]

    @property
    def warnings(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.WARNING]

    @property
    def errors(self) -> list[PatchLog]:
        return [pl for pl in self.all_logs if pl.log_type == LogType.ERROR]

    def complete_patch(self):
        self.patches_completed += 1

    def add_verbose(
        self,
        message: str,
    ):
        log_obj: PatchLog = PatchLog(message, LogType.VERBOSE)
        self.all_logs.append(log_obj)
        self.verbose_observable.fire(log_obj)

    def add_note(
        self,
        message: str,
    ):
        log_obj: PatchLog = PatchLog(message, LogType.NOTE)
        self.all_logs.append(log_obj)
        self.note_observable.fire(log_obj)

    def add_warning(
        self,
        message: str,
    ):
        log_obj: PatchLog = PatchLog(message, LogType.WARNING)
        self.all_logs.append(log_obj)
        self.warning_observable.fire(log_obj)

    def add_error(
        self,
        message: str,
    ):
        log_obj: PatchLog = PatchLog(message, LogType.ERROR)
        self.all_logs.append(log_obj)
        self.error_observable.fire(log_obj)


class PatchLog:
    def __init__(
        self,
        message: str,
        ltype: LogType,
    ):
        self.message: str = message
        self.log_type: LogType = ltype
        self.timestamp: time = datetime.now(tz=timezone.utc).astimezone().time()
        print(self.formatted_message, file=sys.stderr if ltype is LogType.ERROR else sys.stdout)

    @property
    def formatted_message(self) -> str:  # REM: log_type should be first for kotormodsync support.
        return f"[{self.log_type}] [{self.timestamp.strftime('%H:%M:%S')}] {self.message}"
