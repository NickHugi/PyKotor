from __future__ import annotations

from datetime import datetime, timezone

from utility.event import Observable


class PatchLogger:
    def __init__(self) -> None:
        self.verbose_logs: list[PatchLog] = []
        self.notes: list[PatchLog] = []
        self.warnings: list[PatchLog] = []
        self.errors: list[PatchLog] = []
        self.all_logs: list[PatchLog] = []  # used for ordered logging, e.g. when writing the logfile

        self.verbose_observable: Observable = Observable()
        self.note_observable: Observable = Observable()
        self.warning_observable: Observable = Observable()
        self.error_observable: Observable = Observable()

        self.patches_completed: int = 0

    def complete_patch(self) -> None:
        self.patches_completed += 1

    def add_verbose(self, message: str) -> None:
        current_time = datetime.now(tz=timezone.utc).astimezone().time()
        formatted_time = current_time.strftime("%H:%M:%S")
        formatted_message = f"[Verbose] [{formatted_time}] {message}"

        log_obj = PatchLog(formatted_message)
        self.verbose_logs.append(log_obj)
        self.all_logs.append(log_obj)
        self.verbose_observable.fire(formatted_message)

    def add_note(self, message: str) -> None:
        current_time = datetime.now(tz=timezone.utc).astimezone().time()
        formatted_time = current_time.strftime("%H:%M:%S")
        formatted_message = f"[Note] [{formatted_time}] {message}"

        log_obj = PatchLog(formatted_message)
        self.notes.append(log_obj)
        self.all_logs.append(log_obj)
        self.note_observable.fire(formatted_message)

    def add_warning(self, message: str) -> None:
        current_time = datetime.now(tz=timezone.utc).astimezone().time()
        formatted_time = current_time.strftime("%H:%M:%S")
        formatted_message = f"[Warning] [{formatted_time}] {message}"

        log_obj = PatchLog(formatted_message)
        self.warnings.append(log_obj)
        self.all_logs.append(log_obj)
        self.warning_observable.fire(formatted_message)

    def add_error(self, message: str) -> None:
        current_time = datetime.now(tz=timezone.utc).astimezone().time()
        formatted_time = current_time.strftime("%H:%M:%S")
        formatted_message = f"[Error] [{formatted_time}] {message}"

        log_obj = PatchLog(formatted_message)
        self.errors.append(log_obj)
        self.all_logs.append(log_obj)
        self.error_observable.fire(formatted_message)


class PatchLog:
    def __init__(self, message: str):
        self.message: str = message
        print(message)
