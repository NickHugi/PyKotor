from __future__ import annotations

import base64
import os
import pathlib
import subprocess
import sys
import time

from contextlib import suppress
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import requests

from qtpy import QtCore
from qtpy.QtCore import QTimer, Qt
from qtpy.QtGui import QBrush
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QStyle,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QWidget

    from utility.updater.github import TreeInfoData



if __name__ == "__main__":
    with suppress(Exception):
        def update_sys_path(path: pathlib.Path):
            working_dir = str(path)
            if working_dir not in sys.path:
                sys.path.append(working_dir)

        file_absolute_path = pathlib.Path(__file__).resolve()

        pykotor_path = file_absolute_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
        pykotor_gl_path = file_absolute_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
        if pykotor_gl_path.exists():
            update_sys_path(pykotor_gl_path.parent)
        utility_path = file_absolute_path.parents[6] / "Libraries" / "Utility" / "src"
        if utility_path.exists():
            update_sys_path(utility_path)
        toolset_path = file_absolute_path.parents[3] / "toolset"
        if toolset_path.exists():
            update_sys_path(toolset_path.parent)
            os.chdir(toolset_path)


from utility.logger_util import RobustRootLogger
from utility.updater.github import (
    CompleteRepoData,
    ContentInfoData,
    extract_owner_repo,
    get_api_url,
    get_forks_url,
    get_main_url,
)

logger = RobustRootLogger


