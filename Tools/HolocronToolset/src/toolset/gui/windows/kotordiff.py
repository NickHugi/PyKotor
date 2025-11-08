"""KotorDiff integration window for the Holocron Toolset."""

from __future__ import annotations

import os
import sys
import traceback

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtCore import QThread
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

from kotordiff.app import run_application  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from toolset.data.installation import HTInstallation


class KotorDiffThread(QThread):
    """Thread to run KotorDiff operations without blocking the UI."""

    output_signal = QtCore.Signal(str)  # pyright: ignore[reportPrivateImportUsage]
    finished_signal = QtCore.Signal(int)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, args: Namespace, parser: ArgumentParser, unknown_args: list[str]):
        super().__init__()
        self.args = args
        self.parser = parser
        self.unknown_args = unknown_args

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

            # Run KotorDiff
            exit_code = run_application(self.args, self.parser, self.unknown_args)

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
        self._setup_ui()

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

        # Path 3 (Yours - Optional for 3-way diff)
        self._setup_path_selector(
            path_layout,
            "Path 3 (Yours/Optional - for 3-way diff):",
            is_first=False,
            path_num=3,
            optional=True,
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

        # Cache options
        cache_layout = QHBoxLayout()
        self.save_results_check = QCheckBox("Save results to cache")
        cache_layout.addWidget(self.save_results_check)
        self.save_results_edit = QLineEdit()
        self.save_results_edit.setPlaceholderText("results.yaml")
        self.save_results_edit.setEnabled(False)
        cache_layout.addWidget(self.save_results_edit)
        options_layout.addLayout(cache_layout)

        self.save_results_check.toggled.connect(self.save_results_edit.setEnabled)

        # Load from cache
        load_cache_layout = QHBoxLayout()
        self.from_results_check = QCheckBox("Load from cache")
        load_cache_layout.addWidget(self.from_results_check)
        self.from_results_edit = QLineEdit()
        self.from_results_edit.setPlaceholderText("results.yaml")
        self.from_results_edit.setEnabled(False)
        load_cache_layout.addWidget(self.from_results_edit)
        self.from_results_browse_btn = QPushButton("Browse...")
        self.from_results_browse_btn.setEnabled(False)
        self.from_results_browse_btn.clicked.connect(lambda: self._browse_file(self.from_results_edit, "YAML Files (*.yaml *.yml)"))
        load_cache_layout.addWidget(self.from_results_browse_btn)
        options_layout.addLayout(load_cache_layout)

        self.from_results_check.toggled.connect(self.from_results_edit.setEnabled)
        self.from_results_check.toggled.connect(self.from_results_browse_btn.setEnabled)

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
        self.close_btn.clicked.connect(self._close_window)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)

    def _setup_path_selector(
        self,
        parent_layout: QVBoxLayout,
        label_text: str,
        is_first: bool,  # noqa: FBT001
        path_num: int,
        *,
        optional: bool = False,
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
        if optional:
            installation_combo.addItem("[None]", None)
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
            installation = combo.currentData()
            if installation is None:  # [None] selected
                return None
            return str(installation.path())
        text = edit.text().strip()
        return text if text else None

    def _close_window(self):
        """Close the window."""
        self.close()

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

    def _browse_file(
        self,
        line_edit: QLineEdit,
        file_filter: str = "All Files (*)",
    ):
        """Browse for a file."""
        path = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)[0]
        if path:
            line_edit.setText(path)

    def _run_diff(self):
        """Run the KotorDiff operation."""
        # Validate inputs
        mine_path = self._get_path_value(1)
        older_path = self._get_path_value(2)
        yours_path = self._get_path_value(3)

        if not mine_path or not older_path:
            QMessageBox.warning(self, "Invalid Input", "Please provide both Path 1 and Path 2.")
            return

        # Disable run button during execution
        self.run_btn.setEnabled(False)
        self.output_text.clear()
        self.output_text.append("Starting KotorDiff...\n")

        # Build arguments
        from argparse import ArgumentParser, Namespace

        parser = ArgumentParser()
        args = Namespace()

        args.mine = mine_path
        args.older = older_path
        args.yours = yours_path
        args.compare_hashes = self.compare_hashes_check.isChecked()
        args.logging_enabled = True
        args.use_profiler = False
        args.log_level = self.log_level_combo.currentText()
        args.output_mode = "full"
        args.no_color = True
        args.output_log = None
        args.filter = None

        # TSLPatchData options
        if self.tslpatchdata_check.isChecked() and self.tslpatchdata_edit.text().strip():
            args.tslpatchdata = self.tslpatchdata_edit.text().strip()
            args.tslpatchdata_path = Path(args.tslpatchdata)
            args.ini = self.ini_name_edit.text().strip() or "changes.ini"
        else:
            args.tslpatchdata = None
            args.ini = "changes.ini"

        # Cache options
        if self.save_results_check.isChecked() and self.save_results_edit.text().strip():
            args.save_results = self.save_results_edit.text().strip()
        else:
            args.save_results = None

        if self.from_results_check.isChecked() and self.from_results_edit.text().strip():
            args.from_results = self.from_results_edit.text().strip()
        else:
            args.from_results = None

        # Run in thread
        self._diff_thread = KotorDiffThread(args, parser, [])
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
