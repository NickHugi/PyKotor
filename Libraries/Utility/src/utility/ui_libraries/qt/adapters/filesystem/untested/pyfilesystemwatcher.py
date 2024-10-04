from __future__ import annotations

import asyncio
import concurrent.futures
import time

from pathlib import Path

from qasync import asyncSlot  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QObject, Signal  # pyright: ignore[reportPrivateImportUsage]


class FileSystemWatcherError(OSError):
    ...


class PyFileSystemWatcher(QObject):
    directoryChanged = Signal(str)
    fileChanged = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._stop_event = asyncio.Event()
        self._watcher: dict[Path, tuple[float, concurrent.futures.Future | None]] = {}
        self._executor = concurrent.futures.ProcessPoolExecutor()

    def addPath(self, path: str):
        path_obj = Path(path)
        if path_obj in self._watcher:
            return
        if not path_obj.is_file() and not path_obj.is_dir():
            raise FileSystemWatcherError(f"Failed to add path: {path}")
        self._watcher[path_obj] = (path_obj.stat().st_mtime, None)
        asyncio.get_event_loop().call_soon(self._watch_path, path_obj)

    def removePath(self, path: str):
        path_obj = Path(path)
        if path_obj not in self._watcher:
            return
        if self._watcher[path_obj][1] is not None:
            self._watcher[path_obj][1].cancel()
        del self._watcher[path_obj]

    def files(self) -> list[str]:
        return [str(p) for p in self._watcher if p.is_file()]

    def directories(self) -> list[str]:
        return [str(p) for p in self._watcher if p.is_dir()]

    @asyncSlot()
    async def _watch_path(self, path: Path):
        while not self._stop_event.is_set():
            if path not in self._watcher:
                return
            last_modified, future = self._watcher[path]
            current_modified = path.stat().st_mtime
            if current_modified != last_modified:
                self._watcher[path] = (current_modified, None)
                if path.is_file():
                    self.fileChanged.emit(str(path))
                else:
                    self.directoryChanged.emit(str(path))
            if future is not None:
                await future.result()
            future = self._executor.submit(self._sleep, 0.1)
            self._watcher[path] = (current_modified, future)

    def _sleep(self, seconds: float):
        time.sleep(seconds)
