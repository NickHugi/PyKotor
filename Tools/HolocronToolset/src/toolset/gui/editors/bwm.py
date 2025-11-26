from __future__ import annotations

import struct

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QIcon, QImage, QPixmap
from qtpy.QtWidgets import QListWidgetItem, QShortcut

from pykotor.common.misc import Color
from pykotor.resource.formats.bwm import read_bwm, write_bwm
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from utility.common.geometry import SurfaceMaterial

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.bwm import BWM, BWMFace
    from toolset.data.installation import HTInstallation
    from utility.common.geometry import Vector2, Vector3

_TRANS_FACE_ROLE = Qt.ItemDataRole.UserRole + 1  # type: ignore[attr-defined]
_TRANS_EDGE_ROLE = Qt.ItemDataRole.UserRole + 2  # type: ignore[attr-defined]


def calculate_zoom_strength(delta_y: float, sens_setting: int) -> float:
    m = 0.00202
    b = 1
    factor_in = (m * sens_setting + b)
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

        from toolset.uic.qtpy.editors.bwm import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()

        self._bwm: BWM | None = None

        moduleDesignerSettings = ModuleDesignerSettings()

        def int_to_qcolor(intvalue: int) -> QColor:
            color = Color.from_rgba_integer(intvalue)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

        self.material_colors: dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED: int_to_qcolor(moduleDesignerSettings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: int_to_qcolor(moduleDesignerSettings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: int_to_qcolor(moduleDesignerSettings.dirtMaterialColour),
            SurfaceMaterial.GRASS: int_to_qcolor(moduleDesignerSettings.grassMaterialColour),
            SurfaceMaterial.STONE: int_to_qcolor(moduleDesignerSettings.stoneMaterialColour),
            SurfaceMaterial.WOOD: int_to_qcolor(moduleDesignerSettings.woodMaterialColour),
            SurfaceMaterial.WATER: int_to_qcolor(moduleDesignerSettings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: int_to_qcolor(moduleDesignerSettings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: int_to_qcolor(moduleDesignerSettings.transparentMaterialColour),
            SurfaceMaterial.CARPET: int_to_qcolor(moduleDesignerSettings.carpetMaterialColour),
            SurfaceMaterial.METAL: int_to_qcolor(moduleDesignerSettings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: int_to_qcolor(moduleDesignerSettings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: int_to_qcolor(moduleDesignerSettings.swampMaterialColour),
            SurfaceMaterial.MUD: int_to_qcolor(moduleDesignerSettings.mudMaterialColour),
            SurfaceMaterial.LEAVES: int_to_qcolor(moduleDesignerSettings.leavesMaterialColour),
            SurfaceMaterial.LAVA: int_to_qcolor(moduleDesignerSettings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: int_to_qcolor(moduleDesignerSettings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: int_to_qcolor(moduleDesignerSettings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: int_to_qcolor(moduleDesignerSettings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: int_to_qcolor(moduleDesignerSettings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: int_to_qcolor(moduleDesignerSettings.nonWalkGrassMaterialColour),
        }
        self.ui.renderArea.material_colors = self.material_colors
        self.rebuild_materials()

        self.new()

    def _setup_signals(self) -> None:
        self.ui.renderArea.sig_mouse_moved.connect(self.on_mouse_moved)
        self.ui.renderArea.sig_mouse_scrolled.connect(self.on_mouse_scrolled)

        QShortcut("+", self).activated.connect(lambda: self.ui.renderArea.camera.set_zoom(2))
        QShortcut("-", self).activated.connect(lambda: self.ui.renderArea.camera.set_zoom(-2))

    def rebuild_materials(self):
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
        for material, color in self.material_colors.items():
            image = QImage(struct.pack("BBB", color.red(), color.green(), color.blue()) * 16 * 16, 16, 16, QImage.Format.Format_RGB888)
            icon = QIcon(QPixmap(image))
            text = material.name.replace("_", " ").title()
            item = QListWidgetItem(icon, text)
            item.setData(Qt.ItemDataRole.UserRole, material)  # type: ignore[attr-defined]
            self.ui.materialList.addItem(item)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
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
        self.ui.renderArea.set_walkmeshes([self._bwm])

        def add_trans_item(face: BWMFace, edge: int, transition: int | None):
            if transition is not None:
                item = QListWidgetItem(f"Transition to: {transition}")
                item.setData(_TRANS_FACE_ROLE, face)
                item.setData(_TRANS_EDGE_ROLE, edge)
                self.ui.transList.addItem(item)

        self.ui.transList.clear()
        for face in self._bwm.faces:
            add_trans_item(face, 1, face.trans1)
            add_trans_item(face, 2, face.trans2)
            add_trans_item(face, 3, face.trans3)

    def build(self) -> tuple[bytes, bytes]:
        assert self._bwm is not None
        data = bytearray()
        write_bwm(self._bwm, data)
        return bytes(data), b""

    def on_mouse_moved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
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
        world: Vector3 = self.ui.renderArea.to_world_coords(screen.x, screen.y)
        world_data: Vector2 = self.ui.renderArea.to_world_delta(delta.x, delta.y)
        assert self._bwm is not None
        face: BWMFace | None = self._bwm.faceAt(world.x, world.y)

        if Qt.MouseButton.LeftButton in buttons and Qt.Key.Key_Control in keys:  # type: ignore[attr-defined]
            self.ui.renderArea.do_cursor_lock(screen)
            self.ui.renderArea.camera.nudge_position(-world_data.x, -world_data.y)
        elif Qt.MouseButton.MiddleButton in buttons and Qt.Key.Key_Control in keys:  # type: ignore[attr-defined]
            self.ui.renderArea.do_cursor_lock(screen)
            self.ui.renderArea.camera.nudge_rotation(delta.x / 50)
        elif Qt.MouseButton.LeftButton in buttons and face is not None:  # face will be None if user is clicking on nothing/background.
            self.change_face_material(face)

        coords_text = f"x: {world.x:.2f}, {world.y:.2f}"
        face_text = f', face: {"None" if face is None else self._bwm.faces.index(face)}'

        screen = self.ui.renderArea.to_render_coords(world.x, world.y)
        xy = f" || x: {screen.x:.2f}, " + f"y: {screen.y:.2f}, "

        self.statusBar().showMessage(coords_text + face_text + xy)

    def on_mouse_scrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if not delta.y:
            return  # sometimes it'll be zero when holding middlemouse-down.
        if Qt.Key.Key_Control not in keys:  # pyright: ignore[reportGeneralTypeIssues, attr-defined]
            return
        sens_setting = ModuleDesignerSettings().zoomCameraSensitivity2d
        zoom_factor = calculate_zoom_strength(delta.y, sens_setting)
        self.ui.renderArea.camera.nudge_zoom(zoom_factor)
        self.ui.renderArea.update()  # Trigger a re-render

    def change_face_material(self, face: BWMFace):
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
        new_material = self.ui.materialList.currentItem().data(Qt.ItemDataRole.UserRole)  # type: ignore[attr-defined]
        if face.material == new_material:
            return
        face.material = new_material

    def onTransitionSelect(self):
        if self.ui.transList.currentItem():
            item: QListWidgetItem | None = self.ui.transList.currentItem()
            self.ui.renderArea.setHighlightedTrans(item.data(_TRANS_FACE_ROLE))  # FIXME: no function 'setHighlightedTrans'
        else:
            self.ui.renderArea.setHighlightedTrans(None)
