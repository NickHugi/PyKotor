"""Tests for Twine format-specific features."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast
from xml.etree import ElementTree

import pytest

from pykotor.common.language import Gender, Language
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine

if TYPE_CHECKING:
    from typing import Any


def test_html_structure():
    """Test HTML format structure."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    # Write to HTML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        write_twine(dlg, f.name, format="html")

        # Parse HTML and verify structure
        with open(f.name, encoding="utf-8") as f2:
            content = f2.read()
            root = ElementTree.fromstring(content)

            # Check basic structure
            assert root.tag == "html"
            story_data = root.find(".//tw-storydata")
            assert story_data is not None

            # Check passage
            passage = story_data.find(".//tw-passagedata")
            assert passage is not None
            assert passage.get("name") == "NPC"
            assert passage.text == "Hello!"


def test_html_style_script():
    """Test HTML style and script preservation."""
    metadata = {
        "style": "body { color: red; }",
        "script": "window.setup = {};",
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    # Write to HTML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        write_twine(dlg, f.name, format="html", metadata=metadata)

        # Parse HTML and verify style/script
        with open(f.name, encoding="utf-8") as f2:
            content = f2.read()
            root = ElementTree.fromstring(content)

            # Check style
            style = root.find(".//style[@type='text/twine-css']")
            assert style is not None
            assert style.text == metadata["style"]

            # Check script
            script = root.find(".//script[@type='text/twine-javascript']")
            assert script is not None
            assert script.text == metadata["script"]


def test_html_tag_colors():
    """Test HTML tag color preservation."""
    metadata = {
        "tag-colors": {
            "entry": "green",
            "reply": "blue",
        },
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    # Write to HTML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        write_twine(dlg, f.name, format="html", metadata=metadata)

        # Parse HTML and verify tag colors
        with open(f.name, encoding="utf-8") as f2:
            content = f2.read()
            root = ElementTree.fromstring(content)

            # Check tag colors
            tags = root.findall(".//tw-tag")
            tag_colors = {tag.get("name"): tag.get("color") for tag in tags}
            assert tag_colors == metadata["tag-colors"]


def test_json_structure():
    """Test JSON format structure."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    # Write to JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")

        # Parse JSON and verify structure
        with open(f.name, encoding="utf-8") as f2:
            data: dict[str, Any] = json.load(f2)

            # Check required fields
            assert "name" in data
            assert "passages" in data
            assert isinstance(data["passages"], list)

            # Check passage
            passage = data["passages"][0]
            assert passage["name"] == "NPC"
            assert passage["text"] == "Hello!"
            assert "tags" in passage
            assert "metadata" in passage


def test_json_metadata():
    """Test JSON metadata preservation."""
    metadata = {
        "name": "Test Story",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "tag-colors": {"reply": "green"},
        "style": "body { color: red; }",
        "script": "window.setup = {};",
        "zoom": 1.5,
        "creator": "PyKotor",
        "creator-version": "1.0.0",
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    # Write to JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json", metadata=metadata)

        # Parse JSON and verify metadata
        with open(f.name, encoding="utf-8") as f2:
            data: dict[str, Any] = json.load(f2)
            for key, value in metadata.items():
                assert data[key.replace("_", "-")] == value


def test_format_detection():
    """Test format detection from content."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    # Test JSON detection
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)
        assert len(new_dlg.starters) == 1

    # Test HTML detection
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as f:
        write_twine(dlg, f.name, format="html")
        new_dlg = read_twine(f.name)
        assert len(new_dlg.starters) == 1


def test_invalid_html():
    """Test handling of invalid HTML."""
    # Missing story data
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        f.write("<html></html>")
        f.flush()
        with pytest.raises(ValueError, match="No story data found"):
            read_twine(f.name)

    # Invalid XML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as f:
        f.write("<not valid xml>")
        f.flush()
        with pytest.raises(ValueError, match="Invalid HTML"):
            read_twine(f.name)


def test_invalid_json():
    """Test handling of invalid JSON."""
    # Invalid JSON syntax
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        f.write("{not valid json")
        f.flush()
        with pytest.raises(ValueError, match="Invalid JSON"):
            read_twine(f.name)

    # Missing required fields
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        json.dump({}, f)  # Empty object
        f.flush()
        dlg = read_twine(f.name)  # Should not raise, but create empty dialog
        assert len(dlg.starters) == 0


def test_format_conversion():
    """Test conversion between formats."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    metadata = {
        "style": "body { color: red; }",
        "script": "window.setup = {};",
        "tag-colors": {"reply": "green"},
    }

    # HTML -> JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as html_file:
        write_twine(dlg, html_file.name, format="html", metadata=metadata)
        html_dlg = read_twine(html_file.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as json_file:
            write_twine(html_dlg, json_file.name, format="json")
            json_dlg = read_twine(json_file.name)

            # Verify structure preserved
            assert len(json_dlg.starters) == 1
            json_entry = json_dlg.starters[0].node
            assert isinstance(json_entry, DLGEntry)
            assert json_entry.speaker == "NPC"
            assert json_entry.text.get(Language.ENGLISH, Gender.MALE) == "Test"

    # JSON -> HTML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as json_file:
        write_twine(dlg, json_file.name, format="json", metadata=metadata)
        json_dlg = read_twine(json_file.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as html_file:
            write_twine(json_dlg, html_file.name, format="html")
            html_dlg = read_twine(html_file.name)

            # Verify structure preserved
            assert len(html_dlg.starters) == 1
            html_entry = html_dlg.starters[0].node
            assert isinstance(html_entry, DLGEntry)
            assert html_entry.speaker == "NPC"
            assert html_entry.text.get(Language.ENGLISH, Gender.MALE) == "Test"


def test_link_syntax():
    """Test Twine link syntax handling."""
    # Create a dialog with various link types
    dlg = DLG()

    entry1 = DLGEntry()
    entry1.speaker = "NPC1"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "First")

    entry2 = DLGEntry()
    entry2.speaker = "NPC2"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Second")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "Reply")

    # Create links
    entry1.links.append(DLGLink(reply))
    reply.links.append(DLGLink(entry2))
    dlg.starters.append(DLGLink(entry1))

    # Write to both formats
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as json_file:
        write_twine(dlg, json_file.name, format="json")

        # Verify JSON links
        with open(json_file.name, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f2)
            passages = cast(list[dict[str, Any]], data["passages"])
            
            # Find entry1's passage
            entry1_passage = next(p for p in passages if p["name"] == "NPC1")
            assert "[[Continue->Reply_1]]" in entry1_passage["text"]

            # Find reply's passage
            reply_passage = next(p for p in passages if p["name"] == "Reply_1")
            assert "[[Continue->NPC2]]" in reply_passage["text"]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as html_file:
        write_twine(dlg, html_file.name, format="html")

        # Verify HTML links
        with open(html_file.name, encoding="utf-8") as f:
            content = f.read()
            root = ElementTree.fromstring(content)

            # Find entry1's passage
            entry1_passage = root.find(".//tw-passagedata[@name='NPC1']")
            assert entry1_passage is not None
            assert "[[Continue->Reply_1]]" in entry1_passage.text

            # Find reply's passage
            reply_passage = root.find(".//tw-passagedata[contains(@tags,'reply')]")
            assert reply_passage is not None
            assert "[[Continue->NPC2]]" in reply_passage.text
