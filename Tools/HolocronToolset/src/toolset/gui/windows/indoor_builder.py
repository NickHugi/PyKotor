from __future__ import annotations

import json
import math
import shutil
import zipfile

from copy import copy, deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from qtpy import QtCore
from qtpy.QtCore import QPointF, QRectF, QTimer, Qt
from qtpy.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QPixmap, QTransform
from qtpy.QtWidgets import QDialog, QFileDialog, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton, QStatusBar, QWidget

from pykotor.common.geometry import Vector2, Vector3
from pykotor.common.stream import BinaryWriter
from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.data.indoorkit import Kit, load_kits
from toolset.data.indoormap import IndoorMap, IndoorMapRoom
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.indoor_settings import IndoorMapSettings
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from utility.error_handling import assert_with_variable_trace, format_exception_with_variables, universal_simplify_exception
from utility.misc import is_debug_mode
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_file

if TYPE_CHECKING:

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QImage, QKeyEvent, QMouseEvent, QPaintEvent, QWheelEvent
    from qtpy.QtWidgets import (
        QAction,  # pyright: ignore[reportPrivateImportUsage]
        QFormLayout,
    )

    from pykotor.resource.formats.bwm import BWMFace
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from toolset.data.indoorkit import KitComponent, KitComponentHook
    from toolset.data.installation import HTInstallation


