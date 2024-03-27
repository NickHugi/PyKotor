from __future__ import annotations

import dataclasses
import platform
import sys

from multiprocessing import Process, Queue
from typing import Any

import markdown
import requests

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout

from config import LOCAL_PROGRAM_INFO
from toolset.config import getRemoteToolsetUpdateInfo
from toolset.gui.dialogs.asyncloader import ProgressDialog
from toolset.gui.windows.main import run_progress_dialog
from utility.logger_util import get_root_logger
from utility.misc import ProcessorArchitecture
from utility.updater.update import AppUpdate


@dataclasses.dataclass
class Asset:
    url: str
    id: int
    name: str
    label: str | None
    state: str
    content_type: str
    size: int
    download_count: int
    created_at: str
    updated_at: str
    browser_download_url: str

@dataclasses.dataclass
class GithubRelease:
    url: str
    assets_url: str
    upload_url: str
    html_url: str
    id: int
    author: dict
    node_id: str
    tag_name: str
    target_commitish: str
    name: str
    draft: bool
    prerelease: bool
    created_at: str
    published_at: str
    assets: list[Asset]
    tarball_url: str
    zipball_url: str
    body: str

    @staticmethod
    def from_json(json_dict: dict) -> GithubRelease:
        assets = [Asset(**asset) for asset in json_dict.get("assets", [])]
        return GithubRelease(
            url=json_dict["url"],
            assets_url=json_dict["assets_url"],
            upload_url=json_dict["upload_url"],
            html_url=json_dict["html_url"],
            id=json_dict["id"],
            author=json_dict["author"],
            node_id=json_dict["node_id"],
            tag_name=json_dict["tag_name"],
            target_commitish=json_dict["target_commitish"],
            name=json_dict["name"],
            draft=json_dict["draft"],
            prerelease=json_dict["prerelease"],
            created_at=json_dict["created_at"],
            published_at=json_dict["published_at"],
            assets=assets,
            tarball_url=json_dict["tarball_url"],
            zipball_url=json_dict["zipball_url"],
            body=json_dict["body"]
        )

def fetch_github_releases():
    url = "https://api.github.com/repos/NickHugi/PyKotor/releases"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        releases_json = response.json()
        # Convert json objects to GithubRelease objects
        return [GithubRelease.from_json(r) for r in releases_json if not r["draft"] and not r["prerelease"]]
    except requests.HTTPError as e:
        get_root_logger().exception(f"Failed to fetch releases: {e}")
        return []

def convert_markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    return markdown.markdown(md_text)

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remoteInfo: dict[str, Any] = {}
        self.releases: list = fetch_github_releases()
        self.setWindowTitle("Update Application")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)
        self.init_ui()
        self.get_config()

    def init_ui(self):
        mainLayout = QVBoxLayout(self)

        # Current version display
        currentVersionLabel = QLabel(f"Your current version: {LOCAL_PROGRAM_INFO['currentVersion']}")
        currentVersionLabel.setFont(QFont("Arial", 10, QFont.Bold))
        mainLayout.addWidget(currentVersionLabel)

        selectionLayout = QHBoxLayout()

        # Release selection combo box
        self.releaseComboBox = QComboBox()
        self.releaseComboBox.setFixedSize(400, 30)  # Increase combo box size
        for release in self.releases:
            self.releaseComboBox.addItem(release["tag_name"], release)
            if release["tag_name"] == LOCAL_PROGRAM_INFO["currentVersion"]:
                # Set current version font to bold in the combo box
                index = self.releaseComboBox.count() - 1
                self.releaseComboBox.setItemData(index, QFont("Arial", 10, QFont.Bold), Qt.FontRole)

        self.releaseComboBox.currentIndexChanged.connect(self.on_release_changed)
        selectionLayout.addWidget(self.releaseComboBox)

        # Custom update button
        updateButton = QPushButton("Install Selected")
        updateButton.clicked.connect(self.on_download_clicked)
        updateButton.setFixedSize(120, 30)  # Ensure consistent button size

        selectionLayout.addWidget(updateButton)
        selectionLayout.setAlignment(Qt.AlignLeft)

        mainLayout.addLayout(selectionLayout)

        # Changelog display
        self.changelogEdit = QTextEdit()
        self.changelogEdit.setReadOnly(True)
        self.changelogEdit.setFont(QFont("Arial", 10))
        mainLayout.addWidget(self.changelogEdit)

        # Button layout
        buttonLayout = QHBoxLayout()

        # Update to the latest version button
        updateLatestButton = QPushButton("Update to Latest")
        updateLatestButton.clicked.connect(self.on_update_latest_clicked)
        updateLatestButton.setFixedSize(800, 50)  # Ensure consistent button size
        buttonLayout.addWidget(updateLatestButton)

        mainLayout.addLayout(buttonLayout)

    def get_config(self):
        result = getRemoteToolsetUpdateInfo()
        if isinstance(result, BaseException):
            raise result
        self.remoteInfo: dict[str, Any] = result
        self.releases: list = fetch_github_releases()

    def on_release_changed(self, index: int):
        release: GithubRelease = self.releaseComboBox.itemData(index)
        if release:
            changelog_html: str = convert_markdown_to_html(release.body)
            self.changelogEdit.setHtml(changelog_html)

    def on_update_latest_clicked(self):
        latest_release = self.releases[0]  # Assuming the first release is the latest
        self.start_update(latest_release)

    def on_download_clicked(self):
        release = self.releaseComboBox.currentData()
        self.start_update(release)

    def start_update(self, release: GithubRelease):
        # Find the asset that matches the architecture and OS
        os_name = platform.system().lower()
        proc_arch = ProcessorArchitecture.from_os().value.lower()
        asset = next((a for a in release.assets if proc_arch in a.name.lower() and os_name in a.name.lower()), None)

        if asset:
            download_url = asset.browser_download_url
            links = [download_url]
        else:
            result = QMessageBox(  # TODO(th3w1zard1): compile from src
                QMessageBox.Question,
                "No asset found for this release.",
                "There are no binaries available for download. Would you like to compile this release from source instead?",
                QMessageBox.Yes | QMessageBox.No,
                None,
                flags=Qt.Window | Qt.Dialog | Qt.WindowStaysOnTopHint,
            ).exec_()
            return
        progress_queue = Queue()
        progress_process = Process(target=run_progress_dialog, args=(progress_queue, "Holocron Toolset is updating and will restart shortly..."))
        progress_process.start()
        self.hide()
        def download_progress_hook(data: dict[str, Any], progress_queue: Queue = progress_queue):
            progress_queue.put(data)

        # Prepare the list of progress hooks with the method from ProgressDialog
        progress_hooks = [download_progress_hook]
        def exitapp(kill_self_here: bool):  # noqa: FBT001
            packaged_data = {"action": "shutdown", "data": {}}
            progress_queue.put(packaged_data)
            ProgressDialog.monitor_and_terminate(progress_process)
            if kill_self_here:
                sys.exit(0)

        updater = AppUpdate(
            links,
            "HolocronToolset",
            LOCAL_PROGRAM_INFO["currentVersion"],
            release.tag_name,
            downloader=None,
            progress_hooks=progress_hooks,
            exithook=exitapp
        )
        try:
            progress_queue.put({"action": "update_status", "text": "Downloading update..."})
            updater.download(background=False)
            progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
            updater.extract_restart()
            progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
            updater.cleanup()
        except Exception:
            get_root_logger().exception("Error occurred while downloading/installing the toolset.")
        finally:
            exitapp(True)

if __name__ == "__main__":
    app = QApplication([])
    dialog = UpdateDialog()
    dialog.show()
    app.exec_()
