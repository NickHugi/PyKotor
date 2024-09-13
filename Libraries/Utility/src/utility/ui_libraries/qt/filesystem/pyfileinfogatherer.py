from __future__ import annotations

import asyncio
import multiprocessing
import os
import queue
import sys

from concurrent.futures import ProcessPoolExecutor
from os import scandir
from typing import Any

from loggerplus import RobustLogger
from qasync import QEventLoop, asyncSlot  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QDir, QElapsedTimer, QFileInfo, QFileSystemWatcher, QObject, QTimer, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import QApplication, QFileIconProvider

from utility.ui_libraries.qt.filesystem.pyextendedinformation import PyQExtendedInformation


def create_watcher_in_child_process(
    directories_changed_queue: multiprocessing.Queue[str | None],
    files_changed_queue: multiprocessing.Queue[str | None],
):
    assert multiprocessing.current_process().name != "MainProcess", "This function must be called in a child process."
    app = QApplication(sys.argv)
    watcher = QFileSystemWatcher()
    watcher.directoryChanged.connect(lambda path: directories_changed_queue.put(path))
    watcher.fileChanged.connect(lambda path: files_changed_queue.put(path))
    sys.exit(app.exec_())


async def addPathsToWatcher(
    paths: list[str],
    task_queue: multiprocessing.Queue[tuple[str, list[str]]],
    result_queue: multiprocessing.Queue[Any],
):
    if task_queue is None:
        return
    task_queue.put(("addPaths", paths))
    result = await result_queue.get()
    if result is None:
        return


async def removePathsFromWatcher(
    paths: list[str],
    task_queue: multiprocessing.Queue[tuple[str, list[str]]],
    result_queue: multiprocessing.Queue[Any],
):
    if task_queue is None:
        return
    task_queue.put(("removePaths", paths))
    result = await result_queue.get()
    if result is None:
        return


async def watchedFiles(
    task_queue: multiprocessing.Queue[tuple[str, list[str]]],
    result_queue: multiprocessing.Queue[Any],
) -> list[str]:
    task_queue.put(("watchedFiles", []))
    result = await result_queue.get()
    if result is None:
        return []
    return result


async def watchedDirectories(
    task_queue: multiprocessing.Queue[tuple[str, list[str]]],
    result_queue: multiprocessing.Queue[Any],
) -> list[str]:
    task_queue.put(("watchedDirectories", []))
    result = await result_queue.get()
    if result is None:
        return []
    return result


