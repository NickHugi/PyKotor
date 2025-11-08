"""KotorDiff integration window for the Holocron Toolset."""

from __future__ import annotations

import os
import sys
import traceback

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtCore import QSettings, QThread
from qtpy.QtGui import QTextCursor
from qtpy.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kotordiff.app import KotorDiffConfig, run_application  # type: ignore[import-not-found]
from pykotor.extract.installation import Installation

if TYPE_CHECKING:
    from toolset.data.installation import HTInstallation


class KotorDiffThread(QThread):
    """Thread to run KotorDiff operations without blocking the UI."""

    output_signal = QtCore.Signal(str)  # pyright: ignore[reportPrivateImportUsage]
    finished_signal = QtCore.Signal(int)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, config: KotorDiffConfig):
        super().__init__()
        self.config = config

    def run(self):
        """Execute KotorDiff in a separate thread."""
        try:
            # Redirect output to our signal
            original_stdout = sys.stdout
            original_stderr = sys.stderr

            class OutputRedirector:
                def __init__(self, signal):
                    self.signal = signal

                def write(self, text):
                    if text.strip():
                        self.signal.emit(text)

                def flush(self):
                    pass

            sys.stdout = OutputRedirector(self.output_signal)
            sys.stderr = OutputRedirector(self.output_signal)

            # Run KotorDiff with the config object
            exit_code = run_application(self.config)

            # Restore stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr

            self.finished_signal.emit(exit_code)
        except Exception as e:  # noqa: BLE001
            self.output_signal.emit(f"Error: {e.__class__.__name__}: {e}{os.linesep}{traceback.format_exc()}")
            self.finished_signal.emit(1)


