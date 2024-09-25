from __future__ import annotations

import typing

from typing import TYPE_CHECKING

from qtpy.QtCore import QModelIndex, QUrl, Qt
from qtpy.QtGui import QPainter, QStandardItemModel
from qtpy.QtWidgets import QComboBox, QFileDialog as RealQFileDialog, QStyle, QStyleOptionComboBox

from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qsidebar import QUrlModel

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex, QRect
    from qtpy.QtGui import QKeyEvent, QPaintEvent, QStandardItem
    from qtpy.QtWidgets import QFileDialog

    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialog import QFileDialogPrivate


class QFileDialogComboBox(QComboBox):
    def __init__(
        self,
        parent: QFileDialog,
    ):
        super().__init__(parent)
        self._private: QFileDialogPrivate | None = None
        self.m_history: list[str] = []
        self.urlModel = QUrlModel(self)
        self.setModel(self.urlModel)

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.qfiledialog import QFileDialog as PublicQFileDialog

        return typing.cast(PublicQFileDialog, self.parent())._private  # noqa: SLF001

    def showPopup(self):
        if self.model().rowCount() > 1:
            QComboBox.showPopup(self)

        self._populateUrlModel()
        self._addRecentPlacesSection()
        self._addUrlsToModel()
        self.setCurrentIndex(0)
        QComboBox.showPopup(self)

    def _populateUrlModel(self) -> None:
        if not isinstance(self.urlModel, QUrlModel):
            raise TypeError("urlModel is not of type QUrlModel")
        self.urlModel.setUrls([])
        self.urlModel.addUrls([QUrl.fromLocalFile(path) for path in self.m_history], -1)

    def _addRecentPlacesSection(self) -> None:
        urls: list[QUrl] = self._getUniqueHistoryUrls()
        if not urls:
            return

        model: QAbstractItemModel = self.model()
        if not isinstance(model, QStandardItemModel):
            raise TypeError("model is not of type QStandardItemModel")

        model.insertRow(model.rowCount())
        idx: QModelIndex = model.index(model.rowCount() - 1, 0)
        model.setData(idx, RealQFileDialog.tr("Recent Places"))

        item: QStandardItem = model.item(idx.row(), idx.column())
        if item is None:
            raise ValueError("Failed to get item from model")

        flags: Qt.ItemFlags = item.flags()
        flags &= ~Qt.ItemFlag.ItemIsEnabled
        item.setFlags(flags)

    def _getUniqueHistoryUrls(self) -> list[QUrl]:
        urls: list[QUrl] = []
        for path in self.m_history:
            url: QUrl = QUrl.fromLocalFile(path)
            if url not in urls:
                urls.insert(0, url)
        return urls

    def _addUrlsToModel(self) -> None:
        urls: list[QUrl] = self._getUniqueHistoryUrls()
        if not isinstance(self.urlModel, QUrlModel):
            raise TypeError("urlModel is not of type QUrlModel")
        self.urlModel.addUrls(urls, -1, move=True)

    def setFileDialogPrivate(self, private: QFileDialogPrivate):
        self._private = private

    def setHistory(self, paths: list[str]):
        self.m_history = paths

    def history(self) -> list[str]:
        return self.m_history

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        edit_rect: QRect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField, self)
        size: int = edit_rect.width() - opt.iconSize.width() - 4
        opt.currentText = opt.fontMetrics.elidedText(opt.currentText, Qt.TextElideMode.ElideMiddle, size)

        self.style().drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt, painter, self)
        self.style().drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt, painter, self)

    def keyPressEvent(self, e: QKeyEvent):
        if not self._private.itemViewKeyboardEvent(e):
            super().keyPressEvent(e)
        e.accept()
