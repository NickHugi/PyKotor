from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QWidget,
)

from toolset.gui.common.flow_layout import FlowLayout


class ExampleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowLayout Example")

        # Scrollable Area Setup
        scroll_area: QScrollArea = QScrollArea(self)  # Create a scroll area that will contain the central widget
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setCentralWidget(scroll_area)

        # Central Widget which will contain the layout
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)  # Set the central widget of the scroll area

        # Flow Layout Setup
        flow_layout: FlowLayout = FlowLayout(central_widget)
        central_widget.setLayout(flow_layout)

        # Adding various widgets to the flow layout
        flow_layout.addWidget(QLabel("Label"))
        flow_layout.addWidget(QPushButton("Button"))
        flow_layout.addWidget(QLineEdit("Edit me"))
        flow_layout.addWidget(QCheckBox("Check me"))
        flow_layout.addWidget(QRadioButton("Choose me"))

        combo: QComboBox = QComboBox()
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        flow_layout.addWidget(combo)

        flow_layout.addWidget(QSlider(Qt.Orientation.Horizontal))
        spin_box: QSpinBox = QSpinBox()
        spin_box.setRange(0, 100)
        flow_layout.addWidget(spin_box)

        progress_bar: QProgressBar = QProgressBar()
        progress_bar.setValue(50)
        flow_layout.addWidget(progress_bar)

        flow_layout.addWidget(QDateEdit())

        # Styling the widgets
        self.apply_styles(central_widget)

    def apply_styles(
        self,
        widget: QWidget,
    ):
        # Apply some color to distinguish widget areas
        palette: QPalette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window,
            QColor(240, 240, 240)
        )  # Light gray background
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())