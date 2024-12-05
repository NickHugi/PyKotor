"""Edge case tests for Twine format conversion."""

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
from pykotor.resource.generics.dlg.io.twine_data import FormatConverter, PassageMetadata, PassageType, TwineLink, TwineMetadata, TwinePassage, TwineStory

if TYPE_CHECKING:
    from typing import Any


def test_empty_dialog():
    """Test handling of empty dialog."""
    dlg = DLG()

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        assert len(new_dlg.starters) == 0
        assert len(new_dlg.all_entries()) == 0
        assert len(new_dlg.all_replies()) == 0


def test_unicode_characters():
    """Test handling of Unicode characters."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC 🚀"  # Emoji
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello 世界")  # Chinese
    entry.text.set_data(Language.FRENCH, Gender.MALE, "Bonjour 🌍")  # French with emoji
    dlg.starters.append(DLGLink(entry))

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        new_entry = new_dlg.starters[0].node
        assert isinstance(new_entry, DLGEntry)
        assert new_entry.speaker == "NPC 🚀"
        assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello 世界"
        assert new_entry.text.get(Language.FRENCH, Gender.MALE) == "Bonjour 🌍"


def test_special_characters():
    """Test handling of special characters in text and metadata."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC <with> special & chars"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Text with <tags> & special chars")
    dlg.starters.append(DLGLink(entry))

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        new_entry = new_dlg.starters[0].node
        assert isinstance(new_entry, DLGEntry)
        assert new_entry.speaker == "NPC <with> special & chars"
        assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Text with <tags> & special chars"


def test_multiple_languages():
    """Test handling of multiple languages."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "English text")
    entry.text.set_data(Language.FRENCH, Gender.MALE, "French text")
    entry.text.set_data(Language.GERMAN, Gender.MALE, "German text")
    dlg.starters.append(DLGLink(entry))

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        new_entry = new_dlg.starters[0].node
        assert isinstance(new_entry, DLGEntry)
        assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "English text"
        assert new_entry.text.get(Language.FRENCH, Gender.MALE) == "French text"
        assert new_entry.text.get(Language.GERMAN, Gender.MALE) == "German text"


def test_kotor_specific_features():
    """Test preservation of KotOR-specific features."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    entry.animation_id = 123
    entry.camera_angle = 45
    entry.camera_id = 1
    entry.fade_type = 2
    entry.quest = "MainQuest"
    entry.sound = "voice.wav"
    entry.vo_resref = "npc_line"
    dlg.starters.append(DLGLink(entry))

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        new_entry = new_dlg.starters[0].node
        assert isinstance(new_entry, DLGEntry)
        assert new_entry.animation_id == 123
        assert new_entry.camera_angle == 45
        assert new_entry.camera_id == 1
        assert new_entry.fade_type == 2
        assert new_entry.quest == "MainQuest"
        assert new_entry.sound == "voice.wav"
        assert new_entry.vo_resref == "npc_line"


def test_twine_specific_features():
    """Test preservation of Twine-specific features."""
    metadata: dict[str, Any] = {
        "name": "Test Story",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "tag-colors": {"reply": "green"},
        "style": "body { color: red; }",
        "script": "window.setup = {};",
        "zoom": 1.5,
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json", metadata=metadata)

        # Verify JSON structure
        with open(f.name, encoding="utf-8") as f2:
            data: dict[str, Any] = json.load(f2)
            assert data["name"] == metadata["name"]
            assert data["format"] == metadata["format"]
            assert data["format-version"] == metadata["format-version"]
            assert data["tag-colors"] == metadata["tag-colors"]
            assert data["style"] == metadata["style"]
            assert data["script"] == metadata["script"]
            assert data["zoom"] == metadata["zoom"]


def test_large_dialog():
    """Test handling of large dialog structures."""
    dlg = DLG()
    prev_entry = None

    # Create a long chain of 1000 nodes
    for i in range(1000):
        entry = DLGEntry()
        entry.speaker = f"NPC{i}"
        entry.text.set_data(Language.ENGLISH, Gender.MALE, f"Text {i}")

        if prev_entry is None:
            dlg.starters.append(DLGLink(entry))
        else:
            reply = DLGReply()
            reply.text.set_data(Language.ENGLISH, Gender.MALE, f"Reply {i}")
            prev_entry.links.append(DLGLink(reply))
            reply.links.append(DLGLink(entry))

        prev_entry = entry

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        assert len(new_dlg.all_entries()) == 1000
        assert len(new_dlg.all_replies()) == 999


def test_missing_fields():
    """Test handling of missing fields in Twine format."""
    # Create minimal JSON
    minimal_json = {
        "passages": [
            {
                "text": "Some text"
                # Missing name, tags, etc.
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        json.dump(minimal_json, f)
        f.flush()
        dlg = read_twine(f.name)
        assert len(dlg.all_entries()) + len(dlg.all_replies()) > 0


def test_duplicate_passage_names():
    """Test handling of duplicate passage names."""
    dlg = DLG()

    # Create entries with same speaker name
    entry1 = DLGEntry()
    entry1.speaker = "NPC"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "First")

    entry2 = DLGEntry()
    entry2.speaker = "NPC"  # Same speaker name
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Second")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "Reply")

    # Link them
    entry1.links.append(DLGLink(reply))
    reply.links.append(DLGLink(entry2))
    dlg.starters.append(DLGLink(entry1))

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        assert len(new_dlg.all_entries()) == 2
        assert len(new_dlg.all_replies()) == 1


def test_empty_text():
    """Test handling of empty or None text."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    # Don't set any text
    dlg.starters.append(DLGLink(entry))

    # Convert to Twine and back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json")
        new_dlg = read_twine(f.name)

        new_entry = new_dlg.starters[0].node
        assert isinstance(new_entry, DLGEntry)
        assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == ""


def test_invalid_metadata():
    """Test handling of invalid metadata."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    # Invalid metadata
    invalid_metadata = {
        "zoom": "not a number",  # Should be float
        "tag-colors": "not a dict",  # Should be dict
    }

    # Should not raise exception
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name, format="json", metadata=invalid_metadata)
        new_dlg = read_twine(f.name)
        assert len(new_dlg.starters) == 1


def test_file_not_found():
    """Test handling of non-existent files."""
    with pytest.raises(FileNotFoundError):
        read_twine("nonexistent.json")

    with pytest.raises(FileNotFoundError):
        read_twine("nonexistent.html")
