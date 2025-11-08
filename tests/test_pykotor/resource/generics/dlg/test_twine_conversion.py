"""Tests for Twine format conversion."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from utility.common.geometry import Vector2
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine
from pykotor.resource.generics.dlg.io.twine_data import (
    FormatConverter,
    PassageMetadata,
    PassageType,
    TwineLink,
    TwineMetadata,
    TwinePassage,
    TwineStory,
)

if TYPE_CHECKING:
    from typing import Any


def test_story_to_dlg_basic():
    """Test basic conversion from TwineStory to DLG."""
    # Create a simple story
    story = TwineStory(
        metadata=TwineMetadata(name="Test Story"),
        passages=[
            TwinePassage(
                name="NPC",
                text="Hello there!",
                type=PassageType.ENTRY,
                pid="1",
                metadata=PassageMetadata(
                    position=Vector2(100, 100),
                    size=Vector2(100, 100),
                ),
            ),
            TwinePassage(
                name="Reply_1",
                text="General Kenobi!",
                type=PassageType.REPLY,
                pid="2",
                metadata=PassageMetadata(
                    position=Vector2(200, 100),
                    size=Vector2(100, 100),
                ),
            ),
        ],
        start_pid="1",
    )

    # Add link
    story.passages[0].links.append(TwineLink(text="Continue", target="Reply_1"))

    # Convert to DLG
    converter = FormatConverter()
    dlg = converter._story_to_dlg(story)

    # Verify structure
    assert len(dlg.starters) == 1
    entry = dlg.starters[0].node
    assert isinstance(entry, DLGEntry)
    assert entry.speaker == "NPC"
    assert entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello there!"

    assert len(entry.links) == 1
    reply = entry.links[0].node
    assert isinstance(reply, DLGReply)
    assert reply.text.get(Language.ENGLISH, Gender.MALE) == "General Kenobi!"


def test_dlg_to_story_basic():
    """Test basic conversion from DLG to TwineStory."""
    # Create a simple dialog
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello there!")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "General Kenobi!")

    entry.links.append(DLGLink(reply))
    dlg.starters.append(DLGLink(entry))

    # Convert to TwineStory
    converter = FormatConverter()
    story = converter._dlg_to_story(dlg)

    # Verify structure
    assert len(story.passages) == 2
    entry_passage = story.start_passage
    assert entry_passage is not None
    assert entry_passage.name == "NPC"
    assert entry_passage.text == "Hello there!"
    assert entry_passage.type == PassageType.ENTRY

    assert len(entry_passage.links) == 1
    reply_passage = next(p for p in story.passages if p.type == PassageType.REPLY)
    assert reply_passage.text == "General Kenobi!"


def test_metadata_preservation():
    """Test preservation of metadata during conversion."""
    # Create a story with metadata
    story = TwineStory(
        metadata=TwineMetadata(
            name="Test Story",
            style="body { color: red; }",
            script="window.setup = {};",
            tag_colors={"reply": "green"},
        ),
        passages=[
            TwinePassage(
                name="NPC",
                text="Test",
                type=PassageType.ENTRY,
                pid="1",
                metadata=PassageMetadata(
                    position=Vector2(100, 100),
                    size=Vector2(100, 100),
                    camera_angle=45,
                    animation_id=123,
                ),
            ),
        ],
        start_pid="1",
    )

    # Convert to DLG and back
    converter = FormatConverter()
    dlg = converter._story_to_dlg(story)
    new_story = converter._dlg_to_story(dlg)

    # Verify metadata preserved
    assert new_story.metadata.style == story.metadata.style
    assert new_story.metadata.script == story.metadata.script
    assert new_story.metadata.tag_colors == story.metadata.tag_colors

    # Verify passage metadata preserved
    new_passage = new_story.start_passage
    assert new_passage is not None
    assert new_passage.metadata.camera_angle == story.passages[0].metadata.camera_angle
    assert new_passage.metadata.animation_id == story.passages[0].metadata.animation_id


def test_circular_references():
    """Test handling of circular references."""
    # Create a dialog with circular reference
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "First")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "Back to start")

    # Create circular reference
    entry.links.append(DLGLink(reply))
    reply.links.append(DLGLink(entry))
    dlg.starters.append(DLGLink(entry))

    # Convert to TwineStory and back
    converter = FormatConverter()
    story = converter._dlg_to_story(dlg)
    new_dlg = converter._story_to_dlg(story)

    # Verify structure preserved
    assert len(new_dlg.starters) == 1
    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert len(new_entry.links) == 1

    new_reply = new_entry.links[0].node
    assert isinstance(new_reply, DLGReply)
    assert len(new_reply.links) == 1
    assert isinstance(new_reply.links[0].node, DLGEntry)


def test_json_format():
    """Test reading/writing JSON format."""
    # Create a simple dialog
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    # Write to JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")

        # Verify JSON structure
        with open(f.name, encoding="utf-8") as f2:
            data: dict[str, Any] = json.load(f2)
            assert "name" in data
            assert "passages" in data
            assert len(data["passages"]) == 1
            assert data["passages"][0]["name"] == "NPC"
            assert data["passages"][0]["text"] == "Hello!"

        # Read back
        new_dlg = read_twine(f.name)
        assert len(new_dlg.starters) == 1
        new_entry = new_dlg.starters[0].node
        assert isinstance(new_entry, DLGEntry)
        assert new_entry.speaker == "NPC"
        assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello!"


def test_html_format():
    """Test reading/writing HTML format."""
    # Create a simple dialog
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    # Write to HTML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        write_twine(dlg, f.name, format="html")

        # Read back
        new_dlg = read_twine(f.name)
        assert len(new_dlg.starters) == 1
        new_entry = new_dlg.starters[0].node
        assert isinstance(new_entry, DLGEntry)
        assert new_entry.speaker == "NPC"
        assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello!"


def test_invalid_formats():
    """Test handling of invalid formats."""
    dlg = DLG()

    # Invalid format
    with pytest.raises(ValueError):
        write_twine(dlg, "test.txt", format="invalid")  # type: ignore

    # Invalid JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        f.write("invalid json")
        f.flush()
        with pytest.raises(ValueError):
            read_twine(f.name)

    # Invalid HTML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        f.write("<not valid html>")
        f.flush()
        with pytest.raises(ValueError):
            read_twine(f.name)


def test_complex_dialog():
    """Test handling of complex dialog structures."""
    # Create a branching dialog
    dlg = DLG()

    entry1 = DLGEntry()
    entry1.speaker = "NPC"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "Choose your path:")

    reply1 = DLGReply()
    reply1.text.set_data(Language.ENGLISH, Gender.MALE, "Path 1")

    reply2 = DLGReply()
    reply2.text.set_data(Language.ENGLISH, Gender.MALE, "Path 2")

    entry2 = DLGEntry()
    entry2.speaker = "NPC"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Path 1 chosen")

    entry3 = DLGEntry()
    entry3.speaker = "NPC"
    entry3.text.set_data(Language.ENGLISH, Gender.MALE, "Path 2 chosen")

    # Link them
    entry1.links.append(DLGLink(reply1))
    entry1.links.append(DLGLink(reply2))
    reply1.links.append(DLGLink(entry2))
    reply2.links.append(DLGLink(entry3))

    dlg.starters.append(DLGLink(entry1))

    # Convert to TwineStory and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        # Verify structure preserved
        assert len(new_dlg.starters) == 1
        new_entry1 = new_dlg.starters[0].node
        assert isinstance(new_entry1, DLGEntry)
        assert len(new_entry1.links) == 2

        # Verify both paths
        for link in new_entry1.links:
            reply = link.node
            assert isinstance(reply, DLGReply)
            assert len(reply.links) == 1
            next_entry = reply.links[0].node
            assert isinstance(next_entry, DLGEntry)
            assert next_entry.text.get(Language.ENGLISH, Gender.MALE) in [
                "Path 1 chosen",
                "Path 2 chosen",
            ]
