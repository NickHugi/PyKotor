"""Comprehensive TSLPatchData editor for creating HoloPatcher/TSLPatcher mods."""

from __future__ import annotations

import configparser

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from toolset.data.installation import HTInstallation


class TSLPatchDataEditor(QDialog):
    """Comprehensive editor for TSLPatchData configuration."""

    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
        tslpatchdata_path: Path | None = None,
    ):
        super().__init__(parent)
        from toolset.gui.common.localization import translate as tr
        self.setWindowTitle(tr("TSLPatchData Editor - Create HoloPatcher Mod"))
        self.resize(1400, 900)

        self.installation = installation
        self.tslpatchdata_path = tslpatchdata_path or Path("tslpatchdata")
        self.ini_config = configparser.ConfigParser(delimiters=("="), allow_no_value=True, strict=False, interpolation=None, inline_comment_prefixes=(";", "#"))

        self._setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        if tslpatchdata_path and tslpatchdata_path.exists():
            self._load_existing_config()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header with path selection
        header_layout = QHBoxLayout()
        from toolset.gui.common.localization import translate as tr
        header_layout.addWidget(QLabel(tr("<b>TSLPatchData Folder:</b>")))
        self.path_edit = QLineEdit(str(self.tslpatchdata_path))
        header_layout.addWidget(self.path_edit)
        browse_btn = QPushButton(tr("Browse..."))
        browse_btn.clicked.connect(self._browse_tslpatchdata_path)
        header_layout.addWidget(browse_btn)
        create_btn = QPushButton(tr("Create New"))
        create_btn.clicked.connect(self._create_new_tslpatchdata)
        header_layout.addWidget(create_btn)
        layout.addLayout(header_layout)

        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: File tree
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        from toolset.gui.common.localization import translate as tr
        left_layout.addWidget(QLabel(tr("<b>Files to Package:</b>")))
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels([tr("File"), tr("Type"), tr("Status")])
        self.file_tree.setColumnWidth(0, 300)
        self.file_tree.itemClicked.connect(self._on_file_selected)
        left_layout.addWidget(self.file_tree)

        # File operation buttons
        file_btn_layout = QHBoxLayout()
        from toolset.gui.common.localization import translate as tr
        add_file_btn = QPushButton(tr("Add File"))
        add_file_btn.clicked.connect(self._add_file)
        file_btn_layout.addWidget(add_file_btn)
        remove_file_btn = QPushButton(tr("Remove"))
        remove_file_btn.clicked.connect(self._remove_file)
        file_btn_layout.addWidget(remove_file_btn)
        scan_diff_btn = QPushButton(tr("Scan from Diff"))
        scan_diff_btn.clicked.connect(self._scan_from_diff)
        file_btn_layout.addWidget(scan_diff_btn)
        left_layout.addLayout(file_btn_layout)

        main_splitter.addWidget(left_panel)

        # Right side: Tabs for configuration
        self.config_tabs = QTabWidget()

        # General Settings Tab
        self._create_general_tab()

        # 2DA Memory Tab
        self._create_2da_memory_tab()

        # TLK StrRef Tab
        self._create_tlk_strref_tab()

        # GFF Fields Tab
        self._create_gff_fields_tab()

        # Scripts Tab
        self._create_scripts_tab()

        # INI Preview Tab
        self._create_ini_preview_tab()

        main_splitter.addWidget(self.config_tabs)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)

        layout.addWidget(main_splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        generate_btn = QPushButton("Generate TSLPatchData")
        generate_btn.clicked.connect(self._generate_tslpatchdata)
        button_layout.addWidget(generate_btn)

        preview_btn = QPushButton("Preview INI")
        preview_btn.clicked.connect(self._preview_ini)
        button_layout.addWidget(preview_btn)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._save_configuration)
        button_layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _create_general_tab(self):
        """Create the general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Mod info
        mod_info_group = QGroupBox("Mod Information")
        mod_info_layout = QVBoxLayout()

        # Mod name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Mod Name:"))
        self.mod_name_edit = QLineEdit()
        name_layout.addWidget(self.mod_name_edit)
        mod_info_layout.addLayout(name_layout)

        # Mod author
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Author:"))
        self.mod_author_edit = QLineEdit()
        author_layout.addWidget(self.mod_author_edit)
        mod_info_layout.addLayout(author_layout)

        # Description
        mod_info_layout.addWidget(QLabel("Description:"))
        self.mod_description_edit = QTextEdit()
        self.mod_description_edit.setMaximumHeight(100)
        mod_info_layout.addWidget(self.mod_description_edit)

        mod_info_group.setLayout(mod_info_layout)
        layout.addWidget(mod_info_group)

        # Installation options
        install_options_group = QGroupBox("Installation Options")
        install_options_layout = QVBoxLayout()

        self.install_to_override_check = QCheckBox("Install files to Override folder")
        self.install_to_override_check.setChecked(True)
        install_options_layout.addWidget(self.install_to_override_check)

        self.backup_files_check = QCheckBox("Backup original files")
        self.backup_files_check.setChecked(True)
        install_options_layout.addWidget(self.backup_files_check)

        self.confirm_overwrites_check = QCheckBox("Confirm before overwriting files")
        self.confirm_overwrites_check.setChecked(True)
        install_options_layout.addWidget(self.confirm_overwrites_check)

        install_options_group.setLayout(install_options_layout)
        layout.addWidget(install_options_group)

        layout.addStretch()
        self.config_tabs.addTab(tab, "General")

    def _create_2da_memory_tab(self):
        """Create the 2DA memory tab for tracking 2DA changes."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<b>2DA Memory Tokens:</b>"))
        layout.addWidget(
            QLabel("Track row numbers in 2DA files that will change during installation.")
        )

        # Splitter for 2DA list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: List of 2DA files
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("2DA Files:"))
        self.twoda_list = QListWidget()
        self.twoda_list.itemClicked.connect(self._on_2da_selected)
        left_layout.addWidget(self.twoda_list)

        add_2da_btn = QPushButton("Add 2DA Memory Token")
        add_2da_btn.clicked.connect(self._add_2da_memory)
        left_layout.addWidget(add_2da_btn)

        splitter.addWidget(left_widget)

        # Right: Token details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Memory Tokens:"))
        self.twoda_tokens_tree = QTreeWidget()
        self.twoda_tokens_tree.setHeaderLabels(["Token Name", "Column", "Row Label", "Used By"])
        self.twoda_tokens_tree.setColumnWidth(0, 150)
        self.twoda_tokens_tree.setColumnWidth(1, 100)
        right_layout.addWidget(self.twoda_tokens_tree)

        token_btn_layout = QHBoxLayout()
        add_token_btn = QPushButton("Add Token")
        add_token_btn.clicked.connect(self._add_2da_token)
        token_btn_layout.addWidget(add_token_btn)
        edit_token_btn = QPushButton("Edit Token")
        edit_token_btn.clicked.connect(self._edit_2da_token)
        token_btn_layout.addWidget(edit_token_btn)
        remove_token_btn = QPushButton("Remove Token")
        remove_token_btn.clicked.connect(self._remove_2da_token)
        token_btn_layout.addWidget(remove_token_btn)
        right_layout.addLayout(token_btn_layout)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

        self.config_tabs.addTab(tab, "2DA Memory")

    def _create_tlk_strref_tab(self):
        """Create the TLK StrRef tab for managing dialog.tlk references."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<b>TLK String References:</b>"))
        layout.addWidget(
            QLabel("Manage string references that will be added to dialog.tlk.")
        )

        # TLK string list
        self.tlk_string_tree = QTreeWidget()
        self.tlk_string_tree.setHeaderLabels(["Token Name", "String", "Used By"])
        self.tlk_string_tree.setColumnWidth(0, 150)
        self.tlk_string_tree.setColumnWidth(1, 400)
        layout.addWidget(self.tlk_string_tree)

        # Buttons
        btn_layout = QHBoxLayout()
        add_str_btn = QPushButton("Add TLK String")
        add_str_btn.clicked.connect(self._add_tlk_string)
        btn_layout.addWidget(add_str_btn)
        edit_str_btn = QPushButton("Edit String")
        edit_str_btn.clicked.connect(self._edit_tlk_string)
        btn_layout.addWidget(edit_str_btn)
        remove_str_btn = QPushButton("Remove String")
        remove_str_btn.clicked.connect(self._remove_tlk_string)
        btn_layout.addWidget(remove_str_btn)

        open_tlk_editor_btn = QPushButton("Open TLK Editor")
        open_tlk_editor_btn.clicked.connect(self._open_tlk_editor)
        btn_layout.addWidget(open_tlk_editor_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.config_tabs.addTab(tab, "TLK StrRef")

    def _create_gff_fields_tab(self):
        """Create the GFF fields tab for viewing field modifications."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<b>GFF Field Modifications:</b>"))
        layout.addWidget(
            QLabel("View and edit fields that will be modified in GFF files.")
        )

        # GFF file list
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: File list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Modified GFF Files:"))
        self.gff_file_list = QListWidget()
        self.gff_file_list.itemClicked.connect(self._on_gff_file_selected)
        left_layout.addWidget(self.gff_file_list)
        splitter.addWidget(left_widget)

        # Right: Field modifications
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Field Modifications:"))
        self.gff_fields_tree = QTreeWidget()
        self.gff_fields_tree.setHeaderLabels(["Field Path", "Old Value", "New Value", "Type"])
        self.gff_fields_tree.setColumnWidth(0, 200)
        self.gff_fields_tree.setColumnWidth(1, 150)
        self.gff_fields_tree.setColumnWidth(2, 150)
        right_layout.addWidget(self.gff_fields_tree)

        btn_layout = QHBoxLayout()
        open_gff_editor_btn = QPushButton("Open in GFF Editor")
        open_gff_editor_btn.clicked.connect(self._open_gff_editor)
        btn_layout.addWidget(open_gff_editor_btn)
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

        self.config_tabs.addTab(tab, "GFF Fields")

    def _create_scripts_tab(self):
        """Create the scripts tab for compiled scripts."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<b>Scripts:</b>"))
        layout.addWidget(
            QLabel("Compiled scripts (.ncs) that will be installed.")
        )

        self.script_list = QListWidget()
        layout.addWidget(self.script_list)

        btn_layout = QHBoxLayout()
        add_script_btn = QPushButton("Add Script")
        add_script_btn.clicked.connect(self._add_script)
        btn_layout.addWidget(add_script_btn)
        remove_script_btn = QPushButton("Remove Script")
        remove_script_btn.clicked.connect(self._remove_script)
        btn_layout.addWidget(remove_script_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.config_tabs.addTab(tab, "Scripts")

    def _create_ini_preview_tab(self):
        """Create the INI preview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<b>changes.ini Preview:</b>"))

        self.ini_preview_text = QTextEdit()
        self.ini_preview_text.setReadOnly(True)
        self.ini_preview_text.setFont(self.font())
        layout.addWidget(self.ini_preview_text)

        btn_layout = QHBoxLayout()
        refresh_preview_btn = QPushButton("Refresh Preview")
        refresh_preview_btn.clicked.connect(self._update_ini_preview)
        btn_layout.addWidget(refresh_preview_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.config_tabs.addTab(tab, "INI Preview")

    # Implementation methods
    def _browse_tslpatchdata_path(self):
        """Browse for tslpatchdata folder."""
        path = QFileDialog.getExistingDirectory(self, "Select TSLPatchData Folder")
        if path:
            self.tslpatchdata_path = Path(path)
            self.path_edit.setText(str(self.tslpatchdata_path))
            self._load_existing_config()

    def _create_new_tslpatchdata(self):
        """Create a new tslpatchdata folder structure."""
        path = QFileDialog.getExistingDirectory(self, "Select Location for New TSLPatchData")
        if not path:
            return

        self.tslpatchdata_path = Path(path) / "tslpatchdata"
        self.tslpatchdata_path.mkdir(exist_ok=True)
        self.path_edit.setText(str(self.tslpatchdata_path))

        from toolset.gui.common.localization import translate as tr, trf
        QMessageBox.information(
            self,
            tr("Created"),
            trf("New tslpatchdata folder created at:\n{path}", path=str(self.tslpatchdata_path)),
        )

    def _load_existing_config(self):
        """Load existing TSLPatchData configuration."""
        ini_path = self.tslpatchdata_path / "changes.ini"
        if not ini_path.exists():
            return

        self.ini_config.read(ini_path)
        # TODO: Parse and populate UI from ini_config
        self._update_ini_preview()

    def _add_file(self):
        """Add a file to the package."""
        from toolset.gui.common.localization import translate as tr
        files = QFileDialog.getOpenFileNames(self, tr("Select Files to Add"))[0]
        for file_path in files:
            from toolset.gui.common.localization import translate as tr
            item = QTreeWidgetItem([Path(file_path).name, tr("Added"), tr("New")])
            self.file_tree.addTopLevelItem(item)

    def _remove_file(self):
        """Remove selected file from package."""
        current = self.file_tree.currentItem()
        if current:
            self.file_tree.takeTopLevelItem(self.file_tree.indexOfTopLevelItem(current))

    def _scan_from_diff(self):
        """Scan files from KotorDiff results."""
        from toolset.gui.common.localization import translate as tr
        QMessageBox.information(
            self,
            tr("Scan from Diff"),
            tr("This will scan a KotorDiff results file and automatically populate files.\n\nNot yet implemented."),
        )

    def _on_file_selected(self, item):
        """Handle file selection in tree."""
        # TODO: Update details based on selected file

    def _add_2da_memory(self):
        """Add a new 2DA memory tracking entry."""
        # TODO: Show dialog to add 2DA

    def _on_2da_selected(self, item):
        """Handle 2DA file selection."""
        # TODO: Load and display tokens for selected 2DA

    def _add_2da_token(self):
        """Add a memory token for the selected 2DA."""
        # TODO: Show dialog to add token

    def _edit_2da_token(self):
        """Edit selected memory token."""
        # TODO: Show edit dialog

    def _remove_2da_token(self):
        """Remove selected memory token."""
        current = self.twoda_tokens_tree.currentItem()
        if current:
            index = self.twoda_tokens_tree.indexOfTopLevelItem(current)
            self.twoda_tokens_tree.takeTopLevelItem(index)

    def _add_tlk_string(self):
        """Add a TLK string reference."""
        # TODO: Show dialog to add string

    def _edit_tlk_string(self):
        """Edit selected TLK string."""
        # TODO: Show edit dialog

    def _remove_tlk_string(self):
        """Remove selected TLK string."""
        current = self.tlk_string_tree.currentItem()
        if current:
            index = self.tlk_string_tree.indexOfTopLevelItem(current)
            self.tlk_string_tree.takeTopLevelItem(index)

    def _open_tlk_editor(self):
        """Open the TLK editor for the installation."""
        if self.installation:
            from pykotor.common.stream import BinaryReader
            from pykotor.resource.type import ResourceType
            from toolset.utils.window import openResourceEditor

            tlk_path = self.installation.path() / "dialog.tlk"
            if tlk_path.is_file():
                openResourceEditor(
                    tlk_path,
                    "dialog",
                    ResourceType.TLK,
                    BinaryReader.load_file(tlk_path),
                    self.installation,
                    self,
                )
            else:
                from toolset.gui.common.localization import translate as tr
                QMessageBox.warning(self, tr("Not Found"), tr("dialog.tlk not found in installation."))
        else:
            QMessageBox.warning(self, tr("No Installation"), tr("No installation loaded."))

    def _on_gff_file_selected(self, item):
        """Handle GFF file selection."""
        # TODO: Load and display field modifications

    def _open_gff_editor(self):
        """Open GFF editor for selected file."""
        # TODO: Open selected GFF in editor

    def _add_script(self):
        """Add a compiled script."""
        from toolset.gui.common.localization import translate as tr
        files = QFileDialog.getOpenFileNames(self, tr("Select Scripts (.ncs)"), "", "Scripts (*.ncs)")[0]
        for file_path in files:
            self.script_list.addItem(Path(file_path).name)

    def _remove_script(self):
        """Remove selected script."""
        current = self.script_list.currentItem()
        if current:
            self.script_list.takeItem(self.script_list.row(current))

    def _update_ini_preview(self):
        """Update the INI preview."""
        # Generate preview from current configuration
        preview_lines = []
        preview_lines.append("[settings]")
        preview_lines.append(f"modname={self.mod_name_edit.text() or 'My Mod'}")
        preview_lines.append(f"author={self.mod_author_edit.text() or 'Unknown'}")
        preview_lines.append("")

        # TODO: Add actual configuration sections
        preview_lines.append("[GFF files]")
        preview_lines.append("; Files to be patched")
        preview_lines.append("")

        preview_lines.append("[2DAMEMORY]")
        preview_lines.append("; 2DA memory tokens")
        preview_lines.append("")

        preview_lines.append("[TLKList]")
        preview_lines.append("; TLK string additions")
        preview_lines.append("")

        self.ini_preview_text.setPlainText("\n".join(preview_lines))

    def _preview_ini(self):
        """Show INI preview in current tab."""
        self.config_tabs.setCurrentIndex(self.config_tabs.indexOf(
            self.config_tabs.widget(self.config_tabs.count() - 1)
        ))
        self._update_ini_preview()

    def _save_configuration(self):
        """Save the configuration to changes.ini."""
        ini_path = self.tslpatchdata_path / "changes.ini"

        # TODO: Actually build and save the INI file
        self._update_ini_preview()

        with open(ini_path, "w") as f:
            f.write(self.ini_preview_text.toPlainText())

        from toolset.gui.common.localization import translate as tr, trf
        QMessageBox.information(
            self,
            tr("Saved"),
            trf("Configuration saved to:\n{path}", path=str(ini_path)),
        )

    def _generate_tslpatchdata(self):
        """Generate the complete TSLPatchData bundle."""
        if not self.tslpatchdata_path.exists():
            self.tslpatchdata_path.mkdir(parents=True)

        # Save configuration
        self._save_configuration()

        # TODO: Copy files to tslpatchdata folder
        # TODO: Generate namespaces.ini
        # TODO: Create installer executable

        from toolset.gui.common.localization import translate as tr, trf
        QMessageBox.information(
            self,
            tr("Generated"),
            trf("TSLPatchData generated at:\n{path}\n\nYou can now distribute this folder with HoloPatcher/TSLPatcher.", path=str(self.tslpatchdata_path)),
        )

