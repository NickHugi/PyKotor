from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QDialog

from toolset.config import PROGRAM_VERSION

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class About(QDialog):
    def __init__(self, parent: QWidget):
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

        from toolset.uic.dialogs import about  # pylint: disable=C0415  # noqa: PLC0415
        self.ui = about.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.closeButton.clicked.connect(self.close)

        self.ui.aboutLabel.setText(self.ui.aboutLabel.text().replace("X.X.X", PROGRAM_VERSION))
