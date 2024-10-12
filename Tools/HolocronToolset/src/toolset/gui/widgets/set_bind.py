from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtWidgets import QWidget

from toolset.utils.misc import MODIFIER_KEY_NAMES, QtMouse, getQtMouseButton, get_qt_key_string_localized

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
        self.record_bind: bool = False

        from toolset.uic.qtpy.widgets.set_bind import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.setButton.keyPressEvent = self.key_pressed
        self.ui.setButton.keyReleaseEvent = self.key_released
        self.ui.setButton.clicked.connect(self.startRecording)
        self.ui.clearButton.clicked.connect(self.clearKeybind)

        self.ui.mouseCombo.setItemData(0, {QtMouse.LeftButton})
        self.ui.mouseCombo.setItemData(1, {QtMouse.MiddleButton})
        self.ui.mouseCombo.setItemData(2, {QtMouse.RightButton})
        self.ui.mouseCombo.setItemData(3, set())  # Any
        self.ui.mouseCombo.setItemData(4, None)   # None

    def startRecording(self):
        self.record_bind = True
        self.keybind.clear()
        self.update_keybind_text()
        self.ui.setKeysEdit.setPlaceholderText("Enter a key...")

    def clearKeybind(self):
        self.keybind.clear()
        self.ui.setKeysEdit.setPlaceholderText("none")
        self.update_keybind_text()

    def key_pressed(self, a0: QKeyEvent):
        if self.record_bind:
            self.keybind.add(a0.key())
            assert isinstance(self.keybind, set), f"{self.keybind!r} <{self.keybind}> ({self.keybind.__class__.__name__}) is not a set"
            self.update_keybind_text()

    def key_released(self, e: QKeyEvent):
        self.record_bind = False
        RobustLogger().info(f"Set keybind to {self.keybind}")

    def set_mouse_and_key_binds(self, bind: Bind):
        # these asserts will be removed automatically with -O PYTHONOPTIMIZE flag, performance isn't affected there.
        assert isinstance(bind, tuple), f"{bind} ({bind.__class__.__name__}) is not a tuple"
        assert len(bind) == 2, f"{len(bind)} != 2"  # noqa: PLR2004
        assert isinstance(bind[0], set), f"{bind[0]!r} <{bind[0]}> ({bind[0].__class__.__name__}) is not a set"
        assert isinstance(bind[1], (set, type(None))), f"{bind[1]!r} <{bind[1]}> ({bind[1].__class__.__name__}) is not a set"

        # Handle Qt6
        mouse_bind = next(iter(bind[1])) if bind[1] else (None if bind[1] is None else set())
        if mouse_bind is not None:
            try:
                mouse_bind = getQtMouseButton(mouse_bind)
            except Exception:
                mouse_bind = None

        if mouse_bind is None:  # none
            self.ui.mouseCombo.setCurrentIndex(4)
        elif not mouse_bind:  # any
            self.ui.mouseCombo.setCurrentIndex(3)
        elif mouse_bind == QtMouse.LeftButton:
            self.ui.mouseCombo.setCurrentIndex(0)
        elif mouse_bind == QtMouse.MiddleButton:
            self.ui.mouseCombo.setCurrentIndex(1)
        elif mouse_bind == QtMouse.RightButton:
            self.ui.mouseCombo.setCurrentIndex(2)
        else:
            raise ValueError(f"{mouse_bind!r} <{mouse_bind}> ({mouse_bind.__class__.__name__}) is not a valid mousebind")

        self.keybind = bind[0]
        self.update_keybind_text()

    def get_mouse_and_key_binds(self) -> Bind:
        mousebind: set[int] = self.ui.mouseCombo.currentData()
        assert isinstance(mousebind, (set, type(None))), f"{mousebind!r} <{mousebind}> ({mousebind.__class__.__name__}) is not a mousebind set"
        assert isinstance(self.keybind, set), f"{self.keybind!r} <{self.keybind}> ({self.keybind.__class__.__name__}) is not a keybind set"
        return self.keybind, mousebind

    def update_keybind_text(self):
        modifiers = [key for key in self.keybind if key in MODIFIER_KEY_NAMES]
        other_keys = [key for key in self.keybind if key not in MODIFIER_KEY_NAMES]
        sorted_keys = modifiers + other_keys
        text = "+".join(get_qt_key_string_localized(key) for key in sorted_keys)
        self.ui.setKeysEdit.setText(text.upper())