class PyFileInfoGatherer(QObject):
    updates = Signal(str, list)
    newListOfFiles = Signal(str, list)
    directoryLoaded = Signal(str)
    nameResolved = Signal(str, str)

    fileCreated = Signal(str)
    fileDeleted = Signal(str)
    fileModified = Signal(str)
    fileAccessed = Signal(str)
    fileContentsModified = Signal(str)
    directoryCreated = Signal(str)
    directoryDeleted = Signal(str)
    directoryModified = Signal(str)
    permissionChanged = Signal(str)
    symbolicLinkChanged = Signal(str)
    accessDenied = Signal(str)
    fileAttributeChanged = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        max_files_before_updates: int = 100,
        *,
        resolveSymlinks: bool = False,  # noqa: N803
    ):
        super().__init__(parent)

        self.max_files_before_updates: int = max_files_before_updates
        self.m_resolveSymlinks: bool = resolveSymlinks

        self.m_watcher: QFileSystemWatcher | None = None
        self.m_watching: bool = False

        self._paths: list[str] = []
        self._files: list[list[str]] = []

        self.process_lock: asyncio.Lock = asyncio.Lock()  # multiprocessing.Lock()

        self.directories_changed_queue: multiprocessing.Queue[str | None] = multiprocessing.Queue()
        self.files_changed_queue: multiprocessing.Queue[str | None] = multiprocessing.Queue()

        self.m_iconProvider: QFileIconProvider = QFileIconProvider()

        self._executor: ProcessPoolExecutor = ProcessPoolExecutor()
        self._abort: asyncio.Event = asyncio.Event()
        QTimer.singleShot(0, self.start_event_loop)

    def iconProvider(self) -> QFileIconProvider:
        return self.m_iconProvider

    def event_loop(self):
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        yield loop
        loop.close()

    def start_event_loop(self):
        asyncio.set_event_loop(QEventLoop(QApplication.instance()))
        asyncio.get_event_loop().create_task(self.run(), name="PyFileInfoGatherer")

    @asyncSlot()
    async def setResolveSymlinks(self, enable: bool):  # noqa: FBT001
        if os.name == "nt":
            self.m_resolveSymlinks = enable

    async def run(self):
        while not self._abort.is_set():
            if not self._paths:
                await asyncio.sleep(0.1)
                continue
            currentPath = self._paths.pop(0)
            currentFiles = self._files.pop(0)
            result = await self.getFileInfos(currentPath, currentFiles)
            async with self.process_lock:
                try:
                    result = self.directories_changed_queue.get(block=False)
                    if result is not None:
                        await self.list(result)
                except queue.Empty:  # noqa: S110
                    ...
                try:
                    result = self.files_changed_queue.get(block=False)
                    if result is not None:
                        await self.updateFile(result)
                except queue.Empty:  # noqa: S110
                    ...

    @asyncSlot()
    async def driveAdded(self):
        await self.fetchExtendedInformation("", [])

    @asyncSlot()
    async def driveRemoved(self):
        drive_info = QDir.drives()
        drives = [await self._translateDriveName(fi) for fi in drive_info]
        self.newListOfFiles.emit("", drives)

    @asyncSlot()
    async def fetchExtendedInformation(self, path: str, files: list[str]):
        loc = len(self._paths) - 1
        while loc >= 0:
            if self._paths[loc] == path and self._files[loc] == files:
                return
            loc -= 1

        self._paths.append(path)
        self._files.append(files)

        if self.m_watcher is not None and not files and path and path.strip() and not path.startswith("//") and path not in await self.watchedDirectories():
            await self.watchPaths([path])

    async def setIconProvider(self, provider: QFileIconProvider):
        self.m_iconProvider = provider

    @asyncSlot()
    async def updateFile(self, filePath: str):  # noqa: N803
        await self.fetchExtendedInformation(
            os.path.dirname(filePath),  # noqa: PTH120
            [os.path.basename(filePath)],  # noqa: PTH119
        )

    @asyncSlot()
    async def watchedFiles(self) -> list[str]:
        task_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        result = await watchedFiles(task_queue, result_queue)
        return result

    @asyncSlot()
    async def watchedDirectories(self) -> list[str]:
        task_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        result = await watchedDirectories(task_queue, result_queue)
        return result

    @asyncSlot()
    async def createWatcher(self):
        asyncio.get_event_loop().run_in_executor(
            self._executor,
            create_watcher_in_child_process,
            self.directories_changed_queue,
            self.files_changed_queue,
        )

    @asyncSlot()
    async def watchPaths(self, paths: list[str]):
        if not self.m_watching:
            print("watchPaths called for the first time, creating and setting up the watcher.")
            await self.createWatcher()
            self.m_watching = True
        print(f"Adding paths to watcher: {paths}")
        task_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        await addPathsToWatcher(paths, task_queue, result_queue)

    @asyncSlot()
    async def unwatchPaths(self, paths: list[str]):
        if self.m_watcher and paths:
            print(f"Removing paths from watcher: {paths}")
            task_queue = multiprocessing.Queue()
            result_queue = multiprocessing.Queue()
            await removePathsFromWatcher(paths, task_queue, result_queue)

    @asyncSlot()
    async def isWatching(self) -> bool:
        result = False
        result = self.m_watching
        return result

    @asyncSlot()
    async def setWatching(self, v: bool):  # noqa: FBT001
        if v != self.m_watching:
            if not v and self.m_watcher:
                task_queue = multiprocessing.Queue()
                result_queue = multiprocessing.Queue()
                await removePathsFromWatcher(await self.watchedFiles(), task_queue, result_queue)
                del self.m_watcher
                self.m_watcher = None
            self.m_watching = v

    @asyncSlot()
    async def clear(self):
        await self.unwatchPaths(await self.watchedFiles())
        await self.unwatchPaths(await self.watchedDirectories())

    @asyncSlot()
    async def removePath(self, path: str):
        await self.unwatchPaths([path])

    @asyncSlot()
    async def list(self, directoryPath: str):  # noqa: N803
        await self.fetchExtendedInformation(directoryPath, [])

    @asyncSlot()
    async def _translateDriveName(self, drive: QFileInfo) -> str:
        driveName = drive.absoluteFilePath()
        if os.name == "nt":  # Windows
            if driveName.startswith("/"):  # UNC host
                return drive.fileName()
            if driveName.endswith("/"):
                driveName = driveName[:-1]
        return driveName

    @asyncSlot()
    async def getFileInfos(self, path: str, files: list[str]):
        """TODO: Create a new function with all of this logic and run in executor."""
        updatedFiles: list[tuple[str, QFileInfo]] = []
        if not path:
            if files:
                infoList: list[QFileInfo] = [QFileInfo(file) for file in files]
            else:
                infoList: list[QFileInfo] = QDir.drives()
            updatedFiles = [(await self._translateDriveName(info), info) for info in infoList]
            self.updates.emit("", updatedFiles)

        base = QElapsedTimer()
        base.start()

        allFiles: list[str] = []
        if not files:
            try:
                with scandir(path) as it:
                    allFiles = [entry.name for entry in it]
            except OSError as e:
                self.accessDenied.emit(path if e.filename is None else e.filename)

        if allFiles:
            self.newListOfFiles.emit(path, allFiles)

        for fileName in files:
            entry_info = QFileInfo(os.path.join(path, fileName))  # noqa: PTH118
            await self._fetch(entry_info, base, updatedFiles, path)

        if files:
            self.updates.emit(path, files)

        self.directoryLoaded.emit(path)

    @asyncSlot()
    async def _fetch(
        self,
        entry_info: QFileInfo,
        base: QElapsedTimer,
        updatedFiles: list[tuple[str, QFileInfo]],  # noqa: N803
        path: str,
    ):
        abs_entry_path = entry_info.filePath()
        try:
            updatedFiles.append((abs_entry_path, entry_info))
            current = QElapsedTimer()
            current.start()

            if len(updatedFiles) > self.max_files_before_updates or base.msecsTo(current) > 1000:  # noqa: PLR2004
                self.updates.emit(path, updatedFiles.copy())
                updatedFiles.clear()
                base.restart()

            if self.m_resolveSymlinks and entry_info.isSymLink():
                try:
                    resolvedName = os.readlink(abs_entry_path)
                    self.nameResolved.emit(abs_entry_path, os.path.basename(resolvedName))  # noqa: PTH119
                except OSError:
                    RobustLogger().warning(f"Access denied: '{abs_entry_path}'")
        except OSError as e:
            error_path = abs_entry_path if e.filename is None else e.filename
            self.accessDenied.emit(error_path)

    @asyncSlot()
    async def getInfo(self, fileInfo: QFileInfo) -> PyQExtendedInformation:  # noqa: N803
        info = PyQExtendedInformation(fileInfo)
        info.icon = self.m_iconProvider.icon(fileInfo)
        info.displayType = self.m_iconProvider.type(fileInfo)

        if not fileInfo.exists() and not fileInfo.isSymLink():
            await self.unwatchPaths([fileInfo.absoluteFilePath()])
        else:
            path = fileInfo.absoluteFilePath()
            if path and fileInfo.exists() and fileInfo.isFile() and fileInfo.isReadable() and path not in await self.watchedFiles():
                await self.watchPaths([path])

        if os.name == "nt" and self.m_resolveSymlinks and info.isSymLink(ignoreNtfsSymLinks=True):
            resolvedInfo = QFileInfo(fileInfo.symLinkTarget()).canonicalFilePath()
            if QFileInfo(resolvedInfo).exists():
                self.nameResolved.emit(fileInfo.filePath(), QFileInfo(resolvedInfo).fileName())

        return info

    @staticmethod
    async def is_file_new(file_path: str, os_time_grace_period: int = 2) -> bool:
        file_info = QFileInfo(file_path)
        creation_time = file_info.birthTime()
        modification_time = file_info.lastModified()

        return creation_time.isValid() and modification_time.isValid() and abs(creation_time.secsTo(modification_time)) < os_time_grace_period


