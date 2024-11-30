from __future__ import annotations

import importlib
import os

from typing import TYPE_CHECKING, Any

import qtpy

from PyQt6.QtWidgets import QStyleFactory
from qtpy.QtCore import (
    QDir,
    QDirIterator,
    QFile,
    QTextStream,
    Qt,
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QMessageBox,
    QStyle,
)

from toolset.gui.widgets.settings.widgets.misc import GlobalSettings
from utility.ui_libraries.qt.widgets.theme.theme_dialog import ThemeDialog

if TYPE_CHECKING:
    from qtpy.QtCore import QCoreApplication, QObject, QPoint
    from qtpy.QtGui import QFont, QMouseEvent, _QAction
    from qtpy.QtWidgets import QLayout, QWidget


class ThemeManager:
    """Manages the application's theme."""

    def __init__(
        self,
        original_style: str | None = None,
    ):
        """Initialize the theme manager."""
        self.original_style: str = original_style or ThemeDialog.get_original_style()

    @staticmethod
    def get_available_themes() -> tuple[str, ...]:
        """List all resources in the specified resource path."""
        it = QDirIterator(QDir(":/themes"), QDirIterator.IteratorFlag.Subdirectories)
        themes: list[str] = []
        while True:
            file = it.next()
            if not file or not file.strip():
                break
            print(file)
            themes.append(os.path.splitext(os.path.basename(file))[0].lower())  # noqa: PTH122, PTH119
        return tuple(themes)


    @staticmethod
    def get_default_styles() -> tuple[str, ...]:
        """Get the available styles."""
        styles: list[str] = []
        for k in QStyleFactory.keys():  # noqa: SIM118
            if not k or not k.strip():
                continue
            print(k)
            styles.append(k.lower())  # noqa: PERF401
        return tuple(styles)

    @classmethod
    def get_original_style(cls) -> str:
        """Get the original style of the application."""
        app: QCoreApplication | None = QApplication.instance()
        assert isinstance(app, QApplication), "QApplication instance not found or not QApplication type."
        app_style: QStyle | None = app.style()
        if app_style is None:
            raise RuntimeError("Failed to get application style")
        return app_style.objectName().lower()

    def _get_theme_config(
        self,
        theme_name: str,
    ) -> dict[str, Any]:
        """Get the configuration for a specific theme."""
        configs: dict[str, dict[str, Any]] = {
            "native": {
                "style": self.original_style,
                "palette": None,  # Will use standard palette
                "sheet": "",
            },
            "fusion (light)": {
                "style": "Fusion",
                "palette": None,
                "sheet": "",
            },
            "fusion (dark)": {
                "style": "Fusion",
                "palette": lambda: self.create_palette(
                    QColor(53, 53, 53),
                    QColor(35, 35, 35),
                    QColor(240, 240, 240),
                    QColor(25, 25, 25),
                    self.adjust_color(QColor("orange"), saturation=80, hue_shift=-10),
                    QColor(255, 69, 0),
                ),
                "sheet": "",
            },
            "amoled": {
                "style": self.original_style,
                "palette": lambda: self.create_palette("#000000", "#141414", "#e67e22", "#f39c12", "#808086", "#FFFFFF"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/AMOLED.qss", app),
            },
            "aqua": {
                "style": self.original_style,
                "palette": None,
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/aqua.qss", app),
            },
            "consolestyle": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#000000", "#1C1C1C", "#F0F0F0", "#585858", "#FF9900", "#FFFFFF"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/ConsoleStyle.qss", app),
            },
            "elegantdark": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#2A2A2A", "#525252", "#00FF00", "#585858", "#BDBDBD", "#FFFFFF"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/ElegantDark.qss", app),
            },
            "macos": {
                "style": self.original_style,
                "palette": None,
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/MacOS.qss", app),
            },
            "manjaromix": {
                "style": self.original_style,
                "palette": lambda: self.create_palette("#222b2e", "#151a1e", "#FFFFFF", "#214037", "#4fa08b", "#027f7f"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/ManjaroMix.qss", app),
            },
            "materialdark": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#1E1D23", "#1E1D23", "#FFFFFF", "#007B50", "#04B97F", "#37EFBA"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/MaterialDark.qss", app),
            },
            "cyberpunk2077": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#030d22", "#262940", "#fdfeff", "#242942", "#310072", "#EA00D9"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/cyberpunk2077.qss", app),
            },
            "andromeda": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#23262E", "#1A1C22", "#D5CED9", "#2A2D44", "#373941", "#00e8c6"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/Andromeda.qss", app),
            },
            "asunadark": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#1b1b1b", "#232323", "#F8F8F2", "#282828", "#531616", "#99202c"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/AsunaDark.qss", app),
            },
            "andromedaitalic": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#23262E", "#1A1C22", "#D5CED9", "#2A2D44", "#373941", "#00e8c6"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/AndromedaItalic.qss", app),
            },
            "astolfo": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#1a1c19", "#241517", "#F8F8F2", "#2b2b2b", "#501C1C", "#d58d9c"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/Astolfo.qss", app),
            },
            "shadesofpurple": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#2D2B55", "#1E1E3F", "#E6E6E6", "#5D4C9D", "#FB94FF", "#9D8BF4"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/ShadesOfPurple.qss", app),
            },
            "monokaidark": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#272822", "#1E1F1C", "#F8F8F2", "#49483E", "#F92672", "#75715E"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/MonokaiDark.qss", app),
            },
            "solarizeddark": {
                "style": "Fusion",
                "palette": lambda: self.create_palette("#002B36", "#073642", "#93A1A1", "#586E75", "#268BD2", "#586E75"),
                "sheet": lambda app: self._get_file_stylesheet(":/themes/other/SolarizedDark.qss", app),
            },
        }
        return configs.get(theme_name, configs["native"])

    @Slot()
    def change_theme(
        self,
        theme: _QAction | str | None = None,
    ):
        """Changes the theme of the application."""
        app: QCoreApplication | None = QApplication.instance()
        assert isinstance(app, QApplication)

        theme_name: str | None = theme.text() if isinstance(theme, QAction) else theme
        assert isinstance(theme_name, str)
        GlobalSettings().selectedTheme = theme_name

        if theme_name == "QDarkStyle":
            if not importlib.util.find_spec("qdarkstyle"):  # pyright: ignore[reportAttributeAccessIssue]
                QMessageBox.critical(None, "Theme not found", "QDarkStyle is not installed in this environment.")
                GlobalSettings().reset_setting("selectedTheme")
                self.change_theme(GlobalSettings().selectedTheme)
                return

            import qdarkstyle  # pyright: ignore[reportMissingImports]

            app.setStyle(self.original_style)
            app_style: QStyle | None = app.style()
            assert isinstance(app_style, QStyle)
            app.setPalette(app_style.standardPalette())
            app.setStyleSheet(qdarkstyle.load_stylesheet())
        else:
            config: dict[str, Any] = self._get_theme_config(theme_name)
            sheet: str = config["sheet"](app) if callable(config["sheet"]) else config["sheet"]
            palette: QPalette | None = config["palette"]() if callable(config["palette"]) else config["palette"]

            print(f"Theme changed to: '{theme_name}'. Native style name: {self.original_style}")
            ThemeDialog.apply_style(app, sheet, config["style"], palette)

    def _get_file_stylesheet(
        self,
        qt_path: str,
        app: QApplication,
    ) -> str:
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
        if not isinstance(qcolor, QColor):
            qcolor = QColor(qcolor)
        h, s, v, _ = qcolor.getHsv()
        assert h is not None, "Hue is None"
        assert s is not None, "Saturation is None"
        assert v is not None, "Value is None"
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
                QPalette.ColorRole.Background: self.adjust_color(primary, lightness=110),  # pyright: ignore[reportAttributeAccessIssue]
                QPalette.ColorRole.Foreground: self.adjust_color(text, lightness=95),  # pyright: ignore[reportAttributeAccessIssue]
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

    @staticmethod
    def setup_custom_title_bar(  # noqa: C901, PLR0913
        main_window: QWidget,
        title: str = "",
        icon_filename: str = "",
        font: QFont | None = None,
        hint: list[str] | None = None,
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
        *,
        bottom_separator: bool = False,
    ) -> QWidget:
        from qtpy.QtCore import QPoint, Qt
        from qtpy.QtGui import QFont, QIcon
        from qtpy.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

        class TitleBar(QWidget):
            def __init__(self, parent: QWidget):
                super().__init__(parent)
                layout: QLayout = QHBoxLayout(self)
                self.setLayout(layout)
                layout.setContentsMargins(0, 0, 0, 0)
                self.setAutoFillBackground(True)

                # Icon
                if icon_filename:
                    self._icon: QLabel = QLabel(self)
                    self._icon.setPixmap(QIcon(icon_filename).pixmap(16, 16))
                elif not parent.windowIcon().isNull():
                    self._icon: QLabel = QLabel(self)
                    self._icon.setPixmap(parent.windowIcon().pixmap(16, 16))
                layout.addWidget(self._icon)

                # Title
                self._title: QLabel = QLabel(title, self)
                self._title.setAlignment(align)
                self._title.setFont(font or QFont("Arial", 12))
                layout.addWidget(self._title)

                # Buttons
                button_style = """
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        width: 30px;
                        height: 30px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 30);
                    }
                """
                if "min" in (hint or []):
                    self.min_button = QPushButton("🗕", self)
                    self.min_button.setStyleSheet(button_style)
                    self.min_button.clicked.connect(parent.showMinimized)
                    layout.addWidget(self.min_button)

                if "max" in (hint or []):
                    self.max_button = QPushButton("🗖", self)
                    self.max_button.setStyleSheet(button_style)
                    self.max_button.clicked.connect(self.toggle_maximize)
                    layout.addWidget(self.max_button)

                if "close" in (hint or []):
                    self.close_button = QPushButton("✕", self)
                    self.close_button.setStyleSheet(button_style)
                    self.close_button.clicked.connect(parent.close)
                    layout.addWidget(self.close_button)

                self.start: QPoint = QPoint(0, 0)
                self.pressing: bool = False

            def mousePressEvent(self, event: QMouseEvent):
                self.start: QPoint = self.mapToGlobal(event.pos())
                self.pressing = True

            def mouseMoveEvent(self, event: QMouseEvent):
                if self.pressing:
                    end: QPoint = self.mapToGlobal(event.pos())
                    movement: QPoint = end - self.start
                    parent: QObject | None = self.parent()
                    assert isinstance(parent, QWidget)
                    parent.setGeometry(
                        parent.x() + movement.x(),
                        parent.y() + movement.y(),
                        parent.width(),
                        parent.height(),
                    )
                    self.start: QPoint = end

            def mouseReleaseEvent(self, event: QMouseEvent):
                self.pressing = False

            def toggle_maximize(self):
                parent: QObject | None = self.parent()
                assert isinstance(parent, QWidget)
                if parent.isMaximized():
                    parent.showNormal()
                    self.max_button.setText("🗖")
                else:
                    parent.showMaximized()
                    self.max_button.setText("🗗")

        # Set up the main window
        main_window.setWindowFlags(main_window.windowFlags() & ~Qt.WindowType.FramelessWindowHint)
        main_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Create the title bar
        title_bar = TitleBar(main_window)

        # Set up the main layout
        layout: QLayout = QHBoxLayout(main_window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title_bar)

        # Add a bottom separator if requested
        if bottom_separator:
            separator = QWidget(main_window)
            separator.setFixedHeight(1)
            separator.setStyleSheet("background-color: #555;")
            layout.addWidget(separator)

        return title_bar
