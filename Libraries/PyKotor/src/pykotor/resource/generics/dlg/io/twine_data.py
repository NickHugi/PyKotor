"""Data structures for Twine format."""

from __future__ import annotations

import json

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from utility.common.geometry import Vector2

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pykotor.common.misc import Color
    from pykotor.resource.generics.dlg.base import DLG


class PassageType(Enum):
    """Type of passage in Twine."""

    ENTRY = auto()  # NPC dialog entry
    REPLY = auto()  # Player dialog reply


@dataclass
class TwineMetadata:
    """Metadata for a Twine story."""

    name: str
    ifid: str = ""  # Unique story identifier
    format: str = "Harlowe"  # Story format name
    format_version: str = "3.3.7"  # Story format version
    zoom: float = 1.0  # Editor zoom level
    creator: str = "PyKotor"  # Creator tool name
    creator_version: str = "1.0.0"  # Creator tool version
    style: str = ""  # Custom CSS
    script: str = ""  # Custom JavaScript
    tag_colors: dict[str, Color] = field(default_factory=dict)  # Tag color mapping


@dataclass
class PassageMetadata:
    """Metadata for a Twine passage."""

    position: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))  # Position in editor
    size: Vector2 = field(default_factory=lambda: Vector2(100.0, 100.0))  # Size in editor
    # KotOR-specific metadata
    speaker: str = ""  # For entries only
    animation_id: int = 0  # Animation to play
    camera_angle: int = 0  # Camera angle
    camera_id: int = 0  # Camera ID
    fade_type: int = 0  # Type of fade
    quest: str = ""  # Associated quest
    sound: str = ""  # Sound to play
    vo_resref: str = ""  # Voice-over resource
    # Additional metadata as needed
    custom: dict[str, str] = field(default_factory=dict)


@dataclass
class TwineLink:
    """A link between passages in Twine."""

    text: str  # Display text
    target: str  # Target passage name
    # KotOR-specific metadata
    is_child: bool = False  # Child link flag
    active_script: str = ""  # Activation script
    active_params: list[str] = field(default_factory=list)  # Script parameters


@dataclass
class TwinePassage:
    """A passage in a Twine story."""

    name: str  # Passage name
    text: str  # Passage content
    type: PassageType  # Entry or Reply
    pid: str = ""  # Passage ID
    tags: list[str] = field(default_factory=list)  # Passage tags
    metadata: PassageMetadata = field(default_factory=PassageMetadata)
    links: list[TwineLink] = field(default_factory=list)


@dataclass
class TwineStory:
    """A complete Twine story."""

    metadata: TwineMetadata
    passages: list[TwinePassage]
    start_pid: str = ""  # Starting passage ID

    @property
    def start_passage(self) -> TwinePassage | None:
        """Get the starting passage."""
        return next((p for p in self.passages if p.pid == self.start_pid), None)

    def get_passage(
        self,
        name: str,
    ) -> TwinePassage | None:
        """Get a passage by name."""
        return next((p for p in self.passages if p.name == name), None)

    def get_passages_by_type(
        self,
        type_: PassageType,
    ) -> Sequence[TwinePassage]:
        """Get all passages of a specific type."""
        return [p for p in self.passages if p.type == type_]

    def get_entries(self) -> Sequence[TwinePassage]:
        """Get all entry passages."""
        return self.get_passages_by_type(PassageType.ENTRY)

    def get_replies(self) -> Sequence[TwinePassage]:
        """Get all reply passages."""
        return self.get_passages_by_type(PassageType.REPLY)

    def get_links_to(
        self,
        passage: TwinePassage,
    ) -> Sequence[tuple[TwinePassage, TwineLink]]:
        """Get all links pointing to a passage."""
        return [(p, link) for p in self.passages for link in p.links if link.target == passage.name]


