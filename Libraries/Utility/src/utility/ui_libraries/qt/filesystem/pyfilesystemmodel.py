from __future__ import annotations

import logging
import os
import shutil
import traceback

from functools import lru_cache
from multiprocessing import Process, Queue
from typing import Any, Callable

from PyQt5.QtCore import (
    QAbstractItemModel,
    QDateTime,
    QDir,
    QFileInfo,
    QMimeData,
    QModelIndex,
    QMutex,
    QMutexLocker,
    QObject,
    QUrl,
    Qt,
    pyqtSignal as Signal,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyle

from .pyfileinfogatherer import PyFileInfoGatherer
from .pyfilesystemmodelsorter import PyFileSystemModelSorter, SortingError
from .pyfilesystemnode import PyFileSystemNode
from .pyfilesystemwatcher import FileSystemWatcherError, PyFileSystemWatcher

logger = logging.getLogger(__name__)

class PyQFileSystemModel(QAbstractItemModel):
    directoryLoaded = Signal(str)
    rootPathChanged = Signal(str)
    fileRenamed = Signal(str, str, str)
    directoryWatchError = Signal(str)
    fileSystemChanged = Signal()
    sortingChanged = Signal()
    dragDropError = Signal(str)
    filterApplied = Signal()
    fileAttributeChanged = Signal(str)
    customDataChanged = Signal(QModelIndex, QModelIndex, object)
    asyncOperationError = Signal(str)
    sortingError = Signal(str)
    fileSystemWatcherError = Signal(str)
    cacheUpdated = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._root = PyFileSystemNode()
        self._fileInfoGatherer = PyFileInfoGatherer(self)
        self._sorter = PyFileSystemModelSorter(self)
        self._fileSystemWatcher = PyFileSystemWatcher(self)
        self._filters = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs
        self._nameFilters = []
        self._task_queue = Queue()
        self._result_queue = Queue()
        self._worker_process = Process(target=self._worker, args=(self._task_queue, self._result_queue))
        self._worker_process.start()

        self._fileInfoGatherer.newListOfFiles.connect(self._addNewListOfFiles)
        self._fileInfoGatherer.updates.connect(self._handleUpdates)
        self._fileInfoGatherer.directoryLoaded.connect(self._handleDirectoryLoaded)
        self._fileSystemWatcher.directoryChanged.connect(self._handleDirectoryChanged)
        self._fileSystemWatcher.fileChanged.connect(self._handleFileChanged)

        self._resolveSymlinks = False
        self._readOnly = False
        self._rootPath = ""
        self._sortColumn = 0
        self._sortOrder = Qt.AscendingOrder
        self._nameFilterDisables = False
        self._cache = {}
        self._customRoles = {}
        self._fileTypeFilters = []
        self._customSorting = None
        self._customFilters = []
        self._dragEnabled = True
        self._mutex = QMutex()
        self._error_retry_count = {}
        self._cache_expiration = 60  # Cache expiration time in seconds
        self._file_watcher_cache = {}
        self._max_watcher_paths = 100

    def __del__(self):
        self._worker_process.terminate()
        self._worker_process.join()
        for watcher in self._file_watcher_cache.values():
            watcher.deleteLater()
        super().__del__()

    def nodeFromIndex(self, index: QModelIndex) -> PyFileSystemNode:
        return index.internalPointer() if index.isValid() else self._root

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
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

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0

        parentItem = self.nodeFromIndex(parent)
        return len(parentItem.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 4  # Name, Size, Type, Date Modified

    @lru_cache(maxsize=10000)
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.column() >= self.columnCount():
            return None

        item = self.nodeFromIndex(index)

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return item.fileName
            elif index.column() == 1:
                return self._sizeString(item.size())
            elif index.column() == 2:
                return item.type()
            elif index.column() == 3:
                return item.lastModified().toString()
        elif role == Qt.DecorationRole and index.column() == 0 and self._style:
            return self._style.standardIcon(QStyle.SP_FileIcon if item.isFile() else QStyle.SP_DirIcon)
        elif role in self._customRoles:
            return self._customRoles[role](item)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Name"
            elif section == 1:
                return "Size"
            elif section == 2:
                return "Type"
            elif section == 3:
                return "Date Modified"
        return None

    def setRootPath(self, path: str) -> QModelIndex:
        if path == self._rootPath and self._root:
            return self.index(0, 0, QModelIndex())

        self._rootPath = path
        self._root = PyFileSystemNode(path)
        self.beginResetModel()
        self._task_queue.put(('fetch_extended_information', (path, [])))
        self._clearCache(emit_signal=True)
        
        if self._fileSystemWatcher.directories():
            self._fileSystemWatcher.removePaths(self._fileSystemWatcher.directories())
        self._watchPath(path)
        self.rootPathChanged.emit(path)
        self.endResetModel()
        return self.index(0, 0, QModelIndex())

    def rootPath(self) -> str:
        return self._rootPath

    def setIconProvider(self, provider: QFileIconProvider):
        self._fileInfoGatherer.setIconProvider(provider)

    def iconProvider(self) -> QFileIconProvider:
        return self._fileInfoGatherer.m_iconProvider

    def _handleDirectoryChanged(self, path: str):
        self._task_queue.put(('refresh_directory', (path,)))
        self.fileSystemChanged.emit(path)

    def _handleFileChanged(self, path: str):
        self._task_queue.put(('refresh_file', (path,)))
        self.fileSystemChanged.emit(path)

    def _refreshDirectory(self, path: str):
        try:
            node = self._nodeForPath(path)
            if node is None:
                return

            old_list = set(node.children.keys())
            new_list = set(os.listdir(path))

            for name in old_list - new_list:
                self._removeNode(node.children[name])

            for name in new_list - old_list:
                self._addNode(node, name)

            for name in old_list & new_list:
                self._updateNode(node.children[name])

            self.layoutChanged.emit()
        except Exception as e:
            logger.error(f"Error refreshing directory {path}: {e}")
            logger.debug(traceback.format_exc())
            self._showErrorMessage(f"Error refreshing directory: {e}")

    def _refreshFile(self, path: str):
        try:
            parent_path = os.path.dirname(path)
            file_name = os.path.basename(path)
            parent_node = self._nodeForPath(parent_path)
            if parent_node and file_name in parent_node.children:
                self._updateNode(parent_node.children[file_name])
            else:
                self._refreshDirectory(parent_path)
            self.layoutChanged.emit()
        except Exception as e:
            logger.error(f"Error refreshing file {path}: {e}")
            logger.debug(traceback.format_exc())
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
        with QMutexLocker(self._mutex):
            parent = node.parent
            if parent:
                row = list(parent.children.values()).index(node)
                self.beginRemoveRows(self.createIndex(parent.row(), 0, parent), row, row)
                del parent.children[node.fileName]
                self.endRemoveRows()
                self._clearCache(emit_signal=True)
        self.layoutChanged.emit()

    def _addNode(self, parent: PyFileSystemNode, name: str):
        with QMutexLocker(self._mutex):
            if name not in parent.children:
                new_node = PyFileSystemNode(name, parent)
                row = len(parent.children)
                self.beginInsertRows(self.createIndex(parent.row(), 0, parent), row, row)
                parent.children[name] = new_node
                self.endInsertRows()
        self._clearCache(emit_signal=True)
        self.layoutChanged.emit()

    def _updateNode(self, node: PyFileSystemNode):
        info = QFileInfo(self.filePath(self.createIndex(node.row(), 0, node)))
        node.populate(info)
        index = self.createIndex(node.row(), 0, node)
        self.dataChanged.emit(index, index.sibling(index.row(), self.columnCount() - 1))
        self._clearCache()
        self.layoutChanged.emit()

    def _getFileInfo(self, path: str) -> QFileInfo:
        return QFileInfo(path)

    def setFilter(self, filters: QDir.Filters):
        if self._filters != filters:
            self._filters = filters
            self._refresh()
            self.filterApplied.emit()

    def filter(self) -> QDir.Filters:
        return self._filters

    def setNameFilters(self, filters: list[str]):
        self._nameFilters = filters
        self._refresh()
        self.filterApplied.emit()

    def nameFilters(self) -> list[str]:
        return self._nameFilters

    def setNameFilterDisables(self, enable: bool):
        if self._nameFilterDisables != enable:
            self._nameFilterDisables = enable
            self._refresh()

    def isNameFilterDisables(self) -> bool:
        return self._nameFilterDisables

    def setFileTypeFilter(self, filters: list[str]):
        self._fileTypeFilters = filters
        self._refresh()
        self.filterApplied.emit()

    def fileTypeFilters(self) -> list[str]:
        return self._fileTypeFilters

    def _refresh(self):
        self.beginResetModel()
        self._root = PyFileSystemNode(self.rootPath())
        self._fileInfoGatherer.fetchExtendedInformation(self.rootPath(), [])
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

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:
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
            path.append(node.fileName)
            node = node.parent
        return os.path.join(self.rootPath(), *reversed(path))

    def fileName(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        return self._getNode(index).fileName

    def isDir(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        return self._getNode(index).isDir()

    def size(self, index: QModelIndex) -> int:
        if not index.isValid():
            return 0
        return self._getNode(index).size()

    def type(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        return self._getNode(index).type()

    def permissions(self, index: QModelIndex) -> QDir.Permissions:
        if not index.isValid() or not self.isDir(index):
            return QDir.Permissions()
        return self._getNode(index).permissions()

    def lastModified(self, index: QModelIndex) -> QDateTime:
        if not index.isValid():
            return QDateTime()
        return self._getNode(index).lastModified()

    def fileInfo(self, index: QModelIndex) -> QFileInfo:
        if not index.isValid():
            return QFileInfo()
        path = self.filePath(index)
        info = QFileInfo(path)
        return info

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
                os.unlink(path)
            self._removeNode(node)
            return True
        except OSError as e:
            logger.error(f"Error removing file/directory: {e}")
            self._showErrorMessage(f"Error removing file/directory: {e}")
            return False

    def mkdir(self, parent: QModelIndex, name: str) -> QModelIndex:
        if not parent.isValid():
            return QModelIndex()
        parent_node = self._getNode(parent)
        path = os.path.join(self.filePath(parent), name)
        try:
            os.mkdir(path)
            new_node = PyFileSystemNode(name, parent_node)
            row = len(parent_node.children)
            self.beginInsertRows(parent, row, row)
            parent_node.children[name] = new_node
            self.endInsertRows()
            return self.createIndex(row, 0, new_node)
        except OSError as e:
            logger.error(f"Error creating directory: {e}")
            self._showErrorMessage(f"Error creating directory: {e}")
            return QModelIndex()

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.CopyAction | Qt.MoveAction

    def mimeTypes(self) -> list[str]:
        return ["text/uri-list"]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        urls = [QUrl.fromLocalFile(self.filePath(index)) for index in indexes if index.column() == 0]
        mimeData = QMimeData()
        mimeData.setUrls(urls)
        return mimeData

    def _copyFile(self, src: str, dest: str):
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            self._refresh()
        except OSError as e:
            logger.error(f"Error copying file: {e}")
            self._showErrorMessage(f"Error copying file: {e}")
    
    def _moveFile(self, src: str, dest: str):
        try:
            shutil.move(src, dest)
            self._refresh()
        except OSError as e:
            self._showErrorMessage(f"Error moving file: {e}")

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
            logger.error(f"Error renaming file: {e}")
            self._showErrorMessage(f"Error renaming file: {e}")
            return False

        node.fileName = newName
        self.dataChanged.emit(index, index)
        self.fileRenamed.emit(parentPath, oldName, newName)
        return True

    def setCustomSorting(self, sortFunction: Callable[[PyFileSystemNode, PyFileSystemNode], int]):
        self._customSorting = sortFunction
        self.sort(self._sortColumn, self._sortOrder)

    async def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._sortColumn = column
        self._sortOrder = order
        try:
            if self._customSorting:
                self._root.children = dict(sorted(self._root.children.items(), key=lambda x: self._customSorting(x[1], x[1])))
            else:
                await self._consumer_manager.run_in_executor(self._sorter.sort, self._root, column, order)
        except SortingError as e:
            logger.error(f"Sorting error: {e}")
            self.sortingError.emit(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during sorting: {e}")
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

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
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

    def _handleUpdates(self, path: str, updates: list[tuple[str, QFileInfo]]):
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

    def _handleDirectoryLoaded(self, path: str):
        self._refreshCache()
        self.directoryLoaded.emit(path)

    def _watchPath(self, path: str):
        if path not in self._file_watcher_cache:
            watcher = PyFileSystemWatcher()
            watcher.directoryChanged.connect(lambda p=path: self._handleDirectoryChanged(p))
            watcher.fileChanged.connect(lambda p=path: self._handleFileChanged(p))
            watcher.addPath(path)
            self._file_watcher_cache[path] = watcher

        # Optimize watchers if necessary
        if len(self._file_watcher_cache) > self._max_watcher_paths:
            self._optimizeWatchers()

    def _cleanupWatchers(self):
        current_time = QDateTime.currentDateTime()
        for path, watcher in list(self._file_watcher_cache.items()):
            if current_time.secsTo(watcher.lastUsed()) > self._watcher_cleanup_interval:
                watcher.removePath(path)
                del self._file_watcher_cache[path]

    def _optimizeWatchers(self):
        sorted_watchers = sorted(self._file_watcher_cache.items(),
                                 key=lambda x: (len(x[1].files()) + len(x[1].directories()), x[1].lastUsed.secsTo(QDateTime.currentDateTime())))
        for path, watcher in sorted_watchers[:len(sorted_watchers) // 2]:
            watcher.removePath(path)
            watcher.deleteLater()
            del self._file_watcher_cache[path]

    def setSorting(self, column: int, order: Qt.SortOrder):
        if self._sortColumn != column or self._sortOrder != order:
            self._sortColumn = column
            self._sortOrder = order
            self.sort(column, order)

    def isDir(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        return self._getNode(index).isDir()

    def fileIcon(self, index: QModelIndex) -> QIcon:
        if not index.isValid():
            return QIcon()
        return self._style.standardIcon(QStyle.SP_FileIcon if self._getNode(index).isFile() else QStyle.SP_DirIcon)

    def fileInfo(self, index: QModelIndex) -> QFileInfo:
        return QFileInfo(self.filePath(index))

    def _showErrorMessage(self, message: str):
        logger.error(message)
        if QApplication.instance():
            QMessageBox.warning(None, "Error", message)
        self.asyncOperationError.emit(message)

    def dragMoveEvent(self, event):
        event.accept()

    @asyncSlotSaved()
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
        if not self._nameFilters:
            return files
        
        import fnmatch
        filtered_files = []
        for file in files:
            if any(fnmatch.fnmatch(file, pattern) for pattern in self._nameFilters):
                filtered_files.append(file)
            elif self._nameFilterDisables:
                filtered_files.append(file)
        if self._fileTypeFilters:
            filtered_files = [file for file in filtered_files if any(file.endswith(ext) for ext in self._fileTypeFilters)]
        
        filtered_files = self._applyCustomFilters(filtered_files)
        return filtered_files

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
                    self._copyFile(srcPath, destPath)
                elif action == Qt.MoveAction:
                    self._moveFile(srcPath, destPath)
                else:
                    return False
            except Exception as e:
                self._showErrorMessage(f"Error during drag and drop operation: {e}")
                return False
        return True

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        self._task_queue.put(('process_drop', (data, action, parent)))
        return True

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
            logger.error(f"Error setting file permissions: {e}")
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
            logger.error(f"Error setting file attributes: {e}")
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

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not self.canDropMimeData(data, action, row, column, parent):
            return False

        if action == Qt.IgnoreAction:
            return True

        parent_path = self.filePath(parent) if parent.isValid() else self.rootPath()

        async def process_url(url):
            srcPath = url.toLocalFile()
            destPath = os.path.join(parentPath, os.path.basename(srcPath))
            try:
                asyncio.create_task(self._copyFile(srcPath, destPath) if action == Qt.CopyAction else self._moveFile(srcPath, destPath))
            except Exception as e:
                self._showErrorMessage(f"Error during drag and drop operation: {e}")

        asyncio.create_task(asyncio.gather(*[process_url(url) for url in data.urls()]))

        return True

    def _applyFilters(self, files: list[str]) -> list[str]:
        filtered_files = self._applyNameFilters(files)
        filtered_files = self._applyCustomFilters(filtered_files)
        return filtered_files

    def refreshPath(self, path: str):
        try:
            node = self._nodeForPath(path)
            if node:
                self._refreshDirectory(path)
            else:
                logger.warning(f"Attempted to refresh non-existent path: {path}")
        except Exception as e:
            logger.error(f"Error refreshing path {path}: {e}")
            logger.debug(traceback.format_exc())
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
            logger.error(f"Error loading file attributes for {file_path}: {e}")
            self._showErrorMessage(f"Error loading file attributes: {e}")

    def _resetErrorRetryCount(self, path: str):
        if path in self._error_retry_count:
            del self._error_retry_count[path]

    def _retryOperation(self, operation: Callable, *args, max_retries: int = 3, **kwargs):
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Operation failed after {max_retries} attempts: {e}")
                    self._showErrorMessage(f"Operation failed: {e}")
                    return None
                time.sleep(min(2 ** attempt, 30))  # Exponential backoff with a maximum of 30 seconds

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

    def _worker(self, task_queue: Queue, result_queue: Queue):
        while True:
            task = task_queue.get()
            if task is None:
                break
            task_name, args = task
            try:
                if task_name == 'fetch_extended_information':
                    self._fileInfoGatherer.fetchExtendedInformation(*args)
                elif task_name == 'refresh_directory':
                    self._refreshDirectory(*args)
                elif task_name == 'refresh_file':
                    self._refreshFile(*args)
                elif task_name == 'process_drop':
                    result = self._processDrop(*args)
                    result_queue.put(('process_drop', result))
            except Exception as e:
                logger.error(f"Error in worker process: {e}")
                result_queue.put(('error', str(e)))

    # Main execution block

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    model = PyQFileSystemModel()
    root_path = QDir.homePath()
    model.setRootPath(root_path)

    view = QTreeView()
    view.setModel(model)
    view.setRootIndex(model.index(root_path))
    view.show()
    
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    with event_loop:
        try:
            event_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            for task in asyncio.all_tasks(event_loop):
                task.cancel()
            event_loop.run_until_complete(event_loop.shutdown_asyncgens())
