from __future__ import annotations

import typing

from typing import TYPE_CHECKING

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import QAbstractItemView, QListView

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex
    from qtpy.QtGui import QKeyEvent
    from qtpy.QtWidgets import QWidget

    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialog import QFileDialogPrivate

class QFileDialogListView(QListView):
    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)

    def setFileDialogPrivate(self, d_pointer: QFileDialogPrivate):
        self._private: QFileDialogPrivate = d_pointer
        self.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
        self.setWrapping(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def setCurrentIndex(self, index: QModelIndex) -> None:
        super().setCurrentIndex(index)

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.qfiledialog import QFileDialog as PublicQFileDialog

        return typing.cast(PublicQFileDialog, self)._private  # noqa: SLF001

    def sizeHint(self) -> QSize:
        height = max(10, self.sizeHintForRow(0))
        return QSize(super().sizeHint().width() * 2, height * 30)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if not self._d_ptr().itemViewKeyboardEvent(e):
            super().keyPressEvent(e)
        e.accept()
