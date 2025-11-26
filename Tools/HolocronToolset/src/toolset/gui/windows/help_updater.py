from __future__ import annotations

import zipfile

from pathlib import Path
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox

from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.gui.windows.help_window import HelpWindow
from utility.error_handling import universal_simplify_exception
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_file

if TYPE_CHECKING:
    from toolset.gui.windows.help_window import HelpWindow


class HelpUpdater:
    def __init__(self, help_window: HelpWindow):
        self.help_window: HelpWindow = help_window

    def check_for_updates(self):
        remote_info: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)
        try:
            if not isinstance(remote_info, dict):
                raise remote_info  # noqa: TRY301

            new_version = str(remote_info["help"]["version"])
            from toolset.gui.common.localization import translate as tr
            if self.help_window.help_content.version is None:
                title = tr("Help book missing")
                text = tr("You do not seem to have a valid help booklet downloaded, would you like to download it?")
            elif is_remote_version_newer(self.help_window.help_content.version, new_version):
                title = tr("Update available")
                text = tr("A newer version of the help book is available for download, would you like to download it?")
            else:
                RobustLogger().debug("No help booklet updates available, using version %s (latest version: %s)", self.help_window.help_content.version, new_version)
                return
        except Exception as e:  # noqa: BLE001
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            from toolset.gui.common.localization import translate as tr
            err_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                tr("An unexpected error occurred while parsing the help booklet."),
                error_msg,
                QMessageBox.StandardButton.Ok,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            err_msg_box.setWindowIcon(self.help_window.windowIcon())
            err_msg_box.exec()
        else:
            new_help_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                title,
                text,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            new_help_msg_box.setWindowIcon(self.help_window.windowIcon())
            new_help_msg_box.addButton(QMessageBox.StandardButton.Yes)
            new_help_msg_box.addButton(QMessageBox.StandardButton.No)
            user_response = new_help_msg_box.exec()
            if user_response == QMessageBox.StandardButton.Yes:

                def task():
                    return self._download_update()

                loader = AsyncLoader(self.help_window, "Download newer help files...", task, "Failed to update.")
                if loader.exec():
                    self.help_window.help_content.setup_contents()

    def _download_update(self):
        help_path = Path("./help").resolve()
        help_path.mkdir(parents=True, exist_ok=True)
        help_zip_path = Path("./help.zip").resolve()
        download_github_file("NickHugi/PyKotor", help_zip_path, "/Tools/HolocronToolset/downloads/help.zip")

        # Extract the ZIP file
        with zipfile.ZipFile(help_zip_path) as zip_file:
            RobustLogger().info("Extracting downloaded content to %s", help_path)
            zip_file.extractall(help_path)

        if is_frozen():
            help_zip_path.unlink()
