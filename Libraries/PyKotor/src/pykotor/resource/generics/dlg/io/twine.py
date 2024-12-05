"""Twine format support for dialog system."""

from __future__ import annotations

import json
import re
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree as ET

try:
    from defusedxml import ElementTree as _ElementTree

    fromstring = _ElementTree.fromstring
except ImportError:
    fromstring = ET.fromstring

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.io.twine_data import FormatConverter, PassageMetadata, PassageType, TwineLink, TwineMetadata, TwinePassage, TwineStory
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from utility.common.geometry import Vector2

if TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias, TypedDict  # pyright: ignore[reportMissingModuleSource]

    Format: TypeAlias = Literal["html", "json"]

    class PassageMetadataDict(TypedDict):
        position: str
        size: str

    class PassageDict(TypedDict):
        name: str
        text: str
        tags: list[str]
        pid: str
        metadata: PassageMetadataDict

    class StoryDict(TypedDict):
        name: str
        ifid: str
        format: str
        format_version: str
        zoom: float
        creator: str
        creator_version: str
        style: str
        script: str
        tag_colors: dict[str, str]
        passages: list[PassageDict]


def read_twine(path: str | Path) -> DLG:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content: str = path.read_text(encoding="utf-8")
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
    fmt: Format = "html",
    metadata: dict[str, Any] | None = None,
) -> None:
    path = Path(path)
    story: TwineStory = _dlg_to_story(dlg, metadata)

    if fmt == "json":
        _write_json(story, path)
    elif fmt == "html":
        _write_html(story, path)
    else:
        raise ValueError(f"Invalid format: {fmt}")


