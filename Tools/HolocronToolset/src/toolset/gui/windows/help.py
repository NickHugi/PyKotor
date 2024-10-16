from __future__ import annotations

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree as ElemTree

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring

    ElemTree.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended due to security concerns.")

import zipfile

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import markdown

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem

from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_file

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QShowEvent
    from qtpy.QtWidgets import QWidget


class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: QWidget | None, startingPage: str | None = None):
        super().__init__(parent)

        self.version: str | None = None

        from toolset.uic.qtpy.windows import help as toolset_help
        self.ui = toolset_help.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_signals()
        self._setup_contents()
        self.starting_page: str | None = startingPage

    def showEvent(self, a0: QShowEvent):
        super().showEvent(a0)
        self.ui.textDisplay.setSearchPaths(["./help"])

        if self.ENABLE_UPDATES:
            self.check_for_updates()

        if self.starting_page is None:
            return
        self.display_file(self.starting_page)

    def _setup_signals(self):
        self.ui.contentsTree.clicked.connect(self.on_contents_clicked)

    def _setup_contents(self):
        self.ui.contentsTree.clear()

        try:
            tree = ElemTree.parse("./help/contents.xml")  # noqa: S314 incorrect warning.
            root = tree.getroot()

            self.version = str(root.get("version", "0.0"))
            self._setup_contents_rec_xml(None, root)

            # Old JSON code:
            # text = Path("./help/contents.xml").read_text()
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)
        except Exception:  # noqa: BLE001
            RobustLogger().debug("Suppressed error in HelpWindow._setupContents", exc_info=True)

    def _setup_contents_rec_json(self, parent: QTreeWidgetItem | None, data: dict[str, Any]):
        addItem: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.ui.contentsTree.addTopLevelItem
            if parent is None
            else parent.addChild
        )

        structure = data.get("structure", {})
        for title in structure:
            item = QTreeWidgetItem([title])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, structure[title]["filename"])
            addItem(item)
            self._setup_contents_rec_json(item, structure[title])

    def _setup_contents_rec_xml(self, parent: QTreeWidgetItem | None, element: ElemTree.Element):
        addItem: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.ui.contentsTree.addTopLevelItem
            if parent is None
            else parent.addChild
        )

        for child in element:
            item = QTreeWidgetItem([child.get("name", "")])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, child.get("file"))
            addItem(item)
            self._setup_contents_rec_xml(item, child)

    def check_for_updates(self):
        remoteInfo = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().use_beta_channel)
        try:
            if not isinstance(remoteInfo, dict):
                raise remoteInfo  # noqa: TRY301

            new_version = str(remoteInfo["help"]["version"])
            if self.version is None:
                title = "Help book missing"
                text = "You do not seem to have a valid help booklet downloaded, would you like to download it?"
            elif is_remote_version_newer(self.version, new_version):
                title = "Update available"
                text = "A newer version of the help book is available for download, would you like to download it?"
            else:
                RobustLogger().debug("No help booklet updates available, using version %s (latest version: %s)", self.version, new_version)
                return
        except Exception as e:  # noqa: BLE001
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            errMsgBox = QMessageBox(
                QMessageBox.Icon.Information,
                "An unexpected error occurred while parsing the help booklet.",
                error_msg,
                QMessageBox.StandardButton.Ok,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            errMsgBox.setWindowIcon(self.windowIcon())
            errMsgBox.exec()
        else:
            newHelpMsgBox = QMessageBox(
                QMessageBox.Icon.Information,
                title,
                text,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            newHelpMsgBox.setWindowIcon(self.windowIcon())
            newHelpMsgBox.addButton(QMessageBox.StandardButton.Yes)
            newHelpMsgBox.addButton(QMessageBox.StandardButton.No)
            user_response = newHelpMsgBox.exec()
            if user_response == QMessageBox.StandardButton.Yes:

                def task():
                    return self._download_update()

                loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                if loader.exec():
                    self._setup_contents()

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

    def display_file(self, filepath: os.PathLike | str):
        filepath = Path(filepath)
        try:
            text: str = decode_bytes_with_fallbacks(filepath.read_bytes())
            html: str = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"]) if filepath.suffix.lower() == ".md" else text
            self.ui.textDisplay.setHtml(html)
        except OSError as e:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Failed to open help file",
                f"Could not access '{filepath}'.\n{universal_simplify_exception(e)}",
            ).exec()

    def on_contents_clicked(self):
        if not self.ui.contentsTree.selectedItems():
            return
        item: QTreeWidgetItem = self.ui.contentsTree.selectedItems()[0]  # type: ignore[arg-type]
        filename = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if filename:
            help_path = Path("./help").resolve()
            file_path = Path(help_path, filename)
            self.ui.textDisplay.setSearchPaths([str(help_path), str(file_path.parent)])
            self.display_file(file_path)
