from __future__ import annotations

import platform

from typing import TYPE_CHECKING, Any

import markdown

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout

from toolset.config import LOCAL_PROGRAM_INFO, is_remote_version_newer, toolset_tag_to_version
from toolset.gui.dialogs.update_github import fetch_and_cache_forks, fetch_fork_releases, filter_releases
from toolset.gui.dialogs.update_process import start_update_process
from utility.misc import ProcessorArchitecture
from utility.updater.github import GithubRelease

if TYPE_CHECKING:
    from utility.updater.github import Asset, GithubRelease


def convert_markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    return markdown.markdown(md_text)


class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowMinMaxButtonsHint  # pyright: ignore[reportArgumentType]
            & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint  # pyright: ignore[reportArgumentType]
        )
        self.remoteInfo: dict[str, Any] = {}
        self.releases: list[GithubRelease] = []
        self.forks_cache: dict[str, list[GithubRelease]] = {}
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
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Include Pre-releases Checkbox
        self.preReleaseCheckBox = QCheckBox("Include Pre-releases")
        self.preReleaseCheckBox.stateChanged.connect(self.on_pre_release_changed)

        # Fetch Releases Button
        fetch_releases_button = QPushButton("Fetch Releases")
        fetch_releases_button.clicked.connect(self.init_config)
        fetch_releases_button.setFixedSize(780, 50)
        main_layout.addWidget(fetch_releases_button)

        form_layout = QFormLayout()

        # Fork Selection Layout
        self.fork_combo_box: QComboBox = QComboBox()
        self.fork_combo_box.setFixedWidth(300)
        self.fork_combo_box.currentIndexChanged.connect(self.on_fork_changed)
        form_layout.addRow("Select Fork:", self.fork_combo_box)

        # Release Selection ComboBox
        self.release_combo_box: QComboBox = QComboBox()
        self.release_combo_box.setFixedWidth(300)
        self.release_combo_box.currentIndexChanged.connect(self.on_release_changed)
        form_layout.addRow("Select Release:", self.release_combo_box)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.preReleaseCheckBox)

        # Install Selected Button
        update_button: QPushButton = QPushButton("Install Selected")
        update_button.clicked.connect(self.on_install_selected)
        update_button.setFixedSize(150, 30)
        main_layout.addWidget(update_button)

        # Changelog Display
        self.changelog_edit: QTextEdit = QTextEdit()
        self.changelog_edit.setReadOnly(True)
        self.changelog_edit.setFont(QFont("Arial", 10))
        main_layout.addWidget(self.changelog_edit)

        # Update to Latest Button
        update_latest_button: QPushButton = QPushButton("Update to Latest")
        update_latest_button.clicked.connect(self.on_update_latest_clicked)
        update_latest_button.setFixedSize(780, 50)
        main_layout.addWidget(update_latest_button)

        # Current Version Display
        current_version_layout: QHBoxLayout = QHBoxLayout()
        current_version_layout.addStretch(1)
        current_version: str = LOCAL_PROGRAM_INFO["currentVersion"]
        version_color: str = "#FFA500" if is_remote_version_newer(current_version, toolset_tag_to_version(self.get_selected_tag())) else "#00FF00"
        version_text: str = f"<span style='font-size:16px; font-weight:bold; color:{version_color};'>{current_version}</span>"
        current_version_label: QLabel = QLabel(f"Holocron Toolset Current Version: {version_text}")
        current_version_label.setFont(QFont("Arial", 12))
        current_version_layout.addWidget(current_version_label)
        current_version_layout.addStretch(1)
        main_layout.addLayout(current_version_layout)

        self.setLayout(main_layout)

    def init_config(self):
        self.set_prerelease(False)
        self.forks_cache = fetch_and_cache_forks()
        self.forks_cache["NickHugi/PyKotor"] = fetch_fork_releases("NickHugi/PyKotor", include_all=True)
        self.populate_fork_combo_box()
        self.on_fork_changed(self.fork_combo_box.currentIndex())

    def populate_fork_combo_box(self):
        self.fork_combo_box.clear()
        self.fork_combo_box.addItem("NickHugi/PyKotor")
        for fork in self.forks_cache:
            self.fork_combo_box.addItem(fork)

    def on_pre_release_changed(
        self,
        state: bool,  # noqa: FBT001
    ):
        self.filter_releases_based_on_prerelease()

    def filter_releases_based_on_prerelease(self):
        selected_fork: str = self.fork_combo_box.currentText()
        if selected_fork in self.forks_cache:
            self.releases = filter_releases(self.forks_cache[selected_fork], self.include_prerelease())
        else:
            self.releases = []

        if not self.include_prerelease() and not self.releases:
            RobustLogger().info("No releases found, attempt to try again with prereleases")
            self.set_prerelease(True)
            return
        self.releases.sort(key=lambda x: bool(is_remote_version_newer("0.0.0", x.tag_name)))

        # Update Combo Box
        self.release_combo_box.clear()
        self.changelog_edit.clear()
        for release in self.releases:
            self.release_combo_box.addItem(release.tag_name, release)
        self.on_release_changed(self.release_combo_box.currentIndex())

    def on_fork_changed(
        self,
        index: int,  # noqa: FBT001
    ):
        if index < 0:
            return
        self.filter_releases_based_on_prerelease()

    def get_selected_tag(self) -> str:
        release: GithubRelease = self.release_combo_box.itemData(self.release_combo_box.currentIndex())
        return release.tag_name if release else ""

    def on_release_changed(
        self,
        index: int,  # noqa: FBT001
    ):
        if index < 0 or index >= len(self.releases):
            return
        release: GithubRelease = self.release_combo_box.itemData(index)
        if not release:
            return
        changelog_html: str = convert_markdown_to_html(release.body)
        self.changelog_edit.setHtml(changelog_html)

    def get_latest_release(self) -> GithubRelease | None:
        if self.releases:
            return self.releases[0]
        self.set_prerelease(True)
        return self.releases[0] if self.releases else None

    def on_update_latest_clicked(self):
        latest_release: GithubRelease | None = self.get_latest_release()
        if not latest_release:
            RobustLogger().warning("No toolset releases found")
            return
        self.start_update(latest_release)

    def on_install_selected(self):
        release = self.release_combo_box.currentData()
        if not release:
            QMessageBox(QMessageBox.Icon.Information, "Select a release", "No release selected, select one first.").exec()
            return
        self.start_update(release)

    def start_update(self, release: GithubRelease):
        os_name: str = platform.system().lower()
        proc_arch: str = ProcessorArchitecture.from_os().get_machine_repr()
        asset: Asset | None = next((a for a in release.assets if proc_arch in a.name.lower() and os_name in a.name.lower()), None)

        if not asset:
            QMessageBox(
                QMessageBox.Icon.Information,
                "No asset found",
                f"There are no binaries available for download for release '{release.tag_name}'.",
            ).exec()
            return

        download_url: str = asset.browser_download_url
        self.hide()
        start_update_process(release, download_url)
