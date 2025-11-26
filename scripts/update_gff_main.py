#!/usr/bin/env python3
"""Update GFF-File-Format.md to replace generic type sections with links."""

from pathlib import Path
import re

wiki_dir = Path("wiki")
gff_file = wiki_dir / "GFF-File-Format.md"

# Section headers and their file names
sections = [
    ("ARE (Area)", "GFF-ARE"),
    ("DLG (Dialogue)", "GFF-DLG"),
    ("GIT (Game Instance Template)", "GFF-GIT"),
    ("GUI", "GFF-GUI"),
    ("IFO (Module Info)", "GFF-IFO"),
    ("JRL (Journal)", "GFF-JRL"),
    ("PTH (Path)", "GFF-PTH"),
    ("UTC (Creature)", "GFF-UTC"),
    ("UTD (Door)", "GFF-UTD"),
    ("UTE (Encounter)", "GFF-UTE"),
    ("UTI (Item)", "GFF-UTI"),
    ("UTM (Merchant)", "GFF-UTM"),
    ("UTP (Placeable)", "GFF-UTP"),
    ("UTS (Sound)", "GFF-UTS"),
    ("UTT (Trigger)", "GFF-UTT"),
    ("UTW (Waypoint)", "GFF-UTW"),
]

# Read the file
with open(gff_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace each section with a link
for section_title, file_name in sections:
    # Pattern to match from ### Section Title to the next ### or end of Generic Types section
    # We need to match everything from "### Section Title" to just before the next "###" or before "## Implementation Details"
    pattern = rf"### {re.escape(section_title)}.*?(?=\n### |\n## Implementation Details|\Z)"
    
    # Replacement: just a link with blank line after
    replacement = f"### {section_title}\n\nSee [{section_title}]({file_name}) for detailed documentation.\n"
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open(gff_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated GFF-File-Format.md")