@dataclass
class FormatConverter:
    """Handles conversion between KotOR and Twine formats.

    This class manages the mapping of features between formats and handles
    cases where one format has features the other doesn't.

    KotOR -> Twine:
    - Dialog entries become passages with type ENTRY
    - Dialog replies become passages with type REPLY
    - Links preserve their child status and activation scripts
    - Camera/animation/sound data stored in passage metadata
    - Quest/VO data stored in passage metadata

    Twine -> KotOR:
    - ENTRY passages become dialog entries
    - REPLY passages become dialog replies
    - Link text becomes the node text
    - Passage positions preserved in editor
    - Custom metadata mapped to appropriate KotOR fields
    """

    def __init__(self) -> None:
        self.kotor_only_features: set[str] = {
            "animation_id",
            "camera_angle",
            "camera_id",
            "fade_type",
            "quest",
            "sound",
            "vo_resref",
        }
        self.twine_only_features: set[str] = {
            "style",
            "script",
            "tag_colors",
        }

    def store_kotor_metadata(
        self,
        passage: TwinePassage,
        dlg_node: Any,
    ) -> None:
        """Store KotOR-specific metadata in a Twine passage.

        This preserves KotOR features that don't have direct Twine equivalents.
        The data is stored in the passage metadata and can be restored when
        converting back to KotOR format.

        Args:
        ----
            passage: The Twine passage to store metadata in
            dlg_node: The KotOR dialog node to get metadata from
        """
        meta = passage.metadata
        meta.animation_id = getattr(dlg_node, "animation_id", 0)
        meta.camera_angle = getattr(dlg_node, "camera_angle", 0)
        meta.camera_id = getattr(dlg_node, "camera_id", 0)
        meta.fade_type = getattr(dlg_node, "fade_type", 0)
        meta.quest = getattr(dlg_node, "quest", "")
        meta.sound = getattr(dlg_node, "sound", "")
        meta.vo_resref = getattr(dlg_node, "vo_resref", "")

    def restore_kotor_metadata(
        self,
        dlg_node: Any,
        passage: TwinePassage,
    ) -> None:
        """Restore KotOR-specific metadata from a Twine passage.

        This recovers KotOR features that were stored in the Twine metadata
        when converting back to KotOR format.

        Args:
        ----
            dlg_node: The KotOR dialog node to restore metadata to
            passage: The Twine passage to get metadata from
        """
        meta: PassageMetadata = passage.metadata
        for feature in self.kotor_only_features:
            if not hasattr(meta, feature):
                continue
            setattr(dlg_node, feature, getattr(meta, feature))

    def store_twine_metadata(
        self,
        story: TwineStory,
        dlg: DLG,
    ) -> None:
        """Store Twine-specific metadata in a dialog.

        This preserves Twine features that don't have direct KotOR equivalents.
        The data is stored in a way that can be restored when converting back
        to Twine format.

        Args:
        ----
            story: The Twine story to store metadata from
            dlg: The KotOR dialog to store metadata in
        """
        # Store Twine metadata in dialog's comment field as JSON
        twine_data: dict[str, Any] = {
            "style": story.metadata.style,
            "script": story.metadata.script,
            "tag_colors": {k: str(v) for k, v in story.metadata.tag_colors.items()},
            "format": story.metadata.format,
            "format_version": story.metadata.format_version,
            "creator": story.metadata.creator,
            "creator_version": story.metadata.creator_version,
            "zoom": story.metadata.zoom,
        }
        dlg.comment = json.dumps(twine_data)

    def restore_twine_metadata(
        self,
        dlg: DLG,
        story: TwineStory,
    ) -> None:
        """Restore Twine-specific metadata from a dialog.

        This recovers Twine features that were stored in the dialog when
        converting back to Twine format.

        Args:
        ----
            dlg: The KotOR dialog to get metadata from
            story: The Twine story to restore metadata to
        """
        # Try to recover Twine metadata from dialog's comment field
        if not dlg.comment:
            return

        try:
            twine_data: dict[str, Any] = json.loads(dlg.comment)
            story.metadata.style = twine_data.get("style", "")
            story.metadata.script = twine_data.get("script", "")
            story.metadata.tag_colors = dict(twine_data.get("tag_colors", {}).items())
            story.metadata.format = twine_data.get("format", "Harlowe")
            story.metadata.format_version = twine_data.get("format_version", "3.3.7")
            story.metadata.creator = twine_data.get("creator", "PyKotor")
            story.metadata.creator_version = twine_data.get("creator_version", "1.0.0")
            story.metadata.zoom = float(twine_data.get("zoom", 1.0))
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):  # noqa: S110
            # If metadata restoration fails, keep defaults
            pass
