from __future__ import annotations

import typing

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QLineEdit

if TYPE_CHECKING:
    from qtpy.QtGui import QKeyEvent
    from qtpy.QtWidgets import QFileDialog

    from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.private.qfiledialog_p import QFileDialogPrivate


class QFileDialogLineEdit(QLineEdit):
    def __init__(
        self,
        parent: QFileDialog,
    ):
        super().__init__(parent)
        self.hideOnEsc: bool = False
        self._private: QFileDialogPrivate | None = None

    def keyPressEvent(self, e: QKeyEvent):
        """FIXME: this is a hack to avoid propagating key press events
        to the dialog and from there to the "Ok" button.
        """
        super().keyPressEvent(e)
        # not available in pyqt6?
        #if QApplication.navigationMode() == Qt.NavigationMode.NavigationModeKeypadDirectional:
        #    super().keyPressEvent(e)
        #    return

        # key = e.key()
        # super().keyPressEvent(e)
        # if not e.matches(QKeySequence.StandardKey.Cancel) and key != Qt.Key.Key_Back:
        #     e.accept()
        # if self.hideOnEsc and e.key() == Qt.Key.Key_Escape:
        #     self.hide()
        #     e.accept()
        # else:
            # super().keyPressEvent(e)

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.qfiledialogextended.qfiledialog.qfiledialog import QFileDialog as PublicQFileDialog

        return typing.cast(PublicQFileDialog, self)._private  # noqa: SLF001

    def setFileDialogPrivate(self, d_pointer: QFileDialogPrivate):
        self._private = d_pointer
