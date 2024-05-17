from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QEvent, QObject
from qtpy.QtWidgets import QAbstractSpinBox, QComboBox, QDoubleSpinBox, QGroupBox, QSlider, QSpinBox, QWidget

from pykotor.common.misc import Color
from utility.logger_util import RobustRootLogger
from utility.misc import is_int
from utility.system.path import PurePath

if TYPE_CHECKING:
    from toolset.data.misc import Bind
    from toolset.data.settings import Settings
    from toolset.gui.widgets.edit.color import ColorEdit
    from toolset.gui.widgets.set_bind import SetBindWidget


class NoScrollEventFilter(QObject):
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel:
            if isinstance(obj, QWidget):
                RobustRootLogger.debug(f"Blocking scroll on {obj.__class__.__name__} ({obj.objectName()})")
            else:
                RobustRootLogger.debug(f"Blocking scroll on unknown: {obj} (type: {obj.__class__.__name__}) ({obj.objectName()})")
            return True  # Block the event
        return super().eventFilter(obj, event)


class SettingsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.binds: dict[str, SetBindWidget] = {}
        self.colours: dict[str, ColorEdit] = {}
        self.settings: Settings

        # Install the event filter on all child widgets
        self.noScrollEventFilter: NoScrollEventFilter = NoScrollEventFilter()
        self.installEventFilters(self, self.noScrollEventFilter)

    def installEventFilters(
        self,
        parent_widget: QWidget,
        event_filter: QObject,
        path: PurePath | None = None,
        include_types: list[type[QWidget]] | None = None
    ) -> None:
        """Recursively install event filters on all child widgets."""
        if path is None:
            path = PurePath(self.__class__.__name__)
        if include_types is None:
            include_types = [QComboBox, QSlider, QSpinBox, QGroupBox, QAbstractSpinBox, QDoubleSpinBox]

        for widget in parent_widget.findChildren(QWidget):
            widget_path = path / widget.objectName()
            if not widget.objectName():
                widget.setObjectName(widget.__class__.__name__)
                widget_path = path / widget.objectName()
            if isinstance(widget, tuple(include_types)):
                #RobustRootLogger.debug(f"Installing event filter on: {widget_path} (type: {widget.__class__.__name__})")
                widget.installEventFilter(event_filter)
            #else:
            #    RobustRootLogger.debug(f"Skipping NoScrollEventFilter installation on '{widget_path}' due to instance check {widget.__class__.__name__}.")
            self.installEventFilters(widget, event_filter, widget_path, include_types)

    def save(self):
        for bindName, bind_widget in self.binds.items():
            bind = bind_widget.bind()
            if not isinstance(bind, tuple) or (bind[0] is not None and not isinstance(bind[0], set)) or (bind[1] is not None and not isinstance(bind[1], set)):
                RobustRootLogger.error(f"invalid setting bind: '{bindName}', expected a Bind type (tuple with two sets of binds) but got {bind!r} (tuple[{bind[0].__class__.__name__}, {bind[1].__class__.__name__}])")
                bind = self._reset_and_get_default(bindName)
            setattr(self.settings, bindName, bind)
        for colourName, color_widget in self.colours.items():
            color_value = color_widget.color().rgba_integer()
            if not is_int(color_value):
                RobustRootLogger.error(f"invalid color setting: '{colourName}', expected a rgba color integer, but got {color_value!r} (type {color_value.__class__.__name__})")
                color_value = self._reset_and_get_default(colourName)
            setattr(self.settings, colourName, color_value)

    def _registerBind(self, widget: SetBindWidget, bindName: str):
        bind: Bind = getattr(self.settings, bindName)
        if not isinstance(bind, tuple) or (bind[0] is not None and not isinstance(bind[0], set)) or (bind[1] is not None and not isinstance(bind[1], set)):
            RobustRootLogger.error(f"invalid setting bind: '{bindName}', expected a Bind type (tuple with two sets of binds) but got {bind!r} (tuple[{bind[0].__class__.__name__}, {bind[1].__class__.__name__}])")
            bind = self._reset_and_get_default(bindName)
        widget.setBind(bind)
        self.binds[bindName] = widget

    def _registerColour(self, widget: ColorEdit, colourName: str):
        color_value = getattr(self.settings, colourName)
        if not is_int(color_value):
            RobustRootLogger.error(f"invalid color setting: '{colourName}', expected a rgba color integer, but got {color_value!r} (type {color_value.__class__.__name__})")
            color_value = self._reset_and_get_default(colourName)
        widget.setColor(Color.from_rgba_integer(color_value))
        self.colours[colourName] = widget

    def _reset_and_get_default(self, settingName: str):
        self.settings.settings.remove(settingName)
        result = getattr(self.settings, settingName)
        RobustRootLogger.warning(f"Due to last error, will use default value '{result!r}'" )
        return result
