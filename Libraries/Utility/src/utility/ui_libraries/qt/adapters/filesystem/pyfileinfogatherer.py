from __future__ import annotations

import os
import pathlib
import sys

from ctypes import c_bool
from typing import TYPE_CHECKING

import qtpy  # noqa: E402

if qtpy.QT5:
    from qtpy.QtWidgets import (  # noqa: F401
        QDesktopWidget,
        QUndoCommand,  # pyright: ignore[reportPrivateImportUsage]
        QUndoStack,
    )
elif qtpy.QT6:
    QDesktopWidget = None
    from qtpy.QtGui import (  # noqa: F401
        QUndoCommand,  # pyright: ignore[reportPrivateImportUsage]
        QUndoStack,
    )
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

from utility.ui_libraries.qt.adapters.filesystem.pyextendedinformation import PyQExtendedInformation


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
    if __name__ == "__main__":
        os.chdir(toolset_path)


class PyFileInfoGatherer(QThread):
    updates: Signal = Signal(str, list)
    newListOfFiles: Signal = Signal(str, list)
    directoryLoaded: Signal = Signal(str)
    nameResolved: Signal = Signal(str, str)

    # new signal
    accessDenied: Signal = Signal(str)  # Emitted when access to a file OR folder is denied

    def __init__(
        self,
        parent: QObject | None = None,
        mutex: QMutex | None = None,
        max_files_before_updates: int = 100,
        resolveSymlinks: bool = False,  # noqa: N803, FBT001, FBT002
    ):
        super().__init__(parent)

        # Thread control and synchronization
        self.abort: c_bool = c_bool(False)  # Keep this as a c_bool to match the qt src code (mutable boolean). # noqa: FBT003
        self.mutex: QMutex = QMutex() if mutex is None else mutex
        self.condition: QWaitCondition = QWaitCondition()
        # NOTE: We always want to watch paths, so we initialize it here. This differs from the qt src.
        # The qt src on the other hand initializes the watcher lazily only when needed.
        self.m_watcher: QFileSystemWatcher = QFileSystemWatcher(self)
        self.m_watcher.fileChanged.connect(self.updateFile)
        self.m_watcher.directoryChanged.connect(self.list)
        self.m_iconProvider: QFileIconProvider = QFileIconProvider()

        # File gathering settings
        self.max_files_before_updates: int = max_files_before_updates
        self.m_resolveSymlinks: bool = resolveSymlinks

        # File and path storage
        self._paths: list[str] = []
        self._files: list[list[str]] = []

        self.start(QThread.Priority.LowPriority)

    def __del__(self):
        self.abort.value = True  # noqa: FBT003
        self.condition.wakeAll()
        self.wait()

    def setResolveSymlinks(
        self,
        enable: bool,  # noqa: FBT001
    ):  # noqa: FBT001
        if os.name == "nt":
            self.m_resolveSymlinks = enable

    def run(self):
        while True:
            self.mutex.lock()
            try:
                while not self.abort.value and not self._paths:
                    self.condition.wait(self.mutex)
                if self.abort.value:
                    return
            finally:
                self.mutex.unlock()

            thisPath: str = self._paths.pop(0)
            thisList: list[str] = self._files.pop(0)

            self.getFileInfos(thisPath, thisList)

    def driveAdded(self):
        self.fetchExtendedInformation("", [])

    def driveRemoved(self):
        drive_info: list[QFileInfo] = QDir.drives()
        drives: list[str] = [self._translateDriveName(fi) for fi in drive_info]
        self.newListOfFiles.emit("", drives)

    def fetchExtendedInformation(
        self,
        path: str,
        files: list[str],
    ):
        loc: int = len(self._paths) - 1
        while loc >= 0:
            if self._paths[loc] == path and self._files[loc] == files:
                return
            loc -= 1

        self._paths.append(path)
        self._files.append(files)
        self.condition.wakeAll()

        if (
            not files
            and path
            and path.strip()
            and not path.startswith("//")  # UNC path
            and path not in self.watchedDirectories()
        ):
            print("Watching path:", path)
            self.watchPaths([path])

    def updateFile(
        self,
        filePath: str,  # noqa: N803
    ):
        dir_path: str = os.path.dirname(filePath)  # noqa: PTH120
        file_name: str = os.path.basename(filePath)  # noqa: PTH119
        self.fetchExtendedInformation(dir_path, [file_name])

    def watchedFiles(self) -> list[str]:
        return self.m_watcher.files()

    def watchedDirectories(self) -> list[str]:
        return self.m_watcher.directories()

    def watchPaths(
        self,
        paths: list[str],
    ):
        self.m_watcher.addPaths(paths)

    def unwatchPaths(
        self,
        paths: list[str],
    ):
        self.m_watcher.removePaths(paths)

    def clear(self):
        self.unwatchPaths(self.watchedFiles())
        self.unwatchPaths(self.watchedDirectories())

    def removePath(
        self,
        path: str,
    ):
        self.unwatchPaths([path])

    def list(
        self,
        directoryPath: str,  # noqa: N803
    ):
        self.fetchExtendedInformation(directoryPath, [])

    @staticmethod
    def _translateDriveName(
        drive: QFileInfo,
    ) -> str:
        driveName: str = drive.absoluteFilePath()
        if os.name == "nt":  # Windows
            if driveName.startswith("/"):  # UNC host
                return drive.fileName()
            if driveName.endswith("/"):
                driveName = driveName[:-1]
        return driveName

    def getFileInfos(
        self,
        path: str,
        files: list[str],
    ):  # noqa: N803
        # firstTime must be a c_bool
        # in order to match the qt src code.
        # it is a mutable boolean and c_bool is the best way to represent it.
        firstTime: c_bool = c_bool(True)  # noqa: FBT003
        updatedFiles: list[tuple[str, QFileInfo]] = []
        base = QElapsedTimer()
        base.start()

        if not path:  # List drives
            infoList: list[QFileInfo] = [QFileInfo(file) for file in files] if files else QDir.drives()
            updatedFiles = [(self._translateDriveName(info), info) for info in reversed(infoList)]
            self.updates.emit(path, updatedFiles)
            return

        allFiles: list[str] = []
        if not files:
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        if self.abort.value:
                            return
                        allFiles.append(entry.name)
            except OSError as e:
                self.accessDenied.emit(path if e.filename is None else e.filename)

        if allFiles:
            self.newListOfFiles.emit(path, allFiles)

        filesToCheck: list[str] = files if files else allFiles
        for fileName in filesToCheck:
            with QMutexLocker(self.mutex):
                if self.abort.value:
                    return
            fileInfo = QFileInfo(os.path.join(path, fileName))  # noqa: PTH118
            fileInfo.refresh()  # pyqt equivalent for stat() call
            self._fetch(fileInfo, base, firstTime, updatedFiles, path)

        if updatedFiles:
            self.updates.emit(path, updatedFiles)

        self.directoryLoaded.emit(path)

    def _fetch(
        self,
        fileInfo: QFileInfo,  # noqa: N803
        base: QElapsedTimer,
        firstTime: c_bool,  # noqa: N803
        updatedFiles: list[tuple[str, QFileInfo]],  # noqa: N803
        path: str,
    ) -> c_bool:
        updatedFiles.append((fileInfo.fileName(), fileInfo))
        current = QElapsedTimer()
        current.start()

        if (firstTime.value and len(updatedFiles) > self.max_files_before_updates) or base.msecsTo(current) > 1000:  # noqa: PLR2004
            self.updates.emit(path, updatedFiles)
            updatedFiles.clear()
            base.restart()
            firstTime.value = False

        if self.m_resolveSymlinks and fileInfo.isSymLink():
            try:
                resolvedInfo = QFileInfo(fileInfo.symLinkTarget())
                resolvedInfo = QFileInfo(resolvedInfo.canonicalFilePath())
                if resolvedInfo.exists():
                    self.nameResolved.emit(fileInfo.filePath(), resolvedInfo.fileName())
            except OSError:
                self.accessDenied.emit(fileInfo.filePath())

        return firstTime

    def getInfo(self, fileInfo: QFileInfo) -> PyQExtendedInformation:  # noqa: N803
        info = PyQExtendedInformation(fileInfo)
        info.icon = self.m_iconProvider.icon(fileInfo)
        info.displayType = self.m_iconProvider.type(fileInfo)

        if not fileInfo.exists() and not fileInfo.isSymLink():
            self.unwatchPaths([fileInfo.absoluteFilePath()])
        else:
            path: str = fileInfo.absoluteFilePath()
            if path and fileInfo.exists() and fileInfo.isFile() and fileInfo.isReadable() and path not in self.watchedFiles():
                self.watchPaths([path])

        if os.name == "nt" and self.m_resolveSymlinks and info.isSymLink(ignoreNtfsSymLinks=True):
            resolvedInfo: str = QFileInfo(fileInfo.symLinkTarget()).canonicalFilePath()
            if QFileInfo(resolvedInfo).exists():
                self.nameResolved.emit(fileInfo.filePath(), QFileInfo(resolvedInfo).fileName())

        return info


if __name__ == "__main__":
    import os

    from qtpy.QtWidgets import QApplication

    # Initialize the application (required for Qt signal handling)
    app = QApplication(sys.argv)

    # Initialize the PyFileInfoGatherer
    file_info_gatherer = PyFileInfoGatherer()

    # Connect signals to print to the console
    file_info_gatherer.updates.connect(lambda path, files: print(f"\nUpdates: {path}, {files}"))
    file_info_gatherer.newListOfFiles.connect(lambda path, files: print(f"\nNew List of Files: {path}, {files}"))
    file_info_gatherer.directoryLoaded.connect(lambda path: print(f"\nDirectory Loaded: {path}"))
    file_info_gatherer.nameResolved.connect(lambda original, resolved: print(f"\nName Resolved: {original} -> {resolved}"))

    # Connect the detailed signals
    file_info_gatherer.accessDenied.connect(lambda path: print(f"\nAccess Denied: {path}"))

    # Set the directory to %USERPROFILE%
    user_profile_dir = os.path.expandvars("%USERPROFILE%\\Test")
    file_info_gatherer.list(user_profile_dir)

    # Start the Qt event loop
    sys.exit(app.exec())
