from __future__ import annotations

import base64
import os
import pathlib
import subprocess
import sys
import time

from contextlib import suppress
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

import requests
import requests.structures

from loggerplus import RobustLogger
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

from toolset.gui.common.localization import translate as tr, trf  # type: ignore[import-not-found]
from utility.updater.github import CompleteRepoData, TreeInfoData, extract_owner_repo, get_api_url, get_forks_url, get_main_url

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QClipboard, QIcon
    from qtpy.QtWidgets import QWidget


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
            if __name__ == "__main__":
                os.chdir(toolset_path)

logger = RobustLogger


class GitHubFileSelector(QDialog):
    def __init__(  # noqa: PLR0915
        self,
        *args,
        selected_files: list[str] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint
            & ~QtCore.Qt.WindowType.WindowMinMaxButtonsHint
        )
        self.setWindowTitle(tr("Select a GitHub Repository File"))
        self.setMinimumSize(600, 400)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        if len(args) == 1:
            owner, repo = extract_owner_repo(args[0])
        elif len(args) == 2:  # noqa: PLR2004
            owner, repo = args
        else:
            raise ValueError(repr(args))

        # Set the window icon using a standard QStyle icon
        self_style: QStyle | None = self.style()
        if self_style is None:
            raise RuntimeError("Failed to get QStyle")
        icon: QIcon = self_style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self.setWindowIcon(icon)

        self.owner: str = owner
        self.repo: str = repo
        self.forks_url: str = get_forks_url(owner, repo)
        self.api_url: str = get_api_url(owner, repo)
        self.main_url: str = get_main_url(owner, repo)
        self.selected_files: list[str] = selected_files or []

        self.repo_data: CompleteRepoData | None = None
        self.rate_limit_reset: int | None = None
        self.rate_limit_remaining: int | None = None

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        self.label: QLabel = QLabel(tr("Please select the correct script path or enter manually:"))
        main_layout.addWidget(self.label)

        self.fork_combo_box: QComboBox = QComboBox(self)
        self.fork_combo_box.setFixedWidth(300)
        self.fork_combo_box.currentIndexChanged.connect(self.on_fork_changed)
        main_layout.addWidget(QLabel(tr("Select Fork:")))
        main_layout.addWidget(self.fork_combo_box)

        filter_layout = QHBoxLayout()
        self.filter_edit: QLineEdit = QLineEdit(self)
        self.filter_edit.setPlaceholderText(tr("Type to filter paths..."))
        self.filter_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # pyright: ignore[reportArgumentType]
        self.filter_edit.textChanged.connect(self.on_filter_edit_changed)
        filter_layout.addWidget(self.filter_edit)

        self.search_button: QPushButton = QPushButton(tr("Search"), self)
        self.search_button.clicked.connect(self.search_files)
        filter_layout.addWidget(self.search_button)

        self.refresh_button: QPushButton = QPushButton(tr("Refresh"), self)
        self.refresh_button.clicked.connect(self.refresh_data)
        filter_layout.addWidget(self.refresh_button)

        main_layout.addLayout(filter_layout)

        self.repo_tree_widget: QTreeWidget = QTreeWidget(self)
        self.repo_tree_widget.setColumnCount(1)
        self.repo_tree_widget.setHeaderLabel(tr("GitHub Repository"))
        self.repo_tree_widget.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)  # pyright: ignore[reportArgumentType]
        self.repo_tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.repo_tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.repo_tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        main_layout.addWidget(self.repo_tree_widget)

        self.button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)  # pyright: ignore[reportArgumentType]
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.cloneButton: QPushButton = QPushButton(tr("Clone Repository"), self)
        self.cloneButton.clicked.connect(self.clone_repository)
        main_layout.addWidget(self.cloneButton)

        self.statusBar: QStatusBar = QStatusBar(self)
        main_layout.addWidget(self.statusBar)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.update_rate_limit_status)

        self.selected_path: str | None = None
        self.initialize_repo_data()

        # Initialize filterEdit with selectedFiles and call searchFiles
        if self.selected_files and self.repo_data is not None:
            self.filter_edit.setText(";".join(self.selected_files))
            self.search_files()

    def initialize_repo_data(self) -> CompleteRepoData | None:
        try:
            repo_data = CompleteRepoData.load_repo(self.owner, self.repo)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and "X-RateLimit-Reset" in e.response.headers:  # noqa: PLR2004
                if not self.timer.isActive():
                    QMessageBox.critical(self, tr("You are rate limited."), tr("You have submitted too many requests to github's api, check the status bar at the bottom."))
                    self.start_rate_limit_timer(e)
                return None

            QMessageBox.critical(self, tr("Repository Not Found"), trf("The repository '{owner}/{repo}' had an unexpected error:<br><br>{error}", owner=self.owner, repo=self.repo, error=str(e)))
            forks_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/forks"
            try:
                response: requests.Response = requests.get(forks_url, timeout=15)
                response.raise_for_status()
                forks_data: list[dict[str, Any]] = response.json()
                if forks_data:
                    first_fork = forks_data[0]["full_name"]
                    QMessageBox.information(self, tr("Using Fork"), trf("The main repository is not available. Using the fork: {fork}", fork=first_fork))
                    fork_owner, fork_repo = first_fork.split("/")
                    fork_repo_data: CompleteRepoData | None = CompleteRepoData.load_repo(fork_owner, fork_repo)
                    if fork_repo_data is None:
                        raise RuntimeError(f"Failed to load fork '{first_fork}'")
                    self.fork_combo_box.addItem(first_fork)
                    self._load_repo_data(fork_repo_data, do_fork_combo_update=False)
                    return fork_repo_data
                QMessageBox.critical(self, tr("No Forks Available"), tr("No forks are available to load."))
            except requests.exceptions.RequestException as fork_e:
                QMessageBox.critical(self, tr("Forks Load Error"), trf("Failed to load forks: {error}", error=str(fork_e)))
        else:
            self._load_repo_data(repo_data)
            self.stop_rate_limit_timer()
            return repo_data
        return None

    def _load_repo_data(
        self,
        data: CompleteRepoData,
        *,
        do_fork_combo_update: bool = True,
    ) -> None:
        self.repo_data = data
        if do_fork_combo_update:
            self.populate_fork_combobox()
        selected_fork = self.fork_combo_box.itemText(self.fork_combo_box.currentIndex())
        if not selected_fork or selected_fork == f"{self.owner}/{self.repo} (main)":
            self.load_main_branch_files()
        else:
            self.load_fork(selected_fork)

    def load_main_branch_files(self) -> None:
        if self.repo_data:
            self.repo_tree_widget.clear()
            self.populate_tree_widget()

    def populate_tree_widget(
        self,
        files: list[TreeInfoData] | None = None,
        parent_item: QTreeWidgetItem | None = None,
    ) -> None:
        if files is None:
            if self.repo_data is None or self.repo_data.tree is None:
                return
            files = self.repo_data.tree

        # Dictionary to hold the tree items by their paths
        path_to_item: dict[str, QTreeWidgetItem] = {}

        # Create all tree items without parents first
        for item in files:
            item_path = item.path
            tree_item = QTreeWidgetItem([PurePosixPath(item_path).name])
            tree_item.setToolTip(0, item.url)
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item)
            path_to_item[item_path] = tree_item

        # Add the tree items to their parents
        for item_path, tree_item in path_to_item.items():
            parent_path = str(PurePosixPath(item_path).parent)
            if parent_path in path_to_item:
                parent_item = path_to_item[parent_path]
                parent_item.addChild(tree_item)
            else:
                self.repo_tree_widget.addTopLevelItem(tree_item)

    def load_directory_contents(
        self,
        parent_item: QTreeWidgetItem,
        path: str,
    ) -> None:
        self.populate_tree_widget(parent_item=parent_item)

    def populate_fork_combobox(self) -> None:
        self.fork_combo_box.clear()
        self.fork_combo_box.addItem(f"{self.owner}/{self.repo} (main)")
        if self.repo_data is None or self.repo_data.forks is None:
            return
        for fork in self.repo_data.forks:
            self.fork_combo_box.addItem(fork.full_name)

    def search_files(self):
        self.on_filter_edit_changed()

    def on_filter_edit_changed(self):
        filter_text: str = self.filter_edit.text()
        if filter_text:
            file_names: list[str] = filter_text.lower().split(";")
            self.search_and_highlight(file_names)
            self.expand_all_items()
        else:

            def unhide_item(item: QTreeWidgetItem):
                item.setHidden(False)
                for i in range(item.childCount()):
                    child = item.child(i)
                    unhide_item(child)

            for i in range(self.repo_tree_widget.topLevelItemCount()):
                top_level_item = self.repo_tree_widget.topLevelItem(i)
                if top_level_item is None:
                    continue
                unhide_item(top_level_item)
            self.collapse_all_items()

    def search_and_highlight(
        self,
        partial_file_or_folder_names: list[str],
    ) -> None:
        if self.repo_data is None or self.repo_data.tree is None:
            return
        paths_to_highlight: list[str] = [item.path for item in self.repo_data.tree for partial_file_or_folder_name in partial_file_or_folder_names if partial_file_or_folder_name in item.path.split("/")[-1].lower()]
        self.expand_and_highlight_paths(set(paths_to_highlight))

    def expand_and_highlight_paths(
        self,
        paths: set[str],
    ) -> None:
        def find_item(
            parent: QTreeWidgetItem,
            text: str,
        ) -> QTreeWidgetItem | None:
            for i in range(parent.childCount()):
                child: QTreeWidgetItem | None = parent.child(i)
                if child is None:
                    continue
                if child.text(0) == text:
                    child.setHidden(False)
                    return child
            return None

        def highlight_path(path: str):
            parts: list[str] = path.split("/")
            current_item = None
            for part in parts:
                if current_item:
                    next_item: QTreeWidgetItem | None = find_item(current_item, part)
                    if next_item is None:
                        return  # Stop if the expected part is not found
                    current_item: QTreeWidgetItem = next_item
                else:  # Top level
                    for i in range(self.repo_tree_widget.topLevelItemCount()):
                        child: QTreeWidgetItem | None = self.repo_tree_widget.topLevelItem(i)
                        if child is not None and child.text(0) == part:
                            current_item = child
                            child.setHidden(False)
                            break
                    if current_item is None:
                        return  # Stop if the expected part is not found

            if current_item:
                current_item.setBackground(0, QBrush(Qt.GlobalColor.yellow))
                current_item.setExpanded(True)
                item_data: TreeInfoData | None = current_item.data(0, Qt.ItemDataRole.UserRole)
                if item_data and item_data.type == "tree":
                    unhide_all_children(current_item)

        def unhide_all_children(item: QTreeWidgetItem):
            for i in range(item.childCount()):
                child: QTreeWidgetItem | None = item.child(i)
                if child is None:
                    continue
                child.setHidden(False)
                unhide_all_children(child)

        def hide_all_items():
            for i in range(self.repo_tree_widget.topLevelItemCount()):
                top_level_item: QTreeWidgetItem | None = self.repo_tree_widget.topLevelItem(i)
                if top_level_item is not None:
                    hide_item(top_level_item)

        def hide_item(item: QTreeWidgetItem):
            item.setHidden(True)
            item.setBackground(0, QBrush(Qt.GlobalColor.transparent))
            for i in range(item.childCount()):
                child: QTreeWidgetItem | None = item.child(i)
                if child is None:
                    continue
                hide_item(child)

        hide_all_items()
        for path in paths:
            highlight_path(path)

    def expand_all_items(self):  # sourcery skip: class-extract-method
        root: QTreeWidgetItem | None = self.repo_tree_widget.invisibleRootItem()
        if root is None:
            return
        stack: list[QTreeWidgetItem] = [root]
        while stack:
            item: QTreeWidgetItem = stack.pop()
            item.setExpanded(True)
            stack.extend(item.child(i) for i in range(item.childCount()))

    def collapse_all_items(self):
        root: QTreeWidgetItem | None = self.repo_tree_widget.invisibleRootItem()
        stack: list[QTreeWidgetItem | None] = [root]
        while stack:
            item: QTreeWidgetItem | None = stack.pop()
            item.setExpanded(False)
            stack.extend(item.child(i) for i in range(item.childCount()))

    def get_selected_path(self) -> str | None:
        selected_items: list[QTreeWidgetItem] = self.repo_tree_widget.selectedItems()
        if not selected_items:
            return None

        item: QTreeWidgetItem = selected_items[0]
        item_info: TreeInfoData | None = item.data(0, Qt.ItemDataRole.UserRole)
        if item_info and item_info.type == "blob":
            return item_info.path

        return None

    def accept(self) -> None:
        self.selected_path = self.get_selected_path()
        if not self.selected_path:
            QMessageBox.warning(self, tr("No Selection"), tr("You must select a file."))
            return
        RobustLogger().info(f"{self.__class__.__name__}: User selected '{self.selected_path}'")
        super().accept()

    def on_fork_changed(
        self,
        index: int,
    ) -> None:
        if self.repo_data is not None:
            self._load_repo_data(self.repo_data, do_fork_combo_update=False)

    def load_fork(
        self,
        fork_name: str,
    ) -> None:
        self.repo_tree_widget.clear()
        full_name: str = fork_name
        # Format the contents_url with the proper path and add the recursive parameter
        tree_url: str = f"https://api.github.com/repos/{full_name}/git/trees/master?recursive=1"
        contents_dict: dict[str, Any] = self.api_get(tree_url)
        repo_index: list[TreeInfoData] = [TreeInfoData.from_dict(item) for item in contents_dict["tree"]]
        self.populate_tree_widget(repo_index)
        self.search_files()

    def api_get(
        self,
        url: str,
    ) -> dict[str, Any]:
        try:
            response: requests.Response = requests.get(url, timeout=15)
            response.raise_for_status()
            self.update_rate_limit_info(response.headers)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 403 or "X-RateLimit-Reset" not in e.response.headers:  # noqa: PLR2004
                raise
            self.start_rate_limit_timer(e)
            return {}  # Return an empty dictionary when rate limit is exceeded
        except requests.exceptions.RequestException:
            raise
        finally:
            self.stop_rate_limit_timer()

    def start_rate_limit_timer(
        self,
        e: requests.exceptions.HTTPError | None = None,
    ) -> None:
        if e:
            response: requests.Response = e.response
            if response.status_code == 403 and "X-RateLimit-Reset" in response.headers:  # noqa: PLR2004
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

    def update_rate_limit_info(
        self,
        headers: dict[str, Any] | requests.structures.CaseInsensitiveDict[str],
    ) -> None:
        if "X-RateLimit-Reset" in headers:
            self.rate_limit_reset = int(headers["X-RateLimit-Reset"])
        if "X-RateLimit-Remaining" in headers:
            self.rate_limit_remaining = int(headers["X-RateLimit-Remaining"])

    def on_item_double_clicked(
        self,
        item: QTreeWidgetItem,
        column: int,
    ) -> None:
        item_info: TreeInfoData | None = item.data(0, Qt.ItemDataRole.UserRole)
        if item_info is None:
            print("No item info")
            return
        if item_info.type != "blob":
            print(f"Skipping {item_info.path} of type {item_info.type}")
            return
        self.accept()

    def clone_repository(self) -> None:
        selected_fork = self.fork_combo_box.currentText().replace(" (main)", "")
        if not selected_fork:
            QMessageBox.warning(self, tr("No Fork Selected"), tr("Please select a fork to clone."))
            return

        url = f"https://github.com/{selected_fork}.git"
        try:
            import shlex

            command: list[str] = shlex.split(f"git clone {url}")
            subprocess.run(command, check=True)  # noqa: S603
            QMessageBox.information(self, tr("Clone Successful"), trf("Repository {fork} cloned successfully.", fork=selected_fork))
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, tr("Clone Failed"), trf("Failed to clone repository: {error}", error=str(e)))

    def show_context_menu(
        self,
        position: QPoint,
    ) -> None:
        item: QTreeWidgetItem | None = self.repo_tree_widget.itemAt(position)
        if item is None:
            return
        context_menu = QMenu(self)
        context_menu.addAction(tr("Open in Web Browser")).triggered.connect(lambda: self.open_in_web_browser(item))
        context_menu.addAction(tr("Copy URL")).triggered.connect(lambda: self.copy_url(item))
        context_menu.addAction(tr("Download")).triggered.connect(lambda: self.download(item))
        viewport: QWidget | None = self.repo_tree_widget.viewport()
        if viewport is None:
            return
        context_menu.exec(viewport.mapToGlobal(position))

    def convert_item_to_web_url(
        self,
        item: QTreeWidgetItem,
    ) -> str:
        # Extract owner and repo from self
        owner: str = self.owner
        repo: str = self.repo

        # Extract the file path from the item
        item_info: TreeInfoData | None = item.data(0, Qt.ItemDataRole.UserRole)
        if item_info is None or item_info.type != "blob":
            return ""

        file_path: str = item_info.path
        if self.repo_data is None or not self.repo_data.branches:
            return ""

        # Construct the web URL
        web_url: str = f"https://github.com/{owner}/{repo}/blob/{self.repo_data.branches[0].name}/{file_path}"
        return web_url

    def open_in_web_browser(
        self,
        item: QTreeWidgetItem,
    ) -> None:
        web_url: str = self.convert_item_to_web_url(item)
        if web_url:
            import webbrowser

            webbrowser.open(web_url)

    def copy_url(
        self,
        item: QTreeWidgetItem,
    ) -> None:
        url: str = self.convert_item_to_web_url(item)
        if url:
            clipboard: QClipboard | None = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(url)

    def download(
        self,
        item: QTreeWidgetItem,
    ) -> None:
        urls: list[str] = []
        self.collect_urls(item, urls)
        for url in urls:
            try:
                response: dict[str, Any] = self.api_get(url)
                if isinstance(response, dict) and "content" in response:
                    content: bytes = base64.b64decode(response["content"])
                    filename: str = self.convert_item_to_web_url(item).split("/")[-1]
                    with open(filename, "wb") as file:  # noqa: PTH123
                        file.write(content)
                    QMessageBox.information(self, tr("Download Successful"), trf("Downloaded {filename} to {path}", filename=filename, path=os.path.join(os.path.curdir, filename)))  # noqa: PTH118
                else:
                    QMessageBox.critical(self, tr("Download Failed"), tr("Failed to download the file content."))
            except requests.exceptions.RequestException as e:  # noqa: PERF203
                QMessageBox.critical(self, tr("Download Failed"), trf("Failed to download {name}: {error}", name=url.split('/')[-1], error=str(e)))

    def collect_urls(
        self,
        item: QTreeWidgetItem,
        urls: list[str],
    ) -> None:
        url: str = item.toolTip(0)
        if url:
            urls.append(url)
        for i in range(item.childCount()):
            child: QTreeWidgetItem | None = item.child(i)
            if child is None:
                continue
            self.collect_urls(child, urls)

    def refresh_data(self) -> None:
        data: CompleteRepoData | None = self.initialize_repo_data()
        if data is not None:
            self._load_repo_data(data)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    from toolset.main_init import on_app_crash

    sys.excepthook = on_app_crash

    owner = "KOTORCommunityPatches"
    repo = "Vanilla_KOTOR_Script_Source"

    app = QApplication(sys.argv)
    dialog = GitHubFileSelector(owner, repo, selected_files=["k_act_com33.nss"], parent=None)
    dialog.exec()
