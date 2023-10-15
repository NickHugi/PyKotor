import json
import os
import xml.etree.ElementTree as ElemTree
import zipfile
from contextlib import suppress
from typing import Optional

import markdown
import requests
from config import UPDATE_INFO_LINK
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem, QWidget

from pykotor.common.stream import BinaryReader
from pykotor.tools.path import Path, PurePath
from toolset.gui.dialogs.asyncloader import AsyncLoader


class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: Optional[QWidget], startingPage: Optional[os.PathLike] = None):
        super().__init__(parent)

        self.version: Optional[int] = None

        from toolset.uic.windows import help

        self.ui = help.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()
        self._setupContents()

        self.ui.textDisplay.setSearchPaths(["./help"])

        if self.ENABLE_UPDATES:
            self.checkForUpdates()

        if startingPage:
            self.displayFile(startingPage)

    def _setupSignals(self) -> None:
        self.ui.contentsTree.clicked.connect(self.onContentsClicked)

    def _setupContents(self) -> None:
        self.ui.contentsTree.clear()

        with suppress(Exception):
            tree = ElemTree.parse("./help/contents.xml")
            root = tree.getroot()

            self.version = root.get("version")
            self._setupContentsRecXML(None, root)

            # Old JSON code:

    def _setupContentsRecJSON(self, parent: Optional[QTreeWidgetItem], data: dict) -> None:
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        if "structure" in data:
            for title in data["structure"]:
                item = QTreeWidgetItem([title])
                item.setData(0, QtCore.Qt.UserRole, data["structure"][title]["filename"])
                add(item)
                self._setupContentsRecJSON(item, data["structure"][title])

    def _setupContentsRecXML(self, parent: Optional[QTreeWidgetItem], element: ElemTree.Element) -> None:
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        for child in element:
            item = QTreeWidgetItem([child.get("name")])
            item.setData(0, QtCore.Qt.UserRole, child.get("file"))
            add(item)
            self._setupContentsRecXML(item, child)

    def checkForUpdates(self) -> None:
        with suppress(Exception):
            req = requests.get(UPDATE_INFO_LINK, timeout=120)
            updateInfoData = json.loads(req.text)

            if self.version is None or updateInfoData["help"]["version"] > self.version:
                msgbox = QMessageBox(
                    QMessageBox.Information,
                    "Update available",
                    "A newer version of the help book is available for download, would you like to download it?",
                )
                if msgbox.exec_():

                    def task():
                        return self._downloadUpdate(updateInfoData["help"]["directDownload"])

                    loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                    if loader.exec_():
                        self._setupContents()

    def _downloadUpdate(self, link: str) -> None:
        help_zip = Path("./help", "help.zip")
        if not help_zip.parent.exists():
            help_zip.parent.mkdir(exist_ok=True, parents=True)
        response = requests.get(link, stream=True, timeout=120)
        with help_zip.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        with zipfile.ZipFile(help_zip, "r") as zip_ref:
            zip_ref.extractall(help_zip.parent)

    def displayFile(self, file_path: os.PathLike) -> None:
        pl_file_path = file_path if isinstance(file_path, PurePath) else Path(file_path)
        try:
            text = BinaryReader.load_file(pl_file_path).decode()
            html = (
                markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"])
                if pl_file_path.suffix.lower() == ".md"
                else text
            )
            self.ui.textDisplay.setHtml(html)
        except (OSError, FileNotFoundError):
            QMessageBox(
                QMessageBox.Critical,
                "Failed to open help file",
                f"Could not access '{pl_file_path}'.",
            ).exec_()

    def onContentsClicked(self) -> None:
        if self.ui.contentsTree.selectedItems():
            item = self.ui.contentsTree.selectedItems()[0]
            file_path_str = item.data(0, QtCore.Qt.UserRole)
            if file_path_str:
                help_subvar = Path("./help", file_path_str)
                self.ui.textDisplay.setSearchPaths(
                    ["./help", str(help_subvar)],
                )
                self.displayFile(help_subvar)
