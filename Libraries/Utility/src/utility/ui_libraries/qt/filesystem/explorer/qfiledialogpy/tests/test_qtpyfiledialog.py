from __future__ import annotations

import sys

from collections import defaultdict
from typing import TYPE_CHECKING, ClassVar

from qtpy.QtCore import QDir, QUrl
from qtpy.QtWidgets import QApplication, QFileDialog

if TYPE_CHECKING:
    import subprocess

    from qtpy.QtCore import PYQT_SLOT, Qt
    from qtpy.QtGui import QDragEnterEvent, QDropEvent
    from qtpy.QtWidgets import QWidget


_TESTING: bool = True
"""Provide runtime testing of QFileDialog by inheriting from it, normally only used for type hinting."""


if TYPE_CHECKING:
    _Inherit = QFileDialog
else:
    _Inherit = QFileDialog if _TESTING else object


class TestQFileDialog(_Inherit):
    _DEFAULT_LABELS: ClassVar[dict[QFileDialog.DialogLabel, str]] = {
        QFileDialog.DialogLabel.LookIn: "Look In",
        QFileDialog.DialogLabel.FileName: "File Name",
        QFileDialog.DialogLabel.FileType: "File Type",
        QFileDialog.DialogLabel.Accept: "Accept",
        QFileDialog.DialogLabel.Reject: "Reject",
    }
    def __init__(
        self,
        parent: QWidget | None = None,
        caption: str | None = None,
        directory: str | None = None,
        filter: str | None = None,  # noqa: A002
    ) -> None:
        if not isinstance(self, QFileDialog):
            return
        def get_label_text(label):
            return QFileDialog.setLabelText(self, label, self._DEFAULT_LABELS.get(label, f"<unknown label {label}>"))
        self._labelText: dict[QFileDialog.DialogLabel, str] = defaultdict(get_label_text)
        self._fileMode: QFileDialog.FileMode = QFileDialog.FileMode.AnyFile

        self._acceptMode: QFileDialog.AcceptMode = QFileDialog.AcceptMode.AcceptOpen
        self._viewMode: QFileDialog.ViewMode = QFileDialog.ViewMode.Detail
        self._options: QFileDialog.Option = QFileDialog.Option(0)
        self._nameFilters: list[str] = ["All Files (*)"]
        self._selectedFiles: list[str] = []
        self._selectedUrls: list[QUrl] = []
        self._directoryUrl: QUrl = QUrl("/C:/GitHub/PyKotor/Libraries/Utility")
        self._supportedSchemes: list[str] = []
        self._sidebarUrls: list[QUrl] = []
        self._defaultSuffix: str = ""
        self._whatsThis: str = ""
        self._directory: QDir = QDir("C:/GitHub/PyKotor/Libraries/Utility")

        print(f"fileMode: QFileDialog.FileMode({self._fileMode})")
        print(f"acceptMode: QFileDialog.AcceptMode({self._acceptMode})")
        print(f"viewMode: QFileDialog.ViewMode({self._viewMode})")
        print(f"options: QFileDialog.Options({self._options})")
        print(f"nameFilters: f{self._nameFilters}")
        print(f"selectedFiles: f{self._selectedFiles}")
        print(f"selectedUrls: f{self._selectedUrls}")
        print(f"directoryUrl: 'QUrl('{self._directoryUrl.path()}')'")
        print(f"supportedSchemes: 'f{self._supportedSchemes}'")
        print(f"sidebarUrls: 'f{self._sidebarUrls}'")
        print(f"defaultSuffix: 'f{self._defaultSuffix}'")
        print(f"whatsThis: 'f{self._whatsThis}'")
        print(f"directory: QDir('{self._directory.path()}')")
        print(f"default_labels: {self._DEFAULT_LABELS}")
        print(f"labelText: {self._labelText}")

    if TYPE_CHECKING:

        def options(self) -> QFileDialog.Option | QFileDialog.Options:
            return QFileDialog.options(QFileDialog.Option.DontUseNativeDialog)

        def setOptions(self, options: QFileDialog.Option | QFileDialog.Options) -> None:
            return QFileDialog.setOptions(self, options)

        def fileMode(self) -> QFileDialog.FileMode | int:
            return self._fileMode

        def setFileMode(self, mode: int) -> None:
            self._fileMode = mode

        def acceptMode(self) -> QFileDialog.AcceptMode | int:
            return self._acceptMode

        def setAcceptMode(self, mode: int) -> None:
            self._acceptMode = mode

        def viewMode(self) -> QFileDialog.ViewMode | int:
            return self._viewMode

        def setViewMode(self, mode: int) -> None:
            self._viewMode = mode

        def selectedFiles(self) -> list[str]:
            return self._selectedFiles

        def open(self, slot: PYQT_SLOT | None = None) -> None:
            return subprocess.Popen("start", shell=True)  # noqa: S602, S607

        def setVisible(self, visible: bool) -> None:  # noqa: FBT001
            return super().setVisible(visible)

        def selectUrl(self, url: QUrl) -> None:
            return super().selectUrl(url)

        def selectedUrls(self) -> list[QUrl]:
            return self._selectedUrls

        def directoryUrl(self) -> QUrl:
            return self._directoryUrl

        def setDirectoryUrl(self, directory: QUrl):
            self._directoryUrl = directory

        def supportedSchemes(self) -> list[str]:
            return self._supportedSchemes

        def setSupportedSchemes(self, schemes: list[str]):
            self._supportedSchemes = schemes

        def directory(self) -> QDir:
            return self._directory

        def setDirectory(self, directory: str | QDir) -> None:
            self._directory = directory

        def setNameFilters(self, filters: list[str]) -> None:
            self._nameFilters = filters

        def setNameFilter(self, file_filter: str) -> None:
            super().setNameFilter(file_filter)

        def selectFile(self, file_name: str) -> None:
            self._selectedFiles.append(file_name)

        def selectedNameFilter(self) -> str:
            return self._selectedNameFilter

        def setOption(self, option: int, on: bool = True):  # noqa: FBT001, FBT002
            self._options[option] = on

        def testOption(self, option: int) -> bool:
            return option in self._options

        def setMimeTypeFilters(self, filters: list[str]):
            super().setMimeTypeFilters(filters)

        def setSidebarUrls(self, urls: list[QUrl]):
            super().setSidebarUrls(urls)

        def sidebarUrls(self) -> list[QUrl]:
            return super().sidebarUrls()

        def setDefaultSuffix(self, suffix: str):
            super().setDefaultSuffix(suffix)

        def dragEnterEvent(self, event: QDragEnterEvent):
            super().dragEnterEvent(event)

        def dropEvent(self, event: QDropEvent):
            super().dropEvent(event)

        def startDrag(self, supported_actions: Qt.DropAction | Qt.DropActions):
            super().startDrag(supported_actions)

        def setLabelText(self, label: str, text: str):
            super().setLabelText(label, text)

        def enterWhatsThisMode(self):
            super().enterWhatsThisMode()

        def whatsThis(self) -> str:
            super().whatsThis()

        def __del__(self):
            super().__del__()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_dialog = TestQFileDialog(caption="Test")
    file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # noqa: FBT003
    file_dialog.show()
    sys.exit(app.exec())