class IndoorMapBuilder(QMainWindow):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize indoor builder window.

        Args:
        ----
            parent: QWidget | None - Parent widget or None
            installation: HTInstallation | None - Installation object or None

        Processing Logic:
        ----------------
            - Initialize UI components
            - Set up signal connections
            - Set up keyboard shortcuts
            - Populate kit list
            - Set initial map
            - Refresh window title.
        """
        super().__init__(parent)

        self._installation: HTInstallation | None = installation
        self._kits: list[Kit] = []
        self._map: IndoorMap = IndoorMap()
        self._filepath: str = ""

        from toolset.uic.qtpy.windows.indoor_builder import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_signals()
        self._setup_hotkeys()
        self._setup_kits()
        self._refresh_window_title()

        self.ui.mapRenderer.set_map(self._map)

    def _setup_signals(self):
        """Connect signals to slots.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Connect index changed signals from kit and component selectors to selection changed slots
            - Connect action triggers from menu to method calls
            - Connect mouse events on map renderer to handler methods.
        """
        self.ui.kitSelect.currentIndexChanged.connect(self.on_kit_selected)
        self.ui.componentList.currentItemChanged.connect(self.onComponentSelected)

        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSaveAs.triggered.connect(self.save_as)
        self.ui.actionBuild.triggered.connect(self.buildMap)
        self.ui.actionSettings.triggered.connect(lambda: IndoorMapSettings(self, self._installation, self._map, self._kits).exec())
        self.ui.actionDeleteSelected.triggered.connect(self.delete_selected)
        self.ui.actionDownloadKits.triggered.connect(self.open_kit_downloader)
        self.ui.actionInstructions.triggered.connect(self.show_help_window)

        self.ui.mapRenderer.customContextMenuRequested.connect(self.on_context_menu)
        self.ui.mapRenderer.sig_mouse_moved.connect(self.on_mouse_moved)
        self.ui.mapRenderer.sig_mouse_pressed.connect(self.on_mouse_pressed)
        self.ui.mapRenderer.sig_mouse_scrolled.connect(self.on_mouse_scrolled)
        self.ui.mapRenderer.sig_mouse_double_clicked.connect(self.onMouseDoubleClicked)

    def _setup_hotkeys(self):
        self.ui.actionSave.setShortcut(QKeySequence("Ctrl+S"))
        self.ui.actionOpen.setShortcut(QKeySequence("Ctrl+O"))
        self.ui.actionNew.setShortcut(QKeySequence("Ctrl+N"))
        self.ui.actionBuild.setShortcut(QKeySequence("Ctrl+B"))
        self.ui.actionExit.setShortcut(QKeySequence("Ctrl+Q"))
        self.ui.actionSaveAs.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.ui.actionDeleteSelected.setShortcut(QKeySequence("Del"))
        self.ui.actionSettings.setShortcut(QKeySequence("Ctrl+Alt+S"))

    def _setup_kits(self):
        self.ui.kitSelect.clear()
        self._kits = load_kits("./kits")

        if len(self._kits) == 0:
            noKitPrompt = QMessageBox(
                QMessageBox.Icon.Warning,
                "No Kits Available",
                "No kits were detected, would you like to open the Kit downloader?",
            )
            noKitPrompt.addButton(QMessageBox.StandardButton.Yes)
            noKitPrompt.addButton(QMessageBox.StandardButton.No)
            noKitPrompt.setDefaultButton(QMessageBox.StandardButton.No)

            if noKitPrompt.exec() == QMessageBox.StandardButton.Yes:
                self.open_kit_downloader()

        for kit in self._kits:
            self.ui.kitSelect.addItem(kit.name, kit)

    def _refresh_window_title(self):
        if not self._installation:
            self.setWindowTitle("No installation - Map Builder")
        elif not self._filepath:
            self.setWindowTitle(f"{self._installation.name} - Map Builder")
        else:
            self.setWindowTitle(f"{self._filepath} - {self._installation.name} - Map Builder")

    def _refresh_status_bar(self):
        screen: QPoint = self.ui.mapRenderer.mapFromGlobal(self.cursor().pos())
        world: Vector3 = self.ui.mapRenderer.to_world_coords(screen.x(), screen.y())
        obj: IndoorMapRoom | None = self.ui.mapRenderer.room_under_mouse()

        status_bar: QStatusBar | None = self.statusBar()
        assert isinstance(status_bar, QStatusBar)
        status_bar.showMessage(f'X: {world.x}, Y: {world.y}, Object: {obj.component.name if obj else ""}')

    def show_help_window(self):
        window = HelpWindow(self, "./help/tools/2-mapBuilder.md")
        window.setWindowIcon(self.windowIcon())
        window.show()
        window.activateWindow()

    def save(self):
        self._map.generate_mipmap()
        if not self._filepath:
            self.save_as()
        else:
            BinaryWriter.dump(self._filepath, self._map.write())
            self._refresh_window_title()

    def save_as(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Map", Path(self._filepath).name if self._filepath and self._filepath.strip() else "test.indoor", "Indoor Map File (*.indoor)")
        if not filepath or not filepath.strip():
            return
        BinaryWriter.dump(filepath, self._map.write())
        self._filepath = filepath
        self._refresh_window_title()

    def new(self):
        self._filepath = ""
        self._map.reset()
        self._refresh_window_title()

    def open(self):
        """Opens a file dialog to select and load a map file.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Opens a file dialog to select an indoor map file
            - Attempts to load the selected file and rebuild room connections
            - Sets the filepath and refreshes window title on success
            - Shows an error message on failure.
        """
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Map", "", "Indoor Map File (*.indoor)")
        if filepath and str(filepath).strip():
            try:
                self._map.load(Path(filepath).read_bytes(), self._kits)
                self._map.rebuild_room_connections()
                self._filepath = filepath
                self._refresh_window_title()
            except OSError as e:
                QMessageBox(QMessageBox.Icon.Critical, "Failed to load file", str(universal_simplify_exception(e))).exec()

    def open_kit_downloader(self):
        KitDownloader(self).exec()
        self._setup_kits()

    def buildMap(self):
        path = f"{self._installation.module_path() / self._map.module_id}.mod"

        def task():
            return self._map.build(self._installation, self._kits, path)

        msg = f"You can warp to the game using the code 'warp {self._map.module_id}'. "
        msg += f"Map files can be found in:\n{path}"
        loader = AsyncLoader(self, "Building Map...", task, "Failed to build map.")
        if loader.exec():
            QMessageBox(QMessageBox.Icon.Information, "Map built", msg).exec()

    def delete_selected(self):
        for room in self.ui.mapRenderer.selected_rooms():
            self._map.rooms.remove(room)
        self.ui.mapRenderer.clear_selected_rooms()

    def selected_component(self) -> KitComponent | None:
        currentItem: QListWidgetItem | None = self.ui.componentList.currentItem()
        return None if currentItem is None else currentItem.data(Qt.ItemDataRole.UserRole)

    def set_warp_point(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self._map.warpPoint = Vector3(x, y, z)

    def on_kit_selected(self):
        """Selects a kit and populates component list.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Gets the selected kit from the UI kit selection widget
            - Checks if a kit is selected
            - Clears any existing items from the component list
            - Loops through the components in the selected kit
            - Creates a QListWidgetItem for each component
            - Sets the component as item data
            - Adds the item to the component list.
        """
        kit: Kit = self.ui.kitSelect.currentData()

        if not isinstance(kit, Kit):
            return
        self.ui.componentList.clear()
        for component in kit.components:
            item = QListWidgetItem(component.name)
            item.setData(Qt.ItemDataRole.UserRole, component)
            self.ui.componentList.addItem(item)

    def onComponentSelected(self, item: QListWidgetItem):
        if item is None:
            return
        component: KitComponent = item.data(Qt.ItemDataRole.UserRole)
        self.ui.componentImage.setPixmap(QPixmap.fromImage(component.image))
        self.ui.mapRenderer.set_cursor_component(component)

    def on_mouse_moved(
        self,
        screen: Vector2,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        """Handles events when the mouse is moved in the ui.

        Args:
        ----
            screen: Vector2 - Current screen position
            delta: Vector2 - Change in screen position
            buttons: set[int] - Current pressed buttons
            keys: set[int] - Current pressed keys

        Processing Logic:
        ----------------
            - Refresh status bar
            - Convert screen delta to world delta
            - Pan camera if LMB + CTRL pressed
            - Rotate camera if MMB + CTRL pressed
            - Move selected rooms if LMB pressed
            - Update other room positions based on selected room movement
            - Rebuild room connections.
        """
        self._refresh_status_bar()
        world_delta: Vector2 = self.ui.mapRenderer.to_world_delta(delta.x, delta.y)

        if Qt.MouseButton.LeftButton in buttons and Qt.Key.Key_Control not in keys:  # FIXME: bitwise operations are not membership tests
            # LMB + CTRL
            self.ui.mapRenderer.pan_camera(-world_delta.x, -world_delta.y)
        elif Qt.MouseButton.MiddleButton in buttons and Qt.Key.Key_Control in keys:  # FIXME: bitwise operations are not membership tests
            # MMB + CTRL
            self.ui.mapRenderer.rotate_camera(delta.x / 50)
        elif Qt.MouseButton.LeftButton in buttons:
            # LMB
            rooms: list[IndoorMapRoom] = self.ui.mapRenderer.selected_rooms()
            if not rooms:
                return
            active: IndoorMapRoom = rooms[-1]
            for room in rooms:
                room.position.x += world_delta.x
                room.position.y += world_delta.y
            for room in (
                room
                for room in self._map.rooms
                if room not in rooms
            ):
                hook1, hook2 = self.ui.mapRenderer.get_connected_hooks(active, room)
                if hook1 is not None:
                    assert hook2 is not None, assert_with_variable_trace(hook2 is not None)
                    shift: Vector3 = (
                        room.position
                        - active.hook_position(hook1, world_offset=False)
                        + room.hook_position(hook2, world_offset=False)
                    ) - active.position
                    for snapping in rooms:
                        snapping.position = shift + snapping.position
                        # snapping.position += shift
                    # active.position = room.position - active.hook_position(hook1, False) + room.hook_position(hook2, False)
            self._map.rebuild_room_connections()

    def on_mouse_pressed(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        """Handles mouse press events on the map view.

        Args:
        ----
            screen: Vector2 - Mouse position on screen
            buttons: set[int] - Pressed mouse buttons
            keys: set[int] - Pressed modifier keys

        Processing Logic:
        ----------------
            - Checks if left mouse button and control key are pressed
            - Gets component under cursor and selected component
            - Builds indoor map if component selected
            - Clears cursor and selection if shift not pressed
            - Selects room under mouse if room found
            - Clears selection if no room found
            - Toggles cursor flip if middle mouse button and no control pressed.
        """
        if Qt.MouseButton.LeftButton in buttons and Qt.Key.Key_Control not in keys:  # FIXME: bitwise operations are not membership tests
            if self.ui.mapRenderer.cursor_component is not None:
                component: KitComponent | None = self.selected_component()
                if component is not None:
                    self._build_indoor_map_room_and_refresh(component)
                if Qt.Key.Key_Shift not in keys:
                    self.ui.mapRenderer.set_cursor_component(None)
                    self.ui.componentList.clearSelection()
                    self.ui.componentList.setCurrentItem(None)
            else:
                clear_existing: bool = Qt.Key.Key_Shift not in keys
                room: IndoorMapRoom | None = self.ui.mapRenderer.room_under_mouse()
                if room is not None:
                    self.ui.mapRenderer.select_room(room, clear_existing=clear_existing)
                else:
                    self.ui.mapRenderer.clear_selected_rooms()

        if Qt.MouseButton.MiddleButton in buttons and Qt.Key.Key_Shift not in keys:
            self.ui.mapRenderer.toggle_cursor_flip()

    def _build_indoor_map_room_and_refresh(
        self,
        component: KitComponent,
    ):
        """Builds an indoor map room and refreshes the map.

        Args:
        ----
            component: The component to add to the room.

        Builds an indoor map room:
            - Creates a new IndoorMapRoom object
            - Sets its properties from the cursor properties
            - Adds it to the map's rooms list
        Refreshes the map:
            - Rebuilds the room connections
            - Resets the cursor properties
        """
        room = IndoorMapRoom(
            component,
            self.ui.mapRenderer.cursor_point,
            self.ui.mapRenderer.cursor_rotation,
            flip_x=self.ui.mapRenderer.cursor_flip_x,
            flip_y=self.ui.mapRenderer.cursor_flip_y,
        )
        self._map.rooms.append(room)
        self._map.rebuild_room_connections()
        self.ui.mapRenderer.cursor_rotation = 0.0
        self.ui.mapRenderer.cursor_flip_x = False
        self.ui.mapRenderer.cursor_flip_y = False

    def on_mouse_scrolled(
        self,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        if Qt.Key.Key_Control in keys:
            self.ui.mapRenderer.zoom_in_camera(delta.y / 50)
        else:
            self.ui.mapRenderer.cursor_rotation += math.copysign(5, delta.y)

    def onMouseDoubleClicked(
        self,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        room: IndoorMapRoom | None = self.ui.mapRenderer.room_under_mouse()
        if Qt.MouseButton.LeftButton not in buttons or room is None:
            return
        self.ui.mapRenderer.clear_selected_rooms()
        self.add_connected_to_selection(room)

    def on_context_menu(self, point: QPoint):
        world: Vector3 = self.ui.mapRenderer.to_world_coords(point.x(), point.y())
        menu = QMenu(self)

        warp_set_action: QAction | None = menu.addAction("Set Warp Point")
        assert warp_set_action is not None
        warp_set_action.triggered.connect(lambda: self.set_warp_point(world.x, world.y, world.z))

        menu.popup(self.ui.mapRenderer.mapToGlobal(point))

    def keyPressEvent(
        self,
        e: QKeyEvent,
    ):
        self.ui.mapRenderer.keyPressEvent(e)

    def keyReleaseEvent(
        self,
        e: QKeyEvent,
    ):
        self.ui.mapRenderer.keyReleaseEvent(e)

    def add_connected_to_selection(
        self,
        room: IndoorMapRoom,
    ):
        self.ui.mapRenderer.select_room(room, clear_existing=False)
        for hook_index, _hook in enumerate(room.component.hooks):
            hook: IndoorMapRoom | None = room.hooks[hook_index]
            if hook is None or hook in self.ui.mapRenderer.selected_rooms():
                continue
            self.add_connected_to_selection(hook)


class IndoorMapRenderer(QWidget):
    sig_mouse_moved = QtCore.Signal(object, object, object, object)  # screen coords, screen delta, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when mouse is moved over the widget."""

    sig_mouse_scrolled = QtCore.Signal(object, object, object)  # screen delta, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when mouse is scrolled over the widget."""

    sig_mouse_released = QtCore.Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    sig_mouse_pressed = QtCore.Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is pressed on the widget."""

    sig_mouse_double_clicked = QtCore.Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is double clicked on the widget."""

    def __init__(
        self,
        parent: QWidget,
    ):
        """Initialize the indoor map viewer widget.

        Args:
        ----
            parent (QWidget): Parent widget

        Processing Logic:
        ----------------
            - Initialize the indoor map object
            - Initialize variables to track selected rooms, camera position etc
            - Start the main update loop.
        """
        super().__init__(parent)

        self._map: IndoorMap = IndoorMap()
        self._under_mouse_room: IndoorMapRoom | None = None
        self._selected_rooms: list[IndoorMapRoom] = []

        self._cam_position: Vector2 = Vector2.from_null()
        self._cam_rotation: float = 0.0
        self._cam_scale: float = 1.0
        self.cursor_component: KitComponent | None = None
        self.cursor_point: Vector3 = Vector3.from_null()
        self.cursor_rotation: float = 0.0
        self.cursor_flip_x: bool = False
        self.cursor_flip_y: bool = False

        self._keys_down: set[int] = set()
        self._mouse_down: set[int] = set()
        self._mouse_prev: Vector2 = Vector2.from_null()

        self.hide_magnets: bool = False
        self.highlight_rooms_hover: bool = False

        self._loop()

    def _loop(self):
        """The render loop."""
        self.repaint()
        QTimer.singleShot(33, self._loop)

    def set_map(
        self,
        indoor_map: IndoorMap,
    ):
        self._map = indoor_map

    def set_cursor_component(
        self,
        component: KitComponent | None,
    ):
        self.cursor_component = component

    def select_room(
        self,
        room: IndoorMapRoom,
        *,
        clear_existing: bool,
    ):
        if clear_existing:
            self._selected_rooms.clear()
        if room in self._selected_rooms:
            self._selected_rooms.remove(room)
        self._selected_rooms.append(room)

    def room_under_mouse(self) -> IndoorMapRoom | None:
        return self._under_mouse_room

    def selected_rooms(self) -> list[IndoorMapRoom]:
        return self._selected_rooms

    def clear_selected_rooms(self):
        self._selected_rooms.clear()

    def to_render_coords(
        self,
        x: float,
        y: float,
    ) -> Vector2:
        """Returns a screen-space coordinates coverted from the specified world-space coordinates.

        The origin of the
        screen-space coordinates is the top-left of the WalkmeshRenderer widget.

        Args:
        ----
            x: The world-space X value.
            y: The world-space Y value.

        Returns:
        -------
            A vector representing a point on the widget.
        """
        cos: float = math.cos(self._cam_rotation)
        sin: float = math.sin(self._cam_rotation)
        x -= self._cam_position.x
        y -= self._cam_position.y
        x2: float = (x * cos - y * sin) * self._cam_scale + self.width() / 2
        y2: float = (x * sin + y * cos) * self._cam_scale + self.height() / 2
        return Vector2(x2, y2)

    def to_world_coords(
        self,
        x: float,
        y: float,
    ) -> Vector3:
        """Returns the world-space coordinates converted from the specified screen-space coordinates.

        The Z component is calculated using the X/Y components and
        the walkmesh face the mouse is over. If there is no face underneath
        the mouse, the Z component is set to zero.

        Args:
        ----
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
        -------
            A vector representing a point in the world.
        """
        cos: float = math.cos(-self._cam_rotation)
        sin: float = math.sin(-self._cam_rotation)
        x = (x - self.width() / 2) / self._cam_scale
        y = (y - self.height() / 2) / self._cam_scale
        x2: float = x * cos - y * sin + self._cam_position.x
        y2: float = x * sin + y * cos + self._cam_position.y
        return Vector3(x2, y2, 0)

    def to_world_delta(
        self,
        x: float,
        y: float,
    ) -> Vector2:
        """Returns the coordinates representing a change in world-space.

        This is converted from coordinates representing
        a change in screen-space, such as the delta paramater given in a mouseMove event.

        Args:
        ----
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
        -------
            A vector representing a change in position in the world.
        """
        cos: float = math.cos(-self._cam_rotation)
        sin: float = math.sin(-self._cam_rotation)
        x /= self._cam_scale
        y /= self._cam_scale
        x2: float = x * cos - y * sin
        y2: float = x * sin + y * cos
        return Vector2(x2, y2)

    def get_connected_hooks(
        self,
        room1: IndoorMapRoom,
        room2: IndoorMapRoom,
    ) -> tuple[KitComponentHook | None, KitComponentHook | None]:
        """Get connected hooks between two rooms.

        Args:
        ----
            room1: IndoorMapRoom - The first room
            room2: IndoorMapRoom - The second room

        Returns:
        -------
            tuple - A tuple containing the connected hooks or None if no connection

        Processing Logic:
        ----------------
            - Loop through all hooks in room1 and get their positions
            - Loop through all hooks in room2 and get their positions
            - Check distance between each hook pair and return the closest pair if < 1 unit apart
            - Return a tuple of the connected hooks or None if no connection found.
        """
        hook1: KitComponentHook | None = None
        hook2: KitComponentHook | None = None

        for hook in room1.component.hooks:
            hook_pos: Vector3 = room1.hook_position(hook)
            for other_hook in room2.component.hooks:
                other_hook_pos: Vector3 = room2.hook_position(other_hook)
                distance_2d: float = Vector2.from_vector3(hook_pos).distance(Vector2.from_vector3(other_hook_pos))
                if distance_2d < 1:
                    hook1 = hook
                    hook2 = other_hook

        return hook1, hook2

    def toggle_cursor_flip(self):
        if self.cursor_flip_x is True:
            self.cursor_flip_x = False
            self.cursor_flip_y = True
        elif self.cursor_flip_y is True:
            self.cursor_flip_x = False
            self.cursor_flip_y = False
        else:
            self.cursor_flip_x = True
            self.cursor_flip_y = False

    # region Camera Transformations
    def camera_zoom(self) -> float:
        """Returns the current zoom value of the camera.

        Returns:
        -------
            The camera zoom value.
        """
        return self._cam_scale

    def set_camera_zoom(self, zoom: float,):
        """Sets the camera zoom to the specified value. Values smaller than 1.0 are clamped.

        Args:
        ----
            zoom: Zoom-in value.
        """
        self._cam_scale = max(zoom, 1.0)

    def zoom_in_camera(self, zoom: float,):
        """Changes the camera zoom value by the specified amount.

        This method is a wrapper for set_camera_zoom().

        Args:
        ----
            zoom: The value to increase by.
        """
        self.set_camera_zoom(self._cam_scale + zoom)

    def camera_position(self) -> Vector2:
        """Returns the position of the camera.

        Returns:
        -------
            The camera position vector.
        """
        return copy(self._cam_position)

    def set_camera_position(self, x: float, y: float):
        """Sets the camera position to the specified values.

        Args:
        ----
            x: The new X value.
            y: The new Y value.
        """
        self._cam_position.x = x
        self._cam_position.y = y

    def pan_camera(
        self,
        x: float,
        y: float,
    ):
        """Moves the camera by the specified amount. The movement takes into account both the rotation and zoom of the camera.

        Args:
        ----
            x: Units to move the x coordinate.
            y: Units to move the y coordinate.
        """
        self._cam_position.x += x
        self._cam_position.y += y

    def camera_rotation(self) -> float:  # noqa: F811
        """Returns the current angle of the camera in radians.

        Returns:
        -------
            The camera angle in radians.
        """
        return self._cam_rotation

    def set_camera_rotation(
        self,
        radians: float,
    ):
        """Sets the camera rotation to the specified angle.

        Args:
        ----
            radians: The new camera angle.
        """
        self._cam_rotation = radians

    def rotate_camera(
        self,
        radians: float,
    ):
        """Rotates the camera by the angle specified.

        Args:
        ----
            radians: The angle of rotation to apply to the camera.
        """
        self._cam_rotation += radians

    # endregion

    def _draw_image(  # noqa: PLR0913
        self,
        painter: QPainter,
        image: QImage,
        coords: Vector2,
        rotation: float,
        flip_x: bool,  # noqa: FBT001
        flip_y: bool,  # noqa: FBT001
    ):
        """Draws an image.

        Args:
        ----
            painter: QPainter - Painter to draw on
            image: QImage - Image to draw
            coords: Vector2 - Coordinates to draw image at
            rotation: float - Rotation of image in radians
            flip_x: bool - Whether to flip image horizontally
            flip_y: bool - Whether to flip image vertically

        Processing Logic:
        ----------------
            - Applies transformations like translation, rotation and scaling to the painter based on parameters
            - Draws the image onto the painter using the transformed coordinates
            - Restores original painter transformation after drawing.
        """
        original: QTransform = painter.transform()

        true_width, true_height = image.width(), image.height()
        width, height = image.width() / 10, image.height() / 10

        transform: QTransform = self._apply_transformation()
        transform.translate(coords.x, coords.y)
        transform.rotate(rotation)
        transform.scale(-1.0 if flip_x else 1.0, -1.0 if flip_y else 1.0)
        transform.translate(-width / 2, -height / 2)

        painter.setTransform(transform)

        source = QRectF(0, 0, true_width, true_height)
        rect = QRectF(0, 0, width, height)
        painter.drawImage(rect, image, source)

        painter.setTransform(original)

    def _draw_room_highlight(
        self,
        painter: QPainter,
        room: IndoorMapRoom,
        alpha: int,
    ):
        bwm: BWM = deepcopy(room.component.bwm)
        bwm.flip(room.flip_x, room.flip_y)
        bwm.rotate(room.rotation)
        bwm.translate(*room.position)
        painter.setBrush(QColor(255, 255, 255, alpha))
        painter.setPen(Qt.PenStyle.NoPen)
        for face in bwm.faces:
            path: QPainterPath = self._build_face(face)
            painter.drawPath(path)

    def _draw_circle(
        self,
        painter: QPainter,
        coords: Vector2,
    ):
        ...

    def _draw_spawn_point(
        self,
        painter: QPainter,
        coords: Vector3,
    ):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 255, 0, 127))
        painter.drawEllipse(QPointF(coords.x, coords.y), 1.0, 1.0)

        painter.setPen(QPen(QColor(0, 255, 0), 0.4))
        painter.drawLine(
            QPointF(coords.x, coords.y - 1.0),
            QPointF(coords.x, coords.y + 1.0),
        )
        painter.drawLine(
            QPointF(coords.x - 1.0, coords.y),
            QPointF(coords.x + 1.0, coords.y),
        )

    def _build_face(
        self,
        face: BWMFace,
    ) -> QPainterPath:
        """Returns a QPainterPath for the specified face.

        Args:
        ----
            face: A face used in a walkmesh.

        Returns:
        -------
            A QPainterPath object representing a BWMFace.
        """
        v1 = Vector2(face.v1.x, face.v1.y)
        v2 = Vector2(face.v2.x, face.v2.y)
        v3 = Vector2(face.v3.x, face.v3.y)

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()

        return path

    # region Events
    def paintEvent(
        self,
        e: QPaintEvent,
    ):
        """Draws the map view.

        Args:
        ----
            e: QPaintEvent

        Processing Logic:
        ----------------
            - Maps mouse position to world coordinates
            - Applies transformations
            - Draws background rectangle
            - Draws each room image
            - Draws magnets for empty hooks
            - Draws connections between hooked rooms
            - Draws cursor if present
            - Highlights rooms under mouse or selected.
        """
        transform: QTransform = self._apply_transformation()
        painter = QPainter(self)
        painter.setBrush(QColor(0))
        painter.drawRect(0, 0, self.width(), self.height())
        painter.setTransform(transform)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering, True)

        for room in self._map.rooms:
            self._draw_image(painter, room.component.image, Vector2.from_vector3(room.position), room.rotation, room.flip_x, room.flip_y)

            for hook in [] if self.hide_magnets else room.component.hooks:
                hook_index: int = room.component.hooks.index(hook)
                if room.hooks[hook_index] is not None:
                    continue

                hook_pos: Vector3 = room.hook_position(hook)
                painter.setBrush(QColor("red"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(hook_pos.x, hook_pos.y), 0.5, 0.5)

        for room in self._map.rooms:
            for hook_index, hook in enumerate(room.component.hooks):
                if room.hooks[hook_index] is None:
                    continue
                hook_pos: Vector3 = room.hook_position(hook)
                xd: float = math.cos(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                yd: float = math.sin(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                painter.setPen(QPen(QColor(0, 255, 0), 2 / self._cam_scale))
                painter.drawLine(QPointF(hook_pos.x - xd, hook_pos.y - yd), QPointF(hook_pos.x + xd, hook_pos.y + yd))

        if self.cursor_component:
            painter.setOpacity(0.5)
            self._draw_image(
                painter,
                self.cursor_component.image,
                Vector2.from_vector3(self.cursor_point),
                self.cursor_rotation,
                self.cursor_flip_x,
                self.cursor_flip_y,
            )

        if self._under_mouse_room:
            self._draw_room_highlight(painter, self._under_mouse_room, 50)

        for room in self._selected_rooms:
            self._draw_room_highlight(painter, room, 100)

        self._draw_spawn_point(painter, self._map.warpPoint)

    def _apply_transformation(self) -> QTransform:
        result = QTransform()
        result.translate(self.width() / 2, self.height() / 2)
        result.rotate(math.degrees(self._cam_rotation))
        result.scale(self._cam_scale, self._cam_scale)
        result.translate(-self._cam_position.x, -self._cam_position.y)
        return result

    def wheelEvent(
        self,
        e: QWheelEvent,
    ):
        self.sig_mouse_scrolled.emit(
            Vector2(e.angleDelta().x(), e.angleDelta().y()),
            e.buttons(),
            self._keys_down,
        )

    def mouseMoveEvent(
        self,
        e: QMouseEvent,
    ):
        """Handles mouse move events.

        Args:
        ----
            e: QMouseEvent - Mouse event object

        Processing Logic:
        ----------------
            - Calculates mouse position delta since last event
            - Emits sig_mouse_moved signal with updated position info
            - Converts mouse coords to world coords and sets cursor point
            - Checks if cursor is connected to a room and updates cursor position accordingly
            - Finds room under mouse and sets _under_mouse_room attribute.
        """
        event_pos: QPoint = e.pos()
        coords: Vector2 = Vector2(event_pos.x(), event_pos.y())
        coords_delta: Vector2 = Vector2(
            coords.x - self._mouse_prev.x,
            coords.y - self._mouse_prev.y,
        )
        self._mouse_prev = coords
        self.sig_mouse_moved.emit(coords, coords_delta, self._mouse_down, self._keys_down)

        world: Vector3 = self.to_world_coords(coords.x, coords.y)
        self.cursor_point = world

        if self.cursor_component:
            fake_cursor_room = IndoorMapRoom(
                self.cursor_component,
                self.cursor_point,
                self.cursor_rotation,
                flip_x=self.cursor_flip_x,
                flip_y=self.cursor_flip_y,
            )
            for room in self._map.rooms:
                hook1, hook2 = self.get_connected_hooks(fake_cursor_room, room)
                if hook1 is None:
                    continue
                self.cursor_point = (
                    room.position
                    - fake_cursor_room.hook_position(hook1, world_offset=False)
                    + room.hook_position(hook2, world_offset=False)
                )

        self._under_mouse_room = None
        for room in self._map.rooms:
            walkmesh: BWM = room.walkmesh()
            if not walkmesh.faceAt(world.x, world.y):
                continue
            self._under_mouse_room = room
            break

    def mousePressEvent(
        self,
        e: QMouseEvent,
    ):
        event_mouse_button: int | Qt.MouseButton | None = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.add(event_mouse_button)  # pyright: ignore[reportArgumentType]
        event_pos: QPoint = e.pos()
        coords: Vector2 = Vector2(event_pos.x(), event_pos.y())
        self.sig_mouse_pressed.emit(coords, self._mouse_down, self._keys_down)

    def mouseReleaseEvent(
        self,
        e: QMouseEvent,
    ):
        event_mouse_button: int | Qt.MouseButton | None = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.discard(event_mouse_button)  # pyright: ignore[reportArgumentType]
        event_pos: QPoint = e.pos()
        coords: Vector2 = Vector2(event_pos.x(), event_pos.y())
        self.sig_mouse_released.emit(coords, self._mouse_down, self._keys_down)

    def mouseDoubleClickEvent(
        self,
        e: QMouseEvent,
    ):
        event_mouse_button: int | Qt.MouseButton | None = e.button()
        if event_mouse_button is None:
            return
        mouse_down: set[int] = copy(self._mouse_down)
        mouse_down.add(event_mouse_button)  # Called after release event so we need to manually include it
        self.sig_mouse_double_clicked.emit(Vector2(e.x(), e.y()), mouse_down, self._keys_down)

    def keyPressEvent(
        self,
        e: QKeyEvent,
    ):
        self._keys_down.add(e.key())

    def keyReleaseEvent(
        self,
        e: QKeyEvent,
    ):
        self._keys_down.discard(e.key())

    # endregion


class KitDownloader(QDialog):
    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint,
        )

        from toolset.uic.qtpy.dialogs.indoor_downloader import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self._setup_downloads()

    def _setup_downloads(self):
        """Sets up downloads for kits from update info.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Gets update info from server and parses JSON response
            - Checks if each kit is already downloaded
                - If so, sets button to "Already Downloaded" and disables
                - If not, sets button to "Download"
            - Adds kit name and button to layout in group box
        """
        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(
            use_beta_channel=GlobalSettings().useBetaChannel,
        )
        try:
            if not isinstance(
                update_info_data,
                dict,
            ):
                raise update_info_data  # noqa: TRY301

            for kit_name, kit_dict in update_info_data["kits"].items():
                kit_id = kit_dict["id"]
                kit_path = Path(f"kits/{kit_id}.json")
                if kit_path.is_file():
                    button = QPushButton("Already Downloaded")
                    button.setEnabled(True)
                    local_kit_dict = None
                    try:
                        local_kit_dict = json.loads(kit_path.read_text())
                    except Exception as e:  # noqa: BLE001
                        print(universal_simplify_exception(e), "\n in _setup_downloads for kit update check")
                        button.setText("Missing JSON - click to redownload.")
                        button.setEnabled(True)
                    else:
                        local_kit_version = str(local_kit_dict["version"])
                        retrieved_kit_version = str(kit_dict["version"])
                        if is_remote_version_newer(local_kit_version, retrieved_kit_version) is not False:
                            button.setText("Update Available")
                            button.setEnabled(True)
                else:
                    button = QPushButton("Download")
                button.clicked.connect(
                    lambda _=None,
                    kit_dict=kit_dict,
                    button=button: self._download_button_pressed(button, kit_dict)
                )

                layout: QFormLayout | None = self.ui.groupBox.layout()
                if layout is None:
                    msg = "Kit downloader group box layout is None"
                    raise RuntimeError(msg)  # noqa: TRY301
                layout.addRow(kit_name, button)
        except Exception as e:  # noqa: BLE001
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            err_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                "An unexpected error occurred while setting up the kit downloader.",
                error_msg,
                QMessageBox.StandardButton.Ok,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            err_msg_box.setWindowIcon(self.windowIcon())
            err_msg_box.exec()

    def _download_button_pressed(
        self,
        button: QPushButton,
        info_dict: dict,
    ):
        button.setText("Downloading")
        button.setEnabled(False)

        def task() -> bool:
            try:
                return self._download_kit(info_dict["id"])
            except Exception as e:
                print(format_exception_with_variables(e))
                raise

        if is_debug_mode() and not is_frozen():
            # Run synchronously for debugging
            try:
                task()
                button.setText("Download Complete")
            except Exception as e:  # noqa: BLE001
                # Handle exception or log error
                print(format_exception_with_variables(e, message="Error downloading kit"))
                button.setText("Download Failed")
                button.setEnabled(True)
        else:
            loader = AsyncLoader(self, "Downloading Kit...", task, "Failed to download.")
            if loader.exec():
                button.setText("Download Complete")
            else:
                button.setText("Download Failed")
                button.setEnabled(True)

    def _download_kit(
        self,
        kit_id: str,
    ) -> bool:
        kits_path = Path("kits").resolve()
        kits_path.mkdir(parents=True, exist_ok=True)
        kits_zip_path = Path("kits.zip")
        download_github_file("NickHugi/PyKotor", kits_zip_path, "Tools/HolocronToolset/downloads/kits.zip")

        # Extract the ZIP file
        with zipfile.ZipFile("./kits.zip") as zip_file:
            print(f"Extracting downloaded content to {kits_path}")
            tmp_dir = None
            original_exception = None
            try:
                with TemporaryDirectory() as tmp_dir:
                    tempdir_path = Path(tmp_dir)
                    zip_file.extractall(tmp_dir)
                    src_path = str(tempdir_path / kit_id)
                    this_kit_dst_path = kits_path / kit_id
                    print(f"Copying '{src_path}' to '{this_kit_dst_path}'...")
                    if this_kit_dst_path.is_dir():
                        print(f"Deleting old {kit_id} kit folder/files...")
                        shutil.rmtree(this_kit_dst_path)
                    shutil.copytree(src_path, str(this_kit_dst_path))
                    this_kit_json_filename = f"{kit_id}.json"
                    src_kit_json_path = tempdir_path / this_kit_json_filename
                    if not src_kit_json_path.is_file():
                        msg = f"Kit '{kit_id}' is missing the '{this_kit_json_filename}' file, cannot complete download"
                        print(msg)
                        return False
                    shutil.copy(src_kit_json_path, kits_path / this_kit_json_filename)
            except Exception as original_exception:  # pylint: disable=W0718  # noqa: BLE001, F811
                print(format_exception_with_variables(original_exception))
                return False
            finally:
                try:
                    if tmp_dir and Path(tmp_dir).is_dir():
                        shutil.rmtree(tmp_dir)
                except Exception as exc:  # pylint: disable=W0718  # noqa: BLE001
                    print(format_exception_with_variables(exc))

        if kits_zip_path.is_file():
            kits_zip_path.unlink()
        return True
