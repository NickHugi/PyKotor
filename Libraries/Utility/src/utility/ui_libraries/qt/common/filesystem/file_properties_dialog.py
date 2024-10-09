from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from qtpy.QtCore import Qt
from qtpy.QtGui import QFont, QIcon
from qtpy.QtWidgets import QCheckBox, QDialog, QGroupBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget


@dataclass(frozen=True)
class FileProperties:
    name: str
    path: str
    type: str
    size: str
    size_on_disk: str
    created: str
    modified: str
    accessed: str
    mime_type: str
    owner: str
    group: str
    permissions: str
    inode: int
    num_hard_links: int
    device: int
    is_symlink: bool
    symlink_target: str
    md5: str
    sha1: str
    sha256: str
    is_hidden: bool
    is_system: bool
    is_archive: bool
    is_compressed: bool
    is_encrypted: bool
    is_readonly: bool
    is_temporary: bool
    extension: str


class FilePropertiesDialog(QDialog):
    def __init__(self, properties: FileProperties, parent: QWidget | None = None):
        super().__init__(parent)
        self.prop = properties
        self.setWindowTitle(f"Properties - {self.prop.name}")
        self.setMinimumSize(500, 600)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # File icon and name at the top
        top_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon.fromTheme(self.prop.type.lower()).pixmap(64, 64))
        top_layout.addWidget(icon_label)
        name_label = QLabel(self.prop.name)
        name_label.setFont(QFont("Arial", 16, QFont.Bold))
        top_layout.addWidget(name_label)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Tabs for different property categories
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_general_tab(), "General")
        tab_widget.addTab(self.create_security_tab(), "Security")
        tab_widget.addTab(self.create_details_tab(), "Details")
        main_layout.addWidget(tab_widget)

        # OK button at the bottom
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        main_layout.addWidget(ok_button, alignment=Qt.AlignRight)

    def _get_relative_time(self, timestamp: datetime) -> str:
        now = datetime.now().astimezone()
        timestamp = timestamp.replace(tzinfo=now.tzinfo)  # Make timestamp offset-aware
        delta = now - timestamp
        if delta.days > 365:  # noqa: PLR2004
            return f"{delta.days // 365} years ago"
        if delta.days > 30:  # noqa: PLR2004
            return f"{delta.days // 30} months ago"
        if delta.days > 0:
            return f"{delta.days} days ago"
        if delta.seconds > 3600:  # noqa: PLR2004
            return f"{delta.seconds // 3600} hours ago"
        if delta.seconds > 60:  # noqa: PLR2004
            return f"{delta.seconds // 60} minutes ago"
        return "Just now"

    def create_general_tab(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # Type and Location
        type_group = self.create_group_box(
            "Type and Location",
            [
                ("Type:", self.prop.type),
                ("Location:", self.prop.path),
                ("Size:", f"{self.prop.size} ({self.prop.size_on_disk} on disk)"),
            ],
        )
        layout.addWidget(type_group)

        # Dates
        dates_group = self.create_group_box(
            "Dates",
            [
                ("Created:", self.prop.created),
                ("Modified:", self.prop.modified),
                ("Accessed:", self.prop.accessed),
            ],
        )
        layout.addWidget(dates_group)

        # Attributes
        attributes = [
            ("Hidden", self.prop.is_hidden),
            ("Read-only", self.prop.is_readonly),
            ("System", self.prop.is_system),
            ("Archive", self.prop.is_archive),
            ("Temporary", self.prop.is_temporary),
        ]
        attributes_group = self.create_group_box("Attributes", attributes, is_checkbox=True)
        layout.addWidget(attributes_group)

        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_security_tab(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # Owner and Permissions
        security_group = self.create_group_box(
            "Security",
            [
                ("Owner:", self.prop.owner),
                ("Group:", self.prop.group),
                ("Permissions:", self.prop.permissions),
            ],
        )
        layout.addWidget(security_group)
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_details_tab(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # File Details
        details_group = self.create_group_box(
            "File Details",
            [
                ("MIME Type:", self.prop.mime_type),
                ("Extension:", self.prop.extension),
                ("Is Symlink:", "Yes" if self.prop.is_symlink else "No"),
                ("Symlink Target:", self.prop.symlink_target if self.prop.is_symlink else "N/A"),
                ("Inode:", str(self.prop.inode)),
                ("Number of Hard Links:", str(self.prop.num_hard_links)),
                ("Device:", str(self.prop.device)),
            ],
        )
        layout.addWidget(details_group)

        # File Hashes
        hashes_group = self.create_group_box(
            "File Hashes",
            [
                ("MD5:", self.prop.md5),
                ("SHA1:", self.prop.sha1),
                ("SHA256:", self.prop.sha256),
            ],
        )
        layout.addWidget(hashes_group)

        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_group_box(
        self,
        title: str,
        items: list[tuple[str, Any]],
        *,
        is_checkbox: bool = False,
    ) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout()
        for label, value in items:
            if is_checkbox:
                checkbox = QCheckBox(label)
                checkbox.setChecked(value)
                checkbox.setEnabled(False)
                layout.addWidget(checkbox)
            else:
                item_layout = QHBoxLayout()
                label_widget = QLabel(label)
                label_widget.setFont(QFont("Roboto", 9, QFont.Bold))
                item_layout.addWidget(label_widget)
                value_widget = QLabel(value)
                value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
                item_layout.addWidget(value_widget, 1)
                layout.addLayout(item_layout)
        group.setLayout(layout)
        return group
