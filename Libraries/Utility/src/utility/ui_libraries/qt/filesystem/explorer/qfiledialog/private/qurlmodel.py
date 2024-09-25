from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from qtpy.QtCore import QDir, QFileInfo, QMimeData, QModelIndex, QOperatingSystemVersion, QSize, QUrl, Qt
from qtpy.QtGui import QDragEnterEvent, QIcon, QStandardItemModel
from qtpy.QtWidgets import QFileIconProvider, QFileSystemModel

if TYPE_CHECKING:
    from qtpy.QtCore import QObject
    from qtpy.QtGui import QPixmap


class QUrlModel(QStandardItemModel):
    UrlRole: int = Qt.ItemDataRole.UserRole + 1
    EnabledRole: int = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.showFullPath: bool = True
        self.fileSystemModel: QFileSystemModel | None = None
        self.watching: list[QUrlModel.WatchItem] = []
        self.invalidUrls: list[QUrl] = []

    def mimeTypes(self) -> list[str]:
        return ["text/uri-list"]

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        """Create a QMimeData object with URLs for drag and drop.

        If indexes are valid: Returns QMimeData with URLs.
        If indexes are invalid: Returns empty QMimeData.
        """
        urls: list[QUrl] = []
        for index in indexes:
            if index.column() == 0:
                url_data = index.data(self.UrlRole)
                if isinstance(url_data, QUrl):
                    urls.append(url_data)
        data = QMimeData()
        data.setUrls(urls)
        return data

    def canDrop(self, event: QDragEnterEvent) -> bool:
        """We only accept directories, not files.

        If mime type is correct and all URLs are directories: Returns True.
        If mime type is incorrect or any URL is not a directory: Returns False.
        """
        if not isinstance(event, QDragEnterEvent):
            print(f"{type(self)}.canDrop: Event is not QDragEnterEvent")
            return False

        if self.mimeTypes()[0] not in event.mimeData().formats():
            return False

        if self.fileSystemModel is None:
            print(f"{type(self)}.canDrop: FileSystemModel is None")
            return False

        urls: list[QUrl] = event.mimeData().urls()
        for url in urls:
            idx: QModelIndex = self.fileSystemModel.index(url.toLocalFile())
            if not self.fileSystemModel.isDir(idx):
                return False
        return True

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if self.mimeTypes()[0] not in data.formats():
            return False
        self.addUrls(data.urls(), row)
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Get item flags for the item at thegiven index.

        If index is valid: Returns flags with ItemIsEditable and ItemIsDropEnabled removed.
        If index is invalid: Returns default flags.
        """
        if not isinstance(index, QModelIndex):
            print(f"{type(self)}.flags: Index is not QModelIndex")
            return Qt.ItemFlag.NoItemFlags

        flags = super().flags(index)
        if index.isValid():
            flags &= ~Qt.ItemFlag.ItemIsEditable
            flags &= ~Qt.ItemFlag.ItemIsDropEnabled

            if index.data(Qt.ItemDataRole.DecorationRole) is None:
                flags &= ~Qt.ItemFlag.ItemIsEnabled

        return flags

    def setData(self, index: QModelIndex, value: object, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Set data for the item at the given index and role.

        We need to handle setting URL data differently from other data.
        If role is UrlRole and value is QUrl: Sets URL data and returns True.
        If role is not UrlRole or value is not QUrl: Calls super().setData() and returns its result.
        """
        if not isinstance(index, QModelIndex):
            print(f"{type(self)}.setData: Index is not QModelIndex")
            return False

        if role == self.UrlRole and isinstance(value, QUrl):
            return self._setUrlData(index, value)
        return super().setData(index, value, role)

    def _setUrlData(self, index: QModelIndex, url: QUrl) -> bool:
        """Set URL data for the given index and url.

        We need to update multiple data fields based on the URL.
        If fileSystemModel is None: Returns False.
        If fileSystemModel is not None: Updates data fields and returns True.
        """
        if self.fileSystemModel is None:
            print(f"{type(self)}._setUrlData: FileSystemModel is None")
            return False

        dir_index: QModelIndex = self.fileSystemModel.index(url.toLocalFile())
        if self.showFullPath:
            super().setData(index, QDir.toNativeSeparators(self.fileSystemModel.data(dir_index, QFileSystemModel.FilePathRole)))
        else:
            super().setData(index, QDir.toNativeSeparators(self.fileSystemModel.data(dir_index, QFileSystemModel.FilePathRole)), Qt.ItemDataRole.ToolTipRole)
            super().setData(index, self.fileSystemModel.data(dir_index))

        super().setData(index, self.fileSystemModel.data(dir_index, Qt.ItemDataRole.DecorationRole), Qt.ItemDataRole.DecorationRole)
        super().setData(index, url, self.UrlRole)
        return True

    def setUrls(self, urls: list[QUrl]) -> None:
        """Update the model with a new list of URLs.

        Always: Clears existing data and adds new URLs.
        """
        self.removeRows(0, self.rowCount())
        self.watching = []
        self.invalidUrls = []
        self.addUrls(urls, 0)

    def addUrls(self, urls: list[QUrl], row: int = -1, move: bool = True) -> None:  # noqa: FBT001, FBT002
        """Add urls list into the list at row. If move then move existing ones to row.

        Args:
            urls (list[QUrl]): List of URLs to add.
            row (int, optional): Row to insert at. Defaults to -1 (end of list).
            move (bool, optional): Whether to move existing URLs. Defaults to True.
        """
        if row == -1:
            row = self.rowCount()
        row = min(row, self.rowCount())
        for url in reversed(urls):
            if not url.isValid() or url.scheme() != "file":
                continue
            # This makes sure the url is clean
            clean_url = QDir.cleanPath(url.toLocalFile())
            if not clean_url:
                continue
            url = QUrl.fromLocalFile(clean_url)  # noqa: PLW2901

            for j in range(self.rowCount()):
                if move:
                    local = self.index(j, 0).data(self.UrlRole).toLocalFile()
                    cs = Qt.CaseInsensitive if QOperatingSystemVersion.current().type() == QOperatingSystemVersion.Windows else Qt.CaseSensitive
                    if not clean_url == local:
                        self.removeRow(j)
                        if j <= row:
                            row -= 1
                        break

            row = max(row, 0)
            idx = self.fileSystemModel.index(clean_url)
            if not self.fileSystemModel.isDir(idx):
                continue
            self.insertRows(row, 1)
            self.setUrl(self.index(row, 0), url, idx)
            self.watching.append(self.WatchItem(idx, clean_url))

    def urls(self) -> list[QUrl]:
        """Get the list of all URLs stored in the model.
        Always: Returns a list of QUrl objects.
        """
        return [
            url
            for i in range(self.rowCount())
            if isinstance((url := self.data(self.index(i, 0), self.UrlRole)), QUrl)
        ]

    def setFileSystemModel(self, model: QFileSystemModel) -> None:
        """Set the file system model and connect signals for this URL model.

        If model is the same as current: Returns without changes.
        If model is different: Disconnects old signals, connects new ones, and clears data.
        """
        if not isinstance(model, QFileSystemModel):
            print(f"{type(self)}.setFileSystemModel: Model is not QFileSystemModel")
            return

        if model == self.fileSystemModel:
            return

        self._disconnectOldModel()
        self.fileSystemModel = model
        self._connectNewModel()
        self.clear()
        self.insertColumn(0)

    def _disconnectOldModel(self) -> None:
        """Disconnect signals from the old file system model, removing connections before setting a new one.
        If fileSystemModel exists: Disconnects all signals.
        If fileSystemModel doesn't exist: Does nothing.
        """
        if self.fileSystemModel is not None:
            self.fileSystemModel.dataChanged.disconnect(self.dataChanged)
            self.fileSystemModel.layoutChanged.disconnect(self.layoutChanged)
            self.fileSystemModel.rowsRemoved.disconnect(self.layoutChanged)

    def _connectNewModel(self) -> None:
        """Connect signals to the new file system model, allowing communication between the two.

        If fileSystemModel exists: Connects all necessary signals.
        If fileSystemModel doesn't exist: Does nothing.
        """
        if self.fileSystemModel is not None:
            self.fileSystemModel.dataChanged.connect(self.dataChanged)
            self.fileSystemModel.layoutChanged.connect(self.layoutChanged)
            self.fileSystemModel.rowsRemoved.connect(self.layoutChanged)

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex) -> None:  # noqa: N803
        """Handle data changes in the file system model, updating it when the file system model changes.

        If indices are valid: Updates affected items.
        If indices are invalid: Does nothing.
        """
        if not isinstance(topLeft, QModelIndex) or not isinstance(bottomRight, QModelIndex):
            print(f"{type(self)}.dataChanged: Invalid indices")
            return

        parent = topLeft.parent()
        for item in self.watching:
            if self._isIndexAffected(item.index, topLeft, bottomRight, parent):
                self.changed(item.path)

    def _isIndexAffected(self, index: QModelIndex, topLeft: QModelIndex, bottomRight: QModelIndex, parent: QModelIndex) -> bool:  # noqa: N803
        """Check if an index is affected by a data change.

        We need to determine if a specific index needs updating.
        If index is within the changed range: Returns True.
        If index is outside the changed range: Returns False.
        """
        return (
            index.row() >= topLeft.row()
            and index.row() <= bottomRight.row()
            and index.column() >= topLeft.column()
            and index.column() <= bottomRight.column()
            and index.parent() == parent
        )

    def layoutChanged(self) -> None:
        """Update our model when the file system model's layout changes."""
        paths: list[str] = [item.path for item in self.watching]
        self.watching.clear()
        for path in paths:
            new_index: QModelIndex = self.fileSystemModel.index(path)
            self.watching.append(self.WatchItem(new_index, path))
            if new_index.isValid():
                self.changed(path)

    def setUrl(self, index: QModelIndex, url: QUrl, dirIndex: QModelIndex) -> None:  # noqa: N803
        """Set the URL for a specific index in the model.

        We need to update various data fields when setting a URL.
        If URL is empty: Sets computer-related data.
        If URL is not empty: Sets file or directory-related data.
        """
        if (
            not isinstance(index, QModelIndex)
            or not isinstance(url, QUrl)
            or not isinstance(dirIndex, QModelIndex)
        ):
            print(f"{type(self)}.setUrl: Invalid arguments")
            return

        self.setData(index, url, self.UrlRole)
        if url.path() == "":
            self._setComputerData(index)
        else:
            self._setFileOrDirData(index, url, dirIndex)

    def _setComputerData(self, index: QModelIndex) -> None:
        """Set data for the computer (root) item.

        We need to handle the special case of the computer item differently.
        Always: Sets computer name and icon.
        """
        if self.fileSystemModel is None:
            print(f"{type(self)}._setComputerData: FileSystemModel is None")
            return

        self.setData(index, self.fileSystemModel.myComputer())
        self.setData(index, self.fileSystemModel.myComputer(Qt.ItemDataRole.DecorationRole), Qt.ItemDataRole.DecorationRole)

    def _setFileOrDirData(self, index: QModelIndex, url: QUrl, dirIndex: QModelIndex) -> None:  # noqa: N803
        """Updates the name, icon, and other properties for a file or directory.

        If dirIndex is valid: Sets data from file system model.
        If dirIndex is invalid: Sets data for invalid URL.
        """
        if self.fileSystemModel is None:
            print(f"{type(self)}._setFileOrDirData: FileSystemModel is None")
            return

        if dirIndex.isValid():
            self._setValidFileOrDirData(index, dirIndex)
        else:
            self._setInvalidFileOrDirData(index, url)

        self._ensureLargeIcon(index)

    def _setValidFileOrDirData(self, index: QModelIndex, dirIndex: QModelIndex) -> None:  # noqa: N803
        """Updates the file or directory item in the model with correct data from the file system.

        Valid items only.
        """
        if self.showFullPath:
            newName = QDir.toNativeSeparators(dirIndex.data(QFileSystemModel.FilePathRole))
        else:
            newName = dirIndex.data()

        newIcon = dirIndex.data(Qt.ItemDataRole.DecorationRole)

        self.setData(index, newName)
        self.setData(index, newIcon, Qt.ItemDataRole.DecorationRole)
        self.setData(index, True, QUrlModel.EnabledRole)  # noqa: FBT003

    def _setInvalidFileOrDirData(self, index: QModelIndex, url: QUrl) -> None:
        """Sets placeholder name, icon, and disabled state for an invalid item.

        Why? We need to handle cases where the URL is invalid or inaccessible.
        """
        provider = self.fileSystemModel.iconProvider() if self.fileSystemModel else None
        newIcon = provider.icon(QFileIconProvider.IconType.Folder) if provider else QIcon()
        newName = QFileInfo(url.toLocalFile()).fileName()

        self.setData(index, newName)
        self.setData(index, newIcon, Qt.ItemDataRole.DecorationRole)
        self.setData(index, False, QUrlModel.EnabledRole)  # noqa: FBT003

        if url not in self.invalidUrls:
            self.invalidUrls.append(url)

    def _ensureLargeIcon(self, index: QModelIndex) -> None:
        """Ensures a minimum icon size for visual consistency.

        If icon is smaller than 32x32: Scales it up using SmoothTransformation.
        If icon is already 32x32 or larger: Does nothing.
        """
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if not isinstance(icon, QIcon):
            return

        size = icon.actualSize(QSize(32, 32))
        if size.width() < 32:
            smallPixmap: QPixmap = icon.pixmap(QSize(32, 32))
            newIcon = QIcon(smallPixmap.scaledToWidth(32, Qt.TransformationMode.SmoothTransformation))
            self.setData(index, newIcon, Qt.ItemDataRole.DecorationRole)

    def changed(self, path: str) -> None:
        """Update data for a changed path.

        We need to refresh our model when the file system reports changes.
        If path matches a URL in the model: Updates the corresponding item.
        If path doesn't match any URL: Does nothing.
        """
        for i in range(self.rowCount()):
            idx = self.index(i, 0)
            url_data = self.data(idx, self.UrlRole)
            if isinstance(url_data, QUrl) and url_data.toLocalFile() == path:
                self.setData(idx, url_data)
                break

    class WatchItem:  # noqa: D106
        def __init__(self, index: QModelIndex, path: str):
            self.index: QModelIndex = index
            self.path: str = path
