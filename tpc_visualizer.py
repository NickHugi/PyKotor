from __future__ import annotations

import sys

from qtpy.QtCore import Qt
from qtpy.QtGui import QImage, QPixmap
from qtpy.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from pykotor.resource.formats.tpc.tpc_data import TPC, TPCTextureFormat


class TPCVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPC Visualizer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget: QWidget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout: QVBoxLayout = QVBoxLayout(self.central_widget)

        self.image_label: QLabel = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.image_label)

        self.debug_label: QLabel = QLabel(self)
        self.debug_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.debug_label)

        self.button_layout: QHBoxLayout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)

        self.revert_button: QPushButton = QPushButton("Revert", self)
        self.revert_button.clicked.connect(self.revert_image)
        self.button_layout.addWidget(self.revert_button)

        self.current_format: TPCTextureFormat = TPCTextureFormat.RGBA
        self.original_image: bytes  = self.generate_test_image()
        self.current_image: bytes = self.original_image

        self.update_ui()
        self.add_conversion_buttons()

    def generate_test_image(self) -> bytes:
        width, height = 64, 64
        image_data = bytearray()
        for y in range(height):
            for x in range(width):
                r = int(255 * x / width)
                g = int(255 * y / height)
                b = 128
                a = 255
                image_data.extend([r, g, b, a])
        return bytes(image_data)

    def update_ui(self):
        qimage = QImage(self.current_image, 64, 64, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage).scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)
        self.debug_label.setText(f"Current format: {self.current_format.name}")

    def add_conversion_buttons(self):
        compatible_formats = self.get_compatible_formats()
        for fmt in compatible_formats:
            button = QPushButton(f"Convert to {fmt.name}", self)
            button.clicked.connect(lambda _checked, f=fmt: self.convert_image(f))
            self.button_layout.addWidget(button)

    def get_compatible_formats(self) -> list[TPCTextureFormat]:
        all_formats = [
            TPCTextureFormat.Greyscale,
            TPCTextureFormat.RGB,
            TPCTextureFormat.RGBA,
            TPCTextureFormat.DXT1,
            TPCTextureFormat.DXT5,
            TPCTextureFormat.BGRA,
        ]
        return [f for f in all_formats if f != self.current_format]

    def convert_image(self, target_format: TPCTextureFormat):
        conversion_function = self.get_conversion_function(self.current_format, target_format)
        if conversion_function:
            self.current_image = conversion_function(self.current_image, 64, 64)
            self.current_format = target_format
            self.update_ui()
            self.clear_layout(self.button_layout)
            self.add_conversion_buttons()

    def get_conversion_function(self, source_format: TPCTextureFormat, target_format: TPCTextureFormat):
        conversion_map = {
            (TPCTextureFormat.RGBA, TPCTextureFormat.Greyscale): TPC.rgba_to_grey,
            (TPCTextureFormat.RGBA, TPCTextureFormat.RGB): TPC.rgba_to_rgb,
            (TPCTextureFormat.RGBA, TPCTextureFormat.DXT1): TPC.rgba_to_dxt1,
            (TPCTextureFormat.RGBA, TPCTextureFormat.DXT5): TPC.rgba_to_dxt5,
            (TPCTextureFormat.RGBA, TPCTextureFormat.BGRA): TPC.rgba_to_bgra,
            (TPCTextureFormat.RGB, TPCTextureFormat.RGBA): TPC.rgb_to_rgba,
            (TPCTextureFormat.RGB, TPCTextureFormat.Greyscale): TPC.rgb_to_grey,
            (TPCTextureFormat.RGB, TPCTextureFormat.DXT1): TPC.rgb_to_dxt1,
            (TPCTextureFormat.Greyscale, TPCTextureFormat.RGBA): TPC.grey_to_rgba,
            (TPCTextureFormat.Greyscale, TPCTextureFormat.RGB): TPC.grey_to_rgb,
            (TPCTextureFormat.DXT1, TPCTextureFormat.RGBA): TPC.dxt1_to_rgba,
            (TPCTextureFormat.DXT1, TPCTextureFormat.RGB): TPC.dxt1_to_rgb,
            (TPCTextureFormat.DXT5, TPCTextureFormat.RGBA): TPC.dxt5_to_rgba,
            (TPCTextureFormat.DXT5, TPCTextureFormat.RGB): TPC.dxt5_to_rgb,
            (TPCTextureFormat.BGRA, TPCTextureFormat.RGBA): TPC.bgra_to_rgba,
            (TPCTextureFormat.BGRA, TPCTextureFormat.RGB): TPC.bgra_to_rgb,
            (TPCTextureFormat.BGRA, TPCTextureFormat.Greyscale): TPC.bgra_to_grey,
        }
        return conversion_map.get((source_format, target_format))

    def revert_image(self):
        self.current_image = self.original_image
        self.current_format = TPCTextureFormat.RGBA
        self.update_ui()
        self.clear_layout(self.button_layout)
        self.add_conversion_buttons()

    def clear_layout(self, layout: QHBoxLayout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TPCVisualizer()
    window.show()
    sys.exit(app.exec())
