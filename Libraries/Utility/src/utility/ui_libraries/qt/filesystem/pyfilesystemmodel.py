from __future__ import annotations

import os
import pathlib
import shutil
import sys
import typing

from contextlib import suppress
from ctypes import pointer
from typing import TYPE_CHECKING, Any, ClassVar, Iterable, overload

import qtpy  # noqa: E402

from loggerplus import RobustLogger  # noqa: E402
from qtpy.QtCore import QAbstractItemModel, QBasicTimer, QDir, QFileDevice, QFileInfo, QMimeData, QModelIndex, QMutex, QMutexLocker, QTimer, QUrl, QVariant, Qt
from qtpy.QtGui import QIcon  # noqa: E402
from qtpy.QtWidgets import QApplication, QFileIconProvider, QFileSystemModel, QMainWindow, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if __name__ == "__main__":
    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)


    file_absolute_path = pathlib.Path(__file__).resolve()

    pykotor_path = file_absolute_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    pykotor_gl_path = file_absolute_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if pykotor_gl_path.exists():
        update_sys_path(pykotor_gl_path.parent)
    utility_path = file_absolute_path.parents[6] / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        update_sys_path(utility_path)
    toolset_path = file_absolute_path.parents[3] / "toolset"
    if toolset_path.exists():
        update_sys_path(toolset_path.parent)
        os.chdir(toolset_path)

from pathlib import Path  # noqa: E402

from utility.ui_libraries.qt.filesystem.common.pyfileinfogatherer import PyFileInfoGatherer  # noqa: E402
from utility.ui_libraries.qt.filesystem.common.pyfilesystemnode import PyFileSystemNode  # noqa: E402

if TYPE_CHECKING:
    from ctypes import _Pointer, c_bool

    from qtpy.QtCore import (  # pyright: ignore[reportPrivateImportUsage]  # noqa: E402  # noqa: E402  # noqa: E402
        QDateTime,
        QObject,
        QTimerEvent,
        Signal,
    )
    from qtpy.QtWidgets import QScrollBar
    from typing_extensions import Literal


if qtpy.API_NAME in ("PyQt6", "PySide6"):
    QDesktopWidget = None
    from qtpy.QtGui import (  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
        QUndoCommand,
        QUndoStack,
    )
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import (  # noqa: F401  # pyright: ignore[reportPrivateImportUsage]
        QDesktopWidget,
        QUndoCommand,
        QUndoStack,
    )
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")


if os.name == "nt_disabled":
    from ctypes import POINTER, byref, windll
    from ctypes.wintypes import LPCWSTR

    from utility.system.win32.com.com_types import GUID
    from utility.system.win32.com.interfaces import SIGDN, IShellItem
    from utility.system.win32.hresult import HRESULT

    try:
        import comtypes  # pyright: ignore[reportMissingTypeStubs]

        from comtypes.automation import (  # pyright: ignore[reportMissingTypeStubs]
            BSTR,
            IUnknown,
        )
    except ImportError:
        RobustLogger().error("Could not setup the comtypes library, volume functionality will be disabled.")
    else:

        def volumeName(path: str) -> str:
            comtypes.CoInitialize()
            # Create the IShellItem instance for the given path
            SHCreateItemFromParsingName = windll.shell32.SHCreateItemFromParsingName
            print("<SDM> [volumeName scope] SHCreateItemFromParsingName: ", SHCreateItemFromParsingName)

            SHCreateItemFromParsingName.argtypes = [LPCWSTR, POINTER(IUnknown), POINTER(GUID), POINTER(POINTER(IShellItem))]
            print("<SDM> [volumeName scope] SHCreateItemFromParsingName.argtypes: ", SHCreateItemFromParsingName.argtypes)

            SHCreateItemFromParsingName.restype = HRESULT
            print("<SDM> [volumeName scope] SHCreateItemFromParsingName.restype: ", SHCreateItemFromParsingName.restype)

            pShellItem = POINTER(IShellItem)()
            print("<SDM> [volumeName scope] pShellItem: ", pShellItem)

            hr = SHCreateItemFromParsingName(path, POINTER(IUnknown)(), byref(IShellItem._iid_), byref(pShellItem))
            print("<SDM> [volumeName scope] hr: ", hr)

            HRESULT.raise_for_status(hr, "SHCreateItemFromParsingName failed.")

            name = BSTR()
            print("<SDM> [volumeName scope] name: ", name)

            hr = pShellItem.GetDisplayName(SIGDN.SIGDN_NORMALDISPLAY, comtypes.byref(name))
            print("<SDM> [volumeName scope] hr: ", hr)

            if hr != 0:
                raise OSError(f"GetDisplayName failed! HRESULT: {hr}")

            result = name.value
            print("<SDM> [volumeName scope] result: ", result)

            return result
else:

    def volumeName(path: str) -> str:
        return path


def filewatcherenabled(default: bool = True) -> bool:  # noqa: FBT001, FBT002
    watchFiles = os.environ.get("QT_FILESYSTEMMODEL_WATCH_FILES", "").strip()
    if watchFiles:
        with suppress(ValueError):
            return bool(int(watchFiles))
    return default


