from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.theme.theme_dialog import ThemeDialog

if TYPE_CHECKING:
    from qtpy.QtCore import QCoreApplication


class ThemeHandler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Material Theme Playground (Change theme in Runtime)")
        self.resize(600, 400)
        self._init_ui()

    def _init_ui(self):
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)

        # Theme selection
        self._theme_layout: QHBoxLayout = QHBoxLayout()
        self._select_theme_label: QLabel = QLabel("Select Theme")
        self._material_combo_box: QComboBox = QComboBox()
        self._material_combo_box.addItems(list(set(ThemeDialog.get_default_styles()) | set(ThemeDialog.get_available_themes())))
        self._material_combo_box.currentTextChanged.connect(self.apply_theme_in_runtime)
        self._theme_layout.addWidget(self._select_theme_label)
        self._theme_layout.addWidget(self._material_combo_box)

        # Density scale slider
        self._density_layout: QHBoxLayout = QHBoxLayout()
        self._density_label: QLabel = QLabel("Density Scale")
        self._density_scale_slider: QSlider = QSlider()
        self._density_scale_slider.setOrientation(Qt.Orientation.Horizontal)
        self._density_scale_slider.setRange(50, 200)
        self._density_scale_slider.setValue(100)
        self._density_scale_slider.valueChanged.connect(lambda: self.apply_theme_in_runtime(self._material_combo_box.currentText()))
        self._density_layout.addWidget(self._density_label)
        self._density_layout.addWidget(self._density_scale_slider)

        # Font size spin box
        self._font_layout: QHBoxLayout = QHBoxLayout()
        self._font_label: QLabel = QLabel("Font Size")
        self._font_size_spin_box: QSpinBox = QSpinBox()
        self._font_size_spin_box.setRange(8, 24)
        self._font_size_spin_box.setValue(10)
        self._font_size_spin_box.valueChanged.connect(lambda: self.apply_theme_in_runtime(self._material_combo_box.currentText()))
        self._font_layout.addWidget(self._font_label)
        self._font_layout.addWidget(self._font_size_spin_box)

        # Open theme dialog button
        self.theme_dialog_btn: QPushButton = QPushButton("Open Theme Dialog")
        self.theme_dialog_btn.clicked.connect(self.open_theme_dialog)

        # Main layout
        self._main_layout: QVBoxLayout = QVBoxLayout()
        self._main_layout.addLayout(self._theme_layout)
        self._main_layout.addLayout(self._density_layout)
        self._main_layout.addLayout(self._font_layout)
        self._main_layout.addWidget(self.theme_dialog_btn)
        self._central_widget.setLayout(self._main_layout)

        # Initial theme application
        self.apply_theme_in_runtime(self._material_combo_box.currentText())

    def open_theme_dialog(self):
        """Open the theme dialog for runtime theme selection."""
        dialog: ThemeDialog = ThemeDialog()
        if dialog.exec() == ThemeDialog.DialogCode.Accepted:
            self.apply_theme_in_runtime(dialog.get_theme())

    def apply_theme_in_runtime(
        self,
        theme_name: str,
    ) -> None:
        """Apply the selected theme with runtime modifications."""
        font = QFont()
        font.setPointSize(self._font_size_spin_box.value())
        QApplication.setFont(font)
        print(f"Theme changed to: {theme_name}")
        app: QCoreApplication | None = QApplication.instance()
        assert isinstance(app, QApplication), "QApplication instance not found or not QApplication type."
        ThemeDialog.apply_style(app, style=theme_name)
