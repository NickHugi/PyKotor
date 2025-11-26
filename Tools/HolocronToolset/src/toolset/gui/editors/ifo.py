"""Editor for module info (IFO) files."""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QDoubleSpinBox, QFormLayout, QGroupBox, QLineEdit, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.ifo import IFO, dismantle_ifo, read_ifo
from pykotor.resource.type import ResourceType
from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from toolset.data.installation import HTInstallation


class IFOEditor(Editor):
    """Editor for module info (IFO) files."""

    def __init__(self, parent: QWidget | None = None, installation: HTInstallation | None = None):
        """Initialize the IFO editor."""
        supported = [ResourceType.IFO]
        super().__init__(parent, "Module Info Editor", "ifo", supported, supported, installation)

        self.ifo: IFO | None = None
        self.setup_ui()
        self._setup_menus()
        self._add_help_action()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def setup_ui(self):
        """Set up the UI elements."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Basic Info
        basic_group = QGroupBox("Basic Information")
        basic_form = QFormLayout()

        self.name_edit = QTextEdit()
        self.name_edit.setReadOnly(True)
        self.name_edit_btn = QPushButton("Edit Name")
        self.name_edit_btn.clicked.connect(self.edit_name)
        name_layout = QVBoxLayout()
        name_layout.addWidget(self.name_edit)
        name_layout.addWidget(self.name_edit_btn)
        basic_form.addRow("Module Name:", name_layout)

        self.tag_edit = QLineEdit()
        self.tag_edit.textChanged.connect(self.on_value_changed)
        basic_form.addRow("Tag:", self.tag_edit)

        self.vo_id_edit = QLineEdit()
        self.vo_id_edit.textChanged.connect(self.on_value_changed)
        basic_form.addRow("VO ID:", self.vo_id_edit)

        self.hak_edit = QLineEdit()
        self.hak_edit.textChanged.connect(self.on_value_changed)
        basic_form.addRow("Hak:", self.hak_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setReadOnly(True)
        self.desc_edit_btn = QPushButton("Edit Description")
        self.desc_edit_btn.clicked.connect(self.edit_description)
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(self.desc_edit)
        desc_layout.addWidget(self.desc_edit_btn)
        basic_form.addRow("Description:", desc_layout)

        basic_group.setLayout(basic_form)
        layout.addWidget(basic_group)

        # Entry Point
        entry_group = QGroupBox("Entry Point")
        entry_form = QFormLayout()

        self.entry_resref = QLineEdit()
        self.entry_resref.textChanged.connect(self.on_value_changed)
        entry_form.addRow("Area ResRef:", self.entry_resref)

        self.entry_x = QDoubleSpinBox()
        self.entry_x.setRange(-99999.0, 99999.0)
        self.entry_x.valueChanged.connect(self.on_value_changed)
        entry_form.addRow("Entry X:", self.entry_x)

        self.entry_y = QDoubleSpinBox()
        self.entry_y.setRange(-99999.0, 99999.0)
        self.entry_y.valueChanged.connect(self.on_value_changed)
        entry_form.addRow("Entry Y:", self.entry_y)

        self.entry_z = QDoubleSpinBox()
        self.entry_z.setRange(-99999.0, 99999.0)
        self.entry_z.valueChanged.connect(self.on_value_changed)
        entry_form.addRow("Entry Z:", self.entry_z)

        self.entry_dir = QDoubleSpinBox()
        self.entry_dir.setRange(-3.14159, 3.14159)
        self.entry_dir.valueChanged.connect(self.on_value_changed)
        entry_form.addRow("Entry Direction:", self.entry_dir)

        entry_group.setLayout(entry_form)
        layout.addWidget(entry_group)

        # Time Settings
        time_group = QGroupBox("Time Settings")
        time_form = QFormLayout()

        self.dawn_hour = QSpinBox()
        self.dawn_hour.setRange(0, 23)
        self.dawn_hour.valueChanged.connect(self.on_value_changed)
        time_form.addRow("Dawn Hour:", self.dawn_hour)

        self.dusk_hour = QSpinBox()
        self.dusk_hour.setRange(0, 23)
        self.dusk_hour.valueChanged.connect(self.on_value_changed)
        time_form.addRow("Dusk Hour:", self.dusk_hour)

        self.time_scale = QSpinBox()
        self.time_scale.setRange(0, 100)
        self.time_scale.valueChanged.connect(self.on_value_changed)
        time_form.addRow("Time Scale:", self.time_scale)

        self.start_month = QSpinBox()
        self.start_month.setRange(1, 12)
        self.start_month.valueChanged.connect(self.on_value_changed)
        time_form.addRow("Start Month:", self.start_month)

        self.start_day = QSpinBox()
        self.start_day.setRange(1, 31)
        self.start_day.valueChanged.connect(self.on_value_changed)
        time_form.addRow("Start Day:", self.start_day)

        self.start_hour = QSpinBox()
        self.start_hour.setRange(0, 23)
        self.start_hour.valueChanged.connect(self.on_value_changed)
        time_form.addRow("Start Hour:", self.start_hour)

        self.start_year = QSpinBox()
        self.start_year.setRange(0, 9999)
        self.start_year.valueChanged.connect(self.on_value_changed)
        time_form.addRow("Start Year:", self.start_year)

        self.xp_scale = QSpinBox()
        self.xp_scale.setRange(0, 100)
        self.xp_scale.valueChanged.connect(self.on_value_changed)
        time_form.addRow("XP Scale:", self.xp_scale)

        time_group.setLayout(time_form)
        layout.addWidget(time_group)

        # Scripts
        script_group = QGroupBox("Scripts")
        script_form = QFormLayout()

        self.script_fields: dict[str, QLineEdit] = {}
        for script_name in [
            "on_heartbeat", "on_load", "on_start", "on_enter", "on_leave",
            "on_activate_item", "on_acquire_item", "on_user_defined", "on_unacquire_item",
            "on_player_death", "on_player_dying", "on_player_levelup", "on_player_respawn",
            "on_player_rest", "start_movie"
        ]:
            edit = QLineEdit()
            edit.textChanged.connect(self.on_value_changed)
            self.script_fields[script_name] = edit
            script_form.addRow(script_name.replace("_", " ").title() + ":", edit)

        script_group.setLayout(script_form)
        layout.addWidget(script_group)

    def edit_name(self):
        """Edit module name using LocalizedStringDialog."""
        if not self.ifo or not self._installation:
            return
        dialog = LocalizedStringDialog(self, self._installation, self.ifo.mod_name)
        if dialog.exec():
            self.ifo.mod_name = dialog.locstring
            self.update_ui_from_ifo()

    def edit_description(self):
        """Edit module description using LocalizedStringDialog."""
        if not self.ifo or not self._installation:
            return
        dialog = LocalizedStringDialog(self, self._installation, self.ifo.description)
        if dialog.exec():
            self.ifo.description = dialog.locstring
            self.update_ui_from_ifo()

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Load an IFO file."""
        super().load(filepath, resref, restype, data)
        self.ifo = read_ifo(data)
        self.update_ui_from_ifo()

    def build(self) -> tuple[bytes, bytes]:
        """Build IFO file data."""
        if not self.ifo:
            return b"", b""

        data = bytearray()
        write_gff(dismantle_ifo(self.ifo), data)
        return bytes(data), b""

    def new(self) -> None:
        """Create new IFO file."""
        super().new()
        self.ifo = IFO()
        self.update_ui_from_ifo()

    def update_ui_from_ifo(self) -> None:
        """Update UI elements from IFO data."""
        if not self.ifo or not self._installation:
            return

        # Basic Info
        self.name_edit.setText(self._installation.string(self.ifo.mod_name) or "")
        self.tag_edit.setText(self.ifo.tag)
        self.vo_id_edit.setText(self.ifo.vo_id)
        self.hak_edit.setText(self.ifo.hak)
        self.desc_edit.setText(self._installation.string(self.ifo.description) or "")

        # Entry Point
        self.entry_resref.setText(str(self.ifo.resref))
        self.entry_x.setValue(self.ifo.entry_position.x)
        self.entry_y.setValue(self.ifo.entry_position.y)
        self.entry_z.setValue(self.ifo.entry_position.z)
        self.entry_dir.setValue(self.ifo.entry_direction)

        # Time Settings
        self.dawn_hour.setValue(self.ifo.dawn_hour)
        self.dusk_hour.setValue(self.ifo.dusk_hour)
        self.time_scale.setValue(self.ifo.time_scale)
        self.start_month.setValue(self.ifo.start_month)
        self.start_day.setValue(self.ifo.start_day)
        self.start_hour.setValue(self.ifo.start_hour)
        self.start_year.setValue(self.ifo.start_year)
        self.xp_scale.setValue(self.ifo.xp_scale)

        # Scripts
        for script_name, edit in self.script_fields.items():
            edit.setText(str(getattr(self.ifo, script_name)))

    def on_value_changed(self) -> None:
        """Handle UI value changes."""
        if not self.ifo:
            return

        # Basic Info
        self.ifo.tag = self.tag_edit.text()
        self.ifo.vo_id = self.vo_id_edit.text()
        self.ifo.hak = self.hak_edit.text()

        # Entry Point
        self.ifo.resref = ResRef(self.entry_resref.text())
        self.ifo.entry_position.x = self.entry_x.value()
        self.ifo.entry_position.y = self.entry_y.value()
        self.ifo.entry_position.z = self.entry_z.value()
        self.ifo.entry_direction = self.entry_dir.value()

        # Time Settings
        self.ifo.dawn_hour = self.dawn_hour.value()
        self.ifo.dusk_hour = self.dusk_hour.value()
        self.ifo.time_scale = self.time_scale.value()
        self.ifo.start_month = self.start_month.value()
        self.ifo.start_day = self.start_day.value()
        self.ifo.start_hour = self.start_hour.value()
        self.ifo.start_year = self.start_year.value()
        self.ifo.xp_scale = self.xp_scale.value()

        # Scripts
        for script_name, edit in self.script_fields.items():
            setattr(self.ifo, script_name, ResRef(edit.text()))
