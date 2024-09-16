from __future__ import annotations

import asyncio
import os
import shutil
import time
import traceback

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger
from qasync import QEventLoop, asyncSlot  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QAbstractItemModel,
    QDateTime,
    QDir,
    QFileDevice,
    QFileInfo,
    QFileSystemWatcher,
    QMimeData,
    QModelIndex,
    QMutex,
    QThread,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QMessageBox, QStyle, QTreeView

from utility.ui_libraries.qt.filesystem.pyfileinfogatherer import PyFileInfoGatherer
from utility.ui_libraries.qt.filesystem.pyfilesystemmodelsorter import PyFileSystemModelSorter, SortingError
from utility.ui_libraries.qt.filesystem.pyfilesystemnode import PyFileSystemNode

if TYPE_CHECKING:
    import multiprocessing

    from qtpy.QtCore import QObject
    from qtpy.QtWidgets import QFileIconProvider


class PyQFileSystemModel(QAbstractItemModel):
    directoryLoaded = Signal(str)
    rootPathChanged = Signal(str)
    fileRenamed = Signal(str, str, str)
    fileSystemChanged = Signal()
    sortingChanged = Signal()
    sortingError = Signal(str)
    asyncOperationError = Signal(str)
    cacheUpdated = Signal()
    customDataChanged = Signal(QModelIndex, QModelIndex, int)

    fileCreated: Signal = Signal(str)
    fileDeleted: Signal = Signal(str)
    fileModified: Signal = Signal(str)
    fileAccessed: Signal = Signal(str)  # TODO: figure out how to check if a file is accessed
    fileContentsModified: Signal = Signal(str)  # TODO: figure out how to check if a file is written to
    directoryCreated: Signal = Signal(str)
    directoryDeleted: Signal = Signal(str)
    directoryModified: Signal = Signal(str)
    permissionChanged: Signal = Signal(str)  # TODO: figure out how to check if a file's permissions have changed
    symbolicLinkChanged: Signal = Signal(str)
    accessDenied: Signal = Signal(str)  # Emitted when access to a file OR folder is denied
    fileAttributeChanged: Signal = Signal(str)  # TODO: figure out how to check if a file's attributes have changed

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._root: PyFileSystemNode = PyFileSystemNode()
        self._fileInfoGatherer: PyFileInfoGatherer = PyFileInfoGatherer(self)
        self._fileSystemWatcher: QFileSystemWatcher = QFileSystemWatcher(self)
        self._filters: QDir.Filters = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs
        self._nameFilters: list[str] = []
        self._executor: ProcessPoolExecutor = ProcessPoolExecutor()

        self._fileInfoGatherer.newListOfFiles.connect(self._addNewListOfFiles)
        self._fileInfoGatherer.updates.connect(self._handleUpdates)
        self._fileInfoGatherer.directoryLoaded.connect(self._handleDirectoryLoaded)
        self._fileSystemWatcher.directoryChanged.connect(self._handleDirectoryChanged)
        self._fileSystemWatcher.fileChanged.connect(self._handleFileChanged)
        self._mutex: QMutex = QMutex()

        self._resolveSymlinks: bool = False
        self._readOnly: bool = True
        self._rootPath: str = ""
        self._sorter: PyFileSystemModelSorter = PyFileSystemModelSorter(0)
        self._sortOrder: Qt.SortOrder = Qt.AscendingOrder
        self._nameFilterDisables: bool = True
        self._cache: dict[str, Any] = {}
        self._cache_expiration: int = 60  # seconds
        self._customRoles: dict[int, Any] = {}
        self._customFilters: list[str] = []
        self._dragEnabled: bool = True
        self._error_retry_count: dict[str, int] = {}
        self._max_retries: int = 3
        self._watcher_cleanup_interval: int = 300  # seconds
        self._max_watcher_paths: int = 1000
        self._file_watcher_cache: dict[str, Any] = {}

    @property
    def _loop(self) -> QEventLoop:
        return QEventLoop(QApplication.instance())

    @property
    def _sortColumn(self) -> int:
        return self._sorter.sortColumn

    @_sortColumn.setter
    def _sortColumn(self, value: int):
        self._sorter.sortColumn = value

    @property
    def _watcher_thread(self) -> QThread:
        return self._fileSystemWatcher.thread()

    def __del__(self):
        self._executor.shutdown(wait=False)

    def nodeFromIndex(self, index: QModelIndex) -> PyFileSystemNode:
        return index.internalPointer() if index.isValid() else self._root

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:  # noqa: B008
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentNode = self.nodeFromIndex(parent)
        childItem = list(parentNode.children.values())[row]
        if childItem:
            return self.createIndex(row, column, childItem)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        childItem = self.nodeFromIndex(index)
        parentItem = childItem.parent

        if parentItem == self._root or parentItem is None:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if parent.column() > 0:
            return 0

        parentItem = self.nodeFromIndex(parent)
        return len(parentItem.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 4  # Name, Size, Type, Date Modified

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.column() >= self.columnCount():
            return None

        item = self.nodeFromIndex(index)

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return item.fileName
            if index.column() == 1:
                return self._sizeString(item.size())
            if index.column() == 2:
                return item.type()
            if index.column() == 3:
                return item.lastModified().toString()
        elif role == Qt.DecorationRole and index.column() == 0:
            fileInfo = item.fileInfo()
            assert fileInfo is not None, "fileInfo is None"
            return self.iconProvider().icon(fileInfo)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Name"
            if section == 1:
                return "Size"
            if section == 2:
                return "Type"
            if section == 3:
                return "Date Modified"
        return None

    def setRootPath(self, path: str) -> QModelIndex:
        if path == self._rootPath:
            return self.index(0, 0, QModelIndex())

        self._rootPath = path
        self._root = PyFileSystemNode(path)
        self.beginResetModel()
        self._fileInfoGatherer.fetchExtendedInformation(path, [])
        self.endResetModel()

        if self._fileSystemWatcher.directories():
            for directory in self._fileSystemWatcher.directories():
                self._fileSystemWatcher.removePath(directory)
        self._fileSystemWatcher.moveToThread(self._watcher_thread)
        self._watcher_thread.start()
        self._watchPath(path)
        self.rootPathChanged.emit(path)
        return self.index(0, 0, QModelIndex())

    def rootPath(self) -> str:
        return self._rootPath

    def setIconProvider(self, provider: QFileIconProvider):
        self._fileInfoGatherer.setIconProvider(provider)

    def iconProvider(self) -> QFileIconProvider:
        return self._fileInfoGatherer.iconProvider()

    def _handleDirectoryChanged(self, path: str):
        f = self._executor.submit(self._refreshDirectory, path)
        f.add_done_callback(lambda f=f: self.fileSystemChanged.emit(f.result()))

    def _handleFileChanged(self, path: str):
        f = self._executor.submit(self._refreshFile, path)
        f.add_done_callback(lambda f=f: self.fileSystemChanged.emit(f.result()))

    async def _refreshDirectory(self, path: str):
        try:
            node = self._nodeForPath(path)
            if node is None:
                return

            old_list = set(node.children.keys())
            new_list = set(await self._loop.run_in_executor(None, os.listdir, path))

            for name in old_list - new_list:
                await self._loop.run_in_executor(None, self._removeNode, node.children[name])

            for name in new_list - old_list:
                await self._loop.run_in_executor(None, self._addNode, node, name)

            for name in old_list & new_list:
                await self._loop.run_in_executor(None, self._updateNode, node.children[name])

            self.layoutChanged.emit()
        except Exception as e:
            RobustLogger().error(f"Error refreshing directory {path}: {e}")
            self._showErrorMessage(f"Error refreshing directory: {e}")

    def _refreshFile(self, path: str):
        try:
            parent_path = os.path.dirname(path)  # noqa: PTH120
            file_name = os.path.basename(path)  # noqa: PTH119
            parent_node = self._nodeForPath(parent_path)
            if parent_node and file_name in parent_node.children:
                self._updateNode(parent_node.children[file_name])
            else:
                self._loop.run_in_executor(None, self._refreshDirectory, parent_path)
            self.layoutChanged.emit()
        except Exception as e:
            RobustLogger().error(f"Error refreshing file {path}: {e}")
            self._showErrorMessage(f"Error refreshing file: {e}")

    def _nodeForPath(self, path: str) -> PyFileSystemNode | None:
        parts = path.split(os.path.sep)
        node = self._root
        for part in parts:
            if part in node.children:
                node = node.children[part]
            else:
                return None
        return node

    def _removeNode(self, node: PyFileSystemNode):
        parent = node.parent
        if parent:
            row = list(parent.children.values()).index(node)
            self.beginRemoveRows(self.createIndex(parent.row(), 0, parent), row, row)
            del parent.children[node.fileName]
            self.endRemoveRows()
        self.layoutChanged.emit()

    def _addNode(self, parent: PyFileSystemNode, name: str):
        if name not in parent.children:
            new_node = PyFileSystemNode(name, parent)
            row = len(parent.children)
            self.beginInsertRows(self.createIndex(parent.row(), 0, parent), row, row)
            parent.children[name] = new_node
            self.endInsertRows()
        self.layoutChanged.emit()

    def _updateNode(self, node: PyFileSystemNode):
        info = QFileInfo(self.filePath(self.createIndex(node.row(), 0, node)))
        node.populate(info)
        index = self.createIndex(node.row(), 0, node)
        self.dataChanged.emit(index, index.sibling(index.row(), self.columnCount() - 1))
        self.layoutChanged.emit()

    def setFilter(self, filters: QDir.Filters):
        if self._filters != filters:
            self._filters = filters
            self._refresh()

    def filter(self) -> QDir.Filters:
        return self._filters

    def setNameFilters(self, filters: list[str]):
        self._nameFilters = filters
        self._refresh()

    def nameFilters(self) -> list[str]:
        return self._nameFilters

    def setNameFilterDisables(self, enable: bool):  # noqa: FBT001
        if self._nameFilterDisables != enable:
            self._nameFilterDisables = enable
            self._refresh()

    def isNameFilterDisables(self) -> bool:
        return self._nameFilterDisables

    def _refresh(self):
        self.beginResetModel()
        self._executor.submit(self._fileInfoGatherer.fetchExtendedInformation, self._rootPath, [])
        self.endResetModel()

    def canFetchMore(self, parent: QModelIndex) -> bool:
        if not parent.isValid():
            return False
        node = self._getNode(parent)
        return not node.populatedChildren

    def fetchMore(self, parent: QModelIndex):
        if not parent.isValid():
            return
        node = self._getNode(parent)
        if node.populatedChildren:
            return
        path = self.filePath(parent)
        self._fileInfoGatherer.fetchExtendedInformation(path, [])
        node.populatedChildren = True

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:  # noqa: B008
        if not parent.isValid():
            return True
        node = self._getNode(parent)
        return node.isDir()

    def _getNode(self, index: QModelIndex) -> PyFileSystemNode:
        if not index.isValid():
            return self._root
        return index.internalPointer()

    def filePath(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        node = self._getNode(index)
        path = []
        while node is not self._root:
            if node is None:
                raise ValueError("Node is None")
            path.append(node.fileName)
            node = node.parent
        return os.path.join(self.rootPath(), *reversed(path))  # noqa: PTH118

    def fileName(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        return self._getNode(index).fileName

    def size(self, index: QModelIndex) -> int:
        if not index.isValid():
            return 0
        return self._getNode(index).size()

    def type(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        return self._getNode(index).type()

    def permissions(self, index: QModelIndex) -> QFileDevice.Permissions | int:
        if not index.isValid() or not self.isDir(index):
            return QFileDevice.Permissions()
        return self._getNode(index).permissions()

    def lastModified(self, index: QModelIndex) -> QDateTime:
        if not index.isValid():
            return QDateTime()
        return self._getNode(index).lastModified()

    def setResolveSymlinks(self, enable: bool):
        if self._resolveSymlinks != enable:
            self._resolveSymlinks = enable
            self._fileInfoGatherer.setResolveSymlinks(enable)

    def setReadOnly(self, enable: bool):
        self._readOnly = enable

    def isReadOnly(self) -> bool:
        return self._readOnly

    def remove(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        node = self._getNode(index)
        path = self.filePath(index)
        try:
            if node.isDir():
                shutil.rmtree(path)
            else:
                Path(path).unlink(missing_ok=True)
            self._removeNode(node)
        except OSError as e:
            RobustLogger().error(f"Error removing file/directory: {e}")
            self._showErrorMessage(f"Error removing file/directory: {e}")
            return False
        else:
            return True

    def mkdir(self, parent: QModelIndex, name: str) -> QModelIndex:
        if not parent.isValid():
            return QModelIndex()
        parent_node = self._getNode(parent)
        path = os.path.join(self.filePath(parent), name)  # noqa: PTH118
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            new_node = PyFileSystemNode(name, parent_node)
            row = len(parent_node.children)
            self.beginInsertRows(parent, row, row)
            parent_node.children[name] = new_node
            self.endInsertRows()
            return self.createIndex(row, 0, new_node)
        except OSError as e:
            RobustLogger().error(f"Error creating directory: {e}")
            self._showErrorMessage(f"Error creating directory: {e}")
            return QModelIndex()

    def mimeTypes(self) -> list[str]:
        return ["text/uri-list"]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        urls = [QUrl.fromLocalFile(self.filePath(index)) for index in indexes if index.column() == 0]
        mimeData = QMimeData()
        mimeData.setUrls(urls)
        return mimeData

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False

        node = self.nodeFromIndex(index)
        oldName = node.fileName
        newName = value

        if oldName == newName:
            return True

        parentPath = self.filePath(index.parent())
        oldPath = os.path.join(parentPath, oldName)
        newPath = os.path.join(parentPath, newName)

        try:
            os.rename(oldPath, newPath)
        except OSError as e:
            RobustLogger().error(f"Error renaming file: {e}")
            self._showErrorMessage(f"Error renaming file: {e}")
            return False

        node.fileName = newName
        self.dataChanged.emit(index, index)
        self.fileRenamed.emit(parentPath, oldName, newName)
        return True

    def setCustomSorting(self, sortFunction: Callable[[PyFileSystemNode, PyFileSystemNode], int]):
        self._customSorting = sortFunction
        self._loop.call_soon_threadsafe(self.sort, self._sortColumn, self._sortOrder)

    async def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._sortColumn = column
        self._sortOrder = order
        try:
            if self._customSorting:
                mapping_type = dict
                self._root.children = mapping_type(sorted(self._root.children.items(), key=lambda x: self._customSorting(x[1], x[1])))
            else:
                await self._loop.run_in_executor(self._executor, self._sorter.sort, self._root, column, order)
        except SortingError as e:
            RobustLogger().error(f"Sorting error: {e}")
            self.sortingError.emit(str(e))
        except Exception as e:
            RobustLogger().error(f"Unexpected error during sorting: {e}")
        self.layoutChanged.emit()
        self.sortingChanged.emit()

    def _sizeString(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

    def flags(self, index: QModelIndex) -> Qt.ItemFlags | Qt.ItemFlag:
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if index.column() == 0:
            flags |= Qt.ItemIsEditable | Qt.ItemIsDragEnabled

        return flags

    def _addNewListOfFiles(self, path: str, files: list[str]):
        node = self._nodeForPath(path)
        if node is None:
            return

        new_files = set(files) - set(node.children.keys())
        for file_name in new_files:
            self._addNode(node, file_name)
        self.layoutChanged.emit()

    @asyncSlot()
    async def _handleUpdates(self, path: str, updates: list[tuple[str, QFileInfo]]):
        node = self._nodeForPath(path)
        if node is None:
            return

        for file_path, file_info in updates:
            file_name = os.path.basename(file_path)
            if file_name in node.children:
                self._updateNode(node.children[file_name])
            else:
                self._addNode(node, file_name)
        self.layoutChanged.emit()

    @asyncSlot()
    async def _handleDirectoryLoaded(self, path: str):
        self._refreshCache()
        self.directoryLoaded.emit(path)

    @asyncSlot()
    async def _watchPath(self, path: str):
        if path not in self._file_watcher_cache:
            self._fileSystemWatcher.directoryChanged.connect(lambda p=path: self._handleDirectoryChanged(p))
            self._fileSystemWatcher.fileChanged.connect(lambda p=path: self._handleFileChanged(p))
            self._fileSystemWatcher.addPath(path)
            self._file_watcher_cache[path] = self._fileSystemWatcher

        # Optimize watchers if necessary
        if len(self._file_watcher_cache) > self._max_watcher_paths:
            self._optimizeWatchers()

    @asyncSlot()
    async def _cleanupWatchers(self):
        current_time = QDateTime.currentDateTime()
        for path, watcher in list(self._file_watcher_cache.items()):
            if current_time.secsTo(watcher.lastUsed()) > self._watcher_cleanup_interval:
                watcher.removePath(path)
                del self._file_watcher_cache[path]

    @asyncSlot()
    async def _optimizeWatchers(self):
        current_time = QDateTime.currentDateTime()
        sorted_watchers = sorted(
            self._file_watcher_cache.items(),
            key=lambda x: (len(x[1].files()) + len(x[1].directories()), x[1].lastUsed.secsTo(QDateTime.currentDateTime()))
        )
        for path, watcher in sorted_watchers[: len(sorted_watchers) // 2]:
            watcher.removePath(path)
            watcher.deleteLater()
            del self._file_watcher_cache[path]
    @asyncSlot()
    async def setSorting(self, column: int, order: Qt.SortOrder):
        if self._sortColumn != column or self._sortOrder != order:
            self._sortColumn = column
            self._sortOrder = order
            self._loop.run_in_executor(self._executor, self.sort, column, order)

    @asyncSlot()
    async def isDir(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        return self._getNode(index).isDir()

    @asyncSlot()
    async def fileIcon(self, index: QModelIndex) -> QIcon:
        if not index.isValid():
            return QIcon()
        return self._style.standardIcon(QStyle.SP_FileIcon if self._getNode(index).isFile() else QStyle.SP_DirIcon)


    @asyncSlot()
    async def fileInfo(self, index: QModelIndex) -> QFileInfo:
        if not index.isValid():
            return QFileInfo()
        path = self.filePath(index)
        info = QFileInfo(path)
        return info

    @asyncSlot()
    async def _showErrorMessage(self, message: str):
        RobustLogger().error(message)
        app = QApplication.instance()
        if app and QThread.currentThread() == app.thread():
            QMessageBox.warning(None, "Error", message)
        else:
            self.asyncOperationError.emit(message)

    @asyncSlot()
    async def dragMoveEvent(self, event):
        event.accept()

    @asyncSlot()
    async def setRootPathAsync(self, path: str) -> QModelIndex:
        if path == self._rootPath:
            return self.index(0, 0, QModelIndex())

        self._rootPath = path
        self._root = PyFileSystemNode(path)
        self.beginResetModel()
        await self._fileInfoGatherer.fetchExtendedInformation(path, [])
        self.endResetModel()

        if self._fileSystemWatcher.directories():
            self._fileSystemWatcher.removePaths(self._fileSystemWatcher.directories())
        self._fileSystemWatcher.moveToThread(self._watcher_thread)
        self._watcher_thread.start()
        await self._watchPath(path)
        self.rootPathChanged.emit(path)
        return self.index(0, 0, QModelIndex())

    def _applyNameFilters(self, files: list[str]) -> list[str]:
        if not self._nameFilters and not self._fileTypeFilters:
            return self._applyCustomFilters(files)

        import fnmatch

        filtered_files = []
        for file in files:
            if self._nameFilters and any(fnmatch.fnmatch(file, pattern) for pattern in self._nameFilters):
                filtered_files.append(file)
            elif self._nameFilterDisables:
                filtered_files.append(file)
            elif self._fileTypeFilters and any(file.endswith(ext) for ext in self._fileTypeFilters):
                filtered_files.append(file)

        return self._applyCustomFilters(filtered_files)

    def _clearCache(self, emit_signal: bool = False):
        self._cache.clear()
        self.data.cache_clear()
        if emit_signal:
            self.cacheUpdated.emit()
        self.layoutChanged.emit()

    def _cacheFileInfo(self, path: str, info: QFileInfo):
        self._cache[path] = (info, QDateTime.currentDateTime())

    def _getCachedFileInfo(self, path: str) -> QFileInfo | None:
        cached_data = self._cache.get(path)
        return cached_data[0] if cached_data and cached_data[1].secsTo(QDateTime.currentDateTime()) < self._cache_expiration else None

    def _getFileInfoCached(self, path: str) -> QFileInfo:
        cached_info = self._getCachedFileInfo(path)
        if cached_info:
            return cached_info
        info = self._getFileInfo(path)
        self._cacheFileInfo(path, info)
        return info

    def clearCache(self):
        self._clearCache(emit_signal=True)

    def addCustomRole(self, role: int, callback: Callable[[PyFileSystemNode], Any]):
        self._customRoles[role] = callback

    def removeCustomRole(self, role: int):
        if role in self._customRoles:
            del self._customRoles[role]

    def setCustomData(self, index: QModelIndex, role: int, value: Any):
        if not index.isValid() or role not in self._customRoles:
            return False
        node = self.nodeFromIndex(index)
        self._customRoles[role](node, value)
        self.customDataChanged.emit(index, index, role)
        return True

    def startDrag(self, supportedActions: Qt.DropActions):
        if self._dragEnabled:
            drag = QDrag(self)
            mimeData = self.mimeData(self.selectedIndexes())
            drag.setMimeData(mimeData)
            defaultDropAction = Qt.MoveAction if supportedActions & Qt.MoveAction else Qt.CopyAction
            drag.exec_(supportedActions, defaultDropAction)

    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not data.hasUrls():
            return False
        if column > 0:
            return False
        return True

    def _processDrop(self, data: QMimeData, action: Qt.DropAction, parent: QModelIndex) -> bool:
        parentPath = self.filePath(parent) if parent.isValid() else self.rootPath()
        for url in data.urls():
            srcPath = url.toLocalFile()
            destPath = os.path.join(parentPath, os.path.basename(srcPath))
            try:
                if action == Qt.CopyAction:
                    self._copyFileAsync(srcPath, destPath)
                elif action == Qt.MoveAction:
                    self._moveFileAsync(srcPath, destPath)
                else:
                    return False
            except Exception as e:
                self._showErrorMessage(f"Error during drag and drop operation: {e}")
                return False
        return True

    async def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not self.canDropMimeData(data, action, row, column, parent):
            return False

        if action == Qt.IgnoreAction:
            return True

        parent_path = self.filePath(parent) if parent.isValid() else self.rootPath()

        async def process_url(url):
            srcPath = url.toLocalFile()
            destPath = os.path.join(parent_path, os.path.basename(srcPath))
            try:
                if action == Qt.CopyAction:
                    await self._copyFileAsync(srcPath, destPath)
                elif action == Qt.MoveAction:
                    await self._moveFileAsync(srcPath, destPath)
            except Exception as e:
                self._showErrorMessage(f"Error during drag and drop operation: {e}")

        await asyncio.gather(*[process_url(url) for url in data.urls()])
        return True

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        return asyncio.run(self.dropMimeDataAsync(data, action, row, column, parent))

    def addCustomFilter(self, filter_func: Callable[[str], bool]):
        self._customFilters.append(filter_func)

    def removeCustomFilter(self, filter_func: Callable[[str], bool]):
        if filter_func in self._customFilters:
            self._customFilters.remove(filter_func)

    def _applyCustomFilters(self, files: list[str]) -> list[str]:
        for custom_filter in self._customFilters:
            files = [file for file in files if custom_filter(file)]
        return files

    def setFilePermissions(self, index: QModelIndex, permissions: QDir.Permissions) -> bool:
        if not index.isValid():
            return False

        file_path = self.filePath(index)
        try:
            os.chmod(file_path, permissions)
            node = self._getNode(index)
            node.setPermissions(permissions)
            self.dataChanged.emit(index, index)
            self.fileAttributeChanged.emit(file_path)
            return True
        except OSError as e:
            RobustLogger().error(f"Error setting file permissions: {e}")
            self._showErrorMessage(f"Error setting file permissions: {e}")
            return False

    def setFileAttributes(self, index: QModelIndex, attributes: int) -> bool:
        if not index.isValid() or os.name != "nt":
            return False

        file_path = self.filePath(index)
        try:
            import win32api

            win32api.SetFileAttributes(file_path, attributes)
            node = self._getNode(index)
            node.setAttributes(attributes)
            self.dataChanged.emit(index, index)
            self.fileAttributeChanged.emit(file_path)
            return True
        except Exception as e:
            RobustLogger().error(f"Error setting file attributes: {e}")
            self._showErrorMessage(f"Error setting file attributes: {e}")
            return False

    def supportedDragActions(self) -> Qt.DropActions:
        return Qt.CopyAction | Qt.MoveAction

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.CopyAction | Qt.MoveAction

    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not data.hasUrls():
            return False
        if column > 0:
            return False
        return True

    async def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not self.canDropMimeData(data, action, row, column, parent):
            return False

        if action == Qt.IgnoreAction:
            return True

        parent_path = self.filePath(parent) if parent.isValid() else self.rootPath()

        async def process_url(url):
            srcPath = url.toLocalFile()
            destPath = os.path.join(parent_path, os.path.basename(srcPath))
            try:
                if action == Qt.CopyAction:
                    await self._copyFileAsync(srcPath, destPath)
                elif action == Qt.MoveAction:
                    await self._moveFileAsync(srcPath, destPath)
            except Exception as e:
                self._showErrorMessage(f"Error during drag and drop operation: {e}")

        await asyncio.gather(*[process_url(url) for url in data.urls()])
        return True

    def _copyFile(self, src: str, dest: str):
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            self._refresh()
        except OSError as e:
            RobustLogger().error(f"Error copying file: {e}")
            self._showErrorMessage(f"Error copying file: {e}")

    def _moveFile(self, src: str, dest: str):
        try:
            shutil.move(src, dest)
            self._refresh()
        except OSError as e:
            self._showErrorMessage(f"Error moving file: {e}")

    async def _copyFileAsync(self, src: str, dest: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, shutil.copy2, src, dest)
        self._refreshDirectory(os.path.dirname(dest))

    async def _moveFileAsync(self, src: str, dest: str):
        await self._loop.run_in_executor(None, shutil.move, src, dest)
        await self._loop.run_in_executor(None, self._refreshDirectory, os.path.dirname(src))  # noqa: PTH120
        await self._loop.run_in_executor(None, self._refreshDirectory, os.path.dirname(dest))  # noqa: PTH120

    @asyncSlot()
    async def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:

        parent_path = self.filePath(parent) if parent.isValid() else self.rootPath()

        async def process_url(url):
            srcPath = url.toLocalFile()
            destPath = os.path.join(parent_path, os.path.basename(srcPath))  # noqa: PTH118, PTH119
            try:
                if action == Qt.CopyAction:
                    await self._copyFileAsync(srcPath, destPath)
                elif action == Qt.MoveAction:
                    await self._moveFileAsync(srcPath, destPath)
            except Exception as e:
                self._showErrorMessage(f"Error during drag and drop operation: {e}")
                return False

        await asyncio.gather(*[process_url(url) for url in data.urls()])
        return True

    def _applyFilters(self, files: list[str]) -> list[str]:
        filtered_files = self._applyNameFilters(files)
        filtered_files = self._applyCustomFilters(filtered_files)
        return filtered_files

    @asyncSlot()
    async def refreshPath(self, path: str):
        try:
            node = self._nodeForPath(path)
            if node:
                await self._refreshDirectory(path)
            else:
                RobustLogger().warning(f"Attempted to refresh non-existent path: {path}")
        except Exception as e:
            RobustLogger().error(f"Error refreshing path {path}: {e}")
            RobustLogger().debug(traceback.format_exc())
            self._showErrorMessage(f"Error refreshing path: {e}")

    def _loadFileAttributes(self, index: QModelIndex):
        if not index.isValid():
            return

        node = self._getNode(index)
        file_path = self.filePath(index)

        try:
            file_info = self._getFileInfoCached(file_path)
            node.setAttributes(file_info.attributes())
            node.setPermissions(file_info.permissions())

            self.dataChanged.emit(index, index)
            self.fileAttributeChanged.emit(file_path)
        except Exception as e:
            RobustLogger().error(f"Error loading file attributes for {file_path}: {e}")
            self._showErrorMessage(f"Error loading file attributes: {e}")

    def _resetErrorRetryCount(self, path: str):
        if path in self._error_retry_count:
            del self._error_retry_count[path]

    def _retryOperation(self, operation: Callable, *args, max_retries: int = 3, **kwargs):
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:  # noqa: PERF203
                if attempt == max_retries - 1:
                    RobustLogger().error(f"Operation failed after {max_retries} attempts: {e}")
                    self._showErrorMessage(f"Operation failed: {e}")
                    return None
                time.sleep(min(2**attempt, 30))  # Exponential backoff with a maximum of 30 seconds
        return None

    def setCacheExpiration(self, seconds: int):
        self._cache_expiration = seconds

    def getCacheExpiration(self) -> int:
        return self._cache_expiration

    def _refreshCache(self):
        current_time = QDateTime.currentDateTime()
        expired_keys = [k for k, v in self._cache.items() if v[1].secsTo(current_time) >= self._cache_expiration]
        for key in expired_keys:
            del self._cache[key]
        self._clearCache(emit_signal=True)

    def setWatcherCleanupInterval(self, seconds: int):
        self._watcher_cleanup_interval = seconds

    def getWatcherCleanupInterval(self) -> int:
        return self._watcher_cleanup_interval

    def _worker(self, task_queue: multiprocessing.JoinableQueue, result_queue: multiprocessing.Queue):
        while True:
            task = task_queue.get()
            if task is None:
                break
            task_name, args = task
            try:
                if task_name == "fetch_extended_information":
                    self._fileInfoGatherer.fetchExtendedInformation(*args)
                elif task_name == "refresh_directory":
                    self._refreshDirectory(*args)
                elif task_name == "refresh_file":
                    self._refreshFile(*args)
                elif task_name == "process_drop":
                    result = self._processDrop(*args)
                    result_queue.put(("process_drop", result))
            except Exception as e:
                RobustLogger().error(f"Error in worker process: {e}")
                result_queue.put(("error", str(e)))


if __name__ == "__main__":
    import sys

    import qasync

    app = QApplication(sys.argv)
    model = PyQFileSystemModel()
    root_path = QDir.homePath()
    model.setRootPath(root_path)

    view = QTreeView()
    view.setModel(model)
    view.setRootIndex(model.index(root_path))
    view.show()

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        loop.run_forever()
    async def _copyFile(self, src: str, dest: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, shutil.copy2, src, dest)
        self._refreshDirectory(os.path.dirname(dest))

    async def _moveFile(self, src: str, dest: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, shutil.move, src, dest)
        self._refreshDirectory(os.path.dirname(src))
        self._refreshDirectory(os.path.dirname(dest))
    def _retryOperation(self, operation: Callable, *args, max_retries: int = 3, **kwargs):
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    RobustLogger().error(f"Operation failed after {max_retries} attempts: {e}")
                    self._showErrorMessage(f"Operation failed: {e}")
                    return None
                time.sleep(min(2**attempt, 30))  # Exponential backoff with a maximum of 30 seconds
