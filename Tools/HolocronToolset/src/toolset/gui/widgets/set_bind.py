from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtWidgets import QWidget

from toolset.utils.misc import MODIFIER_KEY_NAMES, QtMouse, getQtKeyStringLocalized, getQtMouseButton
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    from qtpy.QtGui import QKeyEvent

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

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.set_bind import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.set_bind import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.set_bind import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.set_bind import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.setButton.keyPressEvent = self.keyPressed
        self.ui.setButton.keyReleaseEvent = self.keyReleased
        self.ui.setButton.clicked.connect(self.startRecording)
        self.ui.clearButton.clicked.connect(self.clearKeybind)

        self.ui.mouseCombo.setItemData(0, {QtMouse.LeftButton})
        self.ui.mouseCombo.setItemData(1, {QtMouse.MiddleButton})
        self.ui.mouseCombo.setItemData(2, {QtMouse.RightButton})
        self.ui.mouseCombo.setItemData(3, set())  # Any
        self.ui.mouseCombo.setItemData(4, None)   # None

    def startRecording(self):
        self.recordBind = True
        self.keybind.clear()
        self.updateKeybindText()
        self.ui.setKeysEdit.setPlaceholderText("Enter a key...")

    def clearKeybind(self):
        self.keybind.clear()
        self.ui.setKeysEdit.setPlaceholderText("none")
        self.updateKeybindText()

    def keyPressed(self, a0: QKeyEvent):
        if self.recordBind:
            self.keybind.add(a0.key())
            assert isinstance(self.keybind, set), f"{self.keybind!r} <{self.keybind}> ({self.keybind.__class__.__name__}) is not a set"
            self.updateKeybindText()

    def keyReleased(self, e: QKeyEvent):
        self.recordBind = False
        RobustRootLogger.info(f"Set keybind to {self.keybind}")

    def setMouseAndKeyBinds(self, bind: Bind):
        # these asserts will be removed automatically with -O PYTHONOPTIMIZE flag, performance isn't affected there.
        assert isinstance(bind, tuple), f"{bind} ({bind.__class__.__name__}) is not a tuple"
        assert len(bind) == 2, f"{len(bind)} != 2"
        assert isinstance(bind[0], set), f"{bind[0]!r} <{bind[0]}> ({bind[0].__class__.__name__}) is not a set"
        assert isinstance(bind[1], (set, type(None))), f"{bind[1]!r} <{bind[1]}> ({bind[1].__class__.__name__}) is not a set"

        # Handle Qt6
        mouseBind = next(iter(bind[1])) if bind[1] else (None if bind[1] is None else set())
        if mouseBind is not None:
            try:
                mouseBind = getQtMouseButton(mouseBind)
            except Exception:
                mouseBind = None

        if mouseBind is None:  # none
            self.ui.mouseCombo.setCurrentIndex(4)
        elif not mouseBind:  # any
            self.ui.mouseCombo.setCurrentIndex(3)
        elif mouseBind == QtMouse.LeftButton:
            self.ui.mouseCombo.setCurrentIndex(0)
        elif mouseBind == QtMouse.MiddleButton:
            self.ui.mouseCombo.setCurrentIndex(1)
        elif mouseBind == QtMouse.RightButton:
            self.ui.mouseCombo.setCurrentIndex(2)
        else:
            raise ValueError(f"{mouseBind!r} <{mouseBind}> ({mouseBind.__class__.__name__}) is not a valid mousebind")

        self.keybind = bind[0]
        self.updateKeybindText()

    def getMouseAndKeyBinds(self) -> Bind:
        mousebind: set[int] = self.ui.mouseCombo.currentData()
        assert isinstance(mousebind, (set, type(None))), f"{mousebind!r} <{mousebind}> ({mousebind.__class__.__name__}) is not a mousebind set"
        assert isinstance(self.keybind, set), f"{self.keybind!r} <{self.keybind}> ({self.keybind.__class__.__name__}) is not a keybind set"
        return self.keybind, mousebind

    def updateKeybindText(self):
        # Separate modifier keys and other keys
        modifiers = [key for key in self.keybind if key in MODIFIER_KEY_NAMES]
        other_keys = [key for key in self.keybind if key not in MODIFIER_KEY_NAMES]

        # Sort keys: modifiers first, then other keys
        sorted_keys = modifiers + other_keys

        # Create the keybind text
        text = "+".join(getQtKeyStringLocalized(key) for key in sorted_keys)

        # Update the UI element with the keybind text
        self.ui.setKeysEdit.setText(text.upper())

        self.ui.setKeysEdit.setText(text.upper())
