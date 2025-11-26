"""Batch processor for LIP files."""
from __future__ import annotations

import wave

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from qtpy.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from pykotor.resource.formats.lip import LIP, LIPShape, bytes_lip

if TYPE_CHECKING:
    from qtpy.QtWidgets import (
        QWidget,
    )

    from toolset.data.installation import HTInstallation


class BatchLIPProcessor(QDialog):
    """Dialog for batch processing LIP files."""

    def __init__(self, parent: QWidget | None = None, installation: HTInstallation | None = None):
        """Initialize the batch processor."""
        super().__init__(parent)
        self.installation = installation
        self.setWindowTitle("Batch LIP Generator")
        self.setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        # Keep track of files
        self.audio_files: list[Path] = []
        self.output_dir: Optional[Path] = None

    def setup_ui(self):
        """Set up the UI elements."""
        layout = QVBoxLayout(self)

        # Audio files list
        audio_layout = QHBoxLayout()
        self.audio_list = QListWidget()
        self.audio_list.setToolTip("List of WAV files to process")
        audio_layout.addWidget(self.audio_list)

        # Audio file buttons
        button_layout = QVBoxLayout()
        add_audio_btn = QPushButton("Add Files...")
        add_audio_btn.clicked.connect(self.add_audio_files)
        button_layout.addWidget(add_audio_btn)

        remove_audio_btn = QPushButton("Remove Selected")
        remove_audio_btn.clicked.connect(self.remove_audio_file)
        button_layout.addWidget(remove_audio_btn)

        clear_audio_btn = QPushButton("Clear All")
        clear_audio_btn.clicked.connect(self.clear_audio_files)
        button_layout.addWidget(clear_audio_btn)

        audio_layout.addLayout(button_layout)
        layout.addLayout(audio_layout)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        self.output_path.setToolTip("Directory where LIP files will be saved")
        output_layout.addWidget(QLabel("Output Directory:"))
        output_layout.addWidget(self.output_path)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_btn)
        layout.addLayout(output_layout)

        # Process button
        process_btn = QPushButton("Process Files")
        process_btn.clicked.connect(self.process_files)
        layout.addWidget(process_btn)

    def add_audio_files(self):
        """Add WAV files to process."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "", "Audio Files (*.wav)"
        )
        for file in files:
            path = Path(file)
            if path not in self.audio_files:
                self.audio_files.append(path)
                self.audio_list.addItem(path.name)

    def remove_audio_file(self):
        """Remove selected audio file."""
        selected = self.audio_list.selectedItems()
        if not selected:
            return

        for item in selected:
            idx = self.audio_list.row(item)
            self.audio_files.pop(idx)
            self.audio_list.takeItem(idx)

    def clear_audio_files(self):
        """Clear all audio files."""
        self.audio_files.clear()
        self.audio_list.clear()

    def browse_output_dir(self):
        """Select output directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir = Path(dir_path)
            self.output_path.setText(str(self.output_dir))

    def process_files(self):
        """Process all audio files."""
        if not self.audio_files:
            QMessageBox.warning(self, "Error", "No audio files selected")
            return

        if not self.output_dir:
            QMessageBox.warning(self, "Error", "No output directory selected")
            return

        errors = []
        for audio_file in self.audio_files:
            try:
                # Create LIP file
                lip = LIP()

                # Get audio duration
                with wave.open(str(audio_file), "rb") as wav:
                    frames = wav.getnframes()
                    rate = wav.getframerate()
                    duration = frames / float(rate)
                    lip.length = duration

                # Add some basic lip sync - this could be enhanced
                # Currently just adds a few basic shapes evenly spaced
                shapes = [
                    LIPShape.MPB,  # Start with closed mouth
                    LIPShape.AH,   # Open for vowel sound
                    LIPShape.OH,   # Round for O sound
                    LIPShape.MPB,  # Close mouth again
                ]

                interval = duration / (len(shapes) + 1)
                for i, shape in enumerate(shapes, 1):
                    lip.add(interval * i, shape)

                # Save LIP file
                output_path = self.output_dir / f"{audio_file.stem}.lip"
                with open(output_path, "wb") as f:
                    f.write(bytes_lip(lip))

            except Exception as e:
                errors.append(f"{audio_file.name}: {str(e)}")

        if errors:
            QMessageBox.warning(
                self,
                "Errors Occurred",
                "The following errors occurred:\n\n" + "\n".join(errors)
            )
        else:
            QMessageBox.information(
                self,
                "Success",
                f"Successfully processed {len(self.audio_files)} files"
            )
