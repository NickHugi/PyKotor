from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import markdown

from qtpy import QtCore
from qtpy.QtWidgets import QMainWindow, QMessageBox

from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.gui.windows.help_content import HelpContent
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QShowEvent
    from qtpy.QtWidgets import QTreeWidgetItem, QWidget


class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: QWidget | None, startingPage: str | None = None):
        super().__init__(parent)

        from toolset.gui.windows.help_updater import HelpUpdater
        from toolset.uic.qtpy.windows import help as toolset_help

        self.ui = toolset_help.Ui_MainWindow()
        self.ui.setupUi(self)

        self.help_content: HelpContent = HelpContent(self)
        self.help_updater: HelpUpdater = HelpUpdater(self)

        self._setup_signals()
        self.help_content.setup_contents()
        self.starting_page: str | None = startingPage
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def showEvent(self, event: QShowEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().showEvent(event)
        self.ui.textDisplay.setSearchPaths(["./help"])

        if self.ENABLE_UPDATES:
            self.help_updater.check_for_updates()

        if self.starting_page is None:
            return
        self.display_file(self.starting_page)

    def _setup_signals(self):
        self.ui.contentsTree.clicked.connect(self.on_contents_clicked)

    def display_file(self, filepath: os.PathLike | str):
        filepath = Path(filepath)
        try:
            text: str = decode_bytes_with_fallbacks(filepath.read_bytes())
            html: str = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"]) if filepath.suffix.lower() == ".md" else text
            self.ui.textDisplay.setHtml(html)
        except OSError as e:
            from toolset.gui.common.localization import translate as tr, trf
            QMessageBox(
                QMessageBox.Icon.Critical,
                tr("Failed to open help file"),
                trf("Could not access '{filepath}'.\n{error}", filepath=str(filepath), error=str(universal_simplify_exception(e))),
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
