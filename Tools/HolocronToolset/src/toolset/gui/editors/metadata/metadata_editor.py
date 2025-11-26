"""Unified editor for module metadata (GIT/ARE/IFO) files."""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.editors.are import AREEditor
from toolset.gui.editors.git import GITEditor
from toolset.gui.editors.metadata.ifo_editor import IFOEditor

if TYPE_CHECKING:
    import os

    from toolset.data.installation import HTInstallation


class MetadataEditor(Editor):
    """Unified editor for module metadata files."""

    def __init__(
        self,
        parent: QWidget | None = None,
        installation: HTInstallation | None = None,
        supported: list[ResourceType] = [ResourceType.GIT, ResourceType.ARE, ResourceType.IFO],
    ):
        """Initialize the metadata editor."""
        super().__init__(parent, "Module Metadata Editor", "metadata", supported, supported, installation)

        self.setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        self.git_editor: GITEditor | None = None
        self.are_editor: AREEditor | None = None
        self.ifo_editor: IFOEditor | None = None

    def setup_ui(self):
        """Set up the UI elements."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.tab_widget = QTabWidget()
        QVBoxLayout(central_widget).addWidget(self.tab_widget)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Load a metadata file."""
        super().load(filepath, resref, restype, data)

        if not self._installation:
            return

        # Create editors if needed
        if not self.git_editor and restype == ResourceType.GIT:
            self.git_editor = GITEditor(None, self._installation)
            self.tab_widget.addTab(self.git_editor, "GIT")

        if not self.are_editor and restype == ResourceType.ARE:
            self.are_editor = AREEditor(None, self._installation)
            self.tab_widget.addTab(self.are_editor, "ARE")

        if not self.ifo_editor and restype == ResourceType.IFO:
            self.ifo_editor = IFOEditor(None, self._installation)
            self.tab_widget.addTab(self.ifo_editor, "IFO")

        # Load data into appropriate editor
        if restype == ResourceType.GIT and self.git_editor:
            self.git_editor.load(filepath, resref, restype, data)
            self.tab_widget.setCurrentWidget(self.git_editor)
        elif restype == ResourceType.ARE and self.are_editor:
            self.are_editor.load(filepath, resref, restype, data)
            self.tab_widget.setCurrentWidget(self.are_editor)
        elif restype == ResourceType.IFO and self.ifo_editor:
            self.ifo_editor.load(filepath, resref, restype, data)
            self.tab_widget.setCurrentWidget(self.ifo_editor)

    def build(self) -> tuple[bytes, bytes]:
        """Build metadata file data."""
        # Get data from current editor
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, (GITEditor, AREEditor, IFOEditor)):
            return current_widget.build()
        return b"", b""

    def new(self) -> None:
        """Create new metadata file."""
        super().new()
        # Create new file in current editor
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, (GITEditor, AREEditor, IFOEditor)):
            current_widget.new()
