from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtCore import QRectF, QTimer
from qtpy.QtGui import QBrush, QColor, QLinearGradient, QPainter
from qtpy.QtWidgets import QProgressBar

if TYPE_CHECKING:
    from qtpy.QtCore import QRect
    from qtpy.QtGui import QPaintEvent


class AnimatedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer: QTimer = QTimer(self)
        self._timer.timeout.connect(self.update_animation)
        self._timer.start(50)  # Update every 50 ms
        self._offset: int = 0

    def update_animation(self):
        if self.maximum() == self.minimum():
            return
        filled_width = int(self.width() * (self.value() - self.minimum()) / (self.maximum() - self.minimum()))
        if filled_width == 0:
            return
        self._offset = (self._offset + 1) % filled_width
        self.update()

    def paintEvent(
        self,
        event: QPaintEvent,
    ):
        # Call the base class's paintEvent to draw the default progress bar
        super().paintEvent(event)

        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # pyright: ignore[reportAttributeAccessIssue]

        rect: QRect = self.rect()
        chunk_height: int = rect.height()
        chunk_radius: float = chunk_height / 2

        # Calculate the filled width based on the current value
        if self.maximum() == self.minimum():
            filled_width: int = rect.width()
        else:
            filled_width = int(rect.width() * (self.value() - self.minimum()) / (self.maximum() - self.minimum()))
        filled_width = max(filled_width, chunk_height)  # Ensure minimum width to accommodate semicircles

        if filled_width <= 0:
            painter.end()
            return
        # 1. Draw the shimmering effect (moving light)
        light_width: int = chunk_height * 2  # Width of the shimmering light effect
        light_rect: QRectF = QRectF(self._offset - light_width / 2, 0, light_width, chunk_height)

        # Adjust light position if it starts before the progress bar
        if light_rect.left() < rect.left():
            light_rect.moveLeft(rect.left())

        # Adjust light position if it ends after the progress bar
        if light_rect.right() > rect.right():
            light_rect.moveRight(rect.right())

        # Create a linear gradient for the shimmering light effect
        shimmer_gradient: QLinearGradient = QLinearGradient(light_rect.left(), 0, light_rect.right(), 0)
        shimmer_gradient.setColorAt(0, QColor(255, 255, 255, 0))  # Transparent at the edges
        shimmer_gradient.setColorAt(0.5, QColor(255, 255, 255, 150))  # Semi-transparent white in the center
        shimmer_gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Transparent at the edges

        painter.setBrush(QBrush(shimmer_gradient))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)  # pyright: ignore[reportAttributeAccessIssue]
        painter.drawRoundedRect(light_rect, chunk_radius, chunk_radius)

        painter.end()
