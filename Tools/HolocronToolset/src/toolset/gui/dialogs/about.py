from PyQt5.QtWidgets import QDialog, QWidget
from toolset.config import PROGRAM_VERSION


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

        from toolset.uic.dialogs import about
        self.ui = about.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.closeButton.clicked.connect(self.close)

        self.ui.aboutLabel.setText(self.ui.aboutLabel.text().replace("X.X.X", ".".join(map(str, PROGRAM_VERSION))))
