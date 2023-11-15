from __future__ import annotations

import base64
import json
import xml.etree.ElementTree as ElemTree
from contextlib import suppress
from typing import TYPE_CHECKING, Optional

import markdown
import requests
from config import UPDATE_INFO_LINK
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem, QWidget

from pykotor.common.misc import decode_bytes_with_fallbacks
from pykotor.common.stream import BinaryReader
from pykotor.helpers.path import Path, PurePath
from toolset.__main__ import is_debug_mode
from toolset.gui.dialogs.asyncloader import AsyncLoader

if TYPE_CHECKING:
    import os


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

            self.version = int(root.get("version", 0))
            self._setupContentsRecXML(None, root)

            # Old JSON code:
            # text = BinaryReader.load_file("./help/contents.xml")
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)

    def _setupContentsRecJSON(self, parent: Optional[QTreeWidgetItem], data: dict) -> None:
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        if "structure" in data:
            for title in data["structure"]:
                item = QTreeWidgetItem([title])
                item.setData(0, QtCore.Qt.UserRole, data["structure"][title]["filename"])  # type: ignore[attr-defined]
                add(item)
                self._setupContentsRecJSON(item, data["structure"][title])

    def _setupContentsRecXML(self, parent: Optional[QTreeWidgetItem], element: ElemTree.Element) -> None:
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        for child in element:
            item = QTreeWidgetItem([child.get("name")])
            item.setData(0, QtCore.Qt.UserRole, child.get("file"))  # type: ignore[attr-defined]
            add(item)
            self._setupContentsRecXML(item, child)

    def download_file(self, url: str, local_path: os.PathLike | str):
        local_path = local_path if isinstance(local_path, Path) else Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with local_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def download_directory(
        self,
        repo: os.PathLike | str,
        repo_path: os.PathLike | str,
        local_dir: os.PathLike | str,
    ):
        repo = repo if isinstance(repo, PurePath) else PurePath(repo)
        repo_path = repo_path if isinstance(repo_path, PurePath) else PurePath(repo_path)
        api_url = f"https://api.github.com/repos/{repo.as_posix()}/contents/{repo_path.as_posix()}"
        req = requests.get(api_url, timeout=15)
        req.raise_for_status()
        data = req.json()

        for item in data:
            item_path = Path(item["path"])
            local_path = item_path.relative_to("toolset")

            if item["type"] == "file":
                self.download_file(item["download_url"], local_path)
            elif item["type"] == "dir":
                self.download_directory(repo, item_path, local_path)

    def checkForUpdates(self) -> None:
        try:
            req = requests.get(UPDATE_INFO_LINK, timeout=15)
            req.raise_for_status()
            file_data = req.json()
            base64_content = file_data["content"]
            decoded_content = base64.b64decode(base64_content)  # Correctly decoding the base64 content
            updateInfoData = json.loads(decoded_content.decode("utf-8"))

            new_version = int(updateInfoData["help"]["version"])
            if self.version is None or new_version > self.version:
                msgbox = QMessageBox(QMessageBox.Information, "Update available",
                                    "A newer version of the help book is available for download, would you like to download it?")
                msgbox.addButton(QMessageBox.Yes)
                msgbox.addButton(QMessageBox.No)
                user_response = msgbox.exec_()
                if user_response == QMessageBox.Yes:
                    def task():
                        return self._downloadUpdate()
                    if is_debug_mode():
                        # Run synchronously for debugging
                        try:
                            task()
                            self._setupContents()
                        except Exception as e:
                            # Handle exception or log error
                            print(f"Error during update: {e!r}")
                    else:
                        loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                        if loader.exec_():
                            self._setupContents()
        except Exception as e:
            QMessageBox(
                QMessageBox.Information,
                "Unable to fetch latest version of the help booklet.",
                f"Check if you are connected to the internet.\nError: {e!r}",
                QMessageBox.Ok,
                self,
            ).exec_()

    def _downloadUpdate(self) -> None:
        help_path = Path("help")
        if not help_path.exists():
            help_path.mkdir(parents=True)
        self.download_directory("NickHugi/PyKotor", "toolset/help", ".")

    def displayFile(self, filepath: str) -> None:
        try:
            text = decode_bytes_with_fallbacks(BinaryReader.load_file(filepath))
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
            filename = item.data(0, QtCore.Qt.UserRole)  # type: ignore[attr-defined]
            if filename:
                self.ui.textDisplay.setSearchPaths(["./help", f"./help/{Path(filename).parent!s}"])
                self.displayFile(f"./help/{filename}")
