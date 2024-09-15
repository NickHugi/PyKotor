from __future__ import annotations

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QAction, QToolBar, QVBoxLayout, QWidget

from pykotor.common.geometry import Vector3
from pykotor.common.misc import SurfaceMaterial
from pykotor.resource.formats.bwm.bwm_data import BWM


class WalkmeshEditor(QWidget):
    walkmeshUpdated = Signal(BWM)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.walkmesh: BWM | None = None
        self.selected_face: int | None = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.toolbar = QToolBar()
        layout.addWidget(self.toolbar)

        self.addFaceAction = QAction("Add Face", self)
        self.addFaceAction.triggered.connect(self.addFace)
        self.toolbar.addAction(self.addFaceAction)

        self.removeFaceAction = QAction("Remove Face", self)
        self.removeFaceAction.triggered.connect(self.removeFace)
        self.toolbar.addAction(self.removeFaceAction)

        self.mergeFacesAction = QAction("Merge Faces", self)
        self.mergeFacesAction.triggered.connect(self.mergeFaces)
        self.toolbar.addAction(self.mergeFacesAction)

        self.splitFaceAction = QAction("Split Face", self)
        self.splitFaceAction.triggered.connect(self.splitFace)
        self.toolbar.addAction(self.splitFaceAction)

        self.setMaterialAction = QAction("Set Material", self)
        self.setMaterialAction.triggered.connect(self.setMaterial)
        self.toolbar.addAction(self.setMaterialAction)

    def setWalkmesh(self, walkmesh: BWM):
        self.walkmesh = walkmesh
        self.update()

    def addFace(self):
        if self.walkmesh:
            # Logic to add a new face
            new_face = self.walkmesh.add_face(Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0))
            self.selected_face = new_face
            self.walkmeshUpdated.emit(self.walkmesh)

    def removeFace(self):
        if self.walkmesh and self.selected_face is not None:
            # Logic to remove the selected face
            self.walkmesh.remove_face(self.selected_face)
            self.selected_face = None
            self.walkmeshUpdated.emit(self.walkmesh)

    def mergeFaces(self):
        # Logic to merge selected faces
        pass

    def splitFace(self):
        # Logic to split the selected face
        pass

    def setMaterial(self):
        if self.walkmesh and self.selected_face is not None:
            # Logic to set the material of the selected face
            # This could open a dialog to choose the material
            self.walkmesh.faces[self.selected_face].material = SurfaceMaterial.DIRT
            self.walkmeshUpdated.emit(self.walkmesh)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.walkmesh:
            # Logic to render the walkmesh
            pass
