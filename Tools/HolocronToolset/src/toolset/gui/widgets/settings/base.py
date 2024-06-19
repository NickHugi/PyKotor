from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qtpy.QtWidgets import QAbstractSpinBox, QComboBox, QDoubleSpinBox, QGroupBox, QSlider, QSpinBox, QWidget

from pykotor.common.misc import Color
from toolset.gui.common.filters import HoverEventFilter, NoScrollEventFilter
from utility.logger_util import RobustRootLogger
from utility.misc import is_int

if TYPE_CHECKING:
    from qtpy.QtCore import QObject

    from toolset.data.misc import Bind
    from toolset.data.settings import Settings
    from toolset.gui.widgets.edit.color import ColorEdit
    from toolset.gui.widgets.set_bind import SetBindWidget


class SettingsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.binds: dict[str, SetBindWidget] = {}
        self.colours: dict[str, ColorEdit] = {}
        self.settings: Settings

        # Install the event filter on all child widgets
        self.noScrollEventFilter: NoScrollEventFilter = NoScrollEventFilter(self)
        self.hoverEventFilter: HoverEventFilter = HoverEventFilter(self)
        self.installEventFilters(self, self.noScrollEventFilter)
        #self.installEventFilters(self, self.hoverEventFilter, include_types=[QWidget])

    def installEventFilters(
        self,
        parent_widget: QWidget,
        event_filter: QObject,
        include_types: list[type[QWidget]] | None = None
    ) -> None:
        """Recursively install event filters on all child widgets."""
        if include_types is None:
            include_types = [QComboBox, QSlider, QSpinBox, QGroupBox, QAbstractSpinBox, QDoubleSpinBox]

        for widget in parent_widget.findChildren(QWidget):
            if not widget.objectName():
                widget.setObjectName(widget.__class__.__name__)
            if isinstance(widget, tuple(include_types)):
                #RobustRootLogger.debug(f"Installing event filter on: {widget.objectName()} (type: {widget.__class__.__name__})")
                widget.installEventFilter(event_filter)
            #else:
            #    RobustRootLogger.debug(f"Skipping NoScrollEventFilter installation on '{widget.objectName()}' due to instance check {widget.__class__.__name__}.")
            self.installEventFilters(widget, event_filter, include_types)

    def validateBind(self, bindName: str, bind: Bind) -> Bind:
        if not isinstance(bind, tuple) or (bind[0] is not None and not isinstance(bind[0], set)) or (bind[1] is not None and not isinstance(bind[1], set)):
            RobustRootLogger.error(f"Invalid setting bind: '{bindName}', expected a Bind type (tuple with two sets of binds) but got {bind!r} (tuple[{bind[0].__class__.__name__}, {bind[1].__class__.__name__}])")
            bind = self._reset_and_get_default(bindName)
        return bind

    def validateColour(self, colourName: str, color_value: int) -> int:
        if not is_int(color_value):
            RobustRootLogger.error(f"Invalid color setting: '{colourName}', expected a RGBA color integer, but got {color_value!r} (type {color_value.__class__.__name__})")
            color_value = self._reset_and_get_default(colourName)
        return color_value

    def save(self):
        for bindName, bind_widget in self.binds.items():
            bind = self.validateBind(bindName, bind_widget.getMouseAndKeyBinds())
            setattr(self.settings, bindName, bind)
        for colourName, color_widget in self.colours.items():
            color_value = color_widget.color().rgba_integer()
            setattr(self.settings, colourName, color_value)

    def _registerBind(self, widget: SetBindWidget, bindName: str):
        bind = self.validateBind(bindName, getattr(self.settings, bindName))
        widget.setMouseAndKeyBinds(bind)
        self.binds[bindName] = widget

    def _registerColour(self, widget: ColorEdit, colourName: str):
        color_value = self.validateColour(colourName, getattr(self.settings, colourName))
        widget.setColor(Color.from_rgba_integer(color_value))
        self.colours[colourName] = widget

    def _reset_and_get_default(self, settingName: str) -> Any:
        self.settings.reset_setting(settingName)
        result = self.settings.get_default(settingName)
        RobustRootLogger.warning(f"Due to last error, will use default value '{result!r}'" )
        return result
