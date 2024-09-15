from __future__ import annotations

import os
import pathlib
import sys

from ctypes import c_bool
from os import scandir
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from utility.ui_libraries.qt.filesystem.pyextendedinformation import PyQExtendedInformation


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
    QDir,
    QElapsedTimer,
    QFileInfo,
    QFileSystemWatcher,
    QMutex,
    QMutexLocker,
    QThread,
    QWaitCondition,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QFileIconProvider  # noqa: E402

if TYPE_CHECKING:

    from qtpy.QtCore import QObject


class PyFileInfoGatherer(QThread):
    updates = Signal(str, list)
    newListOfFiles = Signal(str, list)
    directoryLoaded = Signal(str)
    nameResolved = Signal(str, str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.path: list[str] = []
        self.files: list[list[str]] = []
        self.abort = False
        self.m_watcher = None
        self.m_iconProvider = QFileIconProvider()
        self.defaultProvider = QFileIconProvider()
        self.m_resolveSymlinks = True if os.name == 'nt' else False
        self.m_watching = True

        self.start(QThread.LowPriority)

    def __del__(self):
        self.abort = True
        with QMutexLocker(self.mutex):
            self.condition.wakeAll()
        self.wait()

    def setResolveSymlinks(self, enable):
        if os.name == 'nt':
            self.m_resolveSymlinks = enable

    def run(self):
        while not self.abort:
            with QMutexLocker(self.mutex):
                while not self.abort and not self.path:
                    self.condition.wait(self.mutex)
                if self.abort:
                    return
                thisPath = self.path.pop(0)
                thisList = self.files.pop(0)

            self.getFileInfos(thisPath, thisList)

    def driveAdded(self):
        self.fetchExtendedInformation("", [])

    def driveRemoved(self):
        drive_info = QDir.drives()
        drives = [self._translateDriveName(fi) for fi in drive_info]
        self.newListOfFiles.emit("", drives)

    def fetchExtendedInformation(self, path, files):
        with QMutexLocker(self.mutex):
            loc = len(self.path) - 1
            while loc >= 0:
                if self.path[loc] == path and self.files[loc] == files:
                    return
                loc -= 1

            self.path.append(path)
            self.files.append(files)
            self.condition.wakeAll()

        if self.m_watcher and not files and path and not path.startswith("//"):
            if path not in self.watchedDirectories():
                self.watchPaths([path])

    def setIconProvider(self, provider: QFileIconProvider):
        with QMutexLocker(self.mutex):
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

    @staticmethod
    def _translateDriveName(drive: QFileInfo) -> str:
        driveName = drive.absoluteFilePath()
        if os.name == "nt":  # Windows
            if driveName.startswith("/"):  # UNC host
                return drive.fileName()
            if driveName.endswith("/"):
                driveName = driveName[:-1]
        return driveName

    def getFileInfos(self, path, files):
        base = QElapsedTimer()
        base.start()
        fileInfo = QFileInfo()
        firstTime = True
        updatedFiles = []

        if not path:  # List drives
            infoList = [QFileInfo(file) for file in files] if files else QDir.drives()
            for i in range(len(infoList) - 1, -1, -1):
                driveInfo = infoList[i]
                driveName = self._translateDriveName(driveInfo)
                updatedFiles.append((driveName, driveInfo))
            self.updates.emit(path, updatedFiles)
            return

        allFiles = []
        if not files:
            try:
                with os.scandir(path) as dirIt:
                    for entry in dirIt:
                        if self.abort:
                            return
                        allFiles.append(entry.name)
            except OSError:
                pass

        if allFiles:
            self.newListOfFiles.emit(path, allFiles)

        filesToCheck = files if files else allFiles
        for fileName in filesToCheck:
            if self.abort:
                return
            fileInfo.setFile(os.path.join(path, fileName))
            fileInfo.refresh()  # Equivalent to stat() call
            firstTime = self._fetch(fileInfo, base, firstTime, updatedFiles, path)

        if updatedFiles:
            self.updates.emit(path, updatedFiles)
        self.directoryLoaded.emit(path)

    def _fetch(self, fileInfo, base, firstTime, updatedFiles, path):
        updatedFiles.append((fileInfo.fileName(), fileInfo))
        current = QElapsedTimer()
        current.start()
        if (firstTime and len(updatedFiles) > 100) or base.msecsTo(current) > 1000:
            self.updates.emit(path, updatedFiles)
            updatedFiles.clear()
            base = current
            firstTime = False

        if self.m_resolveSymlinks and fileInfo.isSymLink():
            resolvedName = fileInfo.symLinkTarget()
            resolvedInfo = QFileInfo(resolvedName)
            resolvedInfo = QFileInfo(resolvedInfo.canonicalFilePath())
            if resolvedInfo.exists():
                self.nameResolved.emit(fileInfo.filePath(), resolvedInfo.fileName())

        return firstTime

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


if __name__ == "__main__":
    import os

    from qtpy.QtWidgets import QApplication

    # Initialize the application (required for Qt signal handling)
    app = QApplication([])

    # Initialize the PyFileInfoGatherer
    file_info_gatherer = PyFileInfoGatherer(_debug_on_main_thread=False)

    # Connect signals to print to the console
    file_info_gatherer.updates.connect(lambda path, files: print(f"\nUpdates: {path}, {files}"))
    file_info_gatherer.newListOfFiles.connect(lambda path, files: print(f"\nNew List of Files: {path}, {files}"))
    file_info_gatherer.directoryLoaded.connect(lambda path: print(f"\nDirectory Loaded: {path}"))
    file_info_gatherer.nameResolved.connect(lambda original, resolved: print(f"\nName Resolved: {original} -> {resolved}"))

    # Connect the detailed signals
    file_info_gatherer.accessDenied.connect(lambda path: print(f"\nAccess Denied: {path}"))

    # Set the directory to %USERPROFILE%
    user_profile_dir = os.path.expandvars("%USERPROFILE%")
    file_info_gatherer.list(user_profile_dir)
    #file_info_gatherer.run()

    # Start the Qt event loop
    sys.exit(app.exec())
