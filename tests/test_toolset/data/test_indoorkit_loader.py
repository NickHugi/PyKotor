"""Tests for indoorkit loader, specifically the available_kits.json issue."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Any
import unittest
from pathlib import Path

# Force offscreen (headless) mode for Qt
# This ensures tests don't fail if no display is available (e.g. CI/CD)
# Must be set before any Qt imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add paths for imports
REPO_ROOT = Path(__file__).parents[3]
TOOLS_PATH = REPO_ROOT / "Tools"
LIBS_PATH = REPO_ROOT / "Libraries"

TOOLSET_SRC = TOOLS_PATH / "HolocronToolset" / "src"
PYKOTOR_PATH = LIBS_PATH / "PyKotor" / "src"
UTILITY_PATH = LIBS_PATH / "Utility" / "src"

if str(TOOLSET_SRC) not in sys.path:
    sys.path.insert(0, str(TOOLSET_SRC))
if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))
if str(UTILITY_PATH) not in sys.path:
    sys.path.insert(0, str(UTILITY_PATH))

from toolset.data.indoorkit.indoorkit_base import Kit
from toolset.data.indoorkit.indoorkit_loader import load_kits  # noqa: E402


class TestIndoorKitLoader(unittest.TestCase):
    """Test indoorkit loader with available_kits.json issue."""

    def test_load_kits_with_available_kits_json_list(self):
        """Test that load_kits() handles available_kits.json being a list without crashing.
        
        This test reproduces the issue where available_kits.json contains a list
        like ["endarspire"] instead of a dict, causing TypeError when trying to
        access kit_json["name"].
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            kits_path: Path = Path(tmpdir) / "kits"
            kits_path.mkdir(parents=True)
            
            # Create a valid kit JSON file
            valid_kit_json: dict[str, Any] = {
                "name": "Test Kit",
                "id": "testkit",
                "ht": "2.2.1",
                "version": 1,
                "doors": [],
                "components": []
            }
            valid_kit_file: Path = kits_path / "testkit.json"
            valid_kit_file.write_text(json.dumps(valid_kit_json), encoding="utf-8")
            
            # Create minimal directory structure for the kit
            kit_dir: Path = kits_path / "testkit"
            kit_dir.mkdir()
            (kit_dir / "textures").mkdir()
            (kit_dir / "lightmaps").mkdir()
            
            # Create the problematic available_kits.json file (a list, not a dict)
            available_kits_json: list[str] = ["testkit"]
            available_kits_file: Path = kits_path / "available_kits.json"
            available_kits_file.write_text(json.dumps(available_kits_json), encoding="utf-8")
            
            # This should not raise TypeError
            # Before the fix, it would crash with:
            # TypeError: list indices must be integers or slices, not str
            kits: list[Kit] = load_kits(str(kits_path))
            
            # Should only load the valid kit, not crash on available_kits.json
            self.assertEqual(len(kits), 1, "Should load exactly one valid kit")
            self.assertEqual(kits[0].name, "Test Kit", "Loaded kit should have correct name")

    def test_load_kits_with_invalid_json_structure(self):
        """Test that load_kits() handles JSON files that aren't valid kit dicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kits_path = Path(tmpdir) / "kits"
            kits_path.mkdir(parents=True)
            
            # Create a valid kit JSON file
            valid_kit_json = {
                "name": "Test Kit",
                "id": "testkit",
                "ht": "2.2.1",
                "version": 1,
                "doors": [],
                "components": []
            }
            valid_kit_file = kits_path / "testkit.json"
            valid_kit_file.write_text(json.dumps(valid_kit_json), encoding="utf-8")
            
            # Create minimal directory structure for the kit
            kit_dir = kits_path / "testkit"
            kit_dir.mkdir()
            (kit_dir / "textures").mkdir()
            (kit_dir / "lightmaps").mkdir()
            
            # Create various invalid JSON files that should be skipped
            # 1. A list (like available_kits.json)
            list_file = kits_path / "list_file.json"
            list_file.write_text(json.dumps(["item1", "item2"]), encoding="utf-8")
            
            # 2. A dict without required fields
            invalid_dict_file = kits_path / "invalid_dict.json"
            invalid_dict_file.write_text(json.dumps({"not_a_kit": True}), encoding="utf-8")
            
            # 3. A string (shouldn't happen but test it)
            string_file = kits_path / "string_file.json"
            string_file.write_text(json.dumps("just a string"), encoding="utf-8")
            
            # This should not raise any exceptions
            kits = load_kits(str(kits_path))
            
            # Should only load the valid kit
            self.assertEqual(len(kits), 1, "Should load exactly one valid kit")
            self.assertEqual(kits[0].name, "Test Kit", "Loaded kit should have correct name")


if __name__ == "__main__":
    unittest.main()

