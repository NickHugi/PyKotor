from __future__ import annotations

import os
import pathlib
import platform
import sys

from multiprocessing import Process, Queue
from typing import Any

import markdown
import requests

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout


def fix_sys_and_cwd_path():
    """Fixes sys.path and current working directory for PyKotor.

    This function will determine whether they have the source files downloaded for pykotor in the expected directory. If they do, we
    insert the source path to pykotor to the beginning of sys.path so it'll have priority over pip's pykotor package if that is installed.
    If the toolset dir exists, change directory to that of the toolset. Allows users to do things like `python -m toolset`
    This function should never be used in frozen code.
    This function also ensures a user can run toolset/__main__.py directly.

    Processing Logic:
    ----------------
        - Checks if PyKotor package exists in parent directory of calling file.
        - If exists, removes parent directory from sys.path and adds to front.
        - Also checks for toolset package and changes cwd to that directory if exists.
        - This ensures packages and scripts can be located correctly on import.
    """

    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    file_absolute_path = pathlib.Path(__file__).resolve()

    pykotor_path = file_absolute_path.parents[7] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    pykotor_gl_path = file_absolute_path.parents[7] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if pykotor_gl_path.exists():
        update_sys_path(pykotor_gl_path.parent)
    utility_path = file_absolute_path.parents[7] / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        update_sys_path(utility_path)
    toolset_path = file_absolute_path.parents[3] / "toolset"
    if toolset_path.exists():
        update_sys_path(toolset_path.parent)
        os.chdir(toolset_path)

fix_sys_and_cwd_path()

from toolset.config import LOCAL_PROGRAM_INFO, getRemoteToolsetUpdateInfo, remoteVersionNewer, toolset_tag_to_version, version_to_toolset_tag
from toolset.gui.dialogs.asyncloader import ProgressDialog
from toolset.gui.windows.main import run_progress_dialog
from utility.logger_util import get_root_logger
from utility.misc import ProcessorArchitecture
from utility.updater.github import GithubRelease
from utility.updater.update import AppUpdate


def fetch_github_releases(include_draft: bool = True, include_prerelease: bool = False) -> list[GithubRelease]:
    url = "https://api.github.com/repos/NickHugi/PyKotor/releases"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        releases_json = response.json()
        # Convert json objects to GithubRelease objects
        return [
            GithubRelease.from_json(r)
            for r in releases_json
            if (
                (include_draft or not r["draft"])
                and (include_prerelease or not r["prerelease"])
                and "toolset" in r["tag_name"].lower()
            )
        ]
    except requests.HTTPError as e:
        get_root_logger().exception(f"Failed to fetch releases: {e}")
        return []

def convert_markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    return markdown.markdown(md_text)

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.include_prerelease: bool = False
        self.remoteInfo: dict[str, Any] = {}
        self.releases: list = fetch_github_releases()
        self.setWindowTitle("Update Application")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)
        self.init_ui()
        self.get_config()

    def init_ui(self):
        mainLayout = QVBoxLayout(self)

        # Option to fetch releases
        fetchReleasesButton = QPushButton("Fetch Releases")
        fetchReleasesButton.clicked.connect(self.on_fetch_releases_clicked)
        mainLayout.addWidget(fetchReleasesButton)

        # Release selection combo box
        self.releaseComboBox = QComboBox()
        self.releaseComboBox.setFixedSize(400, 30)  # Increase combo box size
        release: GithubRelease
        for release in self.releases:
            self.releaseComboBox.addItem(release.tag_name, release)
            if release.tag_name == version_to_toolset_tag(LOCAL_PROGRAM_INFO["currentVersion"]):
                # Set current version font to bold in the combo box
                index = self.releaseComboBox.count() - 1
                self.releaseComboBox.setItemData(index, QFont("Arial", 10, QFont.Bold), Qt.FontRole)

        # Current version display
        currentVersionLayout = QHBoxLayout()
        currentVersionLayout.addStretch(1)
        currentVersion = LOCAL_PROGRAM_INFO["currentVersion"]
        versionColor = self.determine_version_color(currentVersion, toolset_tag_to_version(self.get_selected_tag()))

        # Splitting the label text to apply different styles
        labelText = "Holocron Toolset Current Version: "
        # Applying HTML styling for different font sizes and weights
        versionText = f"<span style='font-size:20px; font-weight:bold; color:{versionColor};'>{currentVersion}</span>"
        currentVersionLabel = QLabel(f"{labelText}{versionText}")
        currentVersionLabel.setFont(QFont("Arial", 16))  # Set the base font size and style

        currentVersionLayout.addWidget(currentVersionLabel)
        currentVersionLayout.addStretch(1)
        mainLayout.addLayout(currentVersionLayout)

        optionsLayout = QHBoxLayout()

        # Include pre-release checkbox
        self.preReleaseCheckBox = QCheckBox("Include Pre-releases")
        self.preReleaseCheckBox.stateChanged.connect(self.on_pre_release_changed)
        optionsLayout.addWidget(self.preReleaseCheckBox)

        mainLayout.addLayout(optionsLayout)

        selectionLayout = QHBoxLayout()

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

    def determine_version_color(self, currentVersion, latestVersion):
        if remoteVersionNewer(currentVersion, latestVersion):
            return "#FFA500"  # Orange
        return "#00FF00"  # Green for up to date

    def get_config(self):
        result = getRemoteToolsetUpdateInfo()
        if isinstance(result, BaseException):
            raise result
        self.remoteInfo: dict[str, Any] = result
        self.releases: list = fetch_github_releases()
        self.on_release_changed(self.releaseComboBox.currentIndex())

    def update_release_combo_box(self):
        self.releaseComboBox.clear()
        release: GithubRelease
        for release in self.releases:
            if "toolset" not in release.tag_name.lower():
                continue
            self.releaseComboBox.addItem(release.tag_name, release)
        self.on_release_changed(self.releaseComboBox.currentIndex())

    def on_fetch_releases_clicked(self):
        # Update include_prerelease based on checkbox state
        self.include_prerelease = self.preReleaseCheckBox.isChecked()
        self.releases = fetch_github_releases(self.include_prerelease)
        self.update_release_combo_box()

    def on_pre_release_changed(self, state: bool):  # noqa: FBT001
        self.include_prerelease = state == Qt.Checked
        self.get_config()

    def get_selected_tag(self) -> str:
        curIndex: int = self.releaseComboBox.currentIndex()
        release: GithubRelease = self.releaseComboBox.itemData(curIndex)
        return release.tag_name if release else ""

    def on_release_changed(self, index: int):
        if index < 0 or index >= len(self.releases):
            return
        release: GithubRelease = self.releaseComboBox.itemData(index)
        if not release:
            return
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
            toolset_tag_to_version(release.tag_name),
            downloader=None,
            progress_hooks=[download_progress_hook],
            exithook=exitapp,
            version_to_tag_parser=version_to_toolset_tag
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