def _read_json(content: str) -> TwineStory:
    try:
        data: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    # Create metadata
    twine_metadata: TwineMetadata = TwineMetadata(
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
    p_data: dict[str, Any] = data.get("passages", [])
    for p_data in data.get("passages", []):
        # Determine passage type
        tags: list[str] = p_data.get("tags", [])
        p_type: PassageType = PassageType.ENTRY if "entry" in tags else PassageType.REPLY

        # Parse metadata
        p_meta: dict[str, Any] = p_data.get("metadata", {})
        position: list[str] = p_meta.get("position", "0,0").split(",")
        size: list[str] = p_meta.get("size", "100,100").split(",")
        passage_metadata: PassageMetadata = PassageMetadata(
            position=Vector2(float(position[0]), float(position[1])),
            size=Vector2(float(size[0]), float(size[1])),
        )

        # Create passage
        passage: TwinePassage = TwinePassage(
            name=p_data.get("name", ""),
            text=p_data.get("text", ""),
            type=p_type,
            pid=p_data.get("pid", str(uuid.uuid4())),
            tags=tags,
            metadata=passage_metadata,
        )

        # Parse links
        link_pattern: str = r"\[\[(.*?)(?:->(.+?))?\]\]"
        for match in re.finditer(link_pattern, passage.text):
            display: str = match.group(1)
            target: str = match.group(2) or display
            passage.links.append(TwineLink(text=display, target=target))

        passages.append(passage)

    return TwineStory(
        metadata=twine_metadata,
        passages=passages,
    )


def _read_html(content: str) -> TwineStory:
    try:
        root: ET.Element = fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid HTML: {e}") from e

    story_data: ET.Element | None = root.find(".//tw-storydata")
    if story_data is None:
        raise ValueError("No story data found in HTML")

    # Create metadata
    twine_metadata: TwineMetadata = TwineMetadata(
        name=story_data.get("name", "Converted Dialog"),
        ifid=story_data.get("ifid", str(uuid.uuid4())),
        format=story_data.get("format", "Harlowe"),
        format_version=story_data.get("format-version", "3.3.7"),
        zoom=float(story_data.get("zoom", 1.0)),
        creator=story_data.get("creator", "PyKotor"),
        creator_version=story_data.get("creator-version", "1.0.0"),
    )

    # Get style/script
    style: ET.Element | None = story_data.find(".//style[@type='text/twine-css']")
    if style is not None and style.text:
        twine_metadata.style = style.text

    script: ET.Element | None = story_data.find(".//script[@type='text/twine-javascript']")
    if script is not None and script.text:
        twine_metadata.script = script.text

    # Get tag colors
    for tag in story_data.findall(".//tw-tag"):
        name: str = tag.get("name", "").strip()
        color: str = tag.get("color", "").strip()
        if not name:
            continue
        if not color:
            continue

        twine_metadata.tag_colors[name] = Color.from_hex_string(color)

    # Create passages
    passages: list[TwinePassage] = []
    for p_data in story_data.findall(".//tw-passagedata"):
        # Determine passage type
        tags: list[str] = p_data.get("tags", "").split()
        p_type: PassageType = PassageType.ENTRY if "entry" in tags else PassageType.REPLY

        # Parse position/size
        position: list[str] = p_data.get("position", "0,0").split(",")
        size: list[str] = p_data.get("size", "100,100").split(",")
        passage_metadata: PassageMetadata = PassageMetadata(
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
            metadata=passage_metadata,
        )

        # Parse links
        link_pattern: str = r"\[\[(.*?)(?:->(.+?))?\]\]"
        for match in re.finditer(link_pattern, passage.text):
            display: str = match.group(1)
            target: str = match.group(2) or display
            passage.links.append(TwineLink(text=display, target=target))

        passages.append(passage)

    return TwineStory(
        metadata=twine_metadata,
        passages=passages,
    )


def _write_json(
    story: TwineStory,
    path: Path,
) -> None:
    """Write a Twine story to JSON format.

    Args:
    ----
        story: The story to write
        path: Path to write to
    """
    data: StoryDict = {
        "name": story.metadata.name,
        "ifid": story.metadata.ifid,
        "format": story.metadata.format,
        "format_version": story.metadata.format_version,
        "zoom": story.metadata.zoom,
        "creator": story.metadata.creator,
        "creator_version": story.metadata.creator_version,
        "style": story.metadata.style,
        "script": story.metadata.script,
        "tag_colors": {k: str(v) for k, v in story.metadata.tag_colors.items()},
        "passages": [],
    }

    for passage in story.passages:
        p_data: PassageDict = {
            "name": passage.name,
            "text": passage.text,
            "tags": passage.tags,
            "pid": passage.pid,
            "metadata": {
                "position": f"{passage.metadata.position.x},{passage.metadata.position.y}",
                "size": f"{passage.metadata.size.x},{passage.metadata.size.y}",
            },
        }
        data["passages"].append(p_data)

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_html(
    story: TwineStory,
    path: Path,
) -> None:
    root: ET.Element = ET.Element("html")
    story_data: ET.Element = ET.SubElement(root, "tw-storydata")

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
        style: ET.Element = ET.SubElement(story_data, "style")
        style.set("role", "stylesheet")
        style.set("id", "twine-user-stylesheet")
        style.set("type", "text/twine-css")
        style.text = story.metadata.style

    if story.metadata.script:
        script: ET.Element = ET.SubElement(story_data, "script")
        script.set("role", "script")
        script.set("id", "twine-user-script")
        script.set("type", "text/twine-javascript")
        script.text = story.metadata.script

    # Add tag colors
    for name, color in story.metadata.tag_colors.items():
        tag: ET.Element = ET.SubElement(story_data, "tw-tag")
        tag.set("name", name)
        tag.set("color", str(color))

    # Add passages
    for passage in story.passages:
        p_data: ET.Element = ET.SubElement(story_data, "tw-passagedata")
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

    tree: ET.ElementTree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _story_to_dlg(story: TwineStory) -> DLG:
    dlg: DLG = DLG()
    converter: FormatConverter = FormatConverter()

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
        source: DLGEntry | DLGReply = nodes[passage.name]
        for link in passage.links:
            if link.target not in nodes:
                continue

            target: DLGEntry | DLGReply = nodes[link.target]
            source.links.append(DLGLink(target))  # pyright: ignore[reportArgumentType]

    # Set starting node
    if story.start_passage and story.start_passage.name in nodes:
        dlg.starters.append(DLGLink(nodes[story.start_passage.name]))  # pyright: ignore[reportArgumentType]

    # Store Twine metadata
    converter.store_twine_metadata(story, dlg)

    return dlg


def _dlg_to_story(
    dlg: DLG,
    metadata: dict[str, Any] | None = None,
) -> TwineStory:
    # Create metadata
    meta: dict[str, Any] = metadata or {}
    story_meta: TwineMetadata = TwineMetadata(
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

    story: TwineStory = TwineStory(metadata=story_meta, passages=[])
    converter: FormatConverter = FormatConverter()

    # Track processed nodes to handle cycles
    processed: set[DLGEntry | DLGReply] = set()
    node_to_passage: dict[DLGEntry | DLGReply, TwinePassage] = {}

    def process_node(
        node: DLGEntry | DLGReply,
        pid: str,
    ) -> TwinePassage:
        """Process a node and its links recursively."""
        if node in processed:
            return node_to_passage[node]

        processed.add(node)

        # Create passage
        passage: TwinePassage = TwinePassage(
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
            if link.node is None:
                continue

            target: TwinePassage = process_node(link.node, str(uuid.uuid4()))
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
        if link.node is None:
            continue

        passage: TwinePassage = process_node(link.node, str(i + 1))
        if i == 0:  # Set first node as starting node
            story.start_pid = passage.pid

    # Restore Twine metadata
    converter.restore_twine_metadata(dlg, story)

    return story
