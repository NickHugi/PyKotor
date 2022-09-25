import math

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QOpenGLWidget, QWidget

from pykotor.common.module import Module
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.gl.models.read_mdl import gl_load_mdl
from pykotor.gl.scene import Scene, RenderObject


class ModelRenderer(QOpenGLWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.scene: Scene = None
        self.installation: Installation = None
        self._modelToLoad = None

    def loop(self) -> None:
        self.repaint()
        QTimer.singleShot(33, self.loop)

    def initializeGL(self) -> None:
        self.scene = Scene(installation=self.installation)
        self.scene.camera.fov = 70
        self.scene.camera.distance = 4
        self.scene.camera.z = 1.8
        self.scene.camera.yaw = math.pi/2
        self.scene.camera.width = self.width()
        self.scene.camera.height = self.height()
        self.scene.show_cursor = False
        QTimer.singleShot(33, self.loop)

    def paintGL(self) -> None:
        if self._modelToLoad is not None:
            self.scene.models["model"] = gl_load_mdl(self.scene, *self._modelToLoad)
            self.scene.objects["model"] = RenderObject("model")

        self.scene.render()

    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)

        if self.scene is not None:
            self.scene.camera.width = e.size().width()
            self.scene.camera.height = e.size().height()

    def setModel(self, data: bytes, data_ext: bytes) -> None:
        mdl = BinaryReader.from_auto(data, 12)
        mdx = BinaryReader.from_auto(data_ext)
        self._modelToLoad = mdl, mdx
