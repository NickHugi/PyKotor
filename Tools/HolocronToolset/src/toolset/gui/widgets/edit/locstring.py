from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import (
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QApplication, QWidget

from pykotor.common.language import LocalizedString
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QMenu

    from toolset.data.installation import HTInstallation


class LocalizedStringLineEdit(QWidget):
    sig_editing_finished: Signal = Signal()

    def __init__(self, parent: QWidget):
        """Initialize a locstring edit widget.

        Args:
        ----
            parent: QWidget - Parent widget

        Processing Logic:
        ----------------
            - Initialize UI from designer file
            - Set initial locstring to invalid
            - Connect edit button to edit_locstring method
            - Connect double click on text to edit_locstring.
        """
        super().__init__(parent)

        from toolset.uic.qtpy.widgets.locstring_edit import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self._locstring: LocalizedString = LocalizedString.from_invalid()

        self.ui.editButton.clicked.connect(self.edit_locstring)
        self.ui.locstringText.mouseDoubleClickEvent = lambda a0: self.edit_locstring()  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        from toolset.gui.common.localization import translate as tr
        self.setToolTip(tr("Double-click to edit this Localized String.<br><br><i>Right-click for more options</i>"))

    def set_installation(self, installation: HTInstallation):
        self._installation: HTInstallation = installation

    def on_context_menu(self, pos: QPoint):
        menu: QMenu = self.ui.locstringText.createStandardContextMenu()
        from toolset.gui.common.localization import translate as tr
        menu.addAction(tr("Edit with TLK")).triggered.connect(self.edit_locstring)
        menu.addAction(tr("Copy")).triggered.connect(self.copy_text)
        menu.exec(self.ui.locstringText.mapToGlobal(pos))

    def copy_text(self):
        """Copies the current text to the clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.ui.locstringText.text())

    def set_locstring(self, locstring: LocalizedString):
        """Sets the localized string for a UI element.

        Args:
        ----
            locstring: {Localized string object to set}

        Processing Logic:
        ----------------
            - Sets the internal locstring property to the passed in value
            - Checks if the stringref is -1
            - If so, sets the text directly from the string and uses white background
            - If not, looks up the string from the talktable and uses a yellow background
        """
        self._locstring = locstring
        if locstring.stringref == -1:
            text = str(locstring)
            self.ui.locstringText.setText(text if text != "-1" else "")
            self.ui.locstringText.setStyleSheet(f"{self.ui.locstringText.styleSheet()} QLineEdit {{background-color: white;}}")
        else:
            self.ui.locstringText.setText(self._installation.talktable().string(locstring.stringref))
            self.ui.locstringText.setStyleSheet(f"{self.ui.locstringText.styleSheet()} QLineEdit {{background-color: #fffded;}}")

    def edit_locstring(self):
        dialog = LocalizedStringDialog(self, self._installation, self._locstring)
        if dialog.exec():
            self.set_locstring(dialog.locstring)
            self.sig_editing_finished.emit()

    def locstring(self) -> LocalizedString:
        return self._locstring

if __name__ == "__main__":
    import os
    import sys

    from pathlib import Path

    from qtpy.QtWidgets import QApplication, QMainWindow

    from toolset.data.installation import HTInstallation

    app = QApplication(sys.argv)
    main_window = QMainWindow()

    # Create a mock installation for testing
    k_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
    if k_path is None:
        k_path = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")
        if k_path is None:
            raise RuntimeError("KOTOR installation not found")

    locstring_edit = LocalizedStringLineEdit(main_window)
    locstring_edit.set_installation(HTInstallation(Path(k_path), "KOTOR"))

    # Set a test localized string
    test_locstring = LocalizedString(0)
    locstring_edit.set_locstring(test_locstring)

    main_window.setCentralWidget(locstring_edit)
    main_window.show()

    sys.exit(app.exec())
