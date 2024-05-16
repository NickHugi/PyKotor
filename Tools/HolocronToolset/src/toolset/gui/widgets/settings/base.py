from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QWidget

from pykotor.common.misc import Color
from utility.logger_util import RobustRootLogger
from utility.misc import is_int

if TYPE_CHECKING:
    from toolset.data.misc import Bind
    from toolset.gui.widgets.edit.color import ColorEdit
    from toolset.gui.widgets.set_bind import SetBindWidget


class SettingsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.binds: list = []
        self.colours: list = []
        self.settings = None

    def _registerBind(self, widget: SetBindWidget, bindName: str):
        bind: Bind = getattr(self.settings, bindName)
        if not isinstance(bind, tuple) or (bind[0] is not None and not isinstance(bind[0], set)) or (bind[1] is not None and not isinstance(bind[1], set)):
            RobustRootLogger.error(f"invalid setting bind: '{bindName}', expected a Bind type (tuple with two sets of binds) but got {bind!r} (tuple[{bind[0].__class__.__name__}, {bind[1].__class__.__name__}])")
            bind = self._reset_and_get_default(bindName)
        widget.setBind(bind)
        self.binds.append((widget, bindName))

    def _registerColour(self, widget: ColorEdit, colourName: str):
        color_value = getattr(self.settings, colourName)
        if not is_int(color_value):
            RobustRootLogger.error(f"invalid color setting: '{colourName}', expected a rgba color integer, but got {color_value!r} (type {color_value.__class__.__name__})")
            color_value = self._reset_and_get_default(colourName)
        widget.setColor(Color.from_rgba_integer(color_value))
        self.colours.append((widget, colourName))

    def _reset_and_get_default(self, settingName: str):
        self.settings.settings.remove(settingName)
        result = getattr(self.settings, settingName)
        RobustRootLogger.warning(f"Due to last error, will use default value '{result!r}'" )
        return result
