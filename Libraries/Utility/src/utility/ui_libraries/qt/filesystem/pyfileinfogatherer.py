from __future__ import annotations

import asyncio
import os
import pathlib
import sys

from ctypes import c_bool
from os import scandir

from loggerplus import RobustLogger
from qasync import QEventLoop, asyncSlot  # pyright: ignore[reportMissingTypeStubs]

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
    QObject,
    QTimer,
    QWaitCondition,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QFileIconProvider  # noqa: E402


class PyFileInfoGatherer(QObject):
    updates: Signal = Signal(str, list)
    newListOfFiles: Signal = Signal(str, list)
    directoryLoaded: Signal = Signal(str)
    nameResolved: Signal = Signal(str, str)

    # TODO(th3w1zard1): move these signals into QFileSystemModel
    fileCreated: Signal = Signal(str)
    fileDeleted: Signal = Signal(str)
    fileModified: Signal = Signal(str)
    fileAccessed: Signal = Signal(str)  # TODO(th3w1zard1): figure out how to check if a file is accessed
    fileContentsModified: Signal = Signal(str)  # TODO(th3w1zard1): figure out how to check if a file is written to
    directoryCreated: Signal = Signal(str)
    directoryDeleted: Signal = Signal(str)
    directoryModified: Signal = Signal(str)
    permissionChanged: Signal = Signal(str)  # TODO(th3w1zard1): figure out how to check if a file's permissions have changed
    symbolicLinkChanged: Signal = Signal(str)
    accessDenied: Signal = Signal(str)  # Emitted when access to a file OR folder is denied
    fileAttributeChanged: Signal = Signal(str)  # TODO(th3w1zard1): figure out how to check if a file's attributes have changed

    def __init__(
        self,
        parent: QObject | None = None,
        max_files_before_updates: int = 100,
        *,
        resolveSymlinks: bool = False,  # noqa: N803
    ):
        super().__init__(parent)

        # Thread control and synchronization
        self.abort: c_bool = c_bool(False)  # noqa: FBT003
        self.condition: QWaitCondition = QWaitCondition()

        # File system watching
        self.m_watcher: QFileSystemWatcher | None = None
        self.m_watching: bool = False

        # File gathering settings
        self.max_files_before_updates: int = max_files_before_updates
        self.m_resolveSymlinks: bool = resolveSymlinks

        # File and path storage
        self._paths: list[str] = []
        self._files: list[list[str]] = []

        # Icon handling
        self.m_iconProvider: QFileIconProvider = QFileIconProvider()
        QTimer.singleShot(0, self.run)

    def __del__(self):
        self.abort.value = True  # noqa: FBT003

    def setResolveSymlinks(self, enable: bool):  # noqa: FBT001
        if os.name == "nt":
            self.m_resolveSymlinks = enable

    @asyncSlot()
    async def run(self):
        while True:
            if not self._paths:
                await asyncio.sleep(0.1)  # Wait for paths to be populated
                continue
            currentPath = self._paths.pop(0)
            currentFiles = self._files.pop(0)
            await self.getFileInfos(currentPath, currentFiles)

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

    async def getFileInfos(self, path: str, files: list[str]):  # noqa: N803
        firstTime = c_bool(True)  # noqa: FBT003
        updatedFiles: list[tuple[str, QFileInfo]] = []
        if not path:
            if files:
                infoList = [QFileInfo(file) for file in files]
            else:
                infoList = QDir.drives()
            updatedFiles = [(self._translateDriveName(info), info) for info in infoList]
            self.updates.emit("", updatedFiles)

        self._base = QElapsedTimer()
        self._base.start()

        allFiles: list[str] = []
        if not files:
            try:
                it = scandir(path)
            except OSError as e:
                self.accessDenied.emit(path if e.filename is None else e.filename)
            else:
                try:
                    for entry in it:
                        if self.abort.value:
                            break
                        try:
                            try:
                                allFiles.append(entry.name)
                            except OSError as e:
                                self.accessDenied.emit(entry.path if e.filename is None else e.filename)
                        except OSError as e:
                            self.accessDenied.emit(entry.path if e.filename is None else e.filename)
                finally:
                    it.close()

        if allFiles:
            self.newListOfFiles.emit(path, allFiles)

        for fileName in files:
            if self.abort.value:
                break
            entry_info = QFileInfo(os.path.join(path, fileName))  # noqa: PTH118
            self._fetch(entry_info, self._base, firstTime, updatedFiles, path)

        if files:
            self.updates.emit(path, files)

        self.directoryLoaded.emit(path)

    def _fetch(
        self,
        entry_info: QFileInfo,
        base: QElapsedTimer,
        firstTime: c_bool,  # noqa: N803
        updatedFiles: list[tuple[str, QFileInfo]],  # noqa: N803
        path: str,
    ):
        print("firstTime: ", firstTime)
        abs_entry_path = entry_info.filePath()
        try:
            updatedFiles.append((abs_entry_path, entry_info))
            current = QElapsedTimer()
            current.start()

            if (
                firstTime.value
                and len(updatedFiles) > self.max_files_before_updates
            ) or base.msecsTo(current) > 1000:  # noqa: PLR2004
                self.updates.emit(path, updatedFiles.copy())
                updatedFiles.clear()
                base.restart()
                firstTime.value = False

            if self.m_resolveSymlinks and entry_info.isSymLink():
                try:
                    resolvedName = os.readlink(abs_entry_path)
                except OSError:  # noqa: TRY302
                    if self.__class__ is PyFileInfoGatherer:
                        RobustLogger().warning(f"Access denied: '{abs_entry_path}'")
                else:
                    self.nameResolved.emit(abs_entry_path, os.path.basename(resolvedName))  # noqa: PTH119
        except OSError as e:
            error_path = abs_entry_path if e.filename is None else e.filename  # noqa: PTH100
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
