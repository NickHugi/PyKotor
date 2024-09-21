from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QVBoxLayout, QWidget

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFileSystemModel, QTreeView
    from qtpy.QtCore import QUrl


class QSidebar(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout(self))

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self._urls: list[QUrl] = []
        self._model: QFileSystemModel | None = None
        self._tree_view: QTreeView | None = None

    def addUrl(self, url: QUrl):
        self._urls.append(url)
        self._tree_view.setModel(self._model)

    def setModelAndUrls(self, model: QFileSystemModel, urls: list[QUrl]):

        self._model = model
        self._urls = urls

        self._tree_view.setModel(self._model)

    def setModel(self, model: QFileSystemModel):
        self._model = model
        self._tree_view.setModel(self._model)


    def setUrls(self, urls: list[QUrl]):
        self._urls = urls
        self._tree_view.setModel(self._model)

        self._urls = urls

    def urls(self) -> list[QUrl]:
        return self._urls


    def setTreeView(self, tree_view: QTreeView):
        self._tree_view = tree_view
        self._tree_view.setModel(self._model)

    def treeView(self) -> QTreeView:
        return self._tree_view

    def model(self) -> QFileSystemModel:
        return self._model














