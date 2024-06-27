from __future__ import annotations

import gc
import multiprocessing
import os
import pathlib
import platform
import sys

from contextlib import suppress
from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, NoReturn

import markdown
import requests

from qtpy import QtCore
from qtpy.QtCore import QThread, Qt
from qtpy.QtGui import QFont, QIcon
from qtpy.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QStyle, QTextEdit, QVBoxLayout

from toolset.config import LOCAL_PROGRAM_INFO, remoteVersionNewer, toolset_tag_to_version, version_to_toolset_tag
from toolset.gui.dialogs.asyncloader import ProgressDialog
from utility.logger_util import RobustRootLogger
from utility.misc import ProcessorArchitecture
from utility.system.os_helper import terminate_child_processes
from utility.updater.github import GithubRelease
from utility.updater.update import AppUpdate

if TYPE_CHECKING:
    from utility.updater.github import Asset


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


def convert_markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    return markdown.markdown(md_text)

def run_progress_dialog(
    progress_queue: Queue,
    title: str = "Operation Progress",
) -> NoReturn:
    """Call this with multiprocessing.Process."""
    app = QApplication(sys.argv)
    dialog = ProgressDialog(progress_queue, title)
    icon = app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
    dialog.setWindowIcon(QIcon(icon))
    dialog.show()
    sys.exit(app.exec_())

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.remoteInfo: dict[str, Any] = {}
        self.releases: list[GithubRelease] = []
        self.forksCache: dict[str, list[GithubRelease]] = {}
        self.setWindowTitle("Update Application")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)
        self.init_ui()
        self.init_config()

    def include_prerelease(self) -> bool:
        return self.preReleaseCheckBox.isChecked()

    def set_prerelease(self, value):
        return self.preReleaseCheckBox.setChecked(value)

    def init_ui(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(10, 10, 10, 10)

        # Include Pre-releases Checkbox
        self.preReleaseCheckBox = QCheckBox("Include Pre-releases")
        self.preReleaseCheckBox.stateChanged.connect(self.on_pre_release_changed)

        # Fetch Releases Button
        fetchReleasesButton = QPushButton("Fetch Releases")
        fetchReleasesButton.clicked.connect(self.init_config)
        fetchReleasesButton.setFixedSize(780, 50)
        mainLayout.addWidget(fetchReleasesButton)

        formLayout = QFormLayout()

        # Fork Selection Layout
        self.forkComboBox = QComboBox()
        self.forkComboBox.setFixedWidth(300)
        #self.forkComboBox.addItem("NickHugi/PyKotor")  # Default repository
        self.forkComboBox.currentIndexChanged.connect(self.on_fork_changed)
        formLayout.addRow("Select Fork:", self.forkComboBox)

        # Release Selection ComboBox
        self.releaseComboBox = QComboBox()
        self.releaseComboBox.setFixedWidth(300)
        self.releaseComboBox.currentIndexChanged.connect(self.on_release_changed)
        # Populate the releaseComboBox with releases
        for release in self.releases:
            self.releaseComboBox.addItem(release.tag_name, release)
            if release.tag_name == version_to_toolset_tag(LOCAL_PROGRAM_INFO["currentVersion"]):
                index = self.releaseComboBox.count() - 1
                self.releaseComboBox.setItemData(index, QFont("Arial", 10, QFont.Bold), Qt.FontRole)
        formLayout.addRow("Select Release:", self.releaseComboBox)

        mainLayout.addLayout(formLayout)
        mainLayout.addWidget(self.preReleaseCheckBox)

        # Install Selected Button
        updateButton = QPushButton("Install Selected")
        updateButton.clicked.connect(self.on_install_selected)
        updateButton.setFixedSize(150, 30)
        mainLayout.addWidget(updateButton)

        # Changelog Display
        self.changelogEdit = QTextEdit()
        self.changelogEdit.setReadOnly(True)
        self.changelogEdit.setFont(QFont("Arial", 10))
        mainLayout.addWidget(self.changelogEdit)

        # Update to Latest Button
        updateLatestButton = QPushButton("Update to Latest")
        updateLatestButton.clicked.connect(self.on_update_latest_clicked)
        updateLatestButton.setFixedSize(780, 50)  # Ensure consistent button size
        mainLayout.addWidget(updateLatestButton)

        # Current Version Display
        currentVersionLayout = QHBoxLayout()
        currentVersionLayout.addStretch(1)
        currentVersion = LOCAL_PROGRAM_INFO["currentVersion"]
        versionColor = "#FFA500" if remoteVersionNewer(currentVersion, toolset_tag_to_version(self.get_selected_tag())) else "#00FF00"
        versionText = f"<span style='font-size:16px; font-weight:bold; color:{versionColor};'>{currentVersion}</span>"
        currentVersionLabel = QLabel(f"Holocron Toolset Current Version: {versionText}")
        currentVersionLabel.setFont(QFont("Arial", 12))
        currentVersionLayout.addWidget(currentVersionLabel)
        currentVersionLayout.addStretch(1)
        mainLayout.addLayout(currentVersionLayout)

        self.setLayout(mainLayout)


    def init_config(self):
        self.set_prerelease(False)
        self.fetch_and_cache_forks_with_releases()
        self.forksCache["NickHugi/PyKotor"] = self.fetch_fork_releases("NickHugi/PyKotor", include_all=True)
        self.populate_fork_combo_box()
        self.on_fork_changed(self.forkComboBox.currentIndex())

    def fetch_and_cache_forks_with_releases(self):
        self.forksCache.clear()
        forks_url = "https://api.github.com/repos/NickHugi/PyKotor/forks"
        try:
            forks_response = requests.get(forks_url, timeout=15)
            forks_response.raise_for_status()
            forks_json = forks_response.json()
            for fork in forks_json:
                fork_owner_login = fork["owner"]["login"]
                fork_full_name = f"{fork_owner_login}/{fork['name']}"
                self.forksCache[fork_full_name] = self.fetch_fork_releases(fork_full_name, include_all=True)
        except requests.HTTPError as e:
            RobustRootLogger().exception(f"Failed to fetch forks: {e}")


    def fetch_fork_releases(self, fork_full_name: str, *, include_all: bool = False) -> list[GithubRelease]:
        url = f"https://api.github.com/repos/{fork_full_name}/releases"
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            releases_json = response.json()
            if include_all:
                return [GithubRelease.from_json(r) for r in releases_json]
            return [
                GithubRelease.from_json(r) for r in releases_json
                if not r["draft"] and (self.include_prerelease() or not r["prerelease"])
            ]
        except requests.HTTPError as e:
            RobustRootLogger().exception(f"Failed to fetch releases for {fork_full_name}: {e}")
            return []

    def populate_fork_combo_box(self):
        self.forkComboBox.clear()
        self.forkComboBox.addItem("NickHugi/PyKotor")
        for fork in self.forksCache:
            self.forkComboBox.addItem(fork)

    def on_pre_release_changed(self, state: bool):
        self.filter_releases_based_on_prerelease()

    def filter_releases_based_on_prerelease(self):
        selected_fork = self.forkComboBox.currentText()
        if selected_fork in self.forksCache:
            self.releases = [
                release for release in self.forksCache[selected_fork]
                if not release.draft
                and "toolset" in release.tag_name.lower()
                and (self.include_prerelease() or not release.prerelease)
            ]
        else:
            self.releases = []

        if not self.include_prerelease() and not self.releases:  # Don't show empty release comboboxes.
            print("No releases found, attempt to try again with prereleases")
            self.set_prerelease(True)
            return
        self.releases.sort(key=lambda x: bool(remoteVersionNewer("0.0.0", x.tag_name)))

        # Update Combo Box
        self.releaseComboBox.clear()
        self.changelogEdit.clear()
        for release in self.releases:
            self.releaseComboBox.addItem(release.tag_name, release)
        self.on_release_changed(self.releaseComboBox.currentIndex())

    def on_fork_changed(self, index: int):
        if index < 0:
            return
        self.filter_releases_based_on_prerelease()

    def get_selected_tag(self) -> str:
        release: GithubRelease = self.releaseComboBox.itemData(self.releaseComboBox.currentIndex())
        return release.tag_name if release else ""

    def on_release_changed(self, index: int):
        if index < 0 or index >= len(self.releases):
            return
        release: GithubRelease = self.releaseComboBox.itemData(index)
        if not release:
            return
        changelog_html: str = convert_markdown_to_html(release.body)
        self.changelogEdit.setHtml(changelog_html)

    def get_latest_release(self) -> GithubRelease | None:
        if self.releases:
            return self.releases[0]
        self.set_prerelease(True)
        return self.releases[0] if self.releases else None

    def on_update_latest_clicked(self):
        latest_release = self.get_latest_release()
        if not latest_release:
            print("No toolset releases found?")
            return
        self.start_update(latest_release)

    def on_install_selected(self):
        release = self.releaseComboBox.currentData()
        if not release:
            QMessageBox(QMessageBox.Icon.Information, "Select a release", "No release selected, select one first.").exec_()
            return
        self.start_update(release)

    def start_update(self, release: GithubRelease):
        # sourcery skip: remove-unreachable-code
        os_name = platform.system().lower()
        proc_arch = ProcessorArchitecture.from_os().get_machine_repr()
        asset: Asset | None = next((a for a in release.assets if proc_arch in a.name.lower() and os_name in a.name.lower()), None)

        if asset:
            download_url = asset.browser_download_url
            links = [download_url]
        else:
            # TODO(th3w1zard1): compile from src.
            # Realistically wouldn't be that hard, just run ./install_powershell.ps1 and ./compile/compile_toolset.ps1 and run the exe.
            # The difficult part would be finishing LibUpdate, currently only AppUpdate is working.
            return
            result = QMessageBox(  # noqa: F841
                QMessageBox.Icon.Question,
                "No asset found for this release.",
                f"There are no binaries available for download for release '{release.tag_name}'.", #Would you like to compile this release from source instead?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec_()

        progress_queue = Queue()
        progress_process = multiprocessing.Process(
            target=run_progress_dialog,
            args=(
                progress_queue,
                "Holocron Toolset is updating and will restart shortly...",
            ),
        )
        progress_process.start()
        self.hide()

        def download_progress_hook(
            data: dict[str, Any],
            progress_queue: Queue = progress_queue,
        ):
            #get_root_logger().debug("progress data: %s", data)
            progress_queue.put(data)

        def exitapp(kill_self_here: bool):  # noqa: FBT001
            packaged_data = {"action": "shutdown", "data": {}}
            progress_queue.put(packaged_data)
            ProgressDialog.monitor_and_terminate(progress_process)
            gc.collect()
            for obj in gc.get_objects():
                if isinstance(obj, QThread) and obj.isRunning():
                    RobustRootLogger().debug(f"Terminating QThread: {obj}")
                    obj.terminate()
                    obj.wait()
            terminate_child_processes()
            if kill_self_here:
                sys.exit(0)

        def expected_archive_filenames() -> list[str]:
            return [asset.name]

        updater = AppUpdate(
            links,
            "HolocronToolset",
            LOCAL_PROGRAM_INFO["currentVersion"],
            toolset_tag_to_version(release.tag_name),
            downloader=None,
            progress_hooks=[download_progress_hook],
            exithook=exitapp,
            version_to_tag_parser=version_to_toolset_tag,
        )
        updater.get_archive_names = expected_archive_filenames

        try:
            progress_queue.put({"action": "update_status", "text": "Downloading update..."})
            updater.download(background=False)
            progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
            updater.extract_restart()
            progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
            updater.cleanup()
        except Exception:  # noqa: BLE001
            RobustRootLogger().exception("Error occurred while downloading/installing the toolset.")
        finally:
            exitapp(kill_self_here=True)
