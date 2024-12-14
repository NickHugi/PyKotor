from __future__ import annotations

from qtpy.QtCore import (
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QCheckBox, QGridLayout, QGroupBox, QVBoxLayout, QWidget


class StyleWidget(QWidget):
    sig_bold_checked: Signal = Signal(int)
    sig_italic_checked: Signal = Signal(int)

    def __init__(
        self,
        font: QFont = QFont("Arial", 10),
    ):
        super().__init__()
        self._init_ui(font=font)

    def _init_ui(
        self,
        font: QFont,
    ):
        group_box: QGroupBox = QGroupBox()
        group_box.setTitle("Style")

        self._bold_check_bok: QCheckBox = QCheckBox("Bold")
        self._italic_check_box: QCheckBox = QCheckBox("Italic")

        self._bold_check_bok.stateChanged.connect(self.sig_bold_checked)
        self._italic_check_box.stateChanged.connect(self.sig_italic_checked)

        self.set_current_style(font=font)

        lay = QVBoxLayout()
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.addWidget(self._bold_check_bok)
        lay.addWidget(self._italic_check_box)

        group_box.setLayout(lay)

        lay = QGridLayout()
        lay.addWidget(group_box)

        self.setLayout(lay)

    def set_current_style(
        self,
        font: QFont,
    ):
        self._bold_check_bok.setChecked(font.bold())
        self._italic_check_box.setChecked(font.italic())

    def is_bold(self) -> bool:
        return self._bold_check_bok.isChecked()

    def is_italic(self) -> bool:
        return self._italic_check_box.isChecked()
