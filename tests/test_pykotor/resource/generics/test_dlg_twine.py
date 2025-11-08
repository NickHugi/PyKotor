"""Tests for Twine format support in dialog system."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine

if TYPE_CHECKING:
    from typing import Any


@pytest.fixture
def sample_dlg() -> DLG:
    """Create a sample dialog for testing."""
    dlg = DLG()

    # Create some entries and replies
    entry1 = DLGEntry()
    entry1.speaker = "NPC"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "Hello there!")

    reply1 = DLGReply()
    reply1.text.set_data(Language.ENGLISH, Gender.MALE, "General Kenobi!")

    entry2 = DLGEntry()
    entry2.speaker = "NPC"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "You are a bold one.")

    # Link them together
    entry1.links.append(DLGLink(reply1))
    reply1.links.append(DLGLink(entry2))

    # Add starting node
    dlg.starters.append(DLGLink(entry1))

    return dlg


def test_write_read_json(sample_dlg: DLG, tmp_path: Path):
    """Test writing and reading dialog in JSON format."""
    # Write to JSON
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json")

    # Verify JSON structure
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        assert data["name"] == "Converted Dialog"
        assert len(data["passages"]) == 3
        assert any(p["name"] == "NPC" for p in data["passages"])
        assert any(p["text"] == "Hello there!" for p in data["passages"])
        assert any(p["text"] == "General Kenobi!" for p in data["passages"])

    # Read back
    dlg = read_twine(json_file)
    assert len(dlg.starters) == 1
    assert isinstance(dlg.starters[0].node, DLGEntry)
    assert dlg.starters[0].node.text.get(Language.ENGLISH, Gender.MALE) == "Hello there!"


def test_write_read_html(sample_dlg: DLG, tmp_path: Path):
    """Test writing and reading dialog in HTML format."""
    # Write to HTML
    html_file = tmp_path / "test.html"
    write_twine(sample_dlg, html_file)

    # Read back
    dlg = read_twine(html_file)
    assert len(dlg.starters) == 1
    assert isinstance(dlg.starters[0].node, DLGEntry)
    assert dlg.starters[0].node.text.get(Language.ENGLISH, Gender.MALE) == "Hello there!"


def test_metadata_preservation(sample_dlg: DLG, tmp_path: Path):
    """Test that metadata is preserved during write/read."""
    metadata = {
        "name": "Test Dialog",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "tag-colors": {"reply": "green"},
        "style": "body { color: red; }",
        "script": "window.setup = {};",
    }

    # Write with metadata
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json", metadata=metadata)

    # Verify metadata in JSON
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        assert data["name"] == metadata["name"]
        assert data["format"] == metadata["format"]
        assert data["format-version"] == metadata["format-version"]
        assert data["tag-colors"] == metadata["tag-colors"]
        assert data["style"] == metadata["style"]
        assert data["script"] == metadata["script"]


def test_passage_metadata(sample_dlg: DLG, tmp_path: Path):
    """Test that passage metadata (position, size) is preserved."""
    # Add metadata to a node
    entry = sample_dlg.starters[0].node
    if isinstance(entry, DLGEntry):
        entry.comment = json.dumps({"position": "100,200", "size": "100,100"})

    # Write to JSON
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json")

    # Verify metadata in JSON
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        passage = next(p for p in data["passages"] if p["name"] == "NPC")
        assert passage["metadata"]["position"] == "100,200"
        assert passage["metadata"]["size"] == "100,100"


def test_link_preservation(sample_dlg: DLG, tmp_path: Path):
    """Test that links between nodes are preserved."""
    # Write to JSON
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json")

    # Read back
    dlg = read_twine(json_file)

    # Verify links
    assert len(dlg.starters) == 1
    entry1 = dlg.starters[0].node
    assert isinstance(entry1, DLGEntry)
    assert len(entry1.links) == 1

    reply1 = entry1.links[0].node
    assert isinstance(reply1, DLGReply)
    assert len(reply1.links) == 1

    entry2 = reply1.links[0].node
    assert isinstance(entry2, DLGEntry)
    assert entry2.text.get(Language.ENGLISH, Gender.MALE) == "You are a bold one."


def test_invalid_json():
    """Test handling of invalid JSON input."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        f.write("invalid json")
        f.flush()
        with pytest.raises(json.JSONDecodeError):
            read_twine(f.name)


def test_invalid_html():
    """Test handling of invalid HTML input."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        f.write("<not valid html>")
        f.flush()
        with pytest.raises(ValueError):
            read_twine(f.name)


def test_complex_dialog_structure(tmp_path: Path):
    """Test handling of more complex dialog structures."""
    dlg = DLG()

    # Create a branching dialog
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

    # Write and read back
    json_file = tmp_path / "complex.json"
    write_twine(dlg, json_file, format="json")
    loaded_dlg = read_twine(json_file)

    # Verify structure
    assert len(loaded_dlg.starters) == 1
    entry1 = loaded_dlg.starters[0].node
    assert isinstance(entry1, DLGEntry)
    assert len(entry1.links) == 2

    # Verify both paths
    for link in entry1.links:
        reply = link.node
        assert isinstance(reply, DLGReply)
        assert len(reply.links) == 1
        next_entry = reply.links[0].node
        assert isinstance(next_entry, DLGEntry)
        assert next_entry.text.get(Language.ENGLISH, Gender.MALE) in ["Path 1 chosen", "Path 2 chosen"]