class KotorDiffWindow(QMainWindow):
    """Window for running KotorDiff operations."""

    def __init__(
        self,
        parent: QWidget | None = None,
        installations: dict[str, HTInstallation] | None = None,
        active_installation: HTInstallation | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("KotorDiff - Holocron Toolset")
        self.resize(900, 700)

        self._diff_thread: KotorDiffThread | None = None
        self._installations: dict[str, HTInstallation] = installations or {}
        self._active_installation: HTInstallation | None = active_installation
        self._settings = QSettings("HolocronToolset", "KotorDiff")
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Path Selection Group
        path_group = QGroupBox("Paths")
        path_layout = QVBoxLayout()

        # Path 1 (Mine)
        self._setup_path_selector(
            path_layout,
            "Path 1 (Mine/Modified):",
            is_first=True,
            path_num=1,
        )

        # Path 2 (Older)
        self._setup_path_selector(
            path_layout,
            "Path 2 (Older/Vanilla):",
            is_first=False,
            path_num=2,
        )

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # Options Group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        # Compare hashes
        self.compare_hashes_check = QCheckBox("Compare hashes")
        self.compare_hashes_check.setChecked(True)
        options_layout.addWidget(self.compare_hashes_check)

        # TSLPatchData options
        tslpatch_layout = QHBoxLayout()
        self.tslpatchdata_check = QCheckBox("Generate TSLPatchData")
        tslpatch_layout.addWidget(self.tslpatchdata_check)
        self.tslpatchdata_edit = QLineEdit()
        self.tslpatchdata_edit.setPlaceholderText("Path to tslpatchdata folder")
        self.tslpatchdata_edit.setEnabled(False)
        tslpatch_layout.addWidget(self.tslpatchdata_edit)
        self.tslpatchdata_browse_btn = QPushButton("Browse...")
        self.tslpatchdata_browse_btn.setEnabled(False)
        self.tslpatchdata_browse_btn.clicked.connect(lambda: self._browse_directory(self.tslpatchdata_edit))
        tslpatch_layout.addWidget(self.tslpatchdata_browse_btn)
        options_layout.addLayout(tslpatch_layout)

        # INI filename
        ini_layout = QHBoxLayout()
        ini_layout.addWidget(QLabel("INI Filename:"))
        self.ini_name_edit = QLineEdit("changes.ini")
        self.ini_name_edit.setEnabled(False)
        ini_layout.addWidget(self.ini_name_edit)
        options_layout.addLayout(ini_layout)

        self.tslpatchdata_check.toggled.connect(self.tslpatchdata_edit.setEnabled)
        self.tslpatchdata_check.toggled.connect(self.tslpatchdata_browse_btn.setEnabled)
        self.tslpatchdata_check.toggled.connect(self.ini_name_edit.setEnabled)

        # Log level
        log_layout = QHBoxLayout()
        log_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo: QComboBox = QComboBox()
        self.log_level_combo.addItems(["debug", "info", "warning", "error", "critical"])
        self.log_level_combo.setCurrentText("info")
        log_layout.addWidget(self.log_level_combo)
        options_layout.addLayout(log_layout)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Output area
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Diff")
        self.run_btn.clicked.connect(self._run_diff)
        button_layout.addWidget(self.run_btn)

        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.output_text.clear)
        button_layout.addWidget(self.clear_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)

    def _setup_path_selector(
        self,
        parent_layout: QVBoxLayout,
        label_text: str,
        is_first: bool,  # noqa: FBT001
        path_num: int,
    ):
        """Set up a path selector with installation combobox and custom path options."""
        group_layout = QVBoxLayout()

        # Label
        group_layout.addWidget(QLabel(label_text))

        # Radio buttons for selection mode
        radio_layout = QHBoxLayout()
        use_installation_radio = QRadioButton("Use Installation")
        use_custom_path_radio = QRadioButton("Custom Path")

        # Create a button group to ensure these radio buttons are mutually exclusive per path
        button_group = QButtonGroup(self)
        button_group.addButton(use_installation_radio)
        button_group.addButton(use_custom_path_radio)

        # Create the combobox and line edit
        installation_combo = QComboBox()
        installation_combo.setEditable(True)
        path_edit = QLineEdit()
        browse_btn = QPushButton("Browse...")

        # Store widgets for later access
        setattr(self, f"_path{path_num}_button_group", button_group)
        setattr(self, f"_path{path_num}_installation_radio", use_installation_radio)
        setattr(self, f"_path{path_num}_custom_radio", use_custom_path_radio)
        setattr(self, f"_path{path_num}_combo", installation_combo)
        setattr(self, f"_path{path_num}_edit", path_edit)
        setattr(self, f"_path{path_num}_browse", browse_btn)

        # Populate installation combobox
        for name, installation in self._installations.items():
            installation_combo.addItem(name, installation)

        # Set current installation as default for path 1
        if is_first and self._active_installation:
            for i in range(installation_combo.count()):
                if installation_combo.itemData(i) == self._active_installation:
                    installation_combo.setCurrentIndex(i)
                    break

        # Connect radio buttons
        use_installation_radio.toggled.connect(installation_combo.setEnabled)
        use_installation_radio.toggled.connect(lambda checked: path_edit.setDisabled(checked))
        use_installation_radio.toggled.connect(lambda checked: browse_btn.setDisabled(checked))

        # Default to installation mode if we have installations
        if self._installations:
            use_installation_radio.setChecked(True)
            path_edit.setEnabled(False)
            browse_btn.setEnabled(False)
        else:
            use_custom_path_radio.setChecked(True)
            installation_combo.setEnabled(False)

        radio_layout.addWidget(use_installation_radio)
        radio_layout.addWidget(use_custom_path_radio)
        group_layout.addLayout(radio_layout)

        # Installation selector
        group_layout.addWidget(installation_combo)

        # Custom path selector
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(path_edit)
        browse_btn.clicked.connect(lambda: self._browse_path(path_edit))
        custom_layout.addWidget(browse_btn)
        group_layout.addLayout(custom_layout)

        parent_layout.addLayout(group_layout)

    def _get_path_value(self, path_num: int) -> str | None:
        """Get the path value for the given path number."""
        installation_radio = getattr(self, f"_path{path_num}_installation_radio")
        combo = getattr(self, f"_path{path_num}_combo")
        edit = getattr(self, f"_path{path_num}_edit")

        if installation_radio.isChecked():
            # Check if it's a custom text entry or a real installation
            text = combo.currentText().strip()
            if not text:
                return None
            installation = combo.currentData()
            if installation is None:
                # User typed in a custom path
                return text
            return str(installation.path())
        text = edit.text().strip()
        return text if text else None

    def _browse_path(self, line_edit: QLineEdit):
        """Browse for a file or directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not path:
            path = QFileDialog.getOpenFileName(self, "Select File")[0]
        if path:
            line_edit.setText(path)

    def _browse_directory(self, line_edit: QLineEdit):
        """Browse for a directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def _load_settings(self):
        """Load saved settings from QSettings."""
        # Load path selections
        for path_num in [1, 2]:
            use_installation = self._settings.value(f"path{path_num}_use_installation", True, type=bool)
            installation_name = self._settings.value(f"path{path_num}_installation", "")
            custom_path = self._settings.value(f"path{path_num}_custom", "")

            installation_radio = getattr(self, f"_path{path_num}_installation_radio")
            custom_radio = getattr(self, f"_path{path_num}_custom_radio")
            combo = getattr(self, f"_path{path_num}_combo")
            edit = getattr(self, f"_path{path_num}_edit")

            if use_installation:
                installation_radio.setChecked(True)
                # Find and set the installation
                for i in range(combo.count()):
                    if combo.itemText(i) == installation_name:
                        combo.setCurrentIndex(i)
                        break
                else:
                    # If not found, set as text
                    if installation_name:
                        combo.setCurrentText(installation_name)
            else:
                custom_radio.setChecked(True)
                edit.setText(custom_path)

        # Load options
        self.compare_hashes_check.setChecked(self._settings.value("compare_hashes", True, type=bool))
        self.tslpatchdata_check.setChecked(self._settings.value("tslpatchdata_enabled", False, type=bool))
        self.tslpatchdata_edit.setText(self._settings.value("tslpatchdata_path", ""))
        self.ini_name_edit.setText(self._settings.value("ini_filename", "changes.ini"))
        self.log_level_combo.setCurrentText(self._settings.value("log_level", "info"))

    def _save_settings(self):
        """Save current settings to QSettings."""
        # Save path selections
        for path_num in [1, 2]:
            installation_radio = getattr(self, f"_path{path_num}_installation_radio")
            combo = getattr(self, f"_path{path_num}_combo")
            edit = getattr(self, f"_path{path_num}_edit")

            self._settings.setValue(f"path{path_num}_use_installation", installation_radio.isChecked())
            self._settings.setValue(f"path{path_num}_installation", combo.currentText())
            self._settings.setValue(f"path{path_num}_custom", edit.text())

        # Save options
        self._settings.setValue("compare_hashes", self.compare_hashes_check.isChecked())
        self._settings.setValue("tslpatchdata_enabled", self.tslpatchdata_check.isChecked())
        self._settings.setValue("tslpatchdata_path", self.tslpatchdata_edit.text())
        self._settings.setValue("ini_filename", self.ini_name_edit.text())
        self._settings.setValue("log_level", self.log_level_combo.currentText())

    def closeEvent(self, event):  # noqa: N802
        """Handle window close event."""
        self._save_settings()
        super().closeEvent(event)

    def _run_diff(self):
        """Run the KotorDiff operation."""
        # Save settings before running
        self._save_settings()

        # Validate inputs
        path1_str = self._get_path_value(1)
        path2_str = self._get_path_value(2)

        if not path1_str or not path2_str:
            QMessageBox.warning(self, "Invalid Input", "Please provide both Path 1 and Path 2.")
            return

        # Disable run button during execution
        self.run_btn.setEnabled(False)
        self.output_text.clear()
        self.output_text.append("Starting KotorDiff...\n")

        # Convert string paths to Path/Installation objects
        paths: list[Path | Installation] = []
        for path_str in [path1_str, path2_str]:
            path_obj = Path(path_str)
            try:
                # Try to create an Installation object
                installation = Installation(path_obj)
                paths.append(installation)
            except Exception:  # noqa: BLE001
                # Fall back to Path object
                paths.append(path_obj)

        # Build configuration
        config = KotorDiffConfig(
            paths=paths,
            tslpatchdata_path=Path(self.tslpatchdata_edit.text().strip()) if self.tslpatchdata_check.isChecked() and self.tslpatchdata_edit.text().strip() else None,
            ini_filename=self.ini_name_edit.text().strip() or "changes.ini",
            output_log_path=None,
            log_level=self.log_level_combo.currentText(),
            output_mode="full",
            use_colors=False,
            compare_hashes=self.compare_hashes_check.isChecked(),
            use_profiler=False,
            filters=None,
            logging_enabled=True,
        )

        # Run in thread
        self._diff_thread = KotorDiffThread(config)
        self._diff_thread.output_signal.connect(self._append_output)
        self._diff_thread.finished_signal.connect(self._diff_finished)
        self._diff_thread.start()

    def _append_output(self, text: str):
        """Append text to the output area."""
        self.output_text.moveCursor(QTextCursor.End)
        self.output_text.insertPlainText(text)
        self.output_text.moveCursor(QTextCursor.End)

    def _diff_finished(self, exit_code: int):
        """Handle diff completion."""
        self.run_btn.setEnabled(True)

        if exit_code == 0:
            self.output_text.append("\n\nDiff completed successfully!")
            QMessageBox.information(self, "Success", "Diff completed successfully!")
        else:
            self.output_text.append(f"\n\nDiff completed with exit code: {exit_code}")
            QMessageBox.warning(self, "Completed", f"Diff completed with exit code: {exit_code}")
