"""Edge case tests for Twine format support in dialog system."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine

if TYPE_CHECKING:
    from typing import Any


def test_empty_dialog(
    tmp_path: Path,
) -> None:
    """Test handling of empty dialog with no nodes."""
    dlg = DLG()
    json_file: Path = tmp_path / "empty.json"
    write_twine(dlg, json_file)

    # Verify JSON structure
    with open(json_file, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        assert len(data["passages"]) == 0

    # Read back
    loaded_dlg: DLG = read_twine(json_file)
    assert len(loaded_dlg.starters) == 0
    assert len(loaded_dlg.all_entries()) == 0
    assert len(loaded_dlg.all_replies()) == 0


def test_circular_references():
    """Test handling of circular references between nodes."""
    dlg = DLG()

    # Create a circular reference
    entry1 = DLGEntry()
    entry1.speaker = "NPC1"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "First")

    reply1 = DLGReply()
    reply1.text.set_data(Language.ENGLISH, Gender.MALE, "Back to start")

    # Create circular reference
    entry1.links.append(DLGLink(reply1))
    reply1.links.append(DLGLink(entry1))

    dlg.starters.append(DLGLink(entry1))

    # Should not cause infinite recursion
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)

        # Verify structure preserved
        assert len(loaded_dlg.starters) == 1
        loaded_entry: DLGEntry = cast(DLGEntry, loaded_dlg.starters[0].node)
        assert isinstance(loaded_entry, DLGEntry)
        assert len(loaded_entry.links) == 1
        loaded_reply: DLGReply = cast(DLGReply, loaded_entry.links[0].node)
        assert isinstance(loaded_reply, DLGReply)
        assert len(loaded_reply.links) == 1
        assert isinstance(loaded_reply.links[0].node, DLGEntry)


def test_special_characters():
    """Test handling of special characters in text and metadata."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC <with> special & chars"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Text with <tags> & special chars")
    entry.comment = json.dumps({"position": "100,200", "size": "100,100", "custom": "Value with <tags> & special chars"})
    dlg.starters.append(DLGLink(entry))

    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)

        # Verify special chars preserved
        loaded_entry: DLGEntry = cast(DLGEntry, loaded_dlg.starters[0].node)
        assert isinstance(loaded_entry, DLGEntry)
        assert loaded_entry.speaker == "NPC <with> special & chars"
        assert loaded_entry.text.get(Language.ENGLISH, Gender.MALE) == "Text with <tags> & special chars"
        metadata: dict[str, Any] = json.loads(loaded_entry.comment)
        assert metadata["custom"] == "Value with <tags> & special chars"


def test_multiple_languages():
    """Test handling of multiple languages in node text."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "English text")
    entry.text.set_data(Language.FRENCH, Gender.MALE, "French text")
    entry.text.set_data(Language.GERMAN, Gender.MALE, "German text")
    dlg.starters.append(DLGLink(entry))

    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)

        # Verify all languages preserved
        loaded_entry: DLGEntry = cast(DLGEntry, loaded_dlg.starters[0].node)
        assert isinstance(loaded_entry, DLGEntry)
        assert loaded_entry.text.get(Language.ENGLISH, Gender.MALE) == "English text"
        assert loaded_entry.text.get(Language.FRENCH, Gender.MALE) == "French text"
        assert loaded_entry.text.get(Language.GERMAN, Gender.MALE) == "German text"


def test_invalid_metadata():
    """Test handling of invalid metadata in comments."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.comment = "Invalid JSON {{"  # Invalid JSON
    dlg.starters.append(DLGLink(entry))

    # Should not raise exception
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)
        assert len(loaded_dlg.starters) == 1


def test_missing_required_fields():
    """Test handling of missing required fields in Twine format."""
    # Create minimal JSON without required fields
    minimal_json: dict[str, list[dict[str, str]]] = {
        "passages": [
            {
                "text": "Some text"
                # Missing 'name' and 'tags' fields
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        json.dump(minimal_json, f)
        f.flush()
        # Should not raise exception
        dlg: DLG = read_twine(f.name)
        assert len(dlg.all_entries()) + len(dlg.all_replies()) > 0


def test_duplicate_passage_names():
    """Test handling of duplicate passage names in Twine format."""
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

    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)

        # Verify structure preserved
        assert len(loaded_dlg.starters) == 1
        assert len(loaded_dlg.all_entries()) == 2
        assert len(loaded_dlg.all_replies()) == 1


def test_empty_text():
    """Test handling of empty or None text in nodes."""
    dlg = DLG()

    entry = DLGEntry()
    entry.speaker = "NPC"
    # Don't set any text
    dlg.starters.append(DLGLink(entry))

    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)

        # Verify empty text handled
        loaded_entry: DLGEntry = cast(DLGEntry, loaded_dlg.starters[0].node)
        assert isinstance(loaded_entry, DLGEntry)
        assert loaded_entry.text.get(Language.ENGLISH, Gender.MALE) == ""


def test_large_dialog():
    """Test handling of large dialog structures."""
    dlg = DLG()
    prev_entry: DLGEntry | None = None

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

    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)

        # Verify structure preserved
        assert len(loaded_dlg.all_entries()) == 1000
        assert len(loaded_dlg.all_replies()) == 999  # One less reply than entries


def test_unicode_characters():
    """Test handling of Unicode characters in text and metadata."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC 🚀"  # Emoji
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello 世界")  # Chinese
    entry.text.set_data(Language.FRENCH, Gender.MALE, "Bonjour 🌍")  # French with emoji
    entry.comment = json.dumps(
        {
            "position": "100,200",
            "custom": "Value with 漢字",  # Japanese
        }
    )
    dlg.starters.append(DLGLink(entry))

    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        write_twine(dlg, f.name)
        loaded_dlg: DLG = read_twine(f.name)

        # Verify Unicode preserved
        loaded_entry: DLGEntry = cast(DLGEntry, loaded_dlg.starters[0].node)
        assert isinstance(loaded_entry, DLGEntry)
        assert loaded_entry.speaker == "NPC 🚀"
        assert loaded_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello 世界"
        assert loaded_entry.text.get(Language.FRENCH, Gender.MALE) == "Bonjour 🌍"
        metadata: dict[str, Any] = json.loads(loaded_entry.comment)
        assert metadata["custom"] == "Value with 漢字"
