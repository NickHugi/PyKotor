from __future__ import annotations

import os
import pathlib
import sys

from contextlib import suppress
from typing import TYPE_CHECKING

from qtpy.QtGui import QIcon


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    print("<SDM> [update_sys_path scope] working_dir: ", working_dir)

    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()

pykotor_path = file_absolute_path.parents[8] / "Libraries" / "PyKotor" / "src" / "pykotor"
if pykotor_path.exists():
    update_sys_path(pykotor_path.parent)
pykotor_gl_path = file_absolute_path.parents[8] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
if pykotor_gl_path.exists():
    update_sys_path(pykotor_gl_path.parent)
utility_path = file_absolute_path.parents[5]
if utility_path.exists():
    update_sys_path(utility_path)
toolset_path = file_absolute_path.parents[8] / "Tools/HolocronToolset/src/toolset"
if toolset_path.exists():
    update_sys_path(toolset_path.parent)
    os.chdir(toolset_path)
print(toolset_path)
print(utility_path)

import qtpy  # noqa: E402

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    QDesktopWidget = None
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QDesktopWidget, QUndoCommand, QUndoStack  # noqa: F401  # pyright: ignore[reportPrivateImportUsage]
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")



from qtpy.QtCore import (  # noqa: E402
    QDateTime,
    QDir,
    QDirIterator,
    QElapsedTimer,
    QFileDevice,
    QFileInfo,
    QFileSystemWatcher,
    QMutex,
    QMutexLocker,
    QThread,
    QWaitCondition,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QFileIconProvider  # noqa: E402

from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QObject


def filewatcherenabled(default: bool = True) -> bool:  # noqa: FBT001, FBT002
    watchFiles = os.environ.get("QT_FILESYSTEMMODEL_WATCH_FILES", "").strip()
    if watchFiles:
        with suppress(ValueError):
            return bool(int(watchFiles))
    return default


class PyQExtendedInformation(QFileInfo):
    Dir, File, System = range(3)

    def __init__(self, info=None):
        self.mFileInfo: QFileInfo = QFileInfo() if info is None else QFileInfo(info)
        self.displayType: str = ""
        self.icon: QIcon = QIcon()

    def isDir(self) -> bool:
        return self.type() == PyQExtendedInformation.Dir

    def isFile(self) -> bool:
        return self.type() == PyQExtendedInformation.File

    def isSystem(self) -> bool:
        return self.type() == PyQExtendedInformation.System

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PyQExtendedInformation):
            return False
        return (self.mFileInfo == other.mFileInfo and
                self.displayType == other.displayType and
                self.permissions() == other.permissions() and
                self.lastModified() == other.lastModified())

    def fileInfo(self) -> QFileInfo:
        return self.mFileInfo

    def isCaseSensitive(self) -> bool:
        return os.name == "posix"

    def permissions(self) -> QFileDevice.Permissions | int:
        r1 = self.mFileInfo.permissions()
        return QFileDevice.Permissions() if r1 is None else r1

    def type(self):
        if self.mFileInfo.isDir():
            return PyQExtendedInformation.Dir
        if self.mFileInfo.isFile():
            return PyQExtendedInformation.File
        if not self.mFileInfo.exists() and self.mFileInfo.isSymLink():
            return PyQExtendedInformation.System
        return PyQExtendedInformation.System

    def isSymLink(self, ignoreNtfsSymLinks: bool = False) -> bool:  # noqa: N803, FBT002, FBT001
        return (
            self.mFileInfo.suffix().strip().lower() != ".lnk"
            if ignoreNtfsSymLinks and sys.platform == "win32"
            else self.mFileInfo.isSymLink()
        )

    def isHidden(self) -> bool:
        return self.mFileInfo.isHidden()

    def lastModified(self) -> QDateTime:
        r1 = self.mFileInfo.lastModified()
        return QDateTime() if r1 is None else r1

    def size(self) -> int:
        size = -1
        if self.type() == PyQExtendedInformation.Dir:
            size = 0
        elif self.type() == PyQExtendedInformation.File:
            size = self.mFileInfo.size()
        elif not self.mFileInfo.exists() and not self.mFileInfo.isSymLink():
            size = -1
        return size