class GitHubFileSelector(QDialog):
    def __init__(
        self,
        *args,
        selectedFiles: list[str] | None = None,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint))
        self.setWindowTitle("Select a GitHub Repository File")
        self.setMinimumSize(600, 400)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        if len(args) == 1:
            owner, repo = extract_owner_repo(args[0])
        elif len(args) == 2:
            owner, repo = args
        else:
            raise ValueError(repr(args))

        # Set the window icon using a standard QStyle icon
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.setWindowIcon(icon)

        self.owner: str = owner
        self.repo: str = repo
        self.forksUrl: str = get_forks_url(owner, repo)
        self.apiUrl: str = get_api_url(owner, repo)
        self.mainUrl: str = get_main_url(owner, repo)
        self.selectedFiles: list[str] = selectedFiles or []

        self.repoData: CompleteRepoData | None = None
        self.rate_limit_reset: int | None = None
        self.rate_limit_remaining: int | None = None

        mainLayout = QVBoxLayout(self)
        self.setLayout(mainLayout)

        self.label: QLabel = QLabel("Please select the correct script path or enter manually:")
        mainLayout.addWidget(self.label)

        self.forkComboBox: QComboBox = QComboBox(self)
        self.forkComboBox.setFixedWidth(300)
        self.forkComboBox.currentIndexChanged.connect(self.onForkChanged)
        mainLayout.addWidget(QLabel("Select Fork:"))
        mainLayout.addWidget(self.forkComboBox)

        filterLayout = QHBoxLayout()
        self.filterEdit: QLineEdit = QLineEdit(self)
        self.filterEdit.setPlaceholderText("Type to filter paths...")
        self.filterEdit.setFocusPolicy(Qt.StrongFocus)
        self.filterEdit.textChanged.connect(self.onFilterEditChanged)
        filterLayout.addWidget(self.filterEdit)

        self.searchButton: QPushButton = QPushButton("Search", self)
        self.searchButton.clicked.connect(self.searchFiles)
        filterLayout.addWidget(self.searchButton)

        self.refreshButton: QPushButton = QPushButton("Refresh", self)
        self.refreshButton.clicked.connect(self.refresh_data)
        filterLayout.addWidget(self.refreshButton)

        mainLayout.addLayout(filterLayout)

        self.repoTreeWidget: QTreeWidget = QTreeWidget(self)
        self.repoTreeWidget.setColumnCount(1)
        self.repoTreeWidget.setHeaderLabel("GitHub Repository")
        self.repoTreeWidget.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.repoTreeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.repoTreeWidget.customContextMenuRequested.connect(self.show_context_menu)
        self.repoTreeWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)
        mainLayout.addWidget(self.repoTreeWidget)

        self.buttonBox: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)

        self.cloneButton: QPushButton = QPushButton("Clone Repository", self)
        self.cloneButton.clicked.connect(self.clone_repository)
        mainLayout.addWidget(self.cloneButton)

        self.statusBar: QStatusBar = QStatusBar(self)
        mainLayout.addWidget(self.statusBar)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.update_rate_limit_status)

        self.selectedPath: str | None = None
        self.initializeRepoData()

        # Initialize filterEdit with selectedFiles and call searchFiles
        if self.selectedFiles and self.repoData is not None:
            self.filterEdit.setText(";".join(self.selectedFiles))
            self.searchFiles()

    def initializeRepoData(self) -> CompleteRepoData | None:
        try:
            repo_data = CompleteRepoData.load_repo(self.owner, self.repo)
        except requests.exceptions.HTTPError as e:
            if (
                e.response.status_code == 403
                and "X-RateLimit-Reset" in e.response.headers
            ):
                if not self.timer.isActive():
                    QMessageBox.critical(self, "You are rate limited.", "You have submitted too many requests to github's api, check the status bar at the bottom.")
                    self.start_rate_limit_timer(e)
                return None

            QMessageBox.critical(self, "Repository Not Found", f"The repository '{self.owner}/{self.repo}' had an unexpected error:<br><br>{e}")
            forks_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/forks"
            try:
                response = requests.get(forks_url, timeout=15)
                response.raise_for_status()
                forks_data = response.json()
                if forks_data:
                    first_fork = forks_data[0]["full_name"]
                    QMessageBox.information(self, "Using Fork", f"The main repository is not available. Using the fork: {first_fork}")
                    fork_owner, fork_repo = first_fork.split("/")
                    fork_repo_data = CompleteRepoData.load_repo(fork_owner, fork_repo)
                    self.forkComboBox.addItem(first_fork)
                    self._load_repo_data(fork_repo_data, doForkComboUpdate=False)
                    return fork_repo_data
                QMessageBox.critical(self, "No Forks Available", "No forks are available to load.")
            except requests.exceptions.RequestException as fork_e:
                QMessageBox.critical(self, "Forks Load Error", f"Failed to load forks: {fork_e}")
        else:
            self._load_repo_data(repo_data)
            self.stop_rate_limit_timer()
            return repo_data
        return None

    def _load_repo_data(self, data: CompleteRepoData, *, doForkComboUpdate: bool = True):
        self.repoData = data
        if doForkComboUpdate:
            self.populateForkComboBox()
        selectedFork = self.forkComboBox.itemText(self.forkComboBox.currentIndex())
        if not selectedFork or selectedFork == f"{self.owner}/{self.repo} (main)":
            self.loadMainBranchFiles()
        else:
            self.loadFork(selectedFork)

    def loadMainBranchFiles(self) -> None:
        if self.repoData:
            self.repoTreeWidget.clear()
            self.populateTreeWidget()

    def populateTreeWidget(
        self,
        files: list[TreeInfoData] | None = None,
        parent_item: QTreeWidgetItem | None = None,
    ) -> None:
        if files is None:
            files = self.repoData.tree

        # Dictionary to hold the tree items by their paths
        path_to_item: dict[str, QTreeWidgetItem] = {}

        # Create all tree items without parents first
        for item in files:
            item_path = item.path
            tree_item = QTreeWidgetItem([PurePosixPath(item_path).name])
            tree_item.setToolTip(0, item.url)
            tree_item.setData(0, Qt.UserRole, item)
            path_to_item[item_path] = tree_item

        # Add the tree items to their parents
        for item_path, tree_item in path_to_item.items():
            parent_path = str(PurePosixPath(item_path).parent)
            if parent_path in path_to_item:
                parent_item = path_to_item[parent_path]
                parent_item.addChild(tree_item)
            else:
                self.repoTreeWidget.addTopLevelItem(tree_item)

    def loadDirectoryContents(self, parent_item: QTreeWidgetItem, path: str):
        self.populateTreeWidget(parent_item=parent_item)

    def populateForkComboBox(self) -> None:
        self.forkComboBox.clear()
        self.forkComboBox.addItem(f"{self.owner}/{self.repo} (main)")
        for fork in self.repoData.forks:
            self.forkComboBox.addItem(fork.full_name)

    def searchFiles(self):
        self.onFilterEditChanged()

    def onFilterEditChanged(self):
        filter_text = self.filterEdit.text()
        if filter_text:
            file_names = filter_text.lower().split(";")
            self.searchAndHighlight(file_names)
            self.expandAllItems()
        else:
            def unhideItem(item: QTreeWidgetItem):
                item.setHidden(False)
                for i in range(item.childCount()):
                    child = item.child(i)
                    unhideItem(child)

            for i in range(self.repoTreeWidget.topLevelItemCount()):
                topLevelItem = self.repoTreeWidget.topLevelItem(i)
                unhideItem(topLevelItem)
            self.collapseAllItems()

    def searchAndHighlight(self, partial_file_or_folder_names: list[str]):
        paths_to_highlight = [
            item.path
            for item in self.repoData.tree
            for partial_file_or_folder_name in partial_file_or_folder_names
            if partial_file_or_folder_name in item.path.split("/")[-1].lower()
        ]
        self.expandAndHighlightPaths(paths_to_highlight)

    def expandAndHighlightPaths(self, paths: set[str]):
        def find_item(parent: QTreeWidgetItem, text: str) -> QTreeWidgetItem | None:
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.text(0) == text:
                    child.setHidden(False)
                    return child
            return None

        def highlight_path(path: str):
            parts = path.split("/")
            current_item = None
            for part in parts:
                if current_item:
                    next_item = find_item(current_item, part)
                    if next_item is None:
                        return  # Stop if the expected part is not found
                    current_item = next_item
                else:  # Top level
                    for i in range(self.repoTreeWidget.topLevelItemCount()):
                        child = self.repoTreeWidget.topLevelItem(i)
                        if child.text(0) == part:
                            current_item = child
                            child.setHidden(False)
                            break
                    if current_item is None:
                        return  # Stop if the expected part is not found

            if current_item:
                current_item.setBackground(0, QBrush(Qt.yellow))
                current_item.setExpanded(True)
                if current_item.data(0, Qt.UserRole).type == "tree":
                    unhideAllChildren(current_item)

        def unhideAllChildren(item: QTreeWidgetItem):
            for i in range(item.childCount()):
                child = item.child(i)
                child.setHidden(False)
                unhideAllChildren(child)

        def hideAllItems():
            for i in range(self.repoTreeWidget.topLevelItemCount()):
                topLevelItem = self.repoTreeWidget.topLevelItem(i)
                hideItem(topLevelItem)

        def hideItem(item: QTreeWidgetItem):
            item.setHidden(True)
            item.setBackground(0, QBrush(Qt.NoBrush))
            for i in range(item.childCount()):
                child = item.child(i)
                hideItem(child)

        hideAllItems()
        for path in paths:
            highlight_path(path)

    def expandAllItems(self):  # sourcery skip: class-extract-method
        root = self.repoTreeWidget.invisibleRootItem()
        stack = [root]
        while stack:
            item = stack.pop()
            item.setExpanded(True)
            stack.extend(item.child(i) for i in range(item.childCount()))

    def collapseAllItems(self):
        root = self.repoTreeWidget.invisibleRootItem()
        stack = [root]
        while stack:
            item = stack.pop()
            item.setExpanded(False)
            stack.extend(item.child(i) for i in range(item.childCount()))

    def getSelectedPath(self) -> str | None:
        selected_items = self.repoTreeWidget.selectedItems()
        if selected_items:
            item = selected_items[0]
            item_info: TreeInfoData | None = item.data(0, Qt.UserRole)
            if item_info and item_info.type == "blob":
                return item_info.path
                # Construct the URL in the required format
                #return f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{item_info.path}"
        return None

    def accept(self) -> None:
        self.selectedPath = self.getSelectedPath()
        if not self.selectedPath:
            QMessageBox.warning(self, "No Selection", "You must select a file.")
            return
        RobustRootLogger.info(f"{self.__class__.__name__}: User selected '{self.selectedPath}'")
        super().accept()

    def onForkChanged(self, index: int) -> None:
        self._load_repo_data(self.repoData, doForkComboUpdate=False)

    def loadFork(self, forkName: str):
        self.repoTreeWidget.clear()
        full_name = forkName
        # Format the contents_url with the proper path and add the recursive parameter
        tree_url = f"https://api.github.com/repos/{full_name}/git/trees/master?recursive=1"
        contents_dict = self.api_get(tree_url)
        repoIndex = [ContentInfoData.from_dict(item) for item in contents_dict["tree"]]
        self.populateTreeWidget(repoIndex)
        self.searchFiles()

    def api_get(self, url: str) -> dict:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            self.update_rate_limit_info(response.headers)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if (
                e.response.status_code != 403
                or "X-RateLimit-Reset" not in e.response.headers
            ):
                raise
            self.start_rate_limit_timer(e)
        except requests.exceptions.RequestException as e:
            raise
        else:
            self.stop_rate_limit_timer()

    def start_rate_limit_timer(self, e: requests.exceptions.HTTPError = None) -> None:
        if e:
            response = e.response
            if (
                response.status_code == 403
                and "X-RateLimit-Reset" in response.headers
            ):
                self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])
                self.rate_limit_remaining = 0

        self.update_rate_limit_status()
        self.timer.start(1000)  # update every second

    def stop_rate_limit_timer(self) -> None:
        self.timer.stop()
        self.statusBar.clearMessage()

    def update_rate_limit_status(self) -> None:
        if self.rate_limit_reset is None or self.rate_limit_remaining is None:
            return
        if self.rate_limit_remaining > 0:
            self.statusBar.showMessage(f"Requests remaining: {self.rate_limit_remaining}")
            self.stop_rate_limit_timer()
        else:
            remaining_time = max(self.rate_limit_reset - time.time(), 0)
            self.statusBar.showMessage(f"Rate limit exceeded. Try again in {int(remaining_time)} seconds.")
            if int(remaining_time) % 15 == 0:  # Refresh every 15 seconds, sometimes github's X-RateLimit-Reset is wrong.
                self.refresh_data()
            elif remaining_time <= 0:
                self.refresh_data()
                self.stop_rate_limit_timer()

    def update_rate_limit_info(self, headers: dict):
        if "X-RateLimit-Reset" in headers:
            self.rate_limit_reset = int(headers["X-RateLimit-Reset"])
        if "X-RateLimit-Remaining" in headers:
            self.rate_limit_remaining = int(headers["X-RateLimit-Remaining"])

    def onItemDoubleClicked(self, item: QTreeWidgetItem, column: int):
        item_info: TreeInfoData | None = item.data(0, Qt.UserRole)
        if item_info is None or item_info.type != "blob":
            print(f"Skipping {item_info.path} of type {item_info.type}")
            return
        self.accept()

    def clone_repository(self) -> None:
        selectedFork = self.forkComboBox.currentText().replace(" (main)", "")
        if not selectedFork:
            QMessageBox.warning(self, "No Fork Selected", "Please select a fork to clone.")
            return

        url = f"https://github.com/{selectedFork}.git"
        try:
            subprocess.run(["git", "clone", url], check=True)
            QMessageBox.information(self, "Clone Successful", f"Repository {selectedFork} cloned successfully.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Clone Failed", f"Failed to clone repository: {e!s}")

    def show_context_menu(self, position: QPoint):
        item = self.repoTreeWidget.itemAt(position)
        if not item:
            return
        context_menu = QMenu(self)
        context_menu.addAction("Open in Web Browser").triggered.connect(lambda: self.open_in_web_browser(item))
        context_menu.addAction("Copy URL").triggered.connect(lambda: self.copy_url(item))
        context_menu.addAction("Download").triggered.connect(lambda: self.download(item))
        context_menu.exec_(self.repoTreeWidget.viewport().mapToGlobal(position))

    def convert_item_to_web_url(self, item: QTreeWidgetItem) -> str:
        # Extract owner and repo from self
        owner = self.owner
        repo = self.repo

        # Extract the file path from the item
        item_info: TreeInfoData = item.data(0, Qt.UserRole)
        if item_info and item_info.type == "blob":
            file_path = item_info.path

            # Construct the web URL
            web_url = f"https://github.com/{owner}/{repo}/blob/{self.repoData.branches[0].name}/{file_path}"
            return web_url

        return ""

    def open_in_web_browser(self, item: QTreeWidgetItem) -> None:
        web_url = self.convert_item_to_web_url(item)
        if web_url:
            import webbrowser
            webbrowser.open(web_url)

    def copy_url(self, item: QTreeWidgetItem) -> None:
        url = self.convert_item_to_web_url(item)
        if url:
            QApplication.clipboard().setText(url)

    def download(self, item: QTreeWidgetItem) -> None:
        urls: list[str] = []
        self.collect_urls(item, urls)
        for url in urls:
            try:
                response = self.api_get(url)
                if isinstance(response, dict) and "content" in response:
                    content = base64.b64decode(response["content"])
                    filename = self.convert_item_to_web_url(item).split("/")[-1]
                    with open(filename, "wb") as file:
                        file.write(content)
                    QMessageBox.information(self, "Download Successful", f"Downloaded {filename} to {Path(filename).resolve()}")
                else:
                    QMessageBox.critical(self, "Download Failed", "Failed to download the file content.")
            except requests.exceptions.RequestException as e:  # noqa: PERF203
                QMessageBox.critical(self, "Download Failed", f"Failed to download {url.split('/')[-1]}: {e!s}")

    def collect_urls(self, item: QTreeWidgetItem, urls: list[str]):
        url = item.toolTip(0)
        if url:
            urls.append(url)
        for i in range(item.childCount()):
            self.collect_urls(item.child(i), urls)

    def refresh_data(self) -> None:
        data: CompleteRepoData | None = self.initializeRepoData()
        if data is not None:
            self._load_repo_data(data)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    from toolset.__main__ import onAppCrash
    sys.excepthook = onAppCrash

    owner = "KOTORCommunityPatches"
    repo = "Vanilla_KOTOR_Script_Source"

    app = QApplication(sys.argv)
    dialog = GitHubFileSelector(owner, repo, selectedFiles=["k_act_com33.nss"], parent=None)
    dialog.exec_()
