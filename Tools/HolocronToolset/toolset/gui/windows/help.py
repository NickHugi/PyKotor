from __future__ import annotations

import base64
import json
import xml.etree.ElementTree as ElemTree
import zipfile
from contextlib import suppress
from typing import TYPE_CHECKING

import markdown
import requests
from config import UPDATE_INFO_LINK
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem, QWidget

from pykotor.common.stream import BinaryReader
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.utility.path import Path, PurePath
from toolset.__main__ import is_frozen
from toolset.gui.dialogs.asyncloader import AsyncLoader

if TYPE_CHECKING:
    import os


class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: QWidget | None, startingPage: str | None = None):
        super().__init__(parent)

        self.version: tuple[int, ...] | None = None

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

            self.version = tuple(map(int, str(root.get("version", "0.0")).split(".")))
            self._setupContentsRecXML(None, root)

            # Old JSON code:
            # text = BinaryReader.load_file("./help/contents.xml")
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)

    def _setupContentsRecJSON(self, parent: QTreeWidgetItem | None, data: dict) -> None:
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        if "structure" in data:
            for title in data["structure"]:
                item = QTreeWidgetItem([title])
                item.setData(0, QtCore.Qt.UserRole, data["structure"][title]["filename"])  # type: ignore[attr-defined]
                add(item)
                self._setupContentsRecJSON(item, data["structure"][title])

    def _setupContentsRecXML(self, parent: QTreeWidgetItem | None, element: ElemTree.Element) -> None:
        add = self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild

        for child in element:
            item = QTreeWidgetItem([child.get("name")])
            item.setData(0, QtCore.Qt.UserRole, child.get("file"))  # type: ignore[attr-defined]
            add(item)
            self._setupContentsRecXML(item, child)


    def download_file(self, url_or_repo: str, local_path: os.PathLike | str, repo_path=None) -> None:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if repo_path is not None:
            # Construct the API URL for the file in the repository
            owner, repo = PurePath(url_or_repo).parts[-2:]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{PurePath(repo_path).as_posix()}"

            # Get file info from GitHub API
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            file_info = response.json()

            # Check if it's a file and get the download URL
            if file_info["type"] == "file":
                download_url = file_info["download_url"]
            else:
                msg = "The provided repo_path does not point to a file."
                raise ValueError(msg)
        else:
            # Direct URL
            download_url = url_or_repo

        # Download the file
        with requests.get(download_url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with local_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def download_directory(
        self,
        repo: os.PathLike | str,
        local_dir: os.PathLike | str,
        repo_path: os.PathLike | str,
    ) -> None:
        repo = PurePath(repo)
        repo_path = PurePath(repo_path)
        api_url = f"https://api.github.com/repos/{repo.as_posix()}/contents/{repo_path.as_posix()}"
        req = requests.get(api_url, timeout=15)
        req.raise_for_status()
        data = req.json()

        for item in data:
            item_path = Path(item["path"])
            local_path = item_path.relative_to("toolset")

            if item["type"] == "file":
                self.download_file(item["download_url"], Path(local_dir, local_path))
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

            new_version = tuple(map(int, str(updateInfoData["help"]["version"]).split(".")))
            if self.version is None or new_version > self.version:
                msgbox = QMessageBox(
                    QMessageBox.Information,
                    "Update available",
                    "A newer version of the help book is available for download, would you like to download it?",
                )
                msgbox.addButton(QMessageBox.Yes)
                msgbox.addButton(QMessageBox.No)
                user_response = msgbox.exec_()
                if user_response == QMessageBox.Yes:
                    def task():
                        return self._downloadUpdate()
                    loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                    if loader.exec_():
                        self._setupContents()
        except Exception as e:
            QMessageBox(
                QMessageBox.Information,
                "Unable to fetch latest version of the help booklet.",
                (
                    f"Error: {e!r}\n"
                    "Check if you are connected to the internet."
                ),
                QMessageBox.Ok,
                self,
            ).exec_()

    def _downloadUpdate(self) -> None:
        help_path = Path("help").resolve()
        help_path.mkdir(parents=True, exist_ok=True)
        help_zip_path = Path("./help.zip").resolve()
        self.download_file("NickHugi/PyKotor", help_zip_path, "toolset/help.zip")

        # Extract the ZIP file
        with zipfile.ZipFile(help_zip_path) as zip_file:
            print(f"Extracting downloaded content to {help_path!s}")
            zip_file.extractall(help_path)

        if is_frozen():
            help_zip_path.unlink()

    def displayFile(self, filepath: os.PathLike | str) -> None:
        filepath = filepath if isinstance(filepath, Path) else Path(filepath)
        try:
            text = decode_bytes_with_fallbacks(BinaryReader.load_file(filepath))
            html = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"]) if filepath.endswith(".md") else text
            self.ui.textDisplay.setHtml(html)
        except OSError:
            QMessageBox(
                QMessageBox.Critical,
                "Failed to open help file",
                f"Could not access '{filepath!s}'.",
            ).exec_()

    def onContentsClicked(self) -> None:
        if self.ui.contentsTree.selectedItems():
            item = self.ui.contentsTree.selectedItems()[0]
            filename = item.data(0, QtCore.Qt.UserRole)  # type: ignore[attr-defined]
            if filename:
                help_path = Path("./help").resolve()
                file_path = Path(help_path, filename)
                self.ui.textDisplay.setSearchPaths([str(help_path), str(file_path.parent)])
                self.displayFile(file_path)
