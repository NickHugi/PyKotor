from __future__ import annotations

import typing

from typing import TYPE_CHECKING

from qtpy.QtCore import QUrl, Qt
from qtpy.QtGui import QPainter, QStandardItemModel
from qtpy.QtWidgets import QApplication, QComboBox, QFileSystemModel, QStyle, QStyleOptionComboBox

from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qsidebar import QUrlModel

if TYPE_CHECKING:
    from qtpy.QtCore import QRect
    from qtpy.QtGui import QKeyEvent, QPaintEvent
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
        self.setEditable(False) 

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.qfiledialog import QFileDialog as PublicQFileDialog

        return typing.cast(PublicQFileDialog, self)._private  # noqa: SLF001

    def showPopup(self):
        if self.model().rowCount() > 1:
            QComboBox.showPopup(self)

        self.urlModel.setUrls([])
        urls = []
        idx = self._d_ptr().model.index(self._d_ptr().rootPath())
        while idx.isValid():
            url = QUrl.fromLocalFile(idx.data(QFileSystemModel.FilePathRole))
            if url.isValid():
                urls.append(url)
            idx = idx.parent()

        # Add "my computer"
        urls.append(QUrl("file:"))
        self.urlModel.addUrls(urls, 0)

        # Append history
        history_urls = []
        for path in self.m_history:
            url = QUrl.fromLocalFile(path)
            if url not in history_urls:
                history_urls.insert(0, url)

        if history_urls:
            model = self.model()
            model.insertRow(model.rowCount())
            idx = model.index(model.rowCount() - 1, 0)
            model.setData(idx, QApplication.instance().tr("Recent Places"))
            if isinstance(model, QStandardItemModel):
                item = model.item(idx.row(), idx.column())
                if item:
                    flags = item.flags()
                    flags &= ~Qt.ItemIsEnabled
                    item.setFlags(flags)
            self.urlModel.addUrls(history_urls, -1, False)  # noqa: FBT003

        self.setCurrentIndex(0)
        QComboBox.showPopup(self)

    def setFileDialogPrivate(self, private: QFileDialogPrivate):
        self._private = private
        self.urlModel = QUrlModel(self)
        self.urlModel.showFullPath = True
        assert self._private.model is not None
        assert isinstance(self._private.model, QFileSystemModel)
        self.urlModel.setFileSystemModel(self._private.model)
        self.setModel(self.urlModel)

    def setHistory(self, paths: list[str]):
        self.m_history = paths

    def history(self) -> list[str]:
        return self.m_history

    def paintEvent(self, e: QPaintEvent) -> None:
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
