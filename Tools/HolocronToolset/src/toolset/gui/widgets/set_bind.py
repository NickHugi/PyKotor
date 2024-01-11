from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from toolset.utils.misc import getStringFromKey

if TYPE_CHECKING:
    from PyQt5.QtGui import QKeyEvent
    from toolset.data.misc import Bind


class SetBindWidget(QWidget):
    def __init__(self, parent: QWidget):
        """Initializes the widget for setting keybinds.

        Args:
        ----
            parent (QWidget): Parent widget

        Processing Logic:
        ----------------
            - Sets up initial keybind set as empty
            - Loads UI from designer file
            - Connects button click signals to methods
            - Populates mouse combo box with mouse button options.
        """
        super().__init__(parent)

        self.keybind: set[int] = set()
        self.recordBind: bool = False

        from toolset.uic.widgets.set_bind import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.setButton.keyPressEvent = self.keyPressed
        self.ui.setButton.keyReleaseEvent = self.keyReleased
        self.ui.setButton.clicked.connect(self.startRecording)
        self.ui.clearButton.clicked.connect(self.clearKeybind)

        self.ui.mouseCombo.setItemData(0, {QtCore.Qt.MouseButton.LeftButton})
        self.ui.mouseCombo.setItemData(1, {QtCore.Qt.MouseButton.MiddleButton})
        self.ui.mouseCombo.setItemData(2, {QtCore.Qt.MouseButton.RightButton})
        self.ui.mouseCombo.setItemData(3, {})
        self.ui.mouseCombo.setItemData(4, None)

    def startRecording(self):
        self.recordBind = True
        self.keybind.clear()
        self.updateKeybindText()
        self.ui.setKeysEdit.setPlaceholderText("enter a key...")

    def clearKeybind(self):
        self.keybind.clear()
        self.ui.setKeysEdit.setPlaceholderText("none")

    def keyPressed(self, a0: QKeyEvent):
        if self.recordBind:
            self.keybind.add(a0.key())
            self.updateKeybindText()

    def keyReleased(self, e: QKeyEvent):
        self.recordBind = False

    def setBind(self, bind: Bind):
        if bind[1] == {QtCore.Qt.MouseButton.LeftButton}:
            self.ui.mouseCombo.setCurrentIndex(0)
        if bind[1] == {QtCore.Qt.MouseButton.MiddleButton}:
            self.ui.mouseCombo.setCurrentIndex(1)
        if bind[1] == {QtCore.Qt.MouseButton.RightButton}:
            self.ui.mouseCombo.setCurrentIndex(2)
        if bind[1] == set():
            self.ui.mouseCombo.setCurrentIndex(3)
        if bind[1] is None:
            self.ui.mouseCombo.setCurrentIndex(4)

        self.keybind = bind[0]
        self.updateKeybindText()

    def bind(self) -> Bind:
        mousebind: set[int] = self.ui.mouseCombo.currentData()
        return self.keybind, mousebind

    def updateKeybindText(self):
        text: str = ""
        for i, key in enumerate(sorted(self.keybind, reverse=True)):
            text += getStringFromKey(key)
            if i != len(self.keybind) - 1:
                text += "+"

        self.ui.setKeysEdit.setText(text.upper())

