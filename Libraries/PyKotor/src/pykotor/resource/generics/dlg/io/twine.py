"""Twine format support for dialog system."""

from __future__ import annotations

import json
import re
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from xml.etree import ElementTree

from pykotor.common.geometry import Vector2
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.io.twine_data import (
    FormatConverter,
    PassageMetadata,
    PassageType,
    TwineLink,
    TwineMetadata,
    TwinePassage,
    TwineStory,
)
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    Format: TypeAlias = Literal["html", "json"]


def read_twine(path: str | Path) -> DLG:
    """Read a dialog from a Twine file.

    Args:
    ----
        path: Path to the Twine file (HTML or JSON)

    Returns:
    -------
        The loaded dialog

    Raises:
    ------
        ValueError: If the file format is invalid
        FileNotFoundError: If the file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = path.read_text(encoding="utf-8")
    if content.strip().startswith("{"):
        story = _read_json(content)
    elif content.strip().startswith("<"):
        story = _read_html(content)
    else:
        raise ValueError("Invalid Twine format - must be HTML or JSON")

    return _story_to_dlg(story)


def write_twine(
    dlg: DLG,
    path: str | Path,
    format: Format = "html",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write a dialog to a Twine file.

    Args:
    ----
        dlg: The dialog to write
        path: Path to write to
        format: Output format ("html" or "json")
        metadata: Optional metadata to include

    Raises:
    ------
        ValueError: If the format is invalid
    """
    path = Path(path)
    story = _dlg_to_story(dlg, metadata)

    if format == "json":
        _write_json(story, path)
    elif format == "html":
        _write_html(story, path)
    else:
        raise ValueError(f"Invalid format: {format}")


