from __future__ import annotations

from typing import TYPE_CHECKING, cast

from qtpy.QtCore import QEvent, QItemSelectionModel, QPersistentModelIndex, QSize, QUrl, Qt, Signal
from qtpy.QtGui import QAction, QKeyEvent
from qtpy.QtWidgets import QAbstractItemView, QAbstractScrollArea, QListView, QMenu, QStyle, QStyledItemDelegate

from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qurlmodel import QUrlModel

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex, QPoint
    from qtpy.QtGui import QDragEnterEvent, QFocusEvent
    from qtpy.QtWidgets import QFileSystemModel, QStyleOptionViewItem, QWidget


class QSideBarDelegate(QStyledItemDelegate):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().initStyleOption(option, index)
        value = index.data(QUrlModel.EnabledRole)
        if value is not None:
            if not value:
                option.state &= ~QStyle.State_Enabled


class QSidebar(QListView):
    goToUrl = Signal(QUrl)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.urlModel: QUrlModel | None = None

    def setModelAndUrls(self, model: QFileSystemModel, newUrls: list[QUrl]) -> None:
        self.setUniformItemSizes(True)
        self.urlModel = QUrlModel(self)
        self.urlModel.setFileSystemModel(model)
        self.setModel(self.urlModel)
        self.setItemDelegate(QSideBarDelegate(self))

        self.selectionModel().currentChanged.connect(self.clicked)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.urlModel.setUrls(newUrls)
        self.setCurrentIndex(self.model().index(0, 0))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.urlModel and self.urlModel.canDrop(event):
            QListView.dragEnterEvent(self, event)

    def sizeHint(self) -> QSize:
        if self.model():
            return self.sizeHintForIndex(self.model().index(0, 0)) + QSize(2 * self.frameWidth(), 2 * self.frameWidth())
        return QListView.sizeHint(self)

    def selectUrl(self, url: QUrl) -> None:
        self.selectionModel().currentChanged.disconnect(self.clicked)
        self.selectionModel().clear()
        for i in range(self.model().rowCount()):
            if self.model().index(i, 0).data(QUrlModel.UrlRole) == url:
                self.selectionModel().select(self.model().index(i, 0), QItemSelectionModel.Select)
                break
        self.selectionModel().currentChanged.connect(self.clicked)

    def showContextMenu(self, position: QPoint) -> None:
        actions: list[QAction] = []
        if self.indexAt(position).isValid():
            action = QAction(self.tr("Remove"), self)
            if self.indexAt(position).data(QUrlModel.UrlRole).path() == "":
                action.setEnabled(False)
            action.triggered.connect(self.removeEntry)
            actions.append(action)
        if actions:
            QMenu.exec(actions, self.mapToGlobal(position))

    def removeEntry(self) -> None:
        indexes: list[QModelIndex] = self.selectionModel().selectedIndexes()
        persistent_indexes: list[QPersistentModelIndex] = [QPersistentModelIndex(idx) for idx in indexes]
        for persistent in persistent_indexes:
            if persistent.data(QUrlModel.UrlRole).path() != "":
                self.model().removeRow(persistent.row())

    def clicked(self, index: QModelIndex) -> None:
        url = self.model().index(index.row(), 0).data(QUrlModel.UrlRole)
        self.goToUrl.emit(url)
        self.selectUrl(url)

    def focusInEvent(self, event: QFocusEvent) -> None:
        QAbstractScrollArea.focusInEvent(self, event)
        self.viewport().update()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.KeyRelease:
            key_event = cast(QKeyEvent, event)
            if key_event.key() == Qt.Key_Delete:
                self.removeEntry()
                return True
        return QListView.event(self, event)
