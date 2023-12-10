from __future__ import annotations

import base64
import json
import math
import shutil
import zipfile
from contextlib import suppress
from copy import copy, deepcopy
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import requests
from pykotor.common.geometry import Vector2, Vector3
from pykotor.common.stream import BinaryReader, BinaryWriter
from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QPointF, QRectF, QTimer
from PyQt5.QtGui import (
    QColor,
    QImage,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QTransform,
    QWheelEvent,
)
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QWidget,
)
from toolset.__main__ import is_frozen
from toolset.config import UPDATE_INFO_LINK
from toolset.data.indoorkit import Kit, KitComponent, load_kits
from toolset.data.indoormap import IndoorMap, IndoorMapRoom
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.indoor_settings import IndoorMapSettings
from toolset.gui.windows.help import HelpWindow
from utility.misc import is_debug_mode
from utility.path import Path, PurePath

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.bwm import BWMFace
    from toolset.data.installation import HTInstallation


class IndoorMapBuilder(QMainWindow):
    def __init__(self, parent: QWidget, installation: HTInstallation | None = None):
        """Initialize indoor builder window.

        Args:
        ----
            parent: QWidget - Parent widget
            installation: HTInstallation | None - Installation object or None
        Returns:
            None
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

        self._installation: HTInstallation = installation
        self._kits: list[Kit] = []
        self._map: IndoorMap = IndoorMap()
        self._filepath: str = ""

        from toolset.uic.windows.indoor_builder import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()
        self._setupHotkeys()
        self._setupKits()
        self._refreshWindowTitle()

        self.ui.mapRenderer.setMap(self._map)

    def _setupSignals(self) -> None:
        """Connect signals to slots.

        Args:
        ----
            self: {The class instance}: The class instance
        Returns:
            None: Does not return anything
        Processing Logic:
        ----------------
            - Connect index changed signals from kit and component selectors to selection changed slots
            - Connect action triggers from menu to method calls
            - Connect mouse events on map renderer to handler methods.
        """
        self.ui.kitSelect.currentIndexChanged.connect(self.onKitSelected)
        self.ui.componentList.currentItemChanged.connect(self.onComponentSelected)

        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSaveAs.triggered.connect(self.saveAs)
        self.ui.actionBuild.triggered.connect(self.buildMap)
        self.ui.actionSettings.triggered.connect(lambda: IndoorMapSettings(self, self._installation, self._map, self._kits).exec_())
        self.ui.actionDeleteSelected.triggered.connect(self.deleteSelected)
        self.ui.actionDownloadKits.triggered.connect(self.openKitDownloader)
        self.ui.actionInstructions.triggered.connect(self.showHelpWindow)

        self.ui.mapRenderer.customContextMenuRequested.connect(self.onContextMenu)
        self.ui.mapRenderer.mouseMoved.connect(self.onMouseMoved)
        self.ui.mapRenderer.mousePressed.connect(self.onMousePressed)
        self.ui.mapRenderer.mouseScrolled.connect(self.onMouseScrolled)
        self.ui.mapRenderer.mouseDoubleClicked.connect(self.onMouseDoubleClicked)

    def _setupHotkeys(self) -> None:
        self.ui.actionSave.setShortcut(QKeySequence("Ctrl+S"))
        self.ui.actionOpen.setShortcut(QKeySequence("Ctrl+O"))
        self.ui.actionNew.setShortcut(QKeySequence("Ctrl+N"))
        self.ui.actionBuild.setShortcut(QKeySequence("Ctrl+B"))
        self.ui.actionExit.setShortcut(QKeySequence("Ctrl+Q"))
        self.ui.actionSaveAs.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.ui.actionDeleteSelected.setShortcut(QKeySequence("Del"))
        self.ui.actionSettings.setShortcut(QKeySequence("Ctrl+Alt+S"))

    def _setupKits(self) -> None:
        self.ui.kitSelect.clear()
        self._kits = load_kits("./kits")

        if len(self._kits) == 0:
            noKitPrompt = QMessageBox(
                QMessageBox.Warning, "No Kits Available", "No kits were detected, would you like to open the Kit downloader?",
            )
            noKitPrompt.addButton(QMessageBox.Yes)
            noKitPrompt.addButton(QMessageBox.No)
            noKitPrompt.setDefaultButton(QMessageBox.No)

            if noKitPrompt.exec_() == QMessageBox.Yes:
                self.openKitDownloader()

        for kit in self._kits:
            self.ui.kitSelect.addItem(kit.name, kit)

    def _refreshWindowTitle(self) -> None:
        if self._filepath == "":
            self.setWindowTitle(f"{self._installation.name} - Map Builder")
        else:
            self.setWindowTitle(f"{self._filepath} - {self._installation.name} - Map Builder")

    def _refreshStatusBar(self) -> None:
        screen = self.ui.mapRenderer.mapFromGlobal(self.cursor().pos())
        world = self.ui.mapRenderer.toWorldCoords(screen.x(), screen.y())
        obj = self.ui.mapRenderer.roomUnderMouse()

        self.statusBar().showMessage(f'X: {world.x}, Y: {world.y}, Object: {obj.component.name if obj else ""}')

    def showHelpWindow(self) -> None:
        window = HelpWindow(self, "./help/tools/2-mapBuilder.md")
        window.show()

    def save(self) -> None:
        self._map.generateMinimap()
        if self._filepath == "":
            self.saveAs()
        else:
            BinaryWriter.dump(self._filepath, self._map.write())
            self._refreshWindowTitle()

    def saveAs(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Map", "", "Indoor Map File (*.indoor)")
        if filepath:
            BinaryWriter.dump(filepath, self._map.write())
            self._filepath = filepath
            self._refreshWindowTitle()

    def new(self) -> None:
        self._filepath = ""
        self._map.reset()
        self._refreshWindowTitle()

    def open(self) -> None:
        """Opens a file dialog to select and load a map file.

        Args:
        ----
            self: The object instance

        - Opens a file dialog to select an indoor map file
        - Attempts to load the selected file and rebuild room connections
        - Sets the filepath and refreshes window title on success
        - Shows an error message on failure.
        """
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Map", "", "Indoor Map File (*.indoor)")
        if filepath:
            try:
                self._map.load(BinaryReader.load_file(filepath), self._kits)
                self._map.rebuildRoomConnections()
                self._filepath = filepath
                self._refreshWindowTitle()
            except OSError as e:
                QMessageBox(QMessageBox.Critical, "Failed to load file", str(e)).exec_()

    def openKitDownloader(self) -> None:
        KitDownloader(self).exec_()
        self._setupKits()

    def buildMap(self) -> None:
        path = f"{self._installation.module_path() / self._map.moduleId}.mod"

        def task():
            return self._map.build(self._installation, self._kits, path)

        msg = f"You can warp to the game using the code 'warp {self._map.moduleId}'. "
        msg += f"Map files can be found in:\n{path}"
        loader = AsyncLoader(self, "Building Map...", task, "Failed to build map.")
        if loader.exec_():
            QMessageBox(QMessageBox.Information, "Map built", msg).exec_()

    def deleteSelected(self) -> None:
        for room in self.ui.mapRenderer.selectedRooms():
            self._map.rooms.remove(room)
        self.ui.mapRenderer.clearSelectedRooms()

    def selectedComponent(self) -> KitComponent | None:
        currentItem = self.ui.componentList.currentItem()
        return None if currentItem is None else currentItem.data(QtCore.Qt.UserRole)

    def setWarpPoint(self, x: float, y: float, z: float):
        self._map.warpPoint = Vector3(x, y, z)

    def onKitSelected(self) -> None:
        """Selects a kit and populates component list.

        Args:
        ----
            self: The class instance

        - Gets the selected kit from the UI kit selection widget
        - Checks if a kit is selected
        - Clears any existing items from the component list
        - Loops through the components in the selected kit
        - Creates a QListWidgetItem for each component
        - Sets the component as item data
        - Adds the item to the component list.
        """
        kit: Kit = self.ui.kitSelect.currentData()

        if kit is not None:
            self.ui.componentList.clear()
            for component in kit.components:
                item = QListWidgetItem(component.name)
                item.setData(QtCore.Qt.UserRole, component)
                self.ui.componentList.addItem(item)

    def onComponentSelected(self, item: QListWidgetItem) -> None:
        if item is None:
            return
        component: KitComponent = item.data(QtCore.Qt.UserRole)
        self.ui.componentImage.setPixmap(QPixmap.fromImage(component.image))
        self.ui.mapRenderer.setCursorComponent(component)

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
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
        self._refreshStatusBar()
        worldDelta = self.ui.mapRenderer.toWorldDelta(delta.x, delta.y)

        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control in keys:
            # LMB + CTRL
            self.ui.mapRenderer.panCamera(-worldDelta.x, -worldDelta.y)
        elif QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:
            # MMB + CTRL
            self.ui.mapRenderer.rotateCamera(delta.x / 50)
        elif QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control not in keys:
            # LMB
            rooms = self.ui.mapRenderer.selectedRooms()
            if len(rooms) == 0:
                return
            active = rooms[-1]
            for room in rooms:
                room.position.x += worldDelta.x
                room.position.y += worldDelta.y
            for room in [room for room in self._map.rooms if room not in rooms]:
                hook1, hook2 = self.ui.mapRenderer.getConnectedHooks(active, room)
                if hook1 is not None:
                    shift = (
                        room.position - active.hookPosition(hook1, False) + room.hookPosition(hook2, False)
                    ) - active.position
                    for snapping in rooms:
                        snapping.position = shift + snapping.position
                        # snapping.position += shift
                    # active.position = room.position - active.hookPosition(hook1, False) + room.hookPosition(hook2, False)
            self._map.rebuildRoomConnections()

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
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
        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control not in keys:
            if self.ui.mapRenderer._cursorComponent is not None:
                component = self.selectedComponent()
                if component is not None:
                    self._build_indoor_map_room_and_refresh(component)
                if QtCore.Qt.Key_Shift not in keys:
                    self.ui.mapRenderer.setCursorComponent(None)
                    self.ui.componentList.clearSelection()
                    self.ui.componentList.setCurrentItem(None)
            else:
                clearExisting = QtCore.Qt.Key_Shift not in keys
                room = self.ui.mapRenderer.roomUnderMouse()
                if room:
                    self.ui.mapRenderer.selectRoom(self.ui.mapRenderer.roomUnderMouse(), clearExisting)
                else:
                    self.ui.mapRenderer.clearSelectedRooms()

        if QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control not in keys:
            self.ui.mapRenderer.toggleCursorFlip()

    def _build_indoor_map_room_and_refresh(self, component):
        """Builds an indoor map room and refreshes the map.

        Args:
        ----
            component: The component to add to the room.

        Returns:
        -------
            None
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
            self.ui.mapRenderer._cursorPoint,
            self.ui.mapRenderer._cursorRotation,
            self.ui.mapRenderer._cursorFlipX,
            self.ui.mapRenderer._cursorFlipY,
        )
        self._map.rooms.append(room)
        self._map.rebuildRoomConnections()
        self.ui.mapRenderer._cursorRotation = 0.0
        self.ui.mapRenderer._cursorFlipX = False
        self.ui.mapRenderer._cursorFlipY = False

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        if QtCore.Qt.Key_Control in keys:
            self.ui.mapRenderer.zoomInCamera(delta.y / 50)
        else:
            self.ui.mapRenderer._cursorRotation += math.copysign(5, delta.y)

    def onMouseDoubleClicked(self, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        if QtCore.Qt.LeftButton in buttons and self.ui.mapRenderer.roomUnderMouse():
            self.ui.mapRenderer.clearSelectedRooms()
            self.addConnectedToSelection(self.ui.mapRenderer.roomUnderMouse())

    def onContextMenu(self, point: QPoint) -> None:
        world = self.ui.mapRenderer.toWorldCoords(point.x(), point.y())
        menu = QMenu(self)

        menu.addAction("Set Warp Point").triggered.connect(lambda: self.setWarpPoint(world.x, world.y, world.z))

        menu.popup(self.ui.mapRenderer.mapToGlobal(point))

    def keyPressEvent(self, e: QKeyEvent) -> None:
        self.ui.mapRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        self.ui.mapRenderer.keyReleaseEvent(e)

    def addConnectedToSelection(self, room):
        self.ui.mapRenderer.selectRoom(room, False)
        for hookIndex, _hook in enumerate(room.component.hooks):
            if room.hooks[hookIndex] is not None and room.hooks[hookIndex] not in self.ui.mapRenderer.selectedRooms():
                self.addConnectedToSelection(room.hooks[hookIndex])


class IndoorMapRenderer(QWidget):
    mouseMoved = QtCore.pyqtSignal(object, object, object, object)  # screen coords, screen delta, mouse, keys
    """Signal emitted when mouse is moved over the widget."""

    mouseScrolled = QtCore.pyqtSignal(object, object, object)  # screen delta, mouse, keys
    """Signal emitted when mouse is scrolled over the widget."""

    mouseReleased = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    mousePressed = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is pressed on the widget."""

    mouseDoubleClicked = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is double clicked on the widget."""

    def __init__(self, parent: QWidget):
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
        self._underMouseRoom: IndoorMapRoom | None = None
        self._selectedRooms: list[IndoorMapRoom] = []

        self._camPosition: Vector2 = Vector2.from_null()
        self._camRotation: float = 0.0
        self._camScale = 1.0
        self._cursorComponent: KitComponent | None = None
        self._cursorPoint: Vector3 = Vector3.from_null()
        self._cursorRotation: float = 0.0
        self._cursorFlipX: bool = False
        self._cursorFlipY: bool = False

        self._keysDown: set[int] = set()
        self._mouseDown: set[int] = set()
        self._mousePrev: Vector2 = Vector2.from_null()

        self.hideMagnets: bool = False
        self.highlightRoomsHover: bool = False

        self._loop()

    def _loop(self) -> None:
        """The render loop."""
        self.repaint()
        QTimer.singleShot(33, self._loop)

    def setMap(self, indoorMap: IndoorMap) -> None:
        self._map = indoorMap

    def setCursorComponent(self, component: KitComponent | None) -> None:
        self._cursorComponent = component

    def selectRoom(self, room: IndoorMapRoom, clearExisting: bool) -> None:
        if clearExisting:
            self._selectedRooms.clear()
        if room in self._selectedRooms:
            self._selectedRooms.remove(room)
        self._selectedRooms.append(room)

    def roomUnderMouse(self) -> IndoorMapRoom | None:
        return self._underMouseRoom

    def selectedRooms(self) -> list[IndoorMapRoom]:
        return self._selectedRooms

    def clearSelectedRooms(self) -> None:
        self._selectedRooms.clear()

    def toRenderCoords(self, x, y) -> Vector2:
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
        cos = math.cos(self._camRotation)
        sin = math.sin(self._camRotation)
        x -= self._camPosition.x
        y -= self._camPosition.y
        x2 = (x * cos - y * sin) * self._camScale + self.width() / 2
        y2 = (x * sin + y * cos) * self._camScale + self.height() / 2
        return Vector2(x2, y2)

    def toWorldCoords(self, x, y) -> Vector3:
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
        cos = math.cos(-self._camRotation)
        sin = math.sin(-self._camRotation)
        x = (x - self.width() / 2) / self._camScale
        y = (y - self.height() / 2) / self._camScale
        x2 = x * cos - y * sin + self._camPosition.x
        y2 = x * sin + y * cos + self._camPosition.y
        return Vector3(x2, y2, 0)

    def toWorldDelta(self, x, y) -> Vector2:
        """Returns the coordinates representing a change in world-space.

        This is convereted from coordinates representing
        a change in screen-space, such as the delta paramater given in a mouseMove event.

        Args:
        ----
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
        -------
            A vector representing a change in position in the world.
        """
        cos = math.cos(-self._camRotation)
        sin = math.sin(-self._camRotation)
        x = x / self._camScale
        y = y / self._camScale
        x2 = x * cos - y * sin
        y2 = x * sin + y * cos
        return Vector2(x2, y2)

    def getConnectedHooks(self, room1: IndoorMapRoom, room2: IndoorMapRoom) -> tuple:
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
        hook1 = None
        hook2 = None

        for hook in room1.component.hooks:
            hookPos = room1.hookPosition(hook)
            for otherHook in room2.component.hooks:
                otherHookPos = room2.hookPosition(otherHook)
                distance_2d = Vector2.from_vector3(hookPos).distance(Vector2.from_vector3(otherHookPos))
                if distance_2d < 1:
                    hook1 = hook
                    hook2 = otherHook

        return hook1, hook2

    def toggleCursorFlip(self):
        if self._cursorFlipX is True:
            self._cursorFlipX = False
            self._cursorFlipY = True
        elif self._cursorFlipY is True:
            self._cursorFlipX = False
            self._cursorFlipY = False
        else:
            self._cursorFlipX = True
            self._cursorFlipY = False

    # region Camera Transformations
    def cameraZoom(self) -> float:
        """Returns the current zoom value of the camera.

        Returns
        -------
            The camera zoom value.
        """
        return self._camScale

    def setCameraZoom(self, zoom: float) -> None:
        """Sets the camera zoom to the specified value. Values smaller than 1.0 are clamped.

        Args:
        ----
            zoom: Zoom-in value.
        """
        self._camScale = max(zoom, 1.0)

    def zoomInCamera(self, zoom: float) -> None:
        """Changes the camera zoom value by the specified amount.

        This method is a wrapper for setCameraZoom().

        Args:
        ----
            zoom: The value to increase by.
        """
        self.setCameraZoom(self._camScale + zoom)

    def cameraPosition(self) -> Vector2:
        """Returns the position of the camera.

        Returns
        -------
            The camera position vector.
        """
        return copy(self._camPosition)

    def setCameraPosition(self, x: float, y: float) -> None:
        """Sets the camera position to the specified values.

        Args:
        ----
            x: The new X value.
            y: The new Y value.
        """
        self._camPosition.x = x
        self._camPosition.y = y

    def panCamera(self, x: float, y: float) -> None:
        """Moves the camera by the specified amount. The movement takes into account both the rotation and zoom of the
        camera.

        Args:
        ----
            x: Units to move the x coordinate.
            y: Units to move the y coordinate.
        """
        self._camPosition.x += x
        self._camPosition.y += y

    def cameraRotation(self) -> float:
        """Returns the current angle of the camera in radians.

        Returns
        -------
            The camera angle in radians.
        """
        return self._camRotation

    def setCameraRotation(self, radians: float) -> None:
        """Sets the camera rotation to the specified angle.

        Args:
        ----
            radians: The new camera angle.
        """
        self._camRotation = radians

    def rotateCamera(self, radians: float) -> None:
        """Rotates the camera by the angle specified.

        Args:
        ----
            radians: The angle of rotation to apply to the camera.
        """
        self._camRotation += radians

    # endregion

    def _drawImage(self, painter: QPainter, image: QImage, coords: Vector2, rotation: float, flip_x: bool, flip_y: bool) -> None:
        """Draws an image
        Args:
            painter: QPainter - Painter to draw on
            image: QImage - Image to draw
            coords: Vector2 - Coordinates to draw image at
            rotation: float - Rotation of image in radians
            flip_x: bool - Whether to flip image horizontally
            flip_y: bool - Whether to flip image vertically
        Returns:
            None: Does not return anything
        - Applies transformations like translation, rotation and scaling to the painter based on parameters
        - Draws the image onto the painter using the transformed coordinates
        - Restores original painter transformation after drawing.
        """
        original = painter.transform()

        trueWidth, trueHeight = image.width(), image.height()
        width, height = image.width() / 10, image.height() / 10

        transform = self._apply_transformation()
        transform.translate(coords.x, coords.y)
        transform.rotate(rotation)
        transform.scale(-1.0 if flip_x else 1.0, -1.0 if flip_y else 1.0)
        transform.translate(-width / 2, -height / 2)

        painter.setTransform(transform)

        source = QRectF(0, 0, trueWidth, trueHeight)
        rect = QRectF(0, 0, width, height)
        painter.drawImage(rect, image, source)

        painter.setTransform(original)

    def _drawRoomHighlight(self, painter: QPainter, room: IndoorMapRoom, alpha: int) -> None:
        bwm = deepcopy(room.component.bwm)
        bwm.flip(room.flip_x, room.flip_y)
        bwm.rotate(room.rotation)
        bwm.translate(*room.position)
        painter.setBrush(QColor(255, 255, 255, alpha))
        painter.setPen(QtCore.Qt.NoPen)
        for face in bwm.faces:
            path = self._buildFace(face)
            painter.drawPath(path)

    def _drawCircle(self, painter: QPainter, coords: Vector2):
        ...

    def _drawSpawnPoint(self, painter: QPainter, coords: Vector3):
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QColor(0, 255, 0, 127))
        painter.drawEllipse(QPointF(coords.x, coords.y), 1.0, 1.0)

        painter.setPen(QPen(QColor(0, 255, 0), 0.4))
        painter.drawLine(QPointF(coords.x, coords.y - 1.0), QPointF(coords.x, coords.y + 1.0))
        painter.drawLine(QPointF(coords.x - 1.0, coords.y), QPointF(coords.x + 1.0, coords.y))

    def _buildFace(self, face: BWMFace) -> QPainterPath:
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
    def paintEvent(self, e: QPaintEvent) -> None:
        """Draws the map view
        Args:
            e: QPaintEvent
        Returns:
            None
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
        screen = self.mapFromGlobal(self.cursor().pos())
        world = self.toWorldCoords(screen.x(), screen.y())

        transform = self._apply_transformation()
        painter = QPainter(self)
        painter.setBrush(QColor(0))
        painter.drawRect(0, 0, self.width(), self.height())
        painter.setTransform(transform)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.LosslessImageRendering, True)

        for room in self._map.rooms:
            self._drawImage(
                painter, room.component.image, Vector2.from_vector3(room.position), room.rotation, room.flip_x, room.flip_y,
            )

            for hook in [] if self.hideMagnets else room.component.hooks:
                hookIndex = room.component.hooks.index(hook)
                if room.hooks[hookIndex] is not None:
                    continue

                hookPos = room.hookPosition(hook)
                painter.setBrush(QColor("red"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(QPointF(hookPos.x, hookPos.y), 0.5, 0.5)

        for room in self._map.rooms:
            for hookIndex, hook in enumerate(room.component.hooks):
                if room.hooks[hookIndex] is not None:
                    hookPos = room.hookPosition(hook)
                    xd = math.cos(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                    yd = math.sin(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                    painter.setPen(QPen(QColor(0, 255, 0), 2 / self._camScale))
                    painter.drawLine(QPointF(hookPos.x - xd, hookPos.y - yd), QPointF(hookPos.x + xd, hookPos.y + yd))

        if self._cursorComponent:
            painter.setOpacity(0.5)
            self._drawImage(
                painter,
                self._cursorComponent.image,
                Vector2.from_vector3(self._cursorPoint),
                self._cursorRotation,
                self._cursorFlipX,
                self._cursorFlipY,
            )

        if self._underMouseRoom:
            self._drawRoomHighlight(painter, self._underMouseRoom, 50)

        for room in self._selectedRooms:
            self._drawRoomHighlight(painter, room, 100)

        self._drawSpawnPoint(painter, self._map.warpPoint)

    def _apply_transformation(self):
        result = QTransform()
        result.translate(self.width() / 2, self.height() / 2)
        result.rotate(math.degrees(self._camRotation))
        result.scale(self._camScale, self._camScale)
        result.translate(-self._camPosition.x, -self._camPosition.y)
        return result

    def wheelEvent(self, e: QWheelEvent) -> None:
        self.mouseScrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), e.buttons(), self._keysDown)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        """Handles mouse move events.

        Args:
        ----
            e: QMouseEvent - Mouse event object
        Returns:
            None
        - Calculates mouse position delta since last event
        - Emits mouseMoved signal with updated position info
        - Converts mouse coords to world coords and sets cursor point
        - Checks if cursor is connected to a room and updates cursor position accordingly
        - Finds room under mouse and sets _underMouseRoom attribute.
        """
        coords = Vector2(e.x(), e.y())
        coordsDelta = Vector2(coords.x - self._mousePrev.x, coords.y - self._mousePrev.y)
        self._mousePrev = coords
        self.mouseMoved.emit(coords, coordsDelta, self._mouseDown, self._keysDown)

        world = self.toWorldCoords(coords.x, coords.y)
        self._cursorPoint = world

        if self._cursorComponent:
            fakeCursorRoom = IndoorMapRoom(
                self._cursorComponent, self._cursorPoint, self._cursorRotation, self._cursorFlipX, self._cursorFlipY,
            )
            for room in self._map.rooms:
                hook1, hook2 = self.getConnectedHooks(fakeCursorRoom, room)
                if hook1 is not None:
                    self._cursorPoint = (
                        room.position - fakeCursorRoom.hookPosition(hook1, False) + room.hookPosition(hook2, False)
                    )

        self._underMouseRoom = None
        for room in self._map.rooms:
            walkmesh = room.walkmesh()
            if walkmesh.faceAt(world.x, world.y):
                self._underMouseRoom = room
                break

    def mousePressEvent(self, e: QMouseEvent | None) -> None:
        self._mouseDown.add(e.button())
        coords = Vector2(e.x(), e.y())
        self.mousePressed.emit(coords, self._mouseDown, self._keysDown)

    def mouseReleaseEvent(self, e: QMouseEvent | None) -> None:
        self._mouseDown.discard(e.button())

        coords = Vector2(e.x(), e.y())
        self.mouseReleased.emit(coords, self._mouseDown, self._keysDown)

    def mouseDoubleClickEvent(self, e: QMouseEvent | None) -> None:
        mouseDown = copy(self._mouseDown)
        mouseDown.add(e.button())  # Called after release event so we need to manually include it
        self.mouseDoubleClicked.emit(Vector2(e.x(), e.y()), mouseDown, self._keysDown)

    def keyPressEvent(self, e: QKeyEvent | None) -> None:
        self._keysDown.add(e.key())

    def keyReleaseEvent(self, e: QKeyEvent | None) -> None:
        self._keysDown.discard(e.key())

    # endregion


class KitDownloader(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.dialogs.indoor_downloader import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self._setupDownloads()

    def _setupDownloads(self) -> None:
        """Sets up downloads for kits from update info.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None

        - Gets update info from server and parses JSON response
        - Checks if each kit is already downloaded
            - If so, sets button to "Already Downloaded" and disables
            - If not, sets button to "Download"
        - Adds kit name and button to layout in group box
        """
        file_data = self._get_update_data(UPDATE_INFO_LINK)
        base64_content = file_data["content"]
        decoded_content = base64.b64decode(base64_content)  # Correctly decoding the base64 content
        updateInfoData = json.loads(decoded_content.decode("utf-8"))

        for kitName, kitDict in updateInfoData["kits"].items():
            kitId = kitDict["id"]
            kitPath = Path(f"kits/{kitId}.json")
            if kitPath.exists():
                button = QPushButton("Already Downloaded")
                button.setEnabled(False)
                localKitDict = None
                try:
                    localKitDict = json.loads(BinaryReader.load_file(kitPath))
                except Exception as e:
                    print(repr(e),"\n in _setupDownloads for kit update check")
                    button.setText("Missing JSON - click to redownload.")
                    button.setEnabled(True)
                else:
                    with suppress(Exception):
                        local_kit_version = tuple(map(int, str(localKitDict["version"]).split(".")))
                        retrieved_kit_version = tuple(map(int, str(kitDict["version"]).split(".")))
                        if local_kit_version < retrieved_kit_version:
                            button.setText("Update Available")
                            button.setEnabled(True)

            else:
                button = QPushButton("Download")
            button.clicked.connect(
                lambda _,
                kitDict=kitDict,
                button=button: self._downloadButtonPressed(button, kitDict),
            )

            layout: QFormLayout = self.ui.groupBox.layout()
            layout.addRow(kitName, button)

    def _downloadButtonPressed(self, button: QPushButton, infoDict: dict) -> None:
        button.setText("Downloading")
        button.setEnabled(False)

        def task() -> bool:
            try:
                return self._downloadKit(infoDict["id"])
            except Exception as e:
                print(repr(e))
                raise
        if is_debug_mode() and not is_frozen():
            # Run synchronously for debugging
            try:
                task()
                button.setText("Download Complete")
            except Exception as e:
                # Handle exception or log error
                print(f"Error downloading kit: {e!r}")
                button.setText("Download Failed")
                button.setEnabled(True)
        else:
            loader = AsyncLoader(self, "Downloading Kit...", task, "Failed to download.")
            if loader.exec_():
                button.setText("Download Complete")
            else:
                button.setText("Download Failed")
                button.setEnabled(True)

    def download_file(self, url_or_repo: str, local_path: os.PathLike | str, repo_path=None) -> None:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if repo_path is not None:
            # Construct the API URL for the file in the repository
            owner, repo = PurePath(url_or_repo).parts[-2:]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{PurePath(repo_path).as_posix()}"

            file_info = self._get_update_data(api_url)
            # Check if it's a file and get the download URL
            if file_info["type"] == "file":
                download_url = file_info["download_url"]
            else:
                msg = "The provided repo_path does not point to a file."
                raise ValueError(msg)
        else:
            # Direct URL
            download_url = url_or_repo

        # Download the file
        with requests.get(download_url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with local_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def download_directory(
        self,
        repo: os.PathLike | str,
        local_dir: os.PathLike | str,
        repo_path: os.PathLike | str,
    ) -> None:
        """This method should not be used due to github's api restrictions. Use download_file to get a .zip of the folder instead."""  # noqa: D404
        repo = repo if isinstance(repo, PurePath) else PurePath(repo)
        repo_path = repo_path if isinstance(repo_path, PurePath) else PurePath(repo_path)
        api_url = f"https://api.github.com/repos/{repo.as_posix()}/contents/{repo_path.as_posix()}"
        data = self._get_update_data(api_url)
        for item in data:
            item_path = Path(item["path"])
            local_path = item_path.relative_to("toolset")

            if item["type"] == "file":
                self.download_file(item["download_url"], local_path)
            elif item["type"] == "dir":
                self.download_directory(repo, item_path, local_path)

    def _get_update_data(self, link):
        req = requests.get(link, timeout=15)
        req.raise_for_status()
        return req.json()

    def _downloadKit(self, kitId: str) -> bool:
        kits_path = Path("kits").resolve()
        kits_path.mkdir(parents=True, exist_ok=True)
        kits_zip_path = Path("kits.zip")
        self.download_file("NickHugi/PyKotor", kits_zip_path, "Tools/HolocronToolset/downloads/kits.zip")

        # Extract the ZIP file
        with zipfile.ZipFile("./kits.zip") as zip_file:
            print(f"Extracting downloaded content to {kits_path!s}")
            tempdir = None
            original_exception = None
            try:
                with TemporaryDirectory() as tempdir:
                    tempdir_path = Path(tempdir)
                    zip_file.extractall(tempdir)
                    src_path = str(tempdir_path / kitId)
                    this_kit_dst_path = kits_path / kitId
                    print(f"Copying {src_path} to {this_kit_dst_path}...")
                    if this_kit_dst_path.exists():
                        print(f"Deleting old {kitId} kit folder/files...")
                        shutil.rmtree(this_kit_dst_path)
                    shutil.copytree(src_path, str(this_kit_dst_path))
                    this_kit_json_filename = f"{kitId}.json"
                    src_kit_json_path = tempdir_path / this_kit_json_filename
                    if not src_kit_json_path.exists():
                        msg = f"Kit {kitId} is missing the {this_kit_json_filename} file, cannot complete download"
                        print(msg)
                        return False
                    shutil.copy(src_kit_json_path, kits_path / this_kit_json_filename)
            except Exception as original_exception:  # noqa: BLE001
                print(repr(original_exception))
                return False
            finally:
                try:
                    if tempdir:
                        shutil.rmtree(tempdir)
                except Exception:  # noqa: S110, BLE001
                    pass

        if is_frozen() and kits_zip_path.exists():
            kits_zip_path.unlink()
        return True
