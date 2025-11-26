from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any

from qtpy.QtCore import QDir, QDirIterator, Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication, QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QStyleFactory, QVBoxLayout

if TYPE_CHECKING:
    from qtpy.QtCore import QCoreApplication
    from qtpy.QtGui import QPalette
    from qtpy.QtWidgets import QStyle


class ThemeDialog(QDialog):
    """Dialog for selecting and changing application themes."""

    def __init__(self):
        """Initialize the theme dialog."""
        super().__init__()
        self._init_ui()

    @staticmethod
    def get_available_themes() -> tuple[str, ...]:
        """List all resources in the specified resource path."""
        it = QDirIterator(QDir(":/themes"), QDirIterator.IteratorFlag.Subdirectories)
        return tuple(os.path.splitext(os.path.basename(file))[0].lower() for file in iter(it.next, None))


    @staticmethod
    def get_default_styles() -> tuple[str, ...]:
        """Get the available styles."""
        return tuple(k.lower() for k in QStyleFactory.keys())

    @classmethod
    def get_original_style(cls) -> str:
        """Get the original style of the application."""
        app: QCoreApplication | None = QApplication.instance()
        assert isinstance(app, QApplication), "QApplication instance not found or not QApplication type."
        app_style: QStyle | None = app.style()
        if app_style is None:
            raise RuntimeError("Failed to get application style")
        return app_style.objectName().lower()

    @staticmethod
    def adjust_color(
        color: Any,
        lightness: int = 100,
        saturation: int = 100,
        hue_shift: int = 0,
    ) -> QColor:
        """
        Adjusts the color's lightness, saturation, and hue.

        Args:
            color: Input color to adjust.
            lightness: Percentage of lightness adjustment.
            saturation: Percentage of saturation adjustment.
            hue_shift: Degrees to shift the hue.

        Returns:
            Adjusted QColor instance.
        """
        qcolor = QColor(color)
        if not isinstance(qcolor, QColor):
            qcolor = QColor(qcolor)
        h, s, v, _ = qcolor.getHsv()
        assert h is not None, "Hue is None"
        assert s is not None, "Saturation is None"
        assert v is not None, "Value is None"
        s = max(0, min(255, s * saturation // 100))
        return qcolor

    def _init_ui(self):
        """Set up the user interface for the theme dialog."""
        self.setWindowTitle("Theme Selection")
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

        # Theme selection label and combo box
        self._theme_label: QLabel = QLabel("Select Theme:")
        self._theme_combo_box: QComboBox = QComboBox()
        self._theme_combo_box.addItems(set(self.get_available_themes() + self.get_default_styles()))
        self._theme_combo_box.currentTextChanged.connect(self.on_theme_changed)

        # Buttons
        self._ok_button: QPushButton = QPushButton("Apply")
        self._ok_button.clicked.connect(self.accept)
        self._cancel_button: QPushButton = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self.reject)

        # Layout
        self._button_layout: QHBoxLayout = QHBoxLayout()
        self._button_layout.addWidget(self._ok_button)
        self._button_layout.addWidget(self._cancel_button)

        self._main_layout: QVBoxLayout = QVBoxLayout()
        self._main_layout.addWidget(self._theme_label)
        self._main_layout.addWidget(self._theme_combo_box)
        self._main_layout.addLayout(self._button_layout)

        self.setLayout(self._main_layout)

    def on_theme_changed(
        self,
        theme: str,
    ):
        """Handle theme change event."""
        print(f"Theme changed to: {theme}")
        app: QCoreApplication | None = QApplication.instance()
        assert isinstance(app, QApplication), "QApplication instance not found or not QApplication type."
        self.apply_style(app=app, sheet=theme, style=None, palette=None)

    @classmethod
    def apply_style(
        cls,
        app: QApplication,
        sheet: str | None = None,
        style: str | None = None,
        palette: QPalette | None = None,
    ):
        """Apply the style, sheet, and palette to the application."""
        # Set style first (before stylesheet) for proper rendering
        if style:
            style_obj = QStyleFactory.create(style)
            if style_obj:
                app.setStyle(style_obj)
        app_style: QStyle | None = app.style()
        if palette is None and app_style is not None:
            palette = app_style.standardPalette()
        if palette is not None:
            app.setPalette(palette)
        # Set stylesheet last (can override style appearance)
        app.setStyleSheet(sheet or "")

    def get_theme(self) -> str:
        """
        Get the selected theme.

        Returns:
            The name of the selected theme.
        """
        return self._theme_combo_box.currentText()
