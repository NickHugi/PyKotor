from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget

from toolset.utils.misc import MODIFIER_KEY_NAMES, get_qt_key_string_localized

if TYPE_CHECKING:
    from qtpy.QtGui import QKeyEvent

    from toolset.data.misc import Bind


class SetBindWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.keybind: set[Qt.Key] = set()
        self.record_bind: bool = False

        from toolset.uic.qtpy.widgets.set_bind import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.setButton.keyPressEvent = self.keyPressEvent  # type: ignore[method-assign]
        self.ui.setButton.keyReleaseEvent = self.keyReleaseEvent  # type: ignore[method-assign]
        self.ui.setButton.clicked.connect(self.start_recording)
        self.ui.clearButton.clicked.connect(self.clear_keybind)

        self.ui.mouseCombo.setItemData(0, {Qt.MouseButton.LeftButton})
        self.ui.mouseCombo.setItemData(1, {Qt.MouseButton.MiddleButton})
        self.ui.mouseCombo.setItemData(2, {Qt.MouseButton.RightButton})
        self.ui.mouseCombo.setItemData(3, set())  # Any
        self.ui.mouseCombo.setItemData(4, None)   # None

    def start_recording(self):
        self.record_bind = True
        self.keybind.clear()
        self.update_keybind_text()
        from toolset.gui.common.localization import translate as tr
        self.ui.setKeysEdit.setPlaceholderText(tr("Enter a key..."))

    def clear_keybind(self):
        self.keybind.clear()
        from toolset.gui.common.localization import translate as tr
        self.ui.setKeysEdit.setPlaceholderText(tr("none"))
        self.update_keybind_text()

    def keyPressEvent(self, a0: QKeyEvent):
        if self.record_bind:
            self.keybind.add(Qt.Key(a0.key()))
            assert isinstance(self.keybind, set), f"{self.keybind!r} <{self.keybind}> ({self.keybind.__class__.__name__}) is not a set"
            self.update_keybind_text()
        super().keyPressEvent(a0)
    def keyReleaseEvent(self, e: QKeyEvent):
        self.record_bind = False
        RobustLogger().info(f"Set keybind to {self.keybind}")
        super().keyReleaseEvent(e)

    def set_mouse_and_key_binds(self, bind: Bind):
        # these asserts will be removed automatically with -O PYTHONOPTIMIZE flag, performance isn't affected there.
        assert isinstance(bind, tuple), f"{bind} ({bind.__class__.__name__}) is not a tuple"
        assert len(bind) == 2, f"{len(bind)} != 2"  # noqa: PLR2004
        assert isinstance(bind[0], set), f"{bind[0]!r} <{bind[0]}> ({bind[0].__class__.__name__}) is not a set"
        assert isinstance(bind[1], (set, type(None))), f"{bind[1]!r} <{bind[1]}> ({bind[1].__class__.__name__}) is not a set"

        mouse_bind: Qt.MouseButton | set | None = next(iter(bind[1])) if bind[1] else (None if bind[1] is None else set())
        if mouse_bind is None:  # None
            self.ui.mouseCombo.setCurrentIndex(4)
        elif not mouse_bind:  # Any (empty set)
            self.ui.mouseCombo.setCurrentIndex(3)
        elif mouse_bind == Qt.MouseButton.LeftButton:
            self.ui.mouseCombo.setCurrentIndex(0)
        elif mouse_bind == Qt.MouseButton.MiddleButton:
            self.ui.mouseCombo.setCurrentIndex(1)
        elif mouse_bind == Qt.MouseButton.RightButton:
            self.ui.mouseCombo.setCurrentIndex(2)
        else:
            raise ValueError(f"{mouse_bind!r} <{mouse_bind}> ({mouse_bind.__class__.__name__}) is not a valid mousebind")

        self.keybind = bind[0]
        self.update_keybind_text()

    def get_mouse_and_key_binds(self) -> Bind:
        mousebind: set[Qt.MouseButton] = self.ui.mouseCombo.currentData()
        assert isinstance(mousebind, (set, type(None))), f"{mousebind!r} <{mousebind}> ({mousebind.__class__.__name__}) is not a mousebind set"
        assert isinstance(self.keybind, set), f"{self.keybind!r} <{self.keybind}> ({self.keybind.__class__.__name__}) is not a keybind set"
        return self.keybind, mousebind

    def update_keybind_text(self):
        modifiers: list[Qt.Key] = [key for key in self.keybind if key in MODIFIER_KEY_NAMES]
        other_keys: list[Qt.Key] = [key for key in self.keybind if key not in MODIFIER_KEY_NAMES]
        sorted_keys: list[Qt.Key] = modifiers + other_keys
        text: str = "+".join(get_qt_key_string_localized(key) for key in sorted_keys)
        self.ui.setKeysEdit.setText(text.upper())
