from __future__ import annotations

import xml.etree.ElementTree as ElemTree
import zipfile

from typing import TYPE_CHECKING, Callable

import markdown

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem

from pykotor.common.stream import BinaryReader
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.__main__ import is_frozen
from toolset.config import download_github_file, getRemoteToolsetUpdateInfo
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception
from utility.system.path import Path

if TYPE_CHECKING:
    import os

    from PyQt5.QtWidgets import QWidget

class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: QWidget | None, startingPage: str | None = None):
        super().__init__(parent)

        self.version: tuple[int, ...] | None = None

        from toolset.uic.windows import help as toolset_help  # noqa: PLC0415  # pylint: disable=C0415
        self.ui = toolset_help.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()
        self._setupContents()
        self.startingPage: str | None = startingPage

    def showEvent(self, a0):
        super().showEvent(a0)
        self.ui.textDisplay.setSearchPaths(["./help"])

        if self.ENABLE_UPDATES:
            self.checkForUpdates()

        if self.startingPage is not None:
            self.displayFile(self.startingPage)

    def _setupSignals(self):
        self.ui.contentsTree.clicked.connect(self.onContentsClicked)

    def _setupContents(self):
        self.ui.contentsTree.clear()

        try:
            tree = ElemTree.parse("./help/contents.xml")
            root = tree.getroot()

            self.version = tuple(map(int, str(root.get("version", "0.0")).split(".")))
            self._setupContentsRecXML(None, root)

            # Old JSON code:
            # text = BinaryReader.load_file("./help/contents.xml")
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)
        except Exception as e:
            print(f"Suppressed error: {universal_simplify_exception(e)}")

    def _setupContentsRecJSON(self, parent: QTreeWidgetItem | None, data: dict):
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        if "structure" in data:
            for title in data["structure"]:
                item = QTreeWidgetItem([title])
                item.setData(0, QtCore.Qt.UserRole, data["structure"][title]["filename"])
                add(item)
                self._setupContentsRecJSON(item, data["structure"][title])

    def _setupContentsRecXML(self, parent: QTreeWidgetItem | None, element: ElemTree.Element):
        add: Callable[..., None] = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        for child in element:
            item = QTreeWidgetItem([child.get("name", "")])
            item.setData(0, QtCore.Qt.UserRole, child.get("file"))
            add(item)
            self._setupContentsRecXML(item, child)

    def checkForUpdates(self):
        remoteInfo = getRemoteToolsetUpdateInfo(
            useBetaChannel=GlobalSettings().useBetaChannel,
        )
        try:
            if not isinstance(remoteInfo, dict):
                raise remoteInfo  # noqa: TRY301

            new_version = tuple(map(int, str(remoteInfo["help"]["version"]).split(".")))
            if self.version is None or new_version > self.version:
                newHelpMsgBox = QMessageBox(
                    QMessageBox.Information,
                    "Update available",
                    "A newer version of the help book is available for download, would you like to download it?",
                    parent=None,
                    flags=Qt.Window | Qt.Dialog | Qt.WindowStaysOnTopHint
                )
                newHelpMsgBox.setWindowIcon(self.windowIcon())
                newHelpMsgBox.addButton(QMessageBox.Yes)
                newHelpMsgBox.addButton(QMessageBox.No)
                user_response = newHelpMsgBox.exec_()
                if user_response == QMessageBox.Yes:
                    def task():
                        return self._downloadUpdate()
                    loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                    if loader.exec_():
                        self._setupContents()
        except Exception as e:  # noqa: BLE001
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            errMsgBox = QMessageBox(
                QMessageBox.Information,
                "An unexpected error occurred while parsing the help booklet.",
                error_msg,
                QMessageBox.Ok,
                parent=None,
                flags=Qt.Window | Qt.Dialog | Qt.WindowStaysOnTopHint
            )
            errMsgBox.setWindowIcon(self.windowIcon())
            errMsgBox.exec_()

    def _downloadUpdate(self):
        help_path = Path("help").resolve()
        help_path.mkdir(parents=True, exist_ok=True)
        help_zip_path = Path("./help.zip").resolve()
        download_github_file("NickHugi/PyKotor", help_zip_path, "/Tools/HolocronToolset/downloads/help.zip")

        # Extract the ZIP file
        with zipfile.ZipFile(help_zip_path) as zip_file:
            print(f"Extracting downloaded content to {help_path}")
            zip_file.extractall(help_path)

        if is_frozen():
            help_zip_path.unlink()

    def displayFile(self, filepath: os.PathLike | str):
        filepath = Path.pathify(filepath)
        try:
            text: str = decode_bytes_with_fallbacks(BinaryReader.load_file(filepath))
            html: str = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"]) if filepath.suffix.lower() == ".md" else text
            self.ui.textDisplay.setHtml(html)
        except OSError as e:
            QMessageBox(
                QMessageBox.Critical,
                "Failed to open help file",
                f"Could not access '{filepath}'.\n{universal_simplify_exception(e)}",
            ).exec_()

    def onContentsClicked(self):
        if self.ui.contentsTree.selectedItems():
            item: QTreeWidgetItem = self.ui.contentsTree.selectedItems()[0]
            filename = item.data(0, QtCore.Qt.UserRole)
            if filename:
                help_path = Path("./help").resolve()
                file_path = Path(help_path, filename)
                self.ui.textDisplay.setSearchPaths([str(help_path), str(file_path.parent)])
                self.displayFile(file_path)
