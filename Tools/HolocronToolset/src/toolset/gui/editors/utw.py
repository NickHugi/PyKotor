from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.utw import UTW, dismantle_utw, read_utw
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.common.module import GFF
    from toolset.data.installation import HTInstallation


class UTWEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize Waypoint Editor window.

        Args:
        ----
            parent: {Parent widget}
            installation: {Installation object}.

        Processing Logic:
        ----------------
            - Initialize UI elements from designer file
            - Set up menu bar and signal connections
            - Load installation data if provided
            - Initialize UTW object
            - Create new empty waypoint by default.
        """
        supported: list[ResourceType] = [ResourceType.UTW]
        super().__init__(parent, "Waypoint Editor", "waypoint", supported, supported, installation)

        from toolset.uic.qtpy.editors.utw import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self._utw = UTW()

        self.new()

    def _setup_signals(self):
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.resrefGenerateButton.clicked.connect(self.generate_resref)
        self.ui.noteChangeButton.clicked.connect(self.change_note)

    def _setup_installation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.set_installation(installation)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        utw: UTW = read_utw(data)
        self._loadUTW(utw)

    def _loadUTW(self, utw: UTW):
        """Load UTW data into UI elements.

        Args:
        ----
            utw (UTW): UTW object to load data from

        Processing Logic:
        ----------------
            - Load basic UTW data like name, tag and resref into line edits
            - Load advanced data like map note flags and text into checkboxes and line edit
            - Load comment text into plain text edit
            - No return, simply loads UI elements from UTW object.
        """
        self._utw: UTW = utw

        # Basic
        self.ui.nameEdit.set_locstring(utw.name)
        self.ui.tagEdit.setText(utw.tag)
        self.ui.resrefEdit.setText(str(utw.resref))

        # Advanced
        self.ui.isNoteCheckbox.setChecked(utw.has_map_note)
        self.ui.noteEnabledCheckbox.setChecked(utw.map_note_enabled)
        self._load_locstring(self.ui.noteEdit, utw.map_note)  # pyright: ignore[reportArgumentType]

        # Comments
        self.ui.commentsEdit.setPlainText(utw.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTW object from UI controls.

        Args:
        ----
            self: The UI object containing controls.

        Returns:
        -------
            data: The serialized UTWSave object as bytes.
            b"": An empty bytes object.

        Processing Logic:
        ----------------
            - Populate UTW object from UI control values
            - Serialize UTW to bytes using GFF format
            - Return bytes and empty bytes
        """
        utw: UTW = deepcopy(self._utw)

        utw.name = self.ui.nameEdit.locstring()
        utw.tag = self.ui.tagEdit.text()
        utw.resref = ResRef(self.ui.resrefEdit.text())
        utw.has_map_note = self.ui.isNoteCheckbox.isChecked()
        utw.map_note_enabled = self.ui.noteEnabledCheckbox.isChecked()
        try:
            utw.map_note = self.ui.noteEdit.locstring  # FIXME:
        except AttributeError:
            utw.map_note = LocalizedString(self.ui.noteEdit.text())  # ALSO FIXME:
        utw.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff: GFF = dismantle_utw(utw)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTW(UTW())

    def change_name(self):
        assert self._installation is not None
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec():
            self._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)  # pyright: ignore[reportArgumentType]

    def change_note(self):
        assert self._installation is not None
        try:
            dialog = LocalizedStringDialog(self, self._installation, self.ui.noteEdit.locstring)  # pyright: ignore[reportArgumentType]
        except AttributeError:
            dialog = LocalizedStringDialog(self, self._installation, self.ui.noteEdit.text())  # pyright: ignore[reportArgumentType]
        if dialog.exec():
            self._load_locstring(self.ui.noteEdit, dialog.locstring)  # pyright: ignore[reportArgumentType]

    def generate_tag(self):
        if not self.ui.resrefEdit.text():
            self.generate_resref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generate_resref(self):
        if self._resname:
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_way_000")
