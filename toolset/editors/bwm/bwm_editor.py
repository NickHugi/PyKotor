import math
import struct
from typing import Optional, Tuple, Dict, List, Set

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPaintEvent, QPainter, QPen, QColor, QPainterPath, QBrush, QMouseEvent, QImage, \
    QWheelEvent, QKeyEvent
from PyQt5.QtWidgets import QWidget, QListWidgetItem, QShortcut
from pykotor.common.geometry import Vector3, SurfaceMaterial, Vector2
from pykotor.resource.formats.bwm import read_bwm, BWM, BWMFace, write_bwm
from pykotor.resource.generics.git import GITTrigger, GIT
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.editor import Editor


_TRANS_FACE_ROLE = QtCore.Qt.UserRole + 1
_TRANS_EDGE_ROLE = QtCore.Qt.UserRole + 2


class BWMEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.WOK, ResourceType.DWK, ResourceType.PWK]
        super().__init__(parent, "Walkmesh Painter", "walkmesh", supported, supported, installation)

        from editors.bwm import bwm_editor_ui
        self.ui = bwm_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._bwm: Optional[BWM] = None

        self.materialColors: Dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED:      QColor(0xf45086),
            SurfaceMaterial.OBSCURING:      QColor(0x555555),
            SurfaceMaterial.DIRT:           QColor(0x800000),
            SurfaceMaterial.GRASS:          QColor(0x33cc33),
            SurfaceMaterial.STONE:          QColor(0x808080),
            SurfaceMaterial.WOOD:           QColor(0x5e260c),
            SurfaceMaterial.WATER:          QColor(0x0066ff),
            SurfaceMaterial.NON_WALK:       QColor(0xff00ff),
            SurfaceMaterial.TRANSPARENT:    QColor(0xb3ffff),
            SurfaceMaterial.CARPET:         QColor(0xffff00),
            SurfaceMaterial.METAL:          QColor(0x4d4d4d),
            SurfaceMaterial.PUDDLES:        QColor(0x00ffaa),
            SurfaceMaterial.SWAMP:          QColor(0x00995c),
            SurfaceMaterial.MUD:            QColor(0xcc6600),
            SurfaceMaterial.LEAVES:         QColor(0x009933),
            SurfaceMaterial.LAVA:           QColor(0xff944d),
            SurfaceMaterial.BOTTOMLESS_PIT: QColor(0xe6e6e6),
            SurfaceMaterial.DEEP_WATER:     QColor(0x9999ff),
            SurfaceMaterial.DOOR:           QColor(0xffb3b3),
            SurfaceMaterial.NON_WALK_GRASS: QColor(0xb3ffb3),
            SurfaceMaterial.TRIGGER:        QColor(0x4d0033)
        }
        self.ui.renderArea.materialColors = self.materialColors
        self.rebuildMaterials()

        self.new()

    def _setupSignals(self) -> None:
        #self.ui.transList.itemSelectionChanged.connect(self.onTransitionSelect)
        self.ui.renderArea.mouseMoved.connect(self.onMouseMoved)
        self.ui.renderArea.mouseScrolled.connect(self.onMouseScrolled)

        QShortcut("+", self).activated.connect(lambda: self.ui.renderArea.cameraZoom(2))
        QShortcut("-", self).activated.connect(lambda: self.ui.renderArea.cameraZoom(-2))

    def rebuildMaterials(self) -> None:
        self.ui.materialList.clear()
        for material in self.materialColors:
            color = self.materialColors[material]
            image = QImage(struct.pack('BBB', color.red(), color.green(), color.blue()) * 16 * 16, 16, 16, QImage.Format_RGB888)
            icon = QIcon(QPixmap(image))
            text = material.name.replace("_", " ").title()
            item = QListWidgetItem(icon, text)
            item.setData(QtCore.Qt.UserRole, material)
            self.ui.materialList.addItem(item)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        self._bwm = read_bwm(data)
        self.ui.renderArea.setWalkmeshes([self._bwm])

        def addTransItem(face, edge, transition):
            if transition is not None:
                item = QListWidgetItem("Transition to: {}".format(transition))
                item.setData(_TRANS_FACE_ROLE, face)
                item.setData(_TRANS_EDGE_ROLE, edge)
                self.ui.transList.addItem(item)

        self.ui.transList.clear()
        for face in self._bwm.faces:
            addTransItem(face, 1, face.trans1)
            addTransItem(face, 2, face.trans2)
            addTransItem(face, 3, face.trans3)

    def build(self) -> bytes:
        data = bytearray()
        write_bwm(self._bwm, data)
        return data

    def new(self) -> None:
        super().new()

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        world = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        worldData = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        face = self._bwm.faceAt(world.x, world.y)

        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control in keys:
            self.ui.renderArea.panCamera(-worldData.x, -worldData.y)
        elif QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:
            self.ui.renderArea.rotateCamera(delta.x / 50)
        elif QtCore.Qt.LeftButton in buttons:
            self.changeFaceMaterial(face)

        coordsText = "x: {:.2f}, {:.2f}".format(world.x, world.y)
        faceText = ", face: {}".format("None" if face is None else self._bwm.faces.index(face))

        screen = self.ui.renderArea.toRenderCoords(world.x, world.y)
        xy = " || x: {0:.2f}, ".format(screen.x) + "y: {0:.2f}, ".format(screen.y)

        self.statusBar().showMessage(coordsText + faceText + xy)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.Key_Control in keys:
            self.ui.renderArea.zoomInCamera(delta.y / 50)

    def changeFaceMaterial(self, face: BWMFace):
        newMaterial = self.ui.materialList.currentItem().data(QtCore.Qt.UserRole)
        if face and face.material != newMaterial:
            face.material = newMaterial

    def onTransitionSelect(self) -> None:
        if self.ui.transList.currentItem():
            item = self.ui.transList.currentItem()
            self.ui.renderArea.setHighlightedTrans(item.data(_TRANS_FACE_ROLE))
        else:
            self.ui.renderArea.setHighlightedTrans(None)