class PyFileInfoGatherer(QThread):
    updates: Signal = Signal(str, list)
    newListOfFiles: Signal = Signal(str, list)
    directoryLoaded: Signal = Signal(str)
    nameResolved: Signal = Signal(str, str)

    # New signals
    fileCreated: Signal = Signal(str)
    fileDeleted: Signal = Signal(str)
    fileModified: Signal = Signal(str)
    fileAccessed: Signal = Signal(str)  # Read access signal
    fileWriteAccess: Signal = Signal(str)  # Write access signal
    directoryCreated: Signal = Signal(str)
    directoryDeleted: Signal = Signal(str)
    directoryModified: Signal = Signal(str)
    permissionChanged: Signal = Signal(str)
    symbolicLinkChanged: Signal = Signal(str)
    accessDenied: Signal = Signal(str)
    diskSpaceChanged: Signal = Signal(str, int)  # path and new available space
    fileAttributeChanged: Signal = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.mutex: QMutex = QMutex()
        self.condition: QWaitCondition = QWaitCondition()
        self.m_iconProvider: QFileIconProvider = QFileIconProvider()
        self.m_resolveSymlinks: bool = False
        self.m_watching: bool = False
        self.m_watcher: QFileSystemWatcher | None = None
        self.paths: list[str] = []
        self.files: list[list[str]] = []
        self.abort: bool = False
        self.previous_file_info: dict[str, QFileInfo] = {}
        self.start(QThread.Priority.LowPriority)

    def __del__(self):
        self.abort = True
        with QMutexLocker(self.mutex):
            self.condition.wakeAll()
        self.wait()

    def setResolveSymlinks(self, enable: bool):  # noqa: FBT001
        if sys.platform.startswith("win"):
            self.m_resolveSymlinks = enable

    def run(self):
        firstTime = True
        while not self.abort:
            with QMutexLocker(self.mutex):
                while not self.abort and not self.paths:
                    self.condition.wait(self.mutex)
                if self.abort:
                    return
                currentPath = self.paths.pop(0)
                currentFiles = self.files.pop(0)

            self.getFileInfos(currentPath, currentFiles, firstTime=firstTime)

    def driveAdded(self):
        self.fetchExtendedInformation("", [])

    def driveRemoved(self):
        drives = [self._translateDriveName(fi) for fi in QDir.drives()]
        self.newListOfFiles.emit("", drives)

    def fetchExtendedInformation(self, path: str, files: list[str]):
        with QMutexLocker(self.mutex):
            loc = next(
                (i for i, p in enumerate(self.paths) if p == path and self.files[i] == files),
                -1,
            )
            if loc != -1:
                return

            self.paths.append(path)
            self.files.append(files)
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
        _fp_obj = Path(filePath)
        self.fetchExtendedInformation(str(_fp_obj.parent), [_fp_obj.name])

    def watchedFiles(self) -> list[str]:
        return [] if self.m_watcher is None else self.m_watcher.files()

    def watchedDirectories(self) -> list[str]:
        return [] if self.m_watcher is None else self.m_watcher.directories()

    def createWatcher(self):
        self.m_watcher = QFileSystemWatcher(self)
        self.m_watcher.directoryChanged.connect(self.list)
        self.m_watcher.fileChanged.connect(self.updateFile)
        # Platform-specific listener for drive events (Windows)
        #if sys.platform == "win32":
        #    listener = self.watcher.property("_q_driveListener")
        #    if isinstance(listener, QObject):
        #        listener.driveAdded.connect(self.driveAdded)
        #        listener.driveRemoved.connect(self.driveRemoved)

    def watchPaths(self, paths: list[str]):
        if not self.m_watching:
            print("watchPaths called for the first time, creating and setting up the watcher.")
            self.createWatcher()
            self.m_watching = True
        assert self.m_watcher is not None
        self.m_watcher.addPaths(paths)

    def unwatchPaths(self, paths: list[str]):
        if self.m_watcher and paths:
            self.m_watcher.removePaths(paths)

    def isWatching(self) -> bool:
        result = False
        with QMutexLocker(self.mutex):
            result = self.m_watching
        return result

    def setWatching(self, v: bool):  # noqa: FBT001
        with QMutexLocker(self.mutex):
            if v != self.m_watching:
                if not v and self.m_watcher:
                    del self.m_watcher
                    self.m_watcher = None
                self.m_watching = v

    def clear(self):
        with QMutexLocker(self.mutex):
            self.unwatchPaths(self.watchedFiles())
            self.unwatchPaths(self.watchedDirectories())

    def removePath(self, path: str):
        with QMutexLocker(self.mutex):
            self.unwatchPaths([path])

    def list(self, directoryPath: str):  # noqa: N803
        self.fetchExtendedInformation(directoryPath, [])

    def getFileInfos(self, path: str, files: list[str], *, firstTime: bool = False):  # noqa: N803, C901
        print(f"GetFileInfos(path={path}, numFiles={len(files)}, firstTime={firstTime}")
        if not path:
            infoList: list[QFileInfo] = [QFileInfo(file) for file in files] if files else QDir.drives()
            updatedFiles: list[tuple[str, QFileInfo]] = [(self._translateDriveName(driveInfo), driveInfo) for driveInfo in reversed(infoList)]
            self.updates.emit(path, updatedFiles)
            return

        base = QElapsedTimer()
        base.start()

        updatedFiles: list[tuple[str, QFileInfo]] = []
        if not files:
            dirIt = QDirIterator(path, QDir.AllEntries | QDir.System | QDir.Hidden)

            allFiles: list[str] = []
            while dirIt.hasNext():
                with QMutexLocker(self.mutex):
                    if self.abort:
                        return
                dirIt.next()
                fileInfo = dirIt.fileInfo()
                fileInfo.refresh()
                allFiles.append(fileInfo.fileName())
                self._fetch(fileInfo, base, firstTime, updatedFiles, path)

            if allFiles:
                self.newListOfFiles.emit(path, allFiles)

        if files:
            for fileName in files:
                with QMutexLocker(self.mutex):
                    if self.abort:
                        return
                fileInfo = QFileInfo(QDir(path).filePath(fileName))
                fileInfo.refresh()
                self._fetch(fileInfo, base, firstTime, updatedFiles, path)

                if fileInfo.isDir():
                    self.directoryModified.emit(fileInfo.filePath())
                else:
                    self.fileModified.emit(fileInfo.filePath())

                self._emit_detailed_signals(fileInfo)

        if updatedFiles:
            self.updates.emit(path, updatedFiles)

        self.directoryLoaded.emit(path)

    def _emit_detailed_signals(self, fileInfo: QFileInfo):  # noqa: N803
        filePath = fileInfo.filePath()

        if filePath in self.previous_file_info:
            self._handle_previous_files(filePath, fileInfo)
        elif fileInfo.isDir():
            self.directoryCreated.emit(filePath)
        else:
            self.fileCreated.emit(filePath)

        # Update the file info tracking
        self.previous_file_info[filePath] = fileInfo

        # Simulate file access signals
        if os.access(filePath, os.R_OK):
            self.fileAccessed.emit(filePath)
        if os.access(filePath, os.W_OK):
            self.fileWriteAccess.emit(filePath)
        if not os.access(filePath, os.F_OK):
            self.accessDenied.emit(filePath)

    def _handle_previous_files(self, filePath: str, fileInfo: QFileInfo):  # noqa: N803
        prev_info = self.previous_file_info[filePath]

        # Check for modifications
        if fileInfo.lastModified() != prev_info.lastModified():
            self.fileModified.emit(filePath)

        # Check for file size changes (could indicate write access)
        if fileInfo.size() != prev_info.size():
            self.fileWriteAccess.emit(filePath)

        # Check for permission changes
        if fileInfo.permissions() != prev_info.permissions():
            self.permissionChanged.emit(filePath)

        # Check for symbolic link changes
        if fileInfo.isSymLink() != prev_info.isSymLink():
            self.symbolicLinkChanged.emit(filePath)

        # Check for attribute changes
        if fileInfo.isHidden() != prev_info.isHidden():
            self.fileAttributeChanged.emit(filePath)

        # Check for disk space changes if it's a directory
        if fileInfo.isDir():
            new_space = QDir(filePath).entryList(QDir.NoDotAndDotDot | QDir.AllEntries).size()
            old_space = QDir(prev_info.filePath()).entryList(QDir.NoDotAndDotDot | QDir.AllEntries).size()
            if new_space != old_space:
                self.diskSpaceChanged.emit(filePath, new_space)

    def getInfo(self, fileInfo: QFileInfo) -> PyQExtendedInformation:  # noqa: N803
        info = PyQExtendedInformation(fileInfo)
        info.icon = self.m_iconProvider.icon(fileInfo)
        info.displayType = self.m_iconProvider.type(fileInfo)

        if filewatcherenabled():
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

        if sys.platform == "win32" and self.m_resolveSymlinks and info.isSymLink(ignoreNtfsSymLinks=True):
            resolvedInfo = QFileInfo(fileInfo.symLinkTarget()).canonicalFilePath()
            if QFileInfo(resolvedInfo).exists():
                self.nameResolved.emit(fileInfo.filePath(), QFileInfo(resolvedInfo).fileName())

        return info

    def _fetch(self, fileInfo: QFileInfo, base: QElapsedTimer, firstTime: bool, updatedFiles: list, path: str):  # noqa: N803, FBT001
        updatedFiles.append((fileInfo.fileName(), fileInfo))
        current = QElapsedTimer()
        current.start()

        if (firstTime and len(updatedFiles) > 100) or base.msecsTo(current) > 1000:  # noqa: PLR2004
            self.updates.emit(path, updatedFiles)
            updatedFiles.clear()
            base.restart()
            firstTime = False

        if self.m_resolveSymlinks and fileInfo.isSymLink():
            resolvedName = fileInfo.symLinkTarget()
            self.nameResolved.emit(fileInfo.filePath(), resolvedName)

    def _handleRoot(self, files: list[str]):
        infoList = [QFileInfo(file) for file in files] if files else QDir.drives()
        updatedFiles = [(self._translateDriveName(info), info) for info in infoList]
        self.updates.emit("", updatedFiles)

    def _translateDriveName(self, drive: QFileInfo) -> str:
        driveName = Path(drive.path())
        if sys.platform.startswith("win") and driveName.drive.startswith("/"):
            return drive.fileName()
        return str(driveName).rstrip("/")
