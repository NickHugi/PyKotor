from __future__ import annotations

from typing import TYPE_CHECKING, Any

import qtpy

from qtpy.QtCore import (
    QFile,
    QTextStream,
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QMessageBox,
)

from toolset.gui.widgets.settings.misc import GlobalSettings
from ui import stylesheet_resources  # noqa: F401  # pylint: disable=unused-import

if qtpy.API_NAME == "PySide2":  # pylint: disable=ungrouped-imports
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyside2,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
elif qtpy.API_NAME == "PySide6":
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyside6,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
elif qtpy.API_NAME == "PyQt5":
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyqt5,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
elif qtpy.API_NAME == "PyQt6":
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyqt6,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
else:
    raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

if TYPE_CHECKING:
    from qtpy.QtCore import (
        QCoreApplication,
        Qt,  # pyright: ignore[reportPrivateImportUsage]
    )
    from qtpy.QtWidgets import QStyle



class ThemeManager:
    """Manages the application's theme."""

    def __init__(self, original_style: str):
        """Initialize the theme manager."""
        self.original_style = original_style

    @Slot(QApplication, str, object, object, bool)
    def apply_style(
        self,
        app: QApplication,
        sheet: str = "",
        style: str | None = None,
        palette: QPalette | None = None,
        repaint_all_widgets: bool = True,
    ):
        app.setStyleSheet(sheet)
        # self.setWindowFlags(selfFlags() & ~Qt.WindowType.FramelessWindowHint)
        if style is None or style == self.original_style:
            app.setStyle(self.original_style)
        else:
            app.setStyle(style)
            if palette:
                ...
                # still can't get the custom title bar working, leave this disabled until we do.
                # self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        app_style: QStyle | None = app.style()
        if palette is None and app_style is not None:
            palette = app_style.standardPalette()
        if palette is not None:
            app.setPalette(palette)
        if repaint_all_widgets:
            for widget in app.allWidgets():
                if palette is not None:
                    widget.setPalette(palette)
                widget.repaint()

    @Slot()
    def change_theme(self, theme: QAction | str | None = None):
        """Changes the theme of the application.

        Args:
            theme (QAction | str | None): The theme to change to.
        """
        app: QCoreApplication | None = QApplication.instance()
        assert isinstance(app, QApplication), "No Qt Application found or not a QApplication instance."

        print("<SDM> [toggle_stylesheet scope] GlobalSettings().selectedTheme: ", GlobalSettings().selectedTheme)
        GlobalSettings().selectedTheme = theme.text() if isinstance(theme, QAction) else theme
        self.apply_style(app)

        app_style: QStyle | None = app.style()
        assert app_style is not None
        standard_palette: QPalette = app_style.standardPalette()

        palette: QPalette | None = None
        sheet: str = ""
        style: str = self.original_style
        if GlobalSettings().selectedTheme == "Native":
            style = self.original_style
            palette = standard_palette
        elif GlobalSettings().selectedTheme == "Fusion (Light)":
            style = "Fusion"
            self.apply_style(app, sheet, "Fusion")
        elif GlobalSettings().selectedTheme == "Fusion (Dark)":
            style = "Fusion"
            palette = self.create_palette(
                QColor(53, 53, 53),
                QColor(35, 35, 35),
                QColor(240, 240, 240),
                QColor(25, 25, 25),
                self.adjust_color(QColor("orange"), saturation=80, hue_shift=-10),
                QColor(255, 69, 0),
            )
        elif GlobalSettings().selectedTheme == "QDarkStyle":
            try:
                import qdarkstyle  # pyright: ignore[reportMissingTypeStubs]
            except ImportError:
                QMessageBox.critical(self, "Theme not found", "QDarkStyle is not installed in this environment.")
            else:
                app.setStyle(self.original_style)
                app.setPalette(standard_palette)
                app.setStyleSheet(qdarkstyle.load_stylesheet())  # straight from the docs. Not sure why they don't require us to explicitly set a style/palette.
            return
        elif GlobalSettings().selectedTheme == "AMOLED":
            sheet = self._get_file_stylesheet(":/themes/other/AMOLED.qss", app)
            palette = self.create_palette("#000000", "#141414", "#e67e22", "#f39c12", "#808086", "#FFFFFF")
        elif GlobalSettings().selectedTheme == "Aqua":
            style = self.original_style
            sheet = self._get_file_stylesheet(":/themes/other/aqua.qss", app)
        elif GlobalSettings().selectedTheme == "ConsoleStyle":
            style = "Fusion"
            sheet = self._get_file_stylesheet(":/themes/other/ConsoleStyle.qss", app)
            palette = self.create_palette("#000000", "#1C1C1C", "#F0F0F0", "#585858", "#FF9900", "#FFFFFF")
        elif GlobalSettings().selectedTheme == "ElegantDark":
            style = "Fusion"
            sheet = self._get_file_stylesheet(":/themes/other/ElegantDark.qss", app)
            palette = self.create_palette("#2A2A2A", "#525252", "#00FF00", "#585858", "#BDBDBD", "#FFFFFF")
        elif GlobalSettings().selectedTheme == "MacOS":
            style = self.original_style
            sheet = self._get_file_stylesheet(":/themes/other/MacOS.qss", app)
            # dont use, looks worse
            # palette = self.create_palette("#ECECEC", "#D2D8DD", "#272727", "#FBFDFD", "#467DD1", "#FFFFFF")
        elif GlobalSettings().selectedTheme == "ManjaroMix":
            sheet = self._get_file_stylesheet(":/themes/other/ManjaroMix.qss", app)
            palette = self.create_palette("#222b2e", "#151a1e", "#FFFFFF", "#214037", "#4fa08b", "#027f7f")
        elif GlobalSettings().selectedTheme == "MaterialDark":
            style = "Fusion"
            sheet = self._get_file_stylesheet(":/themes/other/MaterialDark.qss", app)
            palette = self.create_palette("#1E1D23", "#1E1D23", "#FFFFFF", "#007B50", "#04B97F", "#37EFBA")
        elif GlobalSettings().selectedTheme == "NeonButtons":
            ...
            # sheet = self._get_file_stylesheet(":/themes/other/NeonButtons.qss", app)
        elif GlobalSettings().selectedTheme == "Ubuntu":
            ...
            # sheet = self._get_file_stylesheet(":/themes/other/Ubuntu.qss", app)
            # palette = self.create_palette("#f0f0f0", "#1e1d23", "#000000", "#f68456", "#ec743f", "#ffffff")
        elif GlobalSettings().selectedTheme == "Breeze (Dark)":
            if qtpy.QT6:
                QMessageBox(QMessageBox.Icon.Critical, "Breeze Unavailable", "Breeze is only supported on qt5 at this time.").exec_()
                return
            sheet = self._get_file_stylesheet(":/dark/stylesheet.qss", app)
        else:
            GlobalSettings().reset_setting("selectedTheme")
            self.change_theme(GlobalSettings().selectedTheme)
        print(f"Theme changed to: '{GlobalSettings().selectedTheme}'. Native style name: {self.original_style}")
        self.apply_style(app, sheet, style, palette)

    def _get_file_stylesheet(self, qt_path: str, app: QApplication) -> str:
        file = QFile(qt_path)
        if not file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            return ""
        try:
            return QTextStream(file).readAll()
        finally:
            file.close()

    def adjust_color(
        self,
        color: Any,
        lightness: int = 100,
        saturation: int = 100,
        hue_shift: int = 0,
    ) -> QColor:
        """Adjusts the color's lightness, saturation, and hue."""
        qcolor = QColor(color)
        h, s, v, _ = qcolor.getHsv()
        s = max(0, min(255, s * saturation // 100))
        v = max(0, min(255, v * lightness // 100))
        h = (h + hue_shift) % 360
        qcolor.setHsv(h, s, v)
        return qcolor

    def create_palette(  # noqa: PLR0913, C901
        self,
        primary: QColor | Qt.GlobalColor | str | int,
        secondary: QColor | Qt.GlobalColor | str | int,
        text: QColor | Qt.GlobalColor | str | int,
        tooltip_base: QColor | Qt.GlobalColor | str | int,
        highlight: QColor | Qt.GlobalColor | str | int,
        bright_text: QColor | Qt.GlobalColor | str | int,
    ) -> QPalette:
        """Create a QPalette using base colors adjusted for specific UI roles."""
        if not isinstance(primary, QColor):
            primary = QColor(primary)
        if not isinstance(secondary, QColor):
            secondary = QColor(secondary)
        if not isinstance(text, QColor):
            text = QColor(text)
        if not isinstance(tooltip_base, QColor):
            tooltip_base = QColor(tooltip_base)
        if not isinstance(highlight, QColor):
            highlight = QColor(highlight)
        if not isinstance(bright_text, QColor):
            bright_text = QColor(bright_text)

        palette = QPalette()
        role_colors: dict[QPalette.ColorRole, QColor] = {
            QPalette.ColorRole.Window: secondary,
            QPalette.ColorRole.Dark: self.adjust_color(primary, lightness=80),
            QPalette.ColorRole.Button: primary,
            QPalette.ColorRole.WindowText: text,
            QPalette.ColorRole.Base: primary,
            QPalette.ColorRole.AlternateBase: self.adjust_color(secondary, lightness=120),
            QPalette.ColorRole.ToolTipBase: tooltip_base,
            QPalette.ColorRole.ToolTipText: self.adjust_color(tooltip_base, lightness=200),  # Slightly lighter for readability
            QPalette.ColorRole.Text: self.adjust_color(text, lightness=90),
            QPalette.ColorRole.ButtonText: self.adjust_color(text, lightness=95),
            QPalette.ColorRole.BrightText: bright_text,
            QPalette.ColorRole.Link: highlight,
            QPalette.ColorRole.LinkVisited: self.adjust_color(highlight, hue_shift=10),
            QPalette.ColorRole.Highlight: highlight,
            QPalette.ColorRole.HighlightedText: self.adjust_color(secondary, lightness=120, saturation=255),
            QPalette.ColorRole.Light: self.adjust_color(primary, lightness=150),
            QPalette.ColorRole.Midlight: self.adjust_color(primary, lightness=130),
            QPalette.ColorRole.Mid: self.adjust_color(primary, lightness=100),
            QPalette.ColorRole.Shadow: self.adjust_color(primary, lightness=50),
            QPalette.ColorRole.PlaceholderText: self.adjust_color(text, lightness=70),
        }

        # Special handling for PyQt5 and PyQt6
        if qtpy.QT5:
            extra_roles = {
                QPalette.ColorRole.Background: self.adjust_color(primary, lightness=110),  # Use Background for PyQt5
                QPalette.ColorRole.Foreground: self.adjust_color(text, lightness=95),  # Use Foreground for PyQt5
            }
        else:
            # In PyQt6, Background and Foreground are handled with Window and WindowText respectively
            extra_roles: dict[QPalette.ColorRole, QColor] = {
                QPalette.ColorRole.Window: self.adjust_color(secondary, lightness=110),
                QPalette.ColorRole.WindowText: self.adjust_color(text, lightness=95),
            }
        role_colors.update(extra_roles)
        for role, color in role_colors.items():
            palette.setColor(QPalette.ColorGroup.Normal, role, color)

        # Create disabled and inactive variations
        for state_key, saturation_factor, lightness_factor in [
            (QPalette.ColorGroup.Disabled, 80, 60),  # More muted and slightly darker
            (QPalette.ColorGroup.Inactive, 90, 80),  # Slightly muted
        ]:
            for role, base_color in role_colors.items():
                adjusted_color: QColor = self.adjust_color(
                    base_color,
                    saturation=saturation_factor,
                    lightness=lightness_factor,
                )
                palette.setColor(state_key, role, adjusted_color)

        return palette