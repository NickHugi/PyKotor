from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from qtpy.QtCore import QEvent, QItemSelectionModel, QPersistentModelIndex, QSize, QUrl, Qt, Signal
from qtpy.QtGui import QAction, QDragEnterEvent, QFocusEvent, QKeyEvent
from qtpy.QtWidgets import QAbstractItemView, QAbstractScrollArea, QListView, QMenu, QStyledItemDelegate

from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qurlmodel import QUrlModel

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex, QPoint
    from qtpy.QtWidgets import QFileSystemModel, QStyleOptionViewItem, QWidget


class QSideBarDelegate(QStyledItemDelegate):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().initStyleOption(option, index)


@dataclass
class SidebarItem:
    url: QUrl
    name: str


class QSidebar(QListView):
    goToUrl = Signal(QUrl)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the QSidebar."""
        super().__init__(parent)
        self.urlModel: QUrlModel | None = None

    def setModelAndUrls(self, model: QFileSystemModel, newUrls: list[QUrl]) -> None:  # noqa: N803
        """Set the model and URLs for the sidebar."""
        self.setUniformItemSizes(True)
        self.urlModel = QUrlModel(self)
        self.urlModel.setFileSystemModel(model)
        self.setModel(self.urlModel)
        self.setItemDelegate(QSideBarDelegate(self))

        self._connectSignals()
        self._setDragDropProperties()
        self._setContextMenuPolicy()
        self._setUrls(newUrls)
        self._setInitialSelection()

    def _connectSignals(self) -> None:
        """Connect signals for the sidebar."""
        if self.selectionModel() is None:
            print(f"{type(self)}._connectSignals: Selection model is None")
            return
        self.selectionModel().currentChanged.connect(self.clicked)

    def _setDragDropProperties(self) -> None:
        """Set drag and drop properties for the sidebar."""
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

    def _setContextMenuPolicy(self) -> None:
        """Set context menu policy for the sidebar."""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def _setUrls(self, newUrls: list[QUrl]) -> None:  # noqa: N803
        """Set URLs for the sidebar model."""
        if self.urlModel is None:
            print(f"{type(self)}._setUrls: URL model is None")
            return
        self.urlModel.setUrls(newUrls)

    def _setInitialSelection(self) -> None:
        """Set initial selection for the sidebar."""
        if self.model() is None:
            print(f"{type(self)}._setInitialSelection: Model is None")
            return
        self.setCurrentIndex(self.model().index(0, 0))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if self.urlModel is None:
            print(f"{type(self)}.dragEnterEvent: URL model is None")
            return
        if isinstance(event, QDragEnterEvent) and self.urlModel.canDrop(event):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def sizeHint(self) -> QSize:
        """Provide a size hint for the sidebar."""
        if self.model() is None:
            return super().sizeHint()
        index = self.model().index(0, 0)
        return self.sizeHintForIndex(index) + QSize(2 * self.frameWidth(), 2 * self.frameWidth())

    def setUrls(self, urls: list[QUrl]) -> None:
        """Set URLs for the sidebar."""
        if self.urlModel is None:
            print(f"{type(self)}.setUrls: URL model is None")
            return
        assert urls is not None, f"{type(self)}.setUrls: URLs is None"
        self.urlModel.setUrls(urls)

    def addUrls(self, urls: list[QUrl], row: int) -> None:
        """Add URLs to the sidebar at a specific row."""
        if self.urlModel is None:
            print(f"{type(self)}.addUrls: URL model is None")
            return
        self.urlModel.addUrls(urls, row)

    def urls(self) -> list[QUrl]:
        """Get the list of URLs in the sidebar."""
        if self.urlModel is None:
            print(f"{type(self)}.urls: URL model is None")
            return []
        return self.urlModel.urls()

    def selectUrl(self, url: QUrl) -> None:
        """Select a specific URL in the sidebar."""
        if self.selectionModel() is None or self.model() is None:
            print(f"{type(self)}.selectUrl: Selection model or model is None")
            return

        self.selectionModel().currentChanged.disconnect(self.clicked)
        self.selectionModel().clear()

        self._selectUrlInModel(url)

        self.selectionModel().currentChanged.connect(self.clicked)

    def removeSelection(self) -> None:
        """Remove the selection from the sidebar."""
        if self.selectionModel() is None or self.model() is None:
            print(f"{type(self)}.removeSelection: Selection model or model is None")
            return
        self.selectionModel().clear()

    def _selectUrlInModel(self, url: QUrl) -> None:
        """Select the URL in the model."""
        if self.model() is None:
            print(f"{type(self)}._selectUrlInModel: Model is None")
            return

        for i in range(self.model().rowCount()):
            index = self.model().index(i, 0)
            url_data = index.data(QUrlModel.UrlRole)
            if isinstance(url_data, QUrl) and url_data == url:
                self.selectionModel().select(index, QItemSelectionModel.SelectionFlag.Select)
                return
        print(f"{type(self)}._selectUrlInModel: URL not found in model")

    def showContextMenu(self, position: QPoint) -> None:
        """Show the context menu for the sidebar."""
        actions: list[QAction] = self._createContextMenuActions(position)
        if actions:
            QMenu.exec(actions, self.mapToGlobal(position))

    def _createContextMenuActions(self, position: QPoint) -> list[QAction]:
        """Create context menu actions for the sidebar."""
        actions: list[QAction] = []
        if self.indexAt(position).isValid():
            action = QAction(self.tr("Remove"), self)
            url_data = self.indexAt(position).data(QUrlModel.UrlRole)
            if isinstance(url_data, QUrl) and url_data.path() == "":
                action.setEnabled(False)
            action.triggered.connect(self.removeEntry)
            actions.append(action)
        return actions

    def removeEntry(self) -> None:
        """Remove the selected entry from the sidebar."""
        if self.model() is None or self.selectionModel() is None:
            print(f"{type(self)}.removeEntry: Model or selection model is None")
            return

        indexes: list[QModelIndex] = self.selectionModel().selectedIndexes()
        persistent_indexes: list[QPersistentModelIndex] = [QPersistentModelIndex(idx) for idx in indexes]
        self._removeSelectedEntries(persistent_indexes)

    def _removeSelectedEntries(self, persistent_indexes: list[QPersistentModelIndex]) -> None:
        """Remove the selected entries from the model."""
        for persistent in persistent_indexes:
            url_data = persistent.data(QUrlModel.UrlRole)
            if isinstance(url_data, QUrl) and url_data.path() != "":
                if self.model() is None:
                    print(f"{type(self)}._removeSelectedEntries: Model is None")
                    return
                self.model().removeRow(persistent.row())

    def clicked(self, index: QModelIndex, _: QModelIndex) -> None:
        """Handle click events on sidebar items."""
        if self.model() is None:
            print(f"{type(self)}.clicked: Model is None")
            return

        url_data: QUrl | None = self.model().index(index.row(), 0).data(QUrlModel.UrlRole)
        if isinstance(url_data, QUrl):
            self.goToUrl.emit(url_data)
            self.selectUrl(url_data)
        print(f"{type(self)}.clicked: URL data is None")

    def focusInEvent(self, event: QFocusEvent) -> None:
        """Handle focus in events."""
        if not isinstance(event, QFocusEvent):
            print(f"{type(self)}.focusInEvent: Event is not QFocusEvent")
            return
        super(QAbstractScrollArea, self).focusInEvent(event)
        self.viewport().update()

    def event(self, event: QEvent) -> bool:
        """Handle general events for the sidebar."""
        if not isinstance(event, QEvent):
            print(f"{type(self)}.event: Event is not QEvent")
            return False
        if event.type() == QEvent.Type.KeyRelease:
            key_event = cast(QKeyEvent, event)
            if key_event.key() == Qt.Key.Key_Delete:
                self.removeEntry()
                return True
        return super().event(event)