class PyFileSystemModel(QAbstractItemModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._rootDir: QDir = QDir()
        self._fileInfoGatherer: PyFileInfoGatherer = PyFileInfoGatherer(self)  # Use QFileInfoGatherer
        self.__fileInfoGathererLock: QMutex = QMutex()
        self._delayedSortTimer: QTimer = QTimer()
        self._delayedSortTimer.setSingleShot(True)
        self._bypassFilters: dict[PyFileSystemNode, Any] = {}
        self._nameFilters: list[str] = []
        self._resolvedSymLinks: dict[Any, Any] = {}  # Dictionary for resolved symlinks
        self._root: PyFileSystemNode = PyFileSystemNode("")
        self._toFetch: list[dict[Literal["node", "dir", "file"], Any]] = []
        self._filesToFetch: list[str] = []
        self._fetchingTimer: QBasicTimer = QBasicTimer()
        self._filters: QDir.Filters | int = QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs
        self._sortColumn: int = 0
        self._sortOrder: Qt.SortOrder = Qt.SortOrder.AscendingOrder
        self._forceSort: bool = True
        self._readOnly: bool = True
        self._setRootPath: bool = False
        self._nameFilterDisables = os.name == "posix"  # False on windows, True on mac and unix
        # This flag is an optimization for QFileDialog. It enables a sort which is
        # not recursive, meaning we sort only what we see.
        self._disableRecursiveSort: bool = False

        # Connections
        self._fileInfoGatherer.updates.connect(self._q_fileSystemChanged)
        self._fileInfoGatherer.newListOfFiles.connect(self._q_directoryChanged)
        self._fileInfoGatherer.nameResolved.connect(self._q_resolvedName)
        # self._fileInfoGatherer.directoryLoaded.connect(self._q_directoryChanged)
        self._delayedSortTimer.timeout.connect(self._q_performDelayedSort)

        def shutdownFileGatherer(abort_atom: _Pointer[c_bool]):
            with QMutexLocker(self.__fileInfoGathererLock):
                abort_atom.contents.value = True

        app = QApplication.instance()
        assert app is not None
        with QMutexLocker(self.__fileInfoGathererLock):
            app.aboutToQuit.connect(lambda atom=pointer(self._fileInfoGatherer.abort): shutdownFileGatherer(atom))  # noqa: B008

    def _watchPaths(self, paths: list[str]):
        self._fileInfoGatherer.watchPaths(paths)

    def createIndex(self, row: int, column: int, obj: Any = ...) -> QModelIndex:
        print(f"createIndex(row={row}, col={column}, obj(type)={obj.__class__.__name__})")
        if isinstance(obj, PyFileSystemNode):
            objFileInfo = obj.fileInfo()
            print(f"createItem: item being created for path: {None if objFileInfo is None else objFileInfo.path()}, filename={obj.fileName}")
        newIndex = super().createIndex(row, column, obj)
        test: bool = newIndex.isValid()
        assert test, f"createIndex's newIndex.isValid(): {test}"
        return newIndex

    def _q_directoryChanged(self, directory: str, files: list[str] | None = None):
        parentNode = self.node(directory, fetch=False)
        RobustLogger().warning(
            f"<SDM> [_q_directoryChanged scope] parentNode: {parentNode} row: {parentNode.row()} path: {parentNode.fileInfo() and parentNode.fileInfo().path()}"
        )

        if len(parentNode.children) == 0:
            return

        if files is None:
            toRemove = [child.fileName for child in parentNode.children.values()]
            print("<SDM> [_q_directoryChanged scope] toRemove: ", toRemove, "length:", len(toRemove))

        else:
            newFilesList = sorted(files)
            print("<SDM> [_q_directoryChanged scope] newFilesList: ", newFilesList, "entry count: ", len(newFilesList))

            toRemove = []
            for child in parentNode.children.values():
                fileName = child.fileName
                print("<SDM> [_q_directoryChanged scope] fileName: ", fileName)

                index = self._binary_search(newFilesList, fileName)
                print("<SDM> [_q_directoryChanged scope] binary search index: ", index)

                if index == len(newFilesList) or newFilesList[index] != fileName:
                    print("<SDM> [_q_directoryChanged scope] remove index: ", index, "fileName: ", fileName)

                    toRemove.append(fileName)

        for fileName in toRemove:
            self.removeNode(parentNode, fileName)

    def _binary_search(self, sorted_list: list[str], item: str) -> int:
        """Helper function to perform binary search on a sorted list."""
        low, high = 0, len(sorted_list)
        while low < high:
            mid = (low + high) // 2
            print("<SDM> [_binary_search scope] mid: ", mid)

            if sorted_list[mid] < item:
                low = mid + 1
                print("<SDM> [_binary_search scope] low: ", low)

            else:
                high = mid
                print("<SDM> [_binary_search scope] high: ", high)

        return low

    def _q_fileSystemChanged(self, path: str, updates: list[tuple[str, QFileInfo]]):  # noqa: C901, PLR0912
        parentNode = self.node(self.index(path))
        if not parentNode:
            return
        print(
            "<SDM> [_q_fileSystemChanged scope] parentNode: ",
            parentNode,
            "row:",
            parentNode.row(),
            "col:",
            parentNode.row(),
            "path:",
            parentNode.fileInfo() and parentNode.fileInfo().path(),
        )

        rowsToUpdate: list[str] = []
        newFiles: list[str] = []

        for fileName, file_info in updates:
            if fileName not in parentNode.children:
                # Add new node if it doesn't exist
                self.addNode(parentNode, fileName, file_info)
                newFiles.append(fileName)
            else:
                node = parentNode.children[fileName]
                print("<SDM> [_q_fileSystemChanged node.fileName ", node.fileName)

                if node.fileName == fileName:
                    node.populate(file_info)
                    if self.filtersAcceptNode(node):
                        if node.isVisible:
                            rowsToUpdate.append(fileName)
                        else:
                            newFiles.append(fileName)
                    elif node.isVisible:
                        visibleLocation = parentNode.visibleChildren.index(fileName)
                        print("<SDM> [_q_fileSystemChanged scope] visibleLocation: ", visibleLocation)

                        self.removeVisibleFile(parentNode, visibleLocation)

        if rowsToUpdate:
            for fileName in rowsToUpdate:
                row = parentNode.visibleChildren.index(fileName)
                topLeft = self.index(row, 0, self.index(path))
                bottomRight = self.index(row, self.columnCount() - 1, self.index(path))

                self.dataChanged.emit(topLeft, bottomRight)

        if newFiles:
            self.addVisibleFiles(parentNode, newFiles)

        if newFiles or (self._sortColumn != 0 and rowsToUpdate):
            self._forceSort = True
            self._q_performDelayedSort()

    if os.name == "nt":

        def _unwatchPathsAt(self, index: QModelIndex) -> list[str]:
            indexNode = self.node(index)
            print("<SDM> [_unwatchPathsAt scope] indexNode: ", indexNode, "row:", indexNode.row(), indexNode.fileName)

            if indexNode is None:
                return []

            caseSensitivity = Qt.CaseSensitivity.CaseSensitive if indexNode.caseSensitive() else Qt.CaseSensitivity.CaseInsensitive
            fInfo = indexNode.fileInfo()

            path = None if fInfo is None else fInfo.filePath()
            print("<SDM> [_unwatchPathsAt scope] path: ", path)
            if path is None:
                return []

            result: list[str] = []

            def filter_paths(watchedPath: str) -> bool:  # noqa: N803
                pathSize = len(path)
                print("<SDM> [filter_paths scope] pathSize: ", pathSize)

                if len(watchedPath) == pathSize:
                    print("<SDM> [filter_paths scope] path: ", path)
                    return (path == watchedPath) if caseSensitivity == Qt.CaseSensitive else (path.lower() == watchedPath.lower())

                if len(watchedPath) > pathSize:
                    print("<SDM> [filter_paths scope] watchedPath[pathSize]: ", watchedPath[pathSize])
                    return watchedPath[pathSize] == "/" and (
                        watchedPath.startswith(path) if caseSensitivity == Qt.CaseSensitive else watchedPath.lower().startswith(path.lower())
                    )

                return False

            # Get watched files and directories
            watchedFiles: list[str] = self._fileInfoGatherer.watchedFiles()
            watchedDirectories: list[str] = self._fileInfoGatherer.watchedDirectories()

            # Apply filter to watched files and directories
            result.extend(filter(filter_paths, watchedFiles))
            result.extend(filter(filter_paths, watchedDirectories))

            # Unwatch the filtered paths
            self._fileInfoGatherer.unwatchPaths(result)

            return result

    def addVisibleFiles(self, parentNode: PyFileSystemNode, newFiles: list[str]):  # noqa: N803
        parentIndex = self.index(parentNode)
        indexHidden = self.isHiddenByFilter(parentNode, parentIndex)

        if not indexHidden:
            self.beginInsertRows(parentIndex, len(parentNode.visibleChildren), len(parentNode.visibleChildren) + len(newFiles) - 1)

        if parentNode.dirtyChildrenIndex == -1:
            parentNode.dirtyChildrenIndex = len(parentNode.visibleChildren)

        for newFile in newFiles:
            parentNode.visibleChildren.append(newFile)
            parentNode.children[newFile].isVisible = True

        if not indexHidden:
            self.endInsertRows()

    def removeVisibleFile(self, parentNode: PyFileSystemNode, vLocation: int):  # noqa: N803
        if vLocation == -1:
            return
        parent = self.index(parentNode)
        indexHidden = self.isHiddenByFilter(parentNode, parent)
        if not indexHidden:
            self.beginRemoveRows(
                parent,
                self.translateVisibleLocation(parentNode, vLocation),
                self.translateVisibleLocation(parentNode, vLocation),
            )
        parentNode.children[parentNode.visibleChildren[vLocation]].isVisible = False
        parentNode.visibleChildren.pop(vLocation)
        if not indexHidden:
            self.endRemoveRows()

    def _q_resolvedName(self, fileName, resolvedName):  # noqa: N803
        print(f"<SDM> [_q_resolvedName(fileName={fileName}, resolvedName={resolvedName})", self._resolvedSymLinks[fileName])
        with QMutexLocker(self.__fileInfoGathererLock):
            print("<SDM> [_q_resolvedName scope] before self._resolvedSymLinks[fileName]: ", self._resolvedSymLinks[fileName])
            self._resolvedSymLinks[fileName] = resolvedName
            print("<SDM> [_q_resolvedName scope] after self._resolvedSymLinks[fileName]: ", self._resolvedSymLinks[fileName])

        node = self.node(self.index(fileName))
        print("<SDM> [_q_resolvedName node.fileName ", node.fileName)

        if node and node.isSymLink():
            node.fileName = resolvedName
            print(f"<SDM> [_q_resolvedName scope] node.fileName<{node.fileName}: ")

            if node.parent:
                try:
                    row = node.parent.visibleChildren.index(fileName)
                    print(f"<SDM> [_q_resolvedName scope] row<{row}>: ", node.parent.visibleChildren[row])

                    node.parent.visibleChildren[row] = resolvedName
                    print(
                        f"<SDM> [_q_resolvedName scope] node<{node.fileName}>.parent<{node.parent.fileName}.visibleChildren<{node.parent.visibleChildren.__len__()}>[row<{row}>]: ",
                        node.parent.visibleChildren[row],
                    )

                    self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
                except ValueError:  # noqa: S110
                    RobustLogger().exception(f"Internal issue trying to access '{fileName}' and resolved '{resolvedName}'")

    def _q_performDelayedSort(self):
        self.sort(self._sortColumn, self._sortOrder)

    def myComputer(self) -> str:
        """While this was attempting to be respectful to the C++, this function is overly stupid.

        In qt5, this just returns either "My Computer" or "Computer". It does not handle linux/mac.

        therefore, this function will always return str(Path(Path().anchor).resolve()) i.e. the root.
        """
        return str(Path(Path().anchor).resolve())

    @overload
    def node(self, path: str | QFileInfo, fetch: bool = True) -> PyFileSystemNode: ...  # noqa: FBT002, FBT001
    @overload
    def node(self, index: QModelIndex) -> PyFileSystemNode: ...
    def node(self, *args, **kwargs) -> PyFileSystemNode:  # noqa: C901  # sourcery skip: low-code-quality
        path: str | None = kwargs.get("path", args[0] if args and isinstance(args[0], str) else None)
        fetch: bool | None = kwargs.get("fetch", args[1] if len(args) > 1 and isinstance(args[1], (int, bool)) else True)
        index: QModelIndex | None = kwargs.get("index", args[0] if args and isinstance(args[0], QModelIndex) else None)
        fileInfo: QFileInfo | None = kwargs.get("fileInfo", args[0] if args and isinstance(args[0], QFileInfo) else None)

        if isinstance(fileInfo, QFileInfo):
            print("<SDM> [node scope] fileInfo: ", fileInfo.path())
            return self.node(self.index(fileInfo.filePath()))
        if isinstance(path, str):
            print("<SDM> [node scope] path: ", path)
            print("<SDM> [node scope] fetch: ", fetch)
            return self._handle_node_path_arg(path, fetch)
        if isinstance(index, QModelIndex):
            print("<SDM> [node scope] index.isValid()", index.isValid(), "index.row()", index.row())
            return index.internalPointer() if index.isValid() else self._root
        raise TypeError("Invalid arguments for node function")

    def _handle_node_path_arg(self, path: os.PathLike | str, fetch: bool) -> PyFileSystemNode:  # noqa: FBT001, C901, PLR0911, PLR0912, PLR0915
        # sourcery skip: low-code-quality
        pathObj = Path.pathify(path)
        if not pathObj.parent.name or pathObj.anchor.startswith(":"):
            print("<SDM> [_handle_node_arg_str scope] path: ", path)

            return self._root

        index = QModelIndex()  # root
        print("<SDM> [_handle_node_arg_str scope] index: ", index)
        print("<SDM> [_handle_node_arg_str scope] index: ", index, "index.row():", index.row(), "index.column():", index.column(), "index.isValid():", index.isValid())

        resolvedPath = Path(os.path.normpath(path)).resolve()
        print("<SDM> [_handle_node_arg_str scope] resolvedPath: ", resolvedPath)

        if os.name == "nt":
            host = resolvedPath.anchor
            print("<SDM> [_handle_node_arg_str scope] host: ", host)

            if host.startswith("\\\\"):  # UNC path
                rootNode = self._root
                if host not in self._root.children:
                    return self._handle_unc_path(resolvedPath, rootNode, host)
                r = rootNode.visibleLocation(host)
                r = self.translateVisibleLocation(rootNode, r)
                index = self.index(r, 0, QModelIndex())

        parent = self.node(index)
        print("<SDM> [_handle_node_arg_str scope] parent: ", parent, "child count:", parent.children.__len__())

        for thisFile in (resolvedPath, *resolvedPath.parents):
            alreadyExisted = str(thisFile).strip() in parent.children
            print("<SDM> [_handle_node_arg_str scope] alreadyExisted: ", alreadyExisted)

            # If the element already exists, ensure it matches case sensitivity requirements
            if alreadyExisted:
                childNode = parent.children[str(thisFile)]
                print("<SDM> [_handle_node_arg_str scope] child_node: ", childNode.fileInfo().path())  # pyright: ignore[reportOptionalMemberAccess]

                if (
                    parent.children and parent.caseSensitive() and childNode.fileInfo().path() != thisFile  # pyright: ignore[reportOptionalMemberAccess]
                ) or (
                    not parent.caseSensitive() and childNode.fileInfo().path().lower() != thisFile.name.lower()  # pyright: ignore[reportOptionalMemberAccess]
                ):
                    alreadyExisted = False

            # Create a new node if the path element does not exist
            if not alreadyExisted:
                info = QFileInfo(str(thisFile.parent))
                if not info.exists():
                    return self._root  # Return root if the path is invalid
                node = self.addNode(parent, str(thisFile), info)
                print("<SDM> [_handle_node_arg_str node.fileName ", node.fileName)

                if fetch:
                    node.populate(self._fileInfoGatherer.getInfo(info))
            else:
                node = parent.children[str(thisFile)]
                print("<SDM> [_handle_node_arg_str node.fileName ", node.fileName)

            if not node.isVisible:
                if alreadyExisted and node.hasInformation() and not fetch:
                    return self._root

                self.addVisibleFiles(parent, [str(thisFile)])
                if node not in self._bypassFilters:
                    self._bypassFilters[node] = 1

                dirPath = str(thisFile.parent)
                if not node.hasInformation() and fetch:
                    self._toFetch.append({"dir": dirPath, "file": thisFile, "node": node})
                    self._fetchingTimer.start(0, self)  # pyright: ignore[reportOptionalMemberAccess]
            parent = node
        return parent

    def _handle_unc_path(self, resolvedPath: Path, rootNode: PyFileSystemNode, host: str) -> PyFileSystemNode:  # noqa: N803
        if len(resolvedPath.parts) == 1 and not resolvedPath.name.endswith("/"):
            return rootNode
        info = QFileInfo(host)
        print("<SDM> [_handle_unc_path scope] info.path(): ", info.path())

        if not info.exists():
            return rootNode
        node = self.addNode(rootNode, host, info)
        print("<SDM> [_handle_unc_path node.fileName ", node.fileName)

        self.addVisibleFiles(rootNode, [host])
        return node

    def isHiddenByFilter(self, indexNode: PyFileSystemNode, index: QModelIndex) -> bool:  # noqa: N803
        """Return true if index which is owned by node is hidden by the filter."""
        return indexNode != self._root and not index.isValid()

    def gatherFileInfo(self, path: str, files: list[str] | None = None):
        self._fileInfoGatherer.fetchExtendedInformation(path, files or [])

    def _fetchingTimerEvent(self):
        self._fetchingTimer.stop()
        for fetch in self._toFetch:
            node: PyFileSystemNode = fetch["node"]
            print("<SDM> [_fetchPendingItems scope] PyFileSystemNode: ", node.fileName, "row:", node.row(), "children:", node.children.__len__())

            if not node.hasInformation():
                self.gatherFileInfo(fetch["dir"], [fetch["file"]])
        self._toFetch.clear()

    def translateVisibleLocation(self, node: PyFileSystemNode, location: int) -> int:
        print("<SDM> [translateVisibleLocation scope] location: ", location)
        return -1 if location == -1 or not node.isVisible else location

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        print("<SDM> [sort scope] order: ", order, "column: ", column)

        if self._sortOrder == order and self._sortColumn == column and not self._forceSort:
            return

        self.layoutAboutToBeChanged.emit()

        self.sortChildren(column, QModelIndex())
        self._sortColumn = column
        self._sortOrder = order
        self._forceSort = False

        self.layoutChanged.emit()

    def rmdir(self, index: QModelIndex) -> bool:
        path = self.filePath(index)
        print("<SDM> [rmdir scope] path: ", path, "index.row()", index.row())

        try:
            shutil.rmtree(path, ignore_errors=False)  # noqa: PTH106
        except OSError as e:
            RobustLogger().exception(f"Failed to rmdir: {e.__class__.__name__}: {e}")
            return False
        else:
            self._fileInfoGatherer.removePath(path)
            return True

    def addNode(self, parentNode: PyFileSystemNode, fileName: str, info: QFileInfo) -> PyFileSystemNode:  # noqa: N803
        node = PyFileSystemNode(fileName, parentNode)
        print("<SDM> [addNode node.fileName ", node.fileName, "parentNode.fileName:", parentNode.fileName if parentNode is not None else None)

        node.populate(info)
        if os.name == "nt" and not parentNode.fileName:
            node.volumeName = volumeName(fileName)
            RobustLogger().warning(f"<SDM> [addNode scope] node.volumeName: '{node.volumeName}'")

        # assert fileName not in parentNode.children
        parentNode.children[fileName] = node
        print(f"<SDM> [addNode scope] parentNode<{parentNode.fileName}>.children<{parentNode.children.__len__()}[fileName<{fileName}>]: ", parentNode.children[fileName])

        return node

    def removeNode(self, parentNode: PyFileSystemNode, name: str):  # noqa: N803
        indexHidden = not self.filtersAcceptNode(parentNode)
        v_location = parentNode.visibleLocation(name)
        print("<SDM> [removeNode scope] indexHidden: ", indexHidden, "name:", name, "parentNode.fileName", parentNode.fileName, "v_location", v_location)
        if v_location >= 0 and not indexHidden:
            parentIndex = self.index(parentNode)
            print("<SDM> [removeNode scope] parentIndex: ", parentIndex)

            self.beginRemoveRows(parentIndex, self.translateVisibleLocation(parentNode, v_location), self.translateVisibleLocation(parentNode, v_location))

        node = parentNode.children.pop(name, None)
        print("<SDM> [removeNode node.fileName ", None if node is None else node.fileName)

        if node:
            del node

        if v_location >= 0:
            parentNode.visibleChildren.remove(name)

        if v_location >= 0 and not indexHidden:
            self.endRemoveRows()

    def sortChildren(self, column: int, parent: QModelIndex):
        index_node = self.node(parent)
        print("<SDM> [sortChildren scope] index_node: ", index_node)

        if not index_node.children:
            return

        values: list[tuple[PyFileSystemNode, int]] = [(child, i) for i, child in enumerate(index_node.children.values()) if self.filtersAcceptNode(child)]
        print("<SDM> [sortChildren scope] values: ", values)

        values.sort(key=lambda item: self._natural_compare(item[0], column))

        index_node.visibleChildren = [item[0].fileName for item in values]
        print("<SDM> [sortChildren scope] index_node.visibleChildren: ", index_node.visibleChildren)

        for node, _ in values:
            node.isVisible = True

    def filtersAcceptNode(self, node: PyFileSystemNode) -> bool:
        if node.parent == self._root:
            print("<SDM> [filtersAcceptNode scope] node.parent: ", node.parent)

            return True

        if not node.hasInformation():  # noqa: SLF001
            return False

        filters = self._filters
        print("<SDM> [filtersAcceptNode scope] filters: ", filters)

        if bool(filters & QDir.Filter.Hidden) and not node.isVisible:
            return False

        if not node.isDir() and not bool(filters & QDir.Filter.Files):
            return False

        if node.isDir() and not bool(filters & bool(QDir.Filter.AllDirs | QDir.Filter.Dirs)):
            return False

        return not (bool(filters & QDir.Filter.NoDotAndDotDot) and (node.fileName in (".", "..")))

    def _natural_compare(self, node: PyFileSystemNode, column: int) -> Any:
        if column == 0:
            return node.fileName.lower()
        if column == 1:
            return node.size()
        if column == 2:
            return node.type()
        if column == 3:
            return node.lastModified().toPyDateTime()
        raise ValueError(f"No column with value of '{column}'")

    def icon(self, index: QModelIndex) -> QIcon:
        node = self.node(index)
        print("<SDM> [icon node.fileName ", node.fileName)

        return node.icon()

    def name(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        node = self.node(index)
        print("<SDM> [name node.fileName ", node.fileName)

        with QMutexLocker(self.__fileInfoGathererLock):
            if self._fileInfoGatherer.m_resolveSymlinks and node.isSymLink():
                fullPath = self.filePath(index)
                print("<SDM> [pyfsmodel.name scope(mutex)] fullPath: ", fullPath, "index.row()", index.row())

                return self._resolvedSymLinks.get(fullPath, node.fileName)
            return node.fileName

    def displayName(self, index: QModelIndex) -> str:
        node = self.node(index)
        print("<SDM> [displayName node.fileName ", node.fileName)

        return node.fileName

    def options(self) -> int | QFileSystemModel.Option | QFileSystemModel.Options:
        result = 0
        if not self.resolveSymlinks():
            result |= QFileSystemModel.DontResolveSymlinks

        # TODO:
        #if not self._fileInfoGatherer.isWatching():
        #    result |= QFileSystemModel.DontWatchForChanges

        provider = self.iconProvider()
        print("<SDM> [options scope] provider: ", provider)

        if provider and bool(provider.options() & QFileIconProvider.DontUseCustomDirectoryIcons):
            result |= QFileSystemModel.DontUseCustomDirectoryIcons

        return result

    def setOptions(self, options: QFileSystemModel.Options):
        changed = options ^ self.options()
        print("<SDM> [setOptions scope] changed: ", changed)

        if bool(changed & QFileSystemModel.DontResolveSymlinks):
            self.setResolveSymlinks(not bool(options & QFileSystemModel.DontResolveSymlinks))

        # TODO:
        #if bool(changed & QFileSystemModel.DontWatchForChanges):
        #    self._fileInfoGatherer.setWatching(not bool(options & QFileSystemModel.DontWatchForChanges))

        if bool(changed & QFileSystemModel.DontUseCustomDirectoryIcons):
            provider = self.iconProvider()
            if provider:
                providerOptions = provider.options()
                if bool(options & QFileSystemModel.DontUseCustomDirectoryIcons):
                    providerOptions |= QFileIconProvider.DontUseCustomDirectoryIcons
                else:
                    providerOptions &= ~QFileIconProvider.DontUseCustomDirectoryIcons
                provider.setOptions(providerOptions)
            else:
                RobustLogger().warning("Setting PyFileSystemModel::DontUseCustomDirectoryIcons has no effect when no provider is used")

    def testOption(self, option: QFileSystemModel.Option) -> bool:
        print("<SDM> [testOption scope] option: ", option)
        return bool(self.options() & option) == option

    def setOption(self, option: QFileSystemModel.Option, on: bool = True):  # noqa: FBT001, FBT002
        self.setOptions(self.options() | option if on else self.options() & ~option)  # pyright: ignore[reportArgumentType]

    def sibling(self, row: int, column: int, idx: QModelIndex) -> QModelIndex:
        return self.index(row, column, self.parent(idx))

    def timerEvent(self, event: QTimerEvent):
        if event.timerId() == self._fetchingTimer.timerId():
            self._fetchingTimerEvent()

    def remove(self, index: QModelIndex) -> bool:
        path = self.filePath(index)
        print("<SDM> [remove scope] path:", path, "index.row():", index.row())

        self._fileInfoGatherer.removePath(path)
        try:
            if os.path.isdir(path):  # noqa: PTH112, PTH110
                shutil.rmtree(path, ignore_errors=False)
            else:
                Path(path).unlink(missing_ok=False)  # noqa: PTH107
        except OSError:
            RobustLogger().exception(f"Failed to rmdir '{path}'")
            return False
        else:
            return True

    def mkdir(self, parent: QModelIndex, name: str) -> QModelIndex:
        dirPath = os.path.join(self.filePath(parent), name)  # noqa: PTH118
        print("<SDM> [mkdir scope] dirPath: ", dirPath)

        try:
            os.mkdir(dirPath)  # noqa: PTH102
        except OSError:
            RobustLogger().exception(f"Failed to mkdir at '{dirPath}'")
            return QModelIndex()
        else:  # sourcery skip: extract-method
            parentNode = self.node(parent)
            print("<SDM> [mkdir scope] parentNode: ", parentNode, "parentNode.row():", parentNode.row(), "parentNode.fileName:", parentNode.fileName)

            _newNode = self.addNode(parentNode, name, QFileInfo(dirPath))
            assert name in parentNode.children
            node = parentNode.children[name]
            print("<SDM> [mkdir scope] node: ", node, "row:", node.row(), "name:", name, "node.fileName", node.fileName)

            node.populate(self._fileInfoGatherer.getInfo(QFileInfo(os.path.abspath(os.path.join(dirPath, name)))))  # noqa: PTH118, PTH100
            self.addVisibleFiles(parentNode, [name])
            return self.index(node)

    def permissions(self, index: QModelIndex) -> QFileDevice.Permissions | int:
        r1 = QFileInfo(self.filePath(index)).permissions()
        print("<SDM> [permissions scope] r1: ", r1)

        return QFileDevice.Permissions() if r1 is None else r1

    def lastModified(self, index: QModelIndex) -> QDateTime:
        node = self.node(index)
        return node.lastModified()

    def type(self, index: QModelIndex) -> str:
        node = self.node(index)
        return node.type()

    def size(self, index: QModelIndex) -> int:
        node = self.node(index)
        return node.size()

    def isDir(self, index: QModelIndex) -> bool:
        node = self.node(index)
        return node.isDir()

    @overload
    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex: ...
    @overload
    def index(self, path: str, column: int = 0) -> QModelIndex: ...
    @overload
    def index(self, node: PyFileSystemNode, *args, **kwargs) -> QModelIndex: ...
    def index(self, *args: Any, **kwargs: Any) -> QModelIndex:  # noqa: PLR0911
        row: int | None = kwargs.get("row", args[0] if args and isinstance(args[0], int) else None)
        column: int = kwargs.get("column", args[1] if len(args) > 1 and isinstance(args[1], (QModelIndex, int)) else 0)
        parent: QModelIndex | None = kwargs.get("parent", args[2] if len(args) > 2 and isinstance(args[2], QModelIndex) else None)  # noqa: PLR2004

        path: str | None = kwargs.get("path", args[0] if args and isinstance(args[0], str) else None)

        node: PyFileSystemNode | None = kwargs.get("node", args[0] if args and isinstance(args[0], PyFileSystemNode) else None)

        if node is not None:
            return self._handle_from_node_arg(node, column)
        if path is not None:
            return self._handle_from_path_arg(path, column)
        if column < 0 or row is not None and row < 0:
            return QModelIndex()

        assert row is not None
        print("<SDM> [index scope] row: ", row)
        parentNode = self.node(QModelIndex() if parent is None else parent)
        print("<SDM> [index scope] parentNode.fileName: ", parentNode.fileName, "parent row:", parentNode.row())

        childName: str = parentNode.visibleChildren[row]
        print("<SDM> [index scope] childName: ", childName)

        childNode: PyFileSystemNode | None = parentNode.children.get(childName)
        print("<SDM> [index scope] childNode.fileName: ", childNode.fileName)

        if childNode is None:
            return QModelIndex()
        return self.createIndex(row, column, childNode)

    def _handle_from_path_arg(self, path: str, column: int) -> QModelIndex:
        print("<SDM> [_handle_from_path_arg scope] path: ", path)
        pathNodeResult = self.node(path)
        print(
            "<SDM> [_handle_from_path_arg scope] pathNodeResult: ",
            pathNodeResult.fileInfo() and pathNodeResult.fileInfo().path(),
            "row",
            pathNodeResult.row(),
            "children count:",
            pathNodeResult.children.__len__(),
        )  # noqa: E501

        idx = self.index(pathNodeResult)
        print("<SDM> [_handle_from_path_arg scope] pathNodeResult idx: ", idx.isValid() and typing.cast(PyFileSystemNode, idx.internalPointer()).fileInfo().path())

        if not idx.isValid():
            return QModelIndex()
        if idx.column() != column:
            idx = idx.sibling(idx.row(), column)
        print("<SDM> [_handle_from_path_arg scope] final idx: ", idx.isValid() and typing.cast(PyFileSystemNode, idx.internalPointer()).fileInfo().path())

        return idx

    def _handle_from_node_arg(self, node: PyFileSystemNode, column: int) -> QModelIndex:
        print("<SDM> [_handle_from_node_arg node.fileName ", node.fileName)
        parentNode: PyFileSystemNode | None = None if node is None else node.parent
        if node is self._root or parentNode is None or not node.isVisible:
            return QModelIndex()

        assert node is not None
        visualRow = self.translateVisibleLocation(parentNode, parentNode.visibleLocation(node.fileName))
        print("<SDM> [_handle_from_node_arg scope] visualRow: ", visualRow)

        return self.createIndex(visualRow, column, node)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        node = self.node(index)
        print("<SDM> [parent node.fileName ", node.fileName, "node.row():", node.row())

        parentNode = node.parent
        print("<SDM> [parent scope] parentNode.fileName: ", None if parentNode is None else parentNode.fileName)

        if parentNode is None:
            return QModelIndex()
        if parentNode is self._root:
            return self._rootIndex

        grandparentNode = parentNode.parent
        print("<SDM> [parent scope] grandparentNode.fileName: ", None if grandparentNode is None else grandparentNode.fileName)

        if grandparentNode is None:
            return QModelIndex()
        row = grandparentNode.visibleChildren.index(parentNode.fileName)
        print("<SDM> [parent scope] row: ", row)

        return self.createIndex(row, 0, parentNode)

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:  # noqa: B008
        if not parent.isValid():
            return False
        parentItem = parent.internalPointer()
        if not isinstance(parentItem, PyFileSystemNode):
            return False
        resultHasChildren = bool(parentItem.children)
        return resultHasChildren

    def canFetchMore(self, parent: QModelIndex) -> bool:
        node = self.node(parent)
        result = not node.populatedChildren
        parentItem: PyFileSystemNode = parent.internalPointer()
        print(
            f"canFetchMore: {result}, node: {node.fileName}, parent.isValid(): {parent.isValid()}, parentItem.fileName: {None if parentItem is None else parentItem.fileName}, childrenCount={None if parentItem is None else len(parentItem.children)}"
        )  # noqa: E501
        return result  # noqa: SLF001

    def fetchMore(self, parent: QModelIndex) -> None:
        if not parent.isValid() or self._filesToFetch:
            return
        path = self.filePath(parent)
        self._filesToFetch.append(path)
        QTimer.singleShot(0, self._fetchPendingFiles)

    def _fetchPendingFiles(self):
        if not self._filesToFetch:
            return
        path = self._filesToFetch.pop(0)
        self.gatherFileInfo(path, [])

    def indexFromItem(self, item: PyFileSystemNode) -> QModelIndex:
        if not isinstance(item, PyFileSystemNode):
            return None

        self._rootIndex = self.createIndex(0, 0, self._root)
        if not self._rootIndex.isValid() or self._rootIndex.internalPointer() == item:
            return self._rootIndex

        parent_node = item.parent
        if parent_node is None:
            return QModelIndex()

        itemRow = item.row()
        print(
            f"indexFromItem: Create index for item {item.fileName} parent_node.info.path() {None if parent_node.info is None else parent_node.info.path()} item.row(): {itemRow}"
        )
        return self.createIndex(itemRow, 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        node = self.node(parent)
        if node is None:
            return 0
        nodeIndex = self.indexFromItem(node)
        if nodeIndex is None or not nodeIndex.isValid() or not node.isVisible:
            return 0
        print("rowCount node is valid! node: ", node.fileName, " node.fileInfo().path(): ", node.fileInfo() and node.fileInfo().path())
        if node == self._root:
            childrenCount = len(self._root.children)
            print(f"rowCount root item children count: {childrenCount}")
            return childrenCount
        rowCountResult = 0 if parent.row() <= 0 else len(node.visibleChildren)
        print("<SDM> [rowCount scope] parent.isValid() ", parent.isValid(), "parent.row():", parent.row(), "rowCount for model:", rowCountResult)
        return rowCountResult

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return self.NumColumns

    def data(self, index: QModelIndex, role: Qt.ItemDataRole | int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: C901, PLR0911, PLR0912
        # print("<SDM> [data scope] int: ", int)

        if not index.isValid() or index.model() != self:
            return QVariant()

        node = self.node(index)
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            print("<SDM> [data scope] node: ", node, "role", role)
            if index.column() == 0:
                return node.fileName
            if index.column() == 1:
                return node.size()
            if index.column() == 2:  # noqa: PLR2004
                return node.type()
            if index.column() == 3:  # noqa: PLR2004
                return node.lastModified()
            RobustLogger().warning(f"data: invalid display value column {index.column()}")
        elif role == Qt.ItemDataRole.DecorationRole:
            icon = node.icon()
            if icon.isNull():
                if node.isDir():
                    icon = self.iconProvider().icon(QFileIconProvider.IconType.Folder)
                else:
                    icon = self.iconProvider().icon(QFileIconProvider.IconType.File)
            return icon
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 1:
                return Qt.AlignmentFlag.AlignRight
        elif role == self.FilePathRole:
            return self.filePath(index)
        elif role == self.FileNameRole:
            return node.fileName

        return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole | int = Qt.ItemDataRole.EditRole) -> bool:
        print(
            f"<SDM> [setData scope] index.row(): {index.row()}, index.internalPointer().fileName: {index and index.internalPointer() and index.internalPointer().fileName}, role: ",
            role,
        )

        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        new_name = value
        print("<SDM> [setData scope] new_name: ", new_name)

        old_name = self.data(index)
        print("<SDM> [setData scope] old_name: ", old_name)

        if new_name == old_name:
            return True

        path = self.filePath(index.parent())
        print("<SDM> [setData scope] path: ", path)

        old_path = os.path.join(path, old_name)  # noqa: PTH118
        print("<SDM> [setData scope] old_path: ", old_path)

        new_path = os.path.join(path, new_name)  # noqa: PTH118
        print("<SDM> [setData scope] new_path: ", new_path)

        if not os.rename(old_path, new_path):  # noqa: PTH104
            return False

        node = self.node(index)
        print("<SDM> [setData node.fileName ", node.fileName)

        parent_node = node.parent
        print("<SDM> [setData scope] parent_node.fileName ", None if parent_node is None else parent_node.fileName)

        if parent_node is not None:
            self.removeNode(parent_node, old_name)
            self.addNode(parent_node, new_name, QFileInfo(new_path))
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        print("<SDM> [flags scope] flags: ", flags)

        if not index.isValid():
            return flags

        node = self.node(index)
        print("<SDM> [flags node.fileName ", node.fileName)

        if not self._readOnly and index.column() == 0 and bool(node.permissions() & QFileDevice.Permission.WriteUser):
            flags |= Qt.ItemFlag.ItemIsEditable
            if node.isDir():
                flags |= Qt.ItemFlag.ItemIsDropEnabled
        return flags

    def mimeTypes(self) -> list[str]:
        return ["text/uri-list"]

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        urls: list[QUrl] = [QUrl.fromLocalFile(self.filePath(index)) for index in indexes if index.column() == 0]
        mime_data = QMimeData()
        mime_data.setUrls(urls)
        return mime_data

    def dropMimeData(self, data: QMimeData | None, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not parent.isValid() or self._readOnly:
            return False

        success: bool = True
        dest_dir = self.filePath(parent)
        print("<SDM> [dropMimeData scope] dest_dir: ", dest_dir)

        if data is None:
            return False
        urls = data.urls()
        print("<SDM> [dropMimeData scope] urls: ", urls, "entry count:", len(urls))

        for url in urls:
            path = url.toLocalFile()
            print("<SDM> [dropMimeData scope] path: ", path)

            file_name = os.path.basename(path)  # noqa: PTH119
            print("<SDM> [dropMimeData scope] file_name: ", file_name)

            dest_path = os.path.join(dest_dir, file_name)  # noqa: PTH118
            print("<SDM> [dropMimeData scope] dest_path: ", dest_path)

            if action == Qt.DropAction.CopyAction:
                success &= shutil.copy(path, dest_path)
            elif action == Qt.DropAction.LinkAction:
                success &= os.symlink(path, dest_path) or False
            elif action == Qt.DropAction.MoveAction:
                success &= shutil.move(path, dest_path)
            else:
                return False

        return success

    def supportedDropActions(self) -> int | Qt.DropActions:
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction | Qt.DropAction.LinkAction

    def filePath(self, index: QModelIndex) -> str:
        path: list[str] = []
        print("<SDM> [filePath scope] path: ", path)

        while index.isValid():
            node = self.node(index)
            print("<SDM> [filePath scope] node.fileName", node.fileName, "node.fileInfo.path()", node.fileInfo() and node.fileInfo().path())

            path.insert(0, node.fileName)
            index = index.parent()
            print("<SDM> [filePath scope] index.row(): ", None if index is None else index.row(), "internalPointer:", index.internalPointer())

        return str(pathlib.Path(*path))

    def fileInfo(self, index: QModelIndex) -> QFileInfo:
        return QFileInfo(self.filePath(index))

    def fileIcon(self, index: QModelIndex) -> QIcon:
        return self.node(index).icon()

    def fileName(self, index: QModelIndex) -> str:
        return self.node(index).fileName

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole | int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: PLR0911
        if role == Qt.ItemDataRole.DecorationRole and section == 0:
            return QIcon()
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "Name"
            if section == 1:
                return "Size"
            if section == 2:  # noqa: PLR2004
                return "Type"
            if section == 3:  # noqa: PLR2004
                return "Date Modified"

        return super().headerData(section, orientation, role)

    def setRootPath(self, newPath: str) -> QModelIndex:  # sourcery skip: class-extract-method  # noqa: N803
        resolvedPath = Path(os.path.normpath(newPath).strip()).resolve()
        print("<SDM> [setRootPath scope] resolvedPath: ", resolvedPath)

        if not resolvedPath.safe_exists():
            print("setRootPath, not resolvedPath.safe_exists()")
            return QModelIndex()

        self._setRootPath = True
        if self._rootDir.path() == resolvedPath:  # Root path was chosen.
            print("setRootPath, self._rootDir.path() == resolvedPath")
            return self.index(self.rootPath())

        if self._root.fileName.strip() == ".":  # Remove the watcher on the previous path
            self._fileInfoGatherer.removePath(self.rootPath())
            self.node(self.rootPath()).populatedChildren = False

        # We have a new valid root path
        self._rootDir: QDir = QDir(str(resolvedPath))
        print("<SDM> [setRootPath scope] self._rootDir: ", self._rootDir.path())
        print("<SDM> [setRootPath scope] resolvedPath: ", resolvedPath)

        newRootIndex: QModelIndex = QModelIndex()
        print("<SDM> [setRootPath scope] newRootIndex: ", newRootIndex.isValid())

        if resolvedPath.parent.name:
            print("setRootPath, bool(resolvedPath.parent.name)")
            newRootIndex = self.createIndex(0, 0, self._root)
            print("<SDM> [setRootPath scope] newRootIndex: ", newRootIndex)

        else:
            print("setRootPath, not bool(resolvedPath.parent.name)")
            self._rootDir.setPath("")

        assert newRootIndex.isValid()
        self.fetchMore(newRootIndex)
        self.rootPathChanged.emit(str(resolvedPath))
        self._forceSort = True
        self._q_performDelayedSort()

        return newRootIndex

    def rootPath(self) -> str:
        return self._rootDir.path()

    def rootDirectory(self) -> QDir:
        dir_ = QDir(self._rootDir)
        print("<SDM> [rootDirectory scope] dir_ = QDir(self._rootDir): ", dir_.path())

        dir_.setNameFilters(self.nameFilters())
        dir_.setFilter(self.filter())  # pyright: ignore[reportArgumentType]
        return dir_

    def setIconProvider(self, provider: QFileIconProvider):
        if self._fileInfoGatherer.m_iconProvider == provider:
            return
        self._fileInfoGatherer.m_iconProvider = provider
        self._q_performDelayedSort()

    def iconProvider(self) -> QFileIconProvider:
        return self._fileInfoGatherer.m_iconProvider

    def setFilter(self, filters: QDir.Filters | QDir.Filter):  # sourcery skip: class-extract-method
        print("<SDM> [setFilter scope] self._filters: ", int(self._filters), "filters:", filters)
        if self._filters == filters:
            return
        self._filters = filters
        self._forceSort = True
        self._q_performDelayedSort()

    def filter(self) -> QDir.Filters | QDir.Filter | int:
        return self._filters

    def setResolveSymlinks(self, enable: bool):  # noqa: FBT001
        if self._resolveSymlinks == enable:
            print(f"<SDM> [setResolveSymlinks scope] self._resolveSymlinks=={enable}: ", self._resolveSymlinks)

            return
        self._resolveSymlinks = enable
        print(f"<SDM> [setResolveSymlinks scope] self._resolveSymlinks!={enable}: ", self._resolveSymlinks)

        self._fileInfoGatherer.setResolveSymlinks(enable)
        self._forceSort = True
        self._q_performDelayedSort()

    def resolveSymlinks(self) -> bool:
        return self._resolveSymlinks

    def setReadOnly(self, enable: bool):  # noqa: FBT001
        self._readOnly = enable
        print("<SDM> [setReadOnly scope] self._readOnly: ", self._readOnly)

    def isReadOnly(self) -> bool:
        return self._readOnly

    def setNameFilterDisables(self, enable: bool):  # noqa: FBT001
        if self._nameFilterDisables == enable:
            return
        self._nameFilterDisables = enable
        print("<SDM> [setNameFilterDisables scope] self._nameFilterDisables: ", self._nameFilterDisables)

        self._forceSort: bool = True
        self._q_performDelayedSort()

    def nameFilterDisables(self) -> bool:
        return self._nameFilterDisables

    def setNameFilters(self, filters: list[str]):
        if self._nameFilters == filters:
            return
        print(f"self._nameFilters<{self._nameFilters}> = {self.__class__.__name__}.setNameFilters(filters={filters})")
        self._nameFilters = filters
        print(f"setNameFilters(filters={self._nameFilters}) changed to f")
        self._forceSort = True
        self._q_performDelayedSort()

    def nameFilters(self) -> list[str]:
        return self._nameFilters

    directoryLoaded: ClassVar[Signal] = QFileSystemModel.directoryLoaded
    rootPathChanged: ClassVar[Signal] = QFileSystemModel.rootPathChanged
    fileRenamed: ClassVar[Signal] = QFileSystemModel.fileRenamed

    Option: type[QFileSystemModel.Option] = QFileSystemModel.Option
    Options: type[QFileSystemModel.Options] = QFileSystemModel.Options
    Roles: type[QFileSystemModel.Roles] = QFileSystemModel.Roles

    DontWatchForChanges: QFileSystemModel.Option = QFileSystemModel.DontWatchForChanges
    DontResolveSymlinks: QFileSystemModel.Option = QFileSystemModel.DontResolveSymlinks
    DontUseCustomDirectoryIcons: QFileSystemModel.Option = QFileSystemModel.Option.DontUseCustomDirectoryIcons

    FileIconRole: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[1] = Qt.ItemDataRole.DecorationRole
    FilePathRole: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[257] = Qt.ItemDataRole.UserRole + 1  # pyright: ignore[reportAssignmentType]
    FileNameRole: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[258] = Qt.ItemDataRole.UserRole + 2  # pyright: ignore[reportAssignmentType]
    FilePermissions: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[259] = Qt.ItemDataRole.UserRole + 3  # pyright: ignore[reportAssignmentType]

    NumColumns: int = 4


class MainWindow(QMainWindow):
    def __init__(self, rootPath: Path):  # noqa: N803
        super().__init__()

        self.setWindowTitle("QTreeView with HTMLDelegate")

        self.fsTreeView: RobustTreeView = RobustTreeView(self, use_columns=True)
        self.fsModel: PyFileSystemModel = PyFileSystemModel(self)
        self.fsTreeView.setModel(self.fsModel)
        self.fsModel.setRootPath(str(rootPath))

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.fsTreeView)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(824, 568)
        self.resize_and_center()

    def resize_and_center(self):
        """Resize and center the window on the screen."""
        self.adjust_view_size()
        screen = QApplication.primaryScreen().geometry()  # pyright: ignore[reportOptionalMemberAccess]
        print("<SDM> [resize_and_center scope] screen: ", screen)

        new_x = (screen.width() - self.width()) // 2
        print("<SDM> [resize_and_center scope] new_x: ", new_x)

        new_y = (screen.height() - self.height()) // 2
        print("<SDM> [resize_and_center scope] new_y: ", new_y)

        new_x = max(0, min(new_x, screen.width() - self.width()))
        print("<SDM> [resize_and_center scope] new_x: ", new_x)

        new_y = max(0, min(new_y, screen.height() - self.height()))
        print("<SDM> [resize_and_center scope] new_y: ", new_y)

        self.move(new_x, new_y)

    def adjust_view_size(self):
        """Adjust the view size based on content."""
        sb: QScrollBar | None = self.fsTreeView.verticalScrollBar()
        print("<SDM> [adjust_view_size scope] sb: ", sb)

        assert sb is not None
        width = sb.width() + 4  # Add some padding
        print("<SDM> [adjust_view_size scope] width: ", width)

        for i in range(self.fsModel.columnCount()):
            width += self.fsTreeView.columnWidth(i)
        print("all column's widths:", width)
        if QDesktopWidget is None:
            app = typing.cast(QApplication, QApplication.instance())
            screen = app.primaryScreen()
            print("<SDM> [adjust_view_size scope] screen: ", screen)

            assert screen is not None
            screen_width = screen.geometry().width()
        else:
            screen_width = QDesktopWidget().availableGeometry().width()
        print("<SDM> [adjust_view_size scope] screen_width: ", screen_width)

        print("Screen width:", screen_width)
        self.resize(min(width, screen_width), self.height())


if __name__ == "__main__":
    print("<SDM> [main block scope] __name__: ", __name__)
    app = QApplication(sys.argv)
    print("<SDM> [adjust_view_size scope] app: ", app)

    base_path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor").resolve()
    print("<SDM> [adjust_view_size scope] base_path: ", base_path)

    main_window = MainWindow(base_path)
    print("<SDM> [adjust_view_size scope] main_window: ", main_window)

    main_window.show()

    sys.exit(app.exec_() if hasattr(app, "exec_") else app.exec())  # pyright: ignore[reportAttributeAccessIssue]
