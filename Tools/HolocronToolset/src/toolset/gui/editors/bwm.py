from __future__ import annotations

import struct

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtGui import QColor, QIcon, QImage, QPixmap
from qtpy.QtWidgets import QListWidgetItem, QShortcut

from pykotor.common.geometry import SurfaceMaterial
from pykotor.common.misc import Color
from pykotor.resource.formats.bwm import read_bwm, write_bwm
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.common.geometry import Vector2, Vector3
    from pykotor.resource.formats.bwm import BWM, BWMFace
    from toolset.data.installation import HTInstallation

_TRANS_FACE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1  # type: ignore[attr-defined]
_TRANS_EDGE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2  # type: ignore[attr-defined]


def calculate_zoom_strength(delta_y: float, sensSetting: int) -> float:
    m = 0.00202
    b = 1
    factor_in = (m * sensSetting + b)
    return 1 / abs(factor_in) if delta_y < 0 else abs(factor_in)


class BWMEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initializes the walkmesh painter window.

        Args:
        ----
            parent: QWidget | None: The parent widget
            installation: HTInstallation | None: The installation

        Processing Logic:
        ----------------
        Initializes UI components and connects signals:
            - Sets up UI from designer file
            - Sets up menus
            - Sets up signal connections
            - Initializes default material colors
            - Rebuilds material dropdown
            - Creates new empty walkmesh.
        """
        supported = [ResourceType.WOK, ResourceType.DWK, ResourceType.PWK]
        super().__init__(parent, "Walkmesh Painter", "walkmesh", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.bwm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.bwm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.bwm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.bwm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._bwm: BWM | None = None

        moduleDesignerSettings = ModuleDesignerSettings()

        def intColorToQColor(intvalue: int) -> QColor:
            color = Color.from_rgba_integer(intvalue)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

        self.materialColors: dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED: intColorToQColor(moduleDesignerSettings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: intColorToQColor(moduleDesignerSettings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: intColorToQColor(moduleDesignerSettings.dirtMaterialColour),
            SurfaceMaterial.GRASS: intColorToQColor(moduleDesignerSettings.grassMaterialColour),
            SurfaceMaterial.STONE: intColorToQColor(moduleDesignerSettings.stoneMaterialColour),
            SurfaceMaterial.WOOD: intColorToQColor(moduleDesignerSettings.woodMaterialColour),
            SurfaceMaterial.WATER: intColorToQColor(moduleDesignerSettings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: intColorToQColor(moduleDesignerSettings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: intColorToQColor(moduleDesignerSettings.transparentMaterialColour),
            SurfaceMaterial.CARPET: intColorToQColor(moduleDesignerSettings.carpetMaterialColour),
            SurfaceMaterial.METAL: intColorToQColor(moduleDesignerSettings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: intColorToQColor(moduleDesignerSettings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: intColorToQColor(moduleDesignerSettings.swampMaterialColour),
            SurfaceMaterial.MUD: intColorToQColor(moduleDesignerSettings.mudMaterialColour),
            SurfaceMaterial.LEAVES: intColorToQColor(moduleDesignerSettings.leavesMaterialColour),
            SurfaceMaterial.LAVA: intColorToQColor(moduleDesignerSettings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: intColorToQColor(moduleDesignerSettings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: intColorToQColor(moduleDesignerSettings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: intColorToQColor(moduleDesignerSettings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: intColorToQColor(moduleDesignerSettings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: intColorToQColor(moduleDesignerSettings.nonWalkGrassMaterialColour),
        }
        self.ui.renderArea.materialColors = self.materialColors
        self.rebuildMaterials()

        self.new()

    def _setupSignals(self):
        self.ui.renderArea.mouseMoved.connect(self.onMouseMoved)
        self.ui.renderArea.mouseScrolled.connect(self.onMouseScrolled)

        QShortcut("+", self).activated.connect(lambda: self.ui.renderArea.camera.setZoom(2))
        QShortcut("-", self).activated.connect(lambda: self.ui.renderArea.camera.setZoom(-2))

    def rebuildMaterials(self):
        """Rebuild the material list.

        Processing Logic:
        ----------------
            - Clear existing items from the material list
            - Loop through all material colors
            - Create image from color and set as icon
            - Format material name as title
            - Create list item with icon and text
            - Add item to material list.
        """
        self.ui.materialList.clear()
        for material, color in self.materialColors.items():
            image = QImage(struct.pack("BBB", color.red(), color.green(), color.blue()) * 16 * 16, 16, 16, QImage.Format_RGB888)
            icon = QIcon(QPixmap(image))
            text = material.name.replace("_", " ").title()
            item = QListWidgetItem(icon, text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, material)  # type: ignore[attr-defined]
            self.ui.materialList.addItem(item)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Loads a resource into the editor.

        Args:
        ----
            filepath: The path to the resource file
            resref: The resource reference
            restype: The resource type
            data: The raw resource data

        Processing Logic:
        ----------------
            - Reads the bwm data from the resource data
            - Sets the loaded bwm on the render area
            - Clears any existing transition items
            - Loops through faces and adds a transition item for each transition
        """
        super().load(filepath, resref, restype, data)

        self._bwm = read_bwm(data)
        self.ui.renderArea.setWalkmeshes([self._bwm])

        def addTransItem(face, edge, transition):
            if transition is not None:
                item = QListWidgetItem(f"Transition to: {transition}")
                item.setData(_TRANS_FACE_ROLE, face)
                item.setData(_TRANS_EDGE_ROLE, edge)
                self.ui.transList.addItem(item)

        self.ui.transList.clear()
        for face in self._bwm.faces:
            addTransItem(face, 1, face.trans1)
            addTransItem(face, 2, face.trans2)
            addTransItem(face, 3, face.trans3)

    def build(self) -> tuple[bytes, bytes]:
        data = bytearray()
        assert self._bwm is not None, assert_with_variable_trace(self._bwm is not None)
        write_bwm(self._bwm, data)
        return bytes(data), b""

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        """Handles mouse movement events in the viewer.

        Args:
        ----
            screen: Vector2 - Current mouse screen position
            delta: Vector2 - Mouse movement since last event
            buttons: set[int] - Currently pressed mouse buttons
            keys: set[int] - Currently pressed keyboard keys

        Processing Logic:
        ----------------
            - Converts mouse position to world and render coordinates
            - Pans/rotates camera if Ctrl + mouse buttons pressed
            - Changes face material if left button pressed
            - Displays coordinates, face index in status bar.
        """
        world: Vector3 = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        worldData: Vector2 = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        assert self._bwm is not None
        face: BWMFace | None = self._bwm.faceAt(world.x, world.y)

        if QtCore.Qt.MouseButton.LeftButton in buttons and QtCore.Qt.Key_Control in keys:  # type: ignore[attr-defined]
            self.ui.renderArea.doCursorLock(screen)
            self.ui.renderArea.camera.nudgePosition(-worldData.x, -worldData.y)
        elif QtCore.Qt.MouseButton.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:  # type: ignore[attr-defined]
            self.ui.renderArea.doCursorLock(screen)
            self.ui.renderArea.camera.nudgeRotation(delta.x / 50)
        elif QtCore.Qt.MouseButton.LeftButton in buttons and face is not None:  # face will be None if user is clicking on nothing/background.
            self.changeFaceMaterial(face)

        coordsText = f"x: {world.x:.2f}, {world.y:.2f}"
        faceText = f', face: {"None" if face is None else self._bwm.faces.index(face)}'

        screen = self.ui.renderArea.toRenderCoords(world.x, world.y)
        xy = f" || x: {screen.x:.2f}, " + f"y: {screen.y:.2f}, "

        self.statusBar().showMessage(coordsText + faceText + xy)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if not delta.y:
            return  # sometimes it'll be zero when holding middlemouse-down.
        if QtCore.Qt.Key_Control in keys:  # type: ignore[reportGeneralTypeIssues, attr-defined]
            sensSetting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoomFactor = calculate_zoom_strength(delta.y, sensSetting)
            self.ui.renderArea.camera.nudgeZoom(zoomFactor)
            self.ui.renderArea.update()  # Trigger a re-render

    def changeFaceMaterial(self, face: BWMFace):
        """Change material of a face.

        Args:
        ----
            face (BWMFace): The face object to change material

        Processing Logic:
        ----------------
            - Check if a face is provided. Perhaps this can be called from an ambiguous/generalized function/event somewhere.
            - Check if the current face material is different than the selected material
            - Assign the selected material to the provided face.
        """
        newMaterial = self.ui.materialList.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)  # type: ignore[attr-defined]
        if face.material != newMaterial:
            face.material = newMaterial

    def onTransitionSelect(self):
        """Select currently highlighted transition in list.

        Processing Logic:
        ----------------
            - Check if a transition is selected in the list
            - If selected, get the selected item and extract the transition data
            - Pass the transition data to the render area to highlight
            - If no item selected, clear any existing highlight.
        """
        if self.ui.transList.currentItem():
            item: QListWidgetItem | None = self.ui.transList.currentItem()
            self.ui.renderArea.setHighlightedTrans(item.data(_TRANS_FACE_ROLE))  # FIXME: no function 'setHighlightedTrans'
        else:
            self.ui.renderArea.setHighlightedTrans(None)
