from __future__ import annotations

import platform

from typing import TYPE_CHECKING, Any

import markdown

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from toolset.config import LOCAL_PROGRAM_INFO, is_remote_version_newer, toolset_tag_to_version
from toolset.gui.dialogs.update_github import fetch_and_cache_forks, fetch_fork_releases, filter_releases
from toolset.gui.dialogs.update_process import start_update_process
from utility.misc import ProcessorArchitecture

if TYPE_CHECKING:
    from utility.updater.github import GithubRelease


def convert_markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    return markdown.markdown(md_text)


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
        self.forkComboBox.currentIndexChanged.connect(self.on_fork_changed)
        formLayout.addRow("Select Fork:", self.forkComboBox)

        # Release Selection ComboBox
        self.releaseComboBox = QComboBox()
        self.releaseComboBox.setFixedWidth(300)
        self.releaseComboBox.currentIndexChanged.connect(self.on_release_changed)
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
        updateLatestButton.setFixedSize(780, 50)
        mainLayout.addWidget(updateLatestButton)

        # Current Version Display
        currentVersionLayout = QHBoxLayout()
        currentVersionLayout.addStretch(1)
        currentVersion = LOCAL_PROGRAM_INFO["currentVersion"]
        versionColor = "#FFA500" if is_remote_version_newer(currentVersion, toolset_tag_to_version(self.get_selected_tag())) else "#00FF00"
        versionText = f"<span style='font-size:16px; font-weight:bold; color:{versionColor};'>{currentVersion}</span>"
        currentVersionLabel = QLabel(f"Holocron Toolset Current Version: {versionText}")
        currentVersionLabel.setFont(QFont("Arial", 12))
        currentVersionLayout.addWidget(currentVersionLabel)
        currentVersionLayout.addStretch(1)
        mainLayout.addLayout(currentVersionLayout)

        self.setLayout(mainLayout)

    def init_config(self):
        self.set_prerelease(False)
        self.forksCache = fetch_and_cache_forks()
        self.forksCache["NickHugi/PyKotor"] = fetch_fork_releases("NickHugi/PyKotor", include_all=True)
        self.populate_fork_combo_box()
        self.on_fork_changed(self.forkComboBox.currentIndex())

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
            self.releases = filter_releases(self.forksCache[selected_fork], self.include_prerelease())
        else:
            self.releases = []

        if not self.include_prerelease() and not self.releases:
            RobustLogger().info("No releases found, attempt to try again with prereleases")
            self.set_prerelease(True)
            return
        self.releases.sort(key=lambda x: bool(is_remote_version_newer("0.0.0", x.tag_name)))

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
            RobustLogger().warning("No toolset releases found")
            return
        self.start_update(latest_release)

    def on_install_selected(self):
        release = self.releaseComboBox.currentData()
        if not release:
            QMessageBox(QMessageBox.Icon.Information, "Select a release", "No release selected, select one first.").exec()
            return
        self.start_update(release)

    def start_update(self, release: GithubRelease):
        os_name = platform.system().lower()
        proc_arch = ProcessorArchitecture.from_os().get_machine_repr()
        asset = next((a for a in release.assets if proc_arch in a.name.lower() and os_name in a.name.lower()), None)

        if not asset:
            QMessageBox(
                QMessageBox.Icon.Information,
                "No asset found",
                f"There are no binaries available for download for release '{release.tag_name}'.",
            ).exec()
            return

        download_url = asset.browser_download_url
        self.hide()
        start_update_process(release, download_url)