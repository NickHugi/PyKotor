import json
import os
import zipfile
from contextlib import suppress
from typing import Dict, Optional
import xml.etree.ElementTree as ET

import markdown
import requests
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QWidget, QTreeWidgetItem, QMessageBox
from pykotor.common.stream import BinaryReader

from config import UPDATE_INFO_LINK
from misc.asyncloader import AsyncLoader


class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.version: Optional[int] = None

        from misc.help import helpwindow_ui
        self.ui = helpwindow_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()
        self._setupContents()

        self.ui.textDisplay.setSearchPaths(["./help"])

        if self.ENABLE_UPDATES:
            self.checkForUpdates()

    def _setupSignals(self) -> None:
        self.ui.contentsTree.clicked.connect(self.onContentsClicked)

    def _setupContents(self) -> None:
        self.ui.contentsTree.clear()

        with suppress(Exception):
            tree = ET.parse("./help/contents.xml")
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

    def _setupContentsRecXML(self, parent: Optional[QTreeWidgetItem], element: ET.Element) -> None:
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        for child in element:
            item = QTreeWidgetItem([child.get("name")])
            item.setData(0, QtCore.Qt.UserRole, child.get("file"))
            add(item)
            self._setupContentsRecXML(item, child)

    def checkForUpdates(self) -> None:
        req = requests.get(UPDATE_INFO_LINK)
        updateInfoData = json.loads(req.text)

        with suppress(Exception):
            if self.version is None or updateInfoData["help"]["version"] > self.version:
                msgbox = QMessageBox(QMessageBox.Information, "Update available",
                                     "A newer version of the help book is available for download, would you like to download it?")
                if msgbox.exec_():
                    task = lambda: self._downloadUpdate(updateInfoData["help"]["directDownload"])
                    loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                    if loader.exec_():
                        self._setupContents()

    def _downloadUpdate(self, link: str) -> None:
        if not os.path.exists("./help"):
            os.mkdir("./help")
        response = requests.get(link, stream=True)
        with open("./help/help.zip", 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        with zipfile.ZipFile("./help/help.zip", 'r') as zip_ref:
            zip_ref.extractall("./help")

    def displayFile(self, filepath: str) -> None:
        try:
            text = BinaryReader.load_file(filepath).decode()
            html = markdown.markdown(text, extensions=['tables']) if filepath.endswith(".md") else text
            self.ui.textDisplay.setHtml(html)
        except (IOError, FileNotFoundError):
            QMessageBox(QMessageBox.Critical, "Failed to open help file", "Could not access '{}'.".format(filepath)).exec_()

    def onContentsClicked(self) -> None:
        if self.ui.contentsTree.selectedItems():
            item = self.ui.contentsTree.selectedItems()[0]
            filename = item.data(0, QtCore.Qt.UserRole)
            if filename is not None and filename != "":
                self.displayFile("./help/{}".format(filename))
