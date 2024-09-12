from PyQt5.QtCore import QObject, QFileSystemWatcher, pyqtSignal as Signal

class FileSystemWatcherError(Exception):
    pass

class PyFileSystemWatcher(QObject):
    directoryChanged = Signal(str)
    fileChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self.directoryChanged)
        self._watcher.fileChanged.connect(self.fileChanged)

    def addPath(self, path):
        if not self._watcher.addPath(path):
            raise FileSystemWatcherError(f"Failed to add path: {path}")

    def removePath(self, path):
        if not self._watcher.removePath(path):
            raise FileSystemWatcherError(f"Failed to remove path: {path}")

    def files(self):
        return self._watcher.files()

    def directories(self):
        return self._watcher.directories()
