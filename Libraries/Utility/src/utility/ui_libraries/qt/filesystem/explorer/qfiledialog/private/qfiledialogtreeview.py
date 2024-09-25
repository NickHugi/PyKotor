from __future__ import annotations

import typing

from typing import TYPE_CHECKING

from qtpy.QtCore import QSize, Qt
from qtpy.QtWidgets import QAbstractItemView, QTreeView

if TYPE_CHECKING:
    from qtpy.QtGui import QKeyEvent
    from qtpy.QtWidgets import QWidget

    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialog import QFileDialogPrivate


class QFileDialogTreeView(QTreeView):
    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)
        self._private: QFileDialogPrivate | None = None

    def setFileDialogPrivate(self, private: QFileDialogPrivate):
        self._private = private
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setSortingEnabled(True)
        self.header().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self.header().setStretchLastSection(False)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    @property
    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.qfiledialog import QFileDialog as PublicQFileDialog

        return typing.cast(PublicQFileDialog, self.parent())._private  # noqa: SLF001

    def keyPressEvent(self, e: QKeyEvent):
        if not self._private.itemViewKeyboardEvent(e):
            super().keyPressEvent(e)
        e.accept()

    def sizeHint(self) -> QSize:
        height: int = max(10, self.sizeHintForRow(0))
        size_hint: QSize = self.header().sizeHint()
        return QSize(size_hint.width() * 4, height * 30)
