from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtWidgets import QDialog

from toolset.config import LOCAL_PROGRAM_INFO

if TYPE_CHECKING:
    from qtpy.QtGui import QShowEvent
    from qtpy.QtWidgets import QWidget


class About(QDialog):
    def __init__(
        self,
        parent: QWidget,
    ):
        """Initializes the About dialog box.

        Args:
        ----
            parent: The parent QWidget.

        Processing Logic:
        ----------------
            - Sets up the UI from the about.py UI file
            - Connects the closeButton clicked signal to close the dialog
            - Replaces the version placeholder in the about text with the actual version.
        """
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint
            & ~QtCore.Qt.WindowType.WindowMinMaxButtonsHint
        )

        from toolset.uic.qtpy.dialogs.about import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.ui.closeButton.clicked.connect(self.close)

        self.ui.aboutLabel.setText(self.ui.aboutLabel.text().replace("X.X.X", LOCAL_PROGRAM_INFO["currentVersion"]))

    def showEvent(self, event: QShowEvent):
        self.setFixedSize(self.size())
