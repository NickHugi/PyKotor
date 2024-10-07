from __future__ import annotations

import re

from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QRegularExpressionValidator


class FileNameValidator(QRegularExpressionValidator):
    INVALID_CHARACTERS = '<>:"/\\|?*'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRegularExpression(self.get_regular_expression())

    @classmethod
    def get_regular_expression(cls) -> QRegularExpression:
        # Create a regular expression pattern that matches valid filename characters
        pattern = f"^[^{re.escape(cls.INVALID_CHARACTERS)}]*$"
        return QRegularExpression(pattern)

    def regularExpression(self) -> QRegularExpression:
        return super().regularExpression()
