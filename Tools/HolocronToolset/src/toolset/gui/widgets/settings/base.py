from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget

from pykotor.common.misc import Color

if TYPE_CHECKING:
    from toolset.gui.widgets.edit.color import ColorEdit
    from toolset.gui.widgets.set_bind import SetBindWidget


class SettingsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.binds: list = []
        self.colours: list = []
        self.settings = None

    def _registerBind(self, widget: SetBindWidget, bindName: str):
        widget.setBind(getattr(self.settings, bindName))
        self.binds.append((widget, bindName))

    def _registerColour(self, widget: ColorEdit, colourName: str):
        widget.setColor(Color.from_rgba_integer(getattr(self.settings, colourName)))
        self.colours.append((widget, colourName))
