from __future__ import annotations

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree as ElemTree

import qtpy

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring

    ElemTree.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended due to security concerns.")

import zipfile

from typing import TYPE_CHECKING, Any, Callable

import markdown

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem

from pykotor.common.stream import BinaryReader
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.config import getRemoteToolsetUpdateInfo, remoteVersionNewer
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception
from utility.logger_util import RobustRootLogger
from utility.system.os_helper import is_frozen
from utility.system.path import Path
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

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.windows import help as toolset_help  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.windows import help as toolset_help  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.windows import help as toolset_help  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.windows import help as toolset_help  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = toolset_help.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()
        self._setupContents()
        self.startingPage: str | None = startingPage

    def showEvent(self, a0: QShowEvent):
        super().showEvent(a0)
        self.ui.textDisplay.setSearchPaths(["./help"])

        if self.ENABLE_UPDATES:
            self.checkForUpdates()

        if self.startingPage is None:
            return
        self.displayFile(self.startingPage)

    def _setupSignals(self):
        self.ui.contentsTree.clicked.connect(self.onContentsClicked)

    def _setupContents(self):
        self.ui.contentsTree.clear()

        try:
            tree = ElemTree.parse("./help/contents.xml")  # noqa: S314 incorrect warning.
            root = tree.getroot()

            self.version = str(root.get("version", "0.0"))
            self._setupContentsRecXML(None, root)

            # Old JSON code:
            # text = BinaryReader.load_file("./help/contents.xml")
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)
        except Exception:
            RobustRootLogger().debug("Suppressed error in HelpWindow._setupContents", exc_info=True)

    def _setupContentsRecJSON(self, parent: QTreeWidgetItem | None, data: dict[str, Any]):
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
            self._setupContentsRecJSON(item, structure[title])

    def _setupContentsRecXML(self, parent: QTreeWidgetItem | None, element: ElemTree.Element):
        addItem: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.ui.contentsTree.addTopLevelItem
            if parent is None
            else parent.addChild
        )

        for child in element:
            item = QTreeWidgetItem([child.get("name", "")])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, child.get("file"))
            addItem(item)
            self._setupContentsRecXML(item, child)

    def checkForUpdates(self):
        remoteInfo = getRemoteToolsetUpdateInfo(useBetaChannel=GlobalSettings().useBetaChannel)
        try:
            if not isinstance(remoteInfo, dict):
                raise remoteInfo  # noqa: TRY301

            new_version = str(remoteInfo["help"]["version"])
            if self.version is None:
                title = "Help book missing"
                text = "You do not seem to have a valid help booklet downloaded, would you like to download it?"
            elif remoteVersionNewer(self.version, new_version):
                title = "Update available"
                text = "A newer version of the help book is available for download, would you like to download it?"
            else:
                RobustRootLogger().debug("No help booklet updates available, using version %s (latest version: %s)", self.version, new_version)
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
            errMsgBox.exec_()
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
            user_response = newHelpMsgBox.exec_()
            if user_response == QMessageBox.StandardButton.Yes:

                def task():
                    return self._downloadUpdate()

                loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                if loader.exec_():
                    self._setupContents()

    def _downloadUpdate(self):
        help_path = Path("./help").resolve()
        help_path.mkdir(parents=True, exist_ok=True)
        help_zip_path = Path("./help.zip").resolve()
        download_github_file("NickHugi/PyKotor", help_zip_path, "/Tools/HolocronToolset/downloads/help.zip")

        # Extract the ZIP file
        with zipfile.ZipFile(help_zip_path) as zip_file:
            RobustRootLogger().info("Extracting downloaded content to %s", help_path)
            zip_file.extractall(help_path)

        if is_frozen():
            help_zip_path.unlink()

    def displayFile(self, filepath: os.PathLike | str):
        filepath = Path.pathify(filepath)
        try:
            text: str = decode_bytes_with_fallbacks(BinaryReader.load_file(filepath))
            html: str = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"]) if filepath.suffix.lower() == ".md" else text
            self.ui.textDisplay.setHtml(html)
        except OSError as e:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Failed to open help file",
                f"Could not access '{filepath}'.\n{universal_simplify_exception(e)}",
            ).exec_()

    def onContentsClicked(self):
        if not self.ui.contentsTree.selectedItems():
            return
        item: QTreeWidgetItem = self.ui.contentsTree.selectedItems()[0]  # type: ignore[arg-type]
        filename = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if filename:
            help_path = Path("./help").resolve()
            file_path = Path(help_path, filename)
            self.ui.textDisplay.setSearchPaths([str(help_path), str(file_path.parent)])
            self.displayFile(file_path)