if __name__ == "__main__":
    # Initialize the application (required for Qt signal handling)
    app = QApplication(sys.argv)

    # Initialize the PyFileInfoGatherer
    file_info_gatherer = PyFileInfoGatherer()

    # Connect signals to print to the console
    # file_info_gatherer.updates.connect(lambda path, files: print(f"\nUpdates: {path}, {files}"))
    file_info_gatherer.newListOfFiles.connect(lambda path, files: print(f"\nNew List of Files: {path}, {files}"))
    file_info_gatherer.directoryLoaded.connect(lambda path: print(f"\nDirectory Loaded: {path}"))
    file_info_gatherer.nameResolved.connect(lambda original, resolved: print(f"\nName Resolved: {original} -> {resolved}"))

    # Connect the detailed signals
    file_info_gatherer.fileCreated.connect(lambda path: print(f"\nFile Created: {path}"))
    file_info_gatherer.fileDeleted.connect(lambda path: print(f"\nFile Deleted: {path}"))
    file_info_gatherer.fileModified.connect(lambda path: print(f"\nFile Modified: {path}"))
    file_info_gatherer.fileAccessed.connect(lambda path: print(f"\nFile Accessed: {path}"))
    file_info_gatherer.fileContentsModified.connect(lambda path: print(f"\nFile Write Access: {path}"))
    file_info_gatherer.directoryCreated.connect(lambda path: print(f"\nDirectory Created: {path}"))
    file_info_gatherer.directoryDeleted.connect(lambda path: print(f"\nDirectory Deleted: {path}"))
    file_info_gatherer.directoryModified.connect(lambda path: print(f"\nDirectory Modified: {path}"))
    file_info_gatherer.permissionChanged.connect(lambda path: print(f"\nPermission Changed: {path}"))
    file_info_gatherer.symbolicLinkChanged.connect(lambda path: print(f"\nSymbolic Link Changed: {path}"))
    file_info_gatherer.accessDenied.connect(lambda path: print(f"\nAccess Denied: {path}"))
    file_info_gatherer.fileAttributeChanged.connect(lambda path: print(f"\nFile Attribute Changed: {path}"))

    # Set the directory to %USERPROFILE%
    user_profile_dir = os.path.expandvars("%USERPROFILE%")

    # Start the Qt event loop
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    async def run_task():
        await file_info_gatherer.list(user_profile_dir)

    with event_loop:
        event_loop.create_task(run_task())
        event_loop.run_until_complete(app_close_event.wait())
