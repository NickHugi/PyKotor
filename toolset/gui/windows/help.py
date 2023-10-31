import json
import os
import xml.etree.ElementTree as ElemTree
import zipfile
from contextlib import suppress
from pathlib import Path
from typing import Dict, Optional

import markdown
import requests
from config import UPDATE_INFO_LINK
from gui.dialogs.asyncloader import AsyncLoader
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem, QWidget

from pykotor.common.stream import BinaryReader


class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: Optional[QWidget], startingPage: Optional[str] = None):
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
            # text = BinaryReader.load_file("./help/contents.xml")
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)

    def _setupContentsRecJSON(self, parent: Optional[QTreeWidgetItem], data: Dict) -> None:
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
            req = requests.get(UPDATE_INFO_LINK, timeout=15)
            updateInfoData = json.loads(req.text)

            if self.version is None or updateInfoData["help"]["version"] > self.version:
                msgbox = QMessageBox(QMessageBox.Information, "Update available",
                                     "A newer version of the help book is available for download, would you like to download it?")
                if msgbox.exec_():
                    def task():
                        return self._downloadUpdate(updateInfoData["help"]["directDownload"])
                    loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                    if loader.exec_():
                        self._setupContents()

    def _downloadUpdate(self, link: str) -> None:
        help_path = Path("help")
        if not help_path.exists():
            help_path.mkdir(parents=True)
        response = requests.get(link, stream=True)
        help_zip_path = help_path / "help.zip"
        with help_zip_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        with zipfile.ZipFile(help_zip_path, "r") as zip_ref:
            zip_ref.extractall("./help")

    def displayFile(self, filepath: str) -> None:
        try:
            text = BinaryReader.load_file(filepath).decode()
            html = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"]) if filepath.lower().endswith(".md") else text
            self.ui.textDisplay.setHtml(html)
        except OSError:
            QMessageBox(
                QMessageBox.Critical,
                "Failed to open help file",
                f"Could not access '{filepath}'.",
            ).exec_()

    def onContentsClicked(self) -> None:
        if self.ui.contentsTree.selectedItems():
            item = self.ui.contentsTree.selectedItems()[0]
            filename = item.data(0, QtCore.Qt.UserRole)
            if filename:
                self.ui.textDisplay.setSearchPaths(["./help", f"./help/{os.path.dirname(filename)}"])
                self.displayFile(f"./help/{filename}")
