from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QMessageBox, QVBoxLayout

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTRoom
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.widgets.renderer.lyt_editor_widget import LYTEditorWidget
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser
from toolset.gui.widgets.renderer.walkmesh_editor import WalkmeshEditor

if TYPE_CHECKING:
    from pathlib import Path

    from qtpy.QtWidgets import QWidget

    from pykotor.common.module import Module
    from toolset.data.installation import HTInstallation

class LYTEditor(Editor):
    """Main editor class for KotOR module layouts.

    Coordinates between the layout editor widget, walkmesh editor,
    and texture browser components.
    """
    """Layout editor for KotOR modules, integrating functionality from KLE."""

    sig_lyt_updated = Signal(LYT)

    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
        module: Module | None = None
    ):
        supported = [ResourceType.LYT]
        super().__init__(parent, "Layout Editor", "none", supported, supported, installation)

        self._module = module
        self._lyt: Optional[LYT] = None

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create editor components
        self.lyt_editor = LYTEditorWidget(self)
        self.walkmesh_editor = WalkmeshEditor(self)
        self.texture_browser = TextureBrowser(self)

        # Add components to layout
        layout.addWidget(self.lyt_editor)

        self._setup_signals()
        if installation:
            self._setup_installation(installation)

        self.new()

    def _setup_signals(self):
        """Set up signal connections between components."""
        # Connect LYT editor signals
        self.lyt_editor.sig_lyt_updated.connect(self._on_lyt_updated)
        self.lyt_editor.sig_walkmesh_requested.connect(self.walkmesh_editor.show)
        self.lyt_editor.sig_texture_browser_requested.connect(self.texture_browser.show)

        # Connect walkmesh editor signals
        self.walkmesh_editor.sig_walkmesh_updated.connect(self.lyt_editor.update_walkmesh)

        # Connect texture browser signals
        self.texture_browser.sig_texture_selected.connect(self.lyt_editor.apply_texture)

    def _setup_installation(self, installation: HTInstallation):
        """Set up installation-specific components."""
        self._installation = installation

    def new(self):
        """Create a new empty layout."""
        super().new()
        self._lyt = LYT()
        self.lyt_editor.set_lyt(self._lyt)

    def load(self, filepath: str | Path, resref: str, restype: ResourceType, data: bytes):
        """Load a layout from file."""
        super().load(filepath, resref, restype, data)
        try:
            self._lyt = LYT.from_data(data)
            self.lyt_editor.set_lyt(self._lyt)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load layout: {str(e)}")

    def save(self) -> bytes | None:
        """Save the current layout to bytes."""
        if self._lyt is None:
            return None
        # Get latest LYT data from editor
        self._lyt = self.lyt_editor.get_lyt()
        return self._lyt.to_data()

    def _on_lyt_updated(self, lyt: LYT):
        """Handle LYT updates from editor."""
        self._lyt = lyt
        self._has_changes = True
        self.sig_lyt_updated.emit(lyt)

    def add_room(self):
        """Add a new room to the layout."""
        if self._lyt is None:
            return

        room = LYTRoom()
        room.position = Vector3(0, 0, 0)
        room.model = "m00xx_empty"  # Default empty room model

        self._lyt.rooms.append(room)
        self.refresh_ui()
        self._has_changes = True

    def delete_selected_room(self):
        """Delete the currently selected room."""
        if self._lyt is None or self._selected_room is None:
            return

        self._lyt.rooms.remove(self._selected_room)
        self._selected_room = None
        self.refresh_ui()
        self._has_changes = True

    def add_door_hook(self):
        """Add a new door hook to the layout."""
        if self._lyt is None:
            return

        hook = LYTDoorHook()
        hook.position = Vector3(0, 0, 0)
        hook.room_id = len(self._lyt.rooms) - 1 if self._lyt.rooms else 0

        self._lyt.door_hooks.append(hook)
        self.refresh_ui()
        self._has_changes = True

    def delete_selected_door_hook(self):
        """Delete the currently selected door hook."""
        if self._lyt is None or self._selected_door_hook is None:
            return

        self._lyt.door_hooks.remove(self._selected_door_hook)
        self._selected_door_hook = None
        self.refresh_ui()
        self._has_changes = True

    def on_room_selection_changed(self):
        """Handle room selection changes."""
        selected_items = self.ui.roomList.selectedItems()
        if not selected_items:
            self._selected_room = None
            return

        room_index = self.ui.roomList.row(selected_items[0])
        self._selected_room = self._lyt.rooms[room_index] if self._lyt else None
        self.update_room_properties()

    def on_door_hook_selection_changed(self):
        """Handle door hook selection changes."""
        selected_items = self.ui.doorHookList.selectedItems()
        if not selected_items:
            self._selected_door_hook = None
            return

        hook_index = self.ui.doorHookList.row(selected_items[0])
        self._selected_door_hook = self._lyt.door_hooks[hook_index] if self._lyt else None
        self.update_door_hook_properties()

    def refresh_ui(self):
        """Refresh all UI elements."""
        if self._lyt is None:
            return

        # Update room list
        self.ui.roomList.clear()
        for i, room in enumerate(self._lyt.rooms):
            self.ui.roomList.addItem(f"Room {i}: {room.model}")

        # Update door hook list
        self.ui.doorHookList.clear()
        for i, hook in enumerate(self._lyt.door_hooks):
            self.ui.doorHookList.addItem(f"Door Hook {i} (Room {hook.room_id})")

        self.update_room_properties()
        self.update_door_hook_properties()

    def update_room_properties(self):
        """Update the room properties panel."""
        if self._selected_room is None:
            self.ui.roomPropertiesGroup.setEnabled(False)
            return

        self.ui.roomPropertiesGroup.setEnabled(True)
        self.ui.roomModelEdit.setText(self._selected_room.model)
        self.ui.roomPosXSpin.setValue(self._selected_room.position.x)
        self.ui.roomPosYSpin.setValue(self._selected_room.position.y)
        self.ui.roomPosZSpin.setValue(self._selected_room.position.z)

    def update_door_hook_properties(self):
        """Update the door hook properties panel."""
        if self._selected_door_hook is None:
            self.ui.doorHookPropertiesGroup.setEnabled(False)
            return

        self.ui.doorHookPropertiesGroup.setEnabled(True)
        self.ui.doorHookRoomSpin.setValue(self._selected_door_hook.room_id)
        self.ui.doorHookPosXSpin.setValue(self._selected_door_hook.position.x)
        self.ui.doorHookPosYSpin.setValue(self._selected_door_hook.position.y)
        self.ui.doorHookPosZSpin.setValue(self._selected_door_hook.position.z)
