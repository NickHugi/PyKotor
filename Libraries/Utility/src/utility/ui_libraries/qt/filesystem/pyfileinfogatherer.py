from __future__ import annotations

import asyncio
import os
import pathlib
import sys

from os import scandir

from loggerplus import RobustLogger
from PyQt5.QtCore import (
    QDir,
    QElapsedTimer,
    QFileInfo,
    QFileSystemWatcher,
    QObject,
    QTimer,
    pyqtSignal as Signal,
)
from PyQt5.QtWidgets import QFileIconProvider

from utility.task_management import TaskConsumer, TaskManager
from utility.ui_libraries.qt.filesystem.pyextendedinformation import PyQExtendedInformation


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

        self.max_files_before_updates = max_files_before_updates
        self.m_resolveSymlinks = resolveSymlinks

        self.m_watcher: QFileSystemWatcher | None = None
        self.m_watching = False

        self._paths: list[str] = []
        self._files: list[list[str]] = []

        self.m_iconProvider = QFileIconProvider()

        self._task_manager = TaskManager()
        self._task_consumer = TaskConsumer(self._task_manager)
        self._task_consumer.start()

        QTimer.singleShot(0, self.run)

    def setResolveSymlinks(self, enable: bool):  # noqa: FBT001
        if os.name == "nt":
            self.m_resolveSymlinks = enable

    async def run(self):
        while True:
            if not self._paths:
                await asyncio.sleep(0.1)
                continue
            currentPath = self._paths.pop(0)
            currentFiles = self._files.pop(0)
            await self._task_manager.run_in_executor(self.getFileInfos, currentPath, currentFiles)

    def driveAdded(self):
        self.fetchExtendedInformation("", [])

    def driveRemoved(self):
        drive_info = QDir.drives()
        drives = [self._translateDriveName(fi) for fi in drive_info]
        self.newListOfFiles.emit("", drives)

    def fetchExtendedInformation(self, path: str, files: list[str]):
        loc = len(self._paths) - 1
        while loc >= 0:
            if self._paths[loc] == path and self._files[loc] == files:
                return
            loc -= 1

        self._paths.append(path)
        self._files.append(files)
        self.condition.wakeAll()

        if (
            self.m_watcher is not None
            and not files
            and path and path.strip()
            and not path.startswith("//")
            and path not in self.watchedDirectories()
        ):
            self.watchPaths([path])

    def setIconProvider(self, provider: QFileIconProvider):
        self.m_iconProvider = provider

    def updateFile(self, filePath: str):  # noqa: N803
        self.fetchExtendedInformation(os.path.dirname(filePath), [os.path.basename(filePath)])  # noqa: PTH120, PTH119

    def watchedFiles(self) -> list[str]:
        return [] if self.m_watcher is None else self.m_watcher.files()

    def watchedDirectories(self) -> list[str]:
        return [] if self.m_watcher is None else self.m_watcher.directories()

    def createWatcher(self):
        self.m_watcher = QFileSystemWatcher(self)
        self.m_watcher.directoryChanged.connect(self.list)
        self.m_watcher.fileChanged.connect(self.updateFile)

    def watchPaths(self, paths: list[str]):
        if not self.m_watching:
            print("watchPaths called for the first time, creating and setting up the watcher.")
            self.createWatcher()
            self.m_watching = True
        assert self.m_watcher is not None
        print(f"Adding paths to watcher: {paths}")
        self.m_watcher.addPaths(paths)

    def unwatchPaths(self, paths: list[str]):
        if self.m_watcher and paths:
            print(f"Removing paths from watcher: {paths}")
            self.m_watcher.removePaths(paths)

    def isWatching(self) -> bool:
        result = False
        result = self.m_watching
        return result

    def setWatching(self, v: bool):  # noqa: FBT001
        if v != self.m_watching:
            if not v and self.m_watcher:
                del self.m_watcher
                self.m_watcher = None
            self.m_watching = v

    def clear(self):
        self.unwatchPaths(self.watchedFiles())
        self.unwatchPaths(self.watchedDirectories())

    def removePath(self, path: str):
        self.unwatchPaths([path])

    def list(self, directoryPath: str):  # noqa: N803
        self.fetchExtendedInformation(directoryPath, [])

    @staticmethod
    def _translateDriveName(drive: QFileInfo) -> str:
        driveName = drive.absoluteFilePath()
        if os.name == "nt":  # Windows
            if driveName.startswith("/"):  # UNC host
                return drive.fileName()
            if driveName.endswith("/"):
                driveName = driveName[:-1]
        return driveName

    def getFileInfos(self, path: str, files: list[str]):
        updatedFiles: list[tuple[str, QFileInfo]] = []
        if not path:
            if files:
                infoList = [QFileInfo(file) for file in files]
            else:
                infoList = QDir.drives()
            updatedFiles = [(self._translateDriveName(info), info) for info in infoList]
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
            entry_info = QFileInfo(os.path.join(path, fileName))
            self._fetch(entry_info, base, updatedFiles, path)

        if files:
            self.updates.emit(path, files)

        self.directoryLoaded.emit(path)

    def _fetch(
        self,
        entry_info: QFileInfo,
        base: QElapsedTimer,
        updatedFiles: list[tuple[str, QFileInfo]],
        path: str,
    ):
        abs_entry_path = entry_info.filePath()
        try:
            updatedFiles.append((abs_entry_path, entry_info))
            current = QElapsedTimer()
            current.start()

            if len(updatedFiles) > self.max_files_before_updates or base.msecsTo(current) > 1000:
                self.updates.emit(path, updatedFiles.copy())
                updatedFiles.clear()
                base.restart()

            if self.m_resolveSymlinks and entry_info.isSymLink():
                try:
                    resolvedName = os.readlink(abs_entry_path)
                    self.nameResolved.emit(abs_entry_path, os.path.basename(resolvedName))
                except OSError:
                    RobustLogger().warning(f"Access denied: '{abs_entry_path}'")
        except OSError as e:
            error_path = abs_entry_path if e.filename is None else e.filename
            self.accessDenied.emit(error_path)

    def getInfo(self, fileInfo: QFileInfo) -> PyQExtendedInformation:  # noqa: N803
        info = PyQExtendedInformation(fileInfo)
        info.icon = self.m_iconProvider.icon(fileInfo)
        info.displayType = self.m_iconProvider.type(fileInfo)

        if not fileInfo.exists() and not fileInfo.isSymLink():
            self.unwatchPaths([fileInfo.absoluteFilePath()])
        else:
            path = fileInfo.absoluteFilePath()
            if (
                path
                and fileInfo.exists()
                and fileInfo.isFile()
                and fileInfo.isReadable()
                and path not in self.watchedFiles()
            ):
                self.watchPaths([path])

        if (
            os.name == "nt"
            and self.m_resolveSymlinks
            and info.isSymLink(ignoreNtfsSymLinks=True)
        ):
            resolvedInfo = QFileInfo(fileInfo.symLinkTarget()).canonicalFilePath()
            if QFileInfo(resolvedInfo).exists():
                self.nameResolved.emit(fileInfo.filePath(), QFileInfo(resolvedInfo).fileName())

        return info

    @staticmethod
    def is_file_new(file_path: str, os_time_grace_period: int = 2) -> bool:
        file_info = QFileInfo(file_path)
        creation_time = file_info.birthTime()
        modification_time = file_info.lastModified()

        return (
            creation_time.isValid()
            and modification_time.isValid()
            and abs(creation_time.secsTo(modification_time)) < os_time_grace_period
        )


if __name__ == "__main__":
    import os

    from qtpy.QtWidgets import QApplication

    # Initialize the application (required for Qt signal handling)
    app = QApplication(sys.argv)

    # Initialize the PyFileInfoGatherer
    file_info_gatherer = PyFileInfoGatherer()

    # Connect signals to print to the console
    #file_info_gatherer.updates.connect(lambda path, files: print(f"\nUpdates: {path}, {files}"))
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
    file_info_gatherer.list(user_profile_dir)

    # Start the Qt event loop
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())
