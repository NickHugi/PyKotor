from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QDir
from qtpy.QtWidgets import QFileDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

class PyFileExplorerBase(QFileDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        filter: str = "",
        initialFilter: str = "",
        options: QFileDialog.Options | QFileDialog.Option = QFileDialog.Option.DontUseNativeDialog,
    ):
        super().__init__(parent, caption, directory, filter)
        self.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        self.setOptions(options)
        self.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs)
        self.setNameFilter(filter)
        self.selectNameFilter(initialFilter)
        self.setViewMode(QFileDialog.ViewMode.Detail)

    def getOpenFileNames(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        filter: str = "",
        initialFilter: str = "",
        options: QFileDialog.Options | QFileDialog.Option = QFileDialog.Option.DontUseNativeDialog,
    ) -> list[str]:
        dialog = PyFileExplorerBase(parent, caption, directory, filter, initialFilter, options)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            return dialog.selectedFiles()
        return []

    def getOpenFileName(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        filter: str = "",
        initialFilter: str = "",
        options: QFileDialog.Options | QFileDialog.Option = QFileDialog.Option.DontUseNativeDialog,
    ) -> str:
        dialog = PyFileExplorerBase(parent, caption, directory, filter, initialFilter, options)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0]
        return ""

    def getSaveFileName(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        filter: str = "",
        initialFilter: str = "",
        options: QFileDialog.Options | QFileDialog.Option = QFileDialog.Option.DontUseNativeDialog,
    ) -> str:
        dialog = PyFileExplorerBase(parent, caption, directory, filter, initialFilter, options)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0]
        return ""

    def getExistingDirectory(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        options: QFileDialog.Options | QFileDialog.Option = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog,
    ) -> str:
        dialog = PyFileExplorerBase(parent, caption, directory, options=options)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0]
        return ""
