from abc import ABC
from typing import List

from PyQt5.QtWidgets import QWidget

from gui.widgets.color_edit import ColorEdit
from gui.widgets.set_bind import SetBindWidget
from pykotor.common.misc import Color


class SettingsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.binds: List = []
        self.colours: List = []
        self.settings = None

    def _registerBind(self, widget: SetBindWidget, bindName: str) -> None:
        widget.setBind(getattr(self.settings, bindName))
        self.binds.append((widget, bindName))

    def _registerColour(self, widget: ColorEdit, colourName: str) -> None:
        widget.setColor(Color.from_rgba_integer(getattr(self.settings, colourName)))
        self.colours.append((widget, colourName))