from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QMainWindow, QWidget

from pykotor.resource.formats.lyt.lyt_data import LYT
from toolset.gui.widgets.renderer.lyt_editor_widget import LYTEditorWidget

if TYPE_CHECKING:
    from toolset.gui.widgets.renderer.module import ModuleRenderer

class LYTEditorWindow(QMainWindow):
    """Main window/dialog for LYT editing.
    
    Coordinates between the editor widget and module renderer.
    
    Responsibilities:
    - Providing the main editor window/dialog
    - Managing the overall editor state
    - Coordinating between editor widget and module renderer
    - Handling file operations (load/save)
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("LYT Editor")
        
        # Create editor widget
        self.editor_widget = LYTEditorWidget(self)
        self.setCentralWidget(self.editor_widget)
        
        self.setup_menus()
        self.setup_toolbars()
        
    def setup_menus(self):
        """Set up the menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&Save", self.save_lyt)
        file_menu.addAction("Save &As...", self.save_lyt_as)
        file_menu.addSeparator()
        file_menu.addAction("&Close", self.close)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction("&Undo", self.editor_widget.undo_stack.undo)
        edit_menu.addAction("&Redo", self.editor_widget.undo_stack.redo)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction("Show &Grid", self.editor_widget.toggle_grid)
        view_menu.addAction("Show &Walkmesh", self.editor_widget.toggle_walkmesh_visibility)
        
    def setup_toolbars(self):
        """Set up the main toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.addAction("Add Room", self.editor_widget.add_room)
        toolbar.addAction("Add Track", self.editor_widget.add_track)
        toolbar.addAction("Add Obstacle", self.editor_widget.add_obstacle)
        toolbar.addAction("Add Door Hook", self.editor_widget.add_door_hook)
        
    def load_lyt(self, lyt: LYT):
        """Load a LYT file for editing."""
        self.editor_widget.set_lyt(lyt)
        
    def save_lyt(self):
        """Save the current LYT file."""
        self.editor_widget.save_lyt()
        
    def save_lyt_as(self):
        """Save the LYT file with a new name."""
        self.editor_widget.save_lyt_as()