def _read_json(content: str) -> TwineStory:
    """Read a Twine story from JSON format.

    Args:
    ----
        content: The JSON content to parse

    Returns:
    -------
        The loaded story

    Raises:
    ------
        ValueError: If the JSON is invalid
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    # Create metadata
    metadata = TwineMetadata(
        name=data.get("name", "Converted Dialog"),
        ifid=data.get("ifid", str(uuid.uuid4())),
        format=data.get("format", "Harlowe"),
        format_version=data.get("format-version", "3.3.7"),
        zoom=float(data.get("zoom", 1.0)),
        creator=data.get("creator", "PyKotor"),
        creator_version=data.get("creator-version", "1.0.0"),
        style=data.get("style", ""),
        script=data.get("script", ""),
        tag_colors=data.get("tag-colors", {}),
    )

    # Create passages
    passages: list[TwinePassage] = []
    for p_data in data.get("passages", []):
        # Determine passage type
        tags = p_data.get("tags", [])
        p_type = PassageType.ENTRY if "entry" in tags else PassageType.REPLY

        # Parse metadata
        p_meta = p_data.get("metadata", {})
        position = p_meta.get("position", "0,0").split(",")
        size = p_meta.get("size", "100,100").split(",")
        metadata = PassageMetadata(
            position=Vector2(float(position[0]), float(position[1])),
            size=Vector2(float(size[0]), float(size[1])),
        )

        # Create passage
        passage = TwinePassage(
            name=p_data.get("name", ""),
            text=p_data.get("text", ""),
            type=p_type,
            pid=p_data.get("pid", str(uuid.uuid4())),
            tags=tags,
            metadata=metadata,
        )

        # Parse links
        link_pattern = r"\[\[(.*?)(?:->(.+?))?\]\]"
        for match in re.finditer(link_pattern, passage.text):
            display = match.group(1)
            target = match.group(2) or display
            passage.links.append(TwineLink(text=display, target=target))

        passages.append(passage)

    return TwineStory(metadata=metadata, passages=passages)


def _read_html(content: str) -> TwineStory:
    """Read a Twine story from HTML format.

    Args:
    ----
        content: The HTML content to parse

    Returns:
    -------
        The loaded story

    Raises:
    ------
        ValueError: If the HTML is invalid
    """
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as e:
        raise ValueError(f"Invalid HTML: {e}") from e

    story_data = root.find(".//tw-storydata")
    if story_data is None:
        raise ValueError("No story data found in HTML")

    # Create metadata
    metadata = TwineMetadata(
        name=story_data.get("name", "Converted Dialog"),
        ifid=story_data.get("ifid", str(uuid.uuid4())),
        format=story_data.get("format", "Harlowe"),
        format_version=story_data.get("format-version", "3.3.7"),
        zoom=float(story_data.get("zoom", 1.0)),
        creator=story_data.get("creator", "PyKotor"),
        creator_version=story_data.get("creator-version", "1.0.0"),
    )

    # Get style/script
    style = story_data.find(".//style[@type='text/twine-css']")
    if style is not None and style.text:
        metadata.style = style.text

    script = story_data.find(".//script[@type='text/twine-javascript']")
    if script is not None and script.text:
        metadata.script = script.text

    # Get tag colors
    for tag in story_data.findall(".//tw-tag"):
        name = tag.get("name", "")
        color = tag.get("color", "")
        if name and color:
            metadata.tag_colors[name] = color

    # Create passages
    passages: list[TwinePassage] = []
    for p_data in story_data.findall(".//tw-passagedata"):
        # Determine passage type
        tags = p_data.get("tags", "").split()
        p_type = PassageType.ENTRY if "entry" in tags else PassageType.REPLY

        # Parse position/size
        position = p_data.get("position", "0,0").split(",")
        size = p_data.get("size", "100,100").split(",")
        metadata = PassageMetadata(
            position=Vector2(float(position[0]), float(position[1])),
            size=Vector2(float(size[0]), float(size[1])),
        )

        # Create passage
        passage = TwinePassage(
            name=p_data.get("name", ""),
            text=p_data.text or "",
            type=p_type,
            pid=p_data.get("pid", str(uuid.uuid4())),
            tags=tags,
            metadata=metadata,
        )

        # Parse links
        link_pattern = r"\[\[(.*?)(?:->(.+?))?\]\]"
        for match in re.finditer(link_pattern, passage.text):
            display = match.group(1)
            target = match.group(2) or display
            passage.links.append(TwineLink(text=display, target=target))

        passages.append(passage)

    return TwineStory(metadata=metadata, passages=passages)


def _write_json(story: TwineStory, path: Path) -> None:
    """Write a Twine story to JSON format.

    Args:
    ----
        story: The story to write
        path: Path to write to
    """
    data = {
        "name": story.metadata.name,
        "ifid": story.metadata.ifid,
        "format": story.metadata.format,
        "format-version": story.metadata.format_version,
        "zoom": story.metadata.zoom,
        "creator": story.metadata.creator,
        "creator-version": story.metadata.creator_version,
        "style": story.metadata.style,
        "script": story.metadata.script,
        "tag-colors": story.metadata.tag_colors,
        "passages": [],
    }

    for passage in story.passages:
        p_data = {
            "name": passage.name,
            "text": passage.text,
            "tags": passage.tags,
            "pid": passage.pid,
            "metadata": {
                "position": f"{passage.metadata.position.x},{passage.metadata.position.y}",
                "size": f"{passage.metadata.size.x},{passage.metadata.size.y}",
            },
        }
        cast(list[dict[str, Any]], data["passages"]).append(p_data)

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_html(story: TwineStory, path: Path) -> None:
    """Write a Twine story to HTML format.

    Args:
    ----
        story: The story to write
        path: Path to write to
    """
    root = ElementTree.Element("html")
    story_data = ElementTree.SubElement(root, "tw-storydata")

    # Set story metadata
    story_data.set("name", story.metadata.name)
    story_data.set("ifid", story.metadata.ifid)
    story_data.set("format", story.metadata.format)
    story_data.set("format-version", story.metadata.format_version)
    story_data.set("zoom", str(story.metadata.zoom))
    story_data.set("creator", story.metadata.creator)
    story_data.set("creator-version", story.metadata.creator_version)

    # Add style/script
    if story.metadata.style:
        style = ElementTree.SubElement(story_data, "style")
        style.set("role", "stylesheet")
        style.set("id", "twine-user-stylesheet")
        style.set("type", "text/twine-css")
        style.text = story.metadata.style

    if story.metadata.script:
        script = ElementTree.SubElement(story_data, "script")
        script.set("role", "script")
        script.set("id", "twine-user-script")
        script.set("type", "text/twine-javascript")
        script.text = story.metadata.script

    # Add tag colors
    for name, color in story.metadata.tag_colors.items():
        tag = ElementTree.SubElement(story_data, "tw-tag")
        tag.set("name", name)
        tag.set("color", str(color))

    # Add passages
    for passage in story.passages:
        p_data = ElementTree.SubElement(story_data, "tw-passagedata")
        p_data.set("name", passage.name)
        p_data.set("tags", " ".join(passage.tags))
        p_data.set("pid", passage.pid)
        p_data.set(
            "position",
            f"{passage.metadata.position.x},{passage.metadata.position.y}",
        )
        p_data.set(
            "size",
            f"{passage.metadata.size.x},{passage.metadata.size.y}",
        )
        p_data.text = passage.text

    tree = ElementTree.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _story_to_dlg(story: TwineStory) -> DLG:
    """Convert a Twine story to a KotOR dialog.

    Args:
    ----
        story: The story to convert

    Returns:
    -------
        The converted dialog
    """
    dlg = DLG()
    converter = FormatConverter()

    # Track created nodes
    nodes: dict[str, DLGEntry | DLGReply] = {}

    # First pass: Create nodes
    for passage in story.passages:
        if passage.type == PassageType.ENTRY:
            node = DLGEntry()
            node.speaker = passage.name
        else:
            node = DLGReply()

        # Set text
        node.text = LocalizedString(-1)
        node.text.set_data(Language.ENGLISH, Gender.MALE, passage.text)

        # Store metadata
        converter.store_kotor_metadata(passage, node)

        nodes[passage.name] = node

    # Second pass: Create links
    for passage in story.passages:
        source = nodes[passage.name]
        for link in passage.links:
            if link.target in nodes:
                target = nodes[link.target]
                source.links.append(DLGLink(target))

    # Set starting node
    if story.start_passage and story.start_passage.name in nodes:
        dlg.starters.append(DLGLink(nodes[story.start_passage.name]))

    # Store Twine metadata
    converter.store_twine_metadata(story, dlg)

    return dlg


def _dlg_to_story(dlg: DLG, metadata: dict[str, Any] | None = None) -> TwineStory:
    """Convert a KotOR dialog to a Twine story.

    Args:
    ----
        dlg: The dialog to convert
        metadata: Optional metadata to include

    Returns:
    -------
        The converted story
    """
    # Create metadata
    meta = metadata or {}
    story_meta = TwineMetadata(
        name=meta.get("name", "Converted Dialog"),
        ifid=meta.get("ifid", str(uuid.uuid4())),
        format=meta.get("format", "Harlowe"),
        format_version=meta.get("format-version", "3.3.7"),
        zoom=float(meta.get("zoom", 1.0)),
        creator=meta.get("creator", "PyKotor"),
        creator_version=meta.get("creator-version", "1.0.0"),
        style=meta.get("style", ""),
        script=meta.get("script", ""),
        tag_colors=meta.get("tag-colors", {}),
    )

    story = TwineStory(metadata=story_meta, passages=[])
    converter = FormatConverter()

    # Track processed nodes to handle cycles
    processed: set[DLGEntry | DLGReply] = set()
    node_to_passage: dict[DLGEntry | DLGReply, TwinePassage] = {}

    def process_node(node: DLGEntry | DLGReply, pid: str) -> TwinePassage:
        """Process a node and its links recursively."""
        if node in processed:
            return node_to_passage[node]

        processed.add(node)

        # Create passage
        passage = TwinePassage(
            name=node.speaker if isinstance(node, DLGEntry) else f"Reply_{len(processed)}",
            text=node.text.get(Language.ENGLISH, Gender.MALE) or "",
            type=PassageType.ENTRY if isinstance(node, DLGEntry) else PassageType.REPLY,
            pid=pid,
            tags=["entry"] if isinstance(node, DLGEntry) else ["reply"],
        )

        # Store metadata
        converter.store_kotor_metadata(passage, node)

        # Process links
        for link in node.links:
            if link.node is not None:
                target = process_node(link.node, str(uuid.uuid4()))
                passage.links.append(
                    TwineLink(
                        text="Continue",
                        target=target.name,
                        is_child=link.is_child,
                        active_script=str(link.active1),
                    ),
                )

        story.passages.append(passage)
        node_to_passage[node] = passage
        return passage

    # Process all nodes starting from starters
    for i, link in enumerate(dlg.starters):
        if link.node is not None:
            passage = process_node(link.node, str(i + 1))
            if i == 0:  # Set first node as starting node
                story.start_pid = passage.pid

    # Restore Twine metadata
    converter.restore_twine_metadata(dlg, story)

    return story
