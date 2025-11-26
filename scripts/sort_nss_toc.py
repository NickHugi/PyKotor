#!/usr/bin/env python3
"""Sort the TOC in NSS-File-Format.md alphabetically within each section."""

import re
from pathlib import Path

wiki_dir = Path("wiki")
nss_file = wiki_dir / "NSS-File-Format.md"

# Read the file
with open(nss_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the TOC section
toc_start = None
toc_end = None

for i, line in enumerate(lines):
    if "## Table of Contents" in line:
        toc_start = i
    elif toc_start is not None and line.strip().startswith("---") and i > toc_start + 5:
        toc_end = i
        break

if toc_start is None or toc_end is None:
    print("Could not find TOC section")
    exit(1)

print(f"Found TOC from line {toc_start+1} to {toc_end+1}")

# Extract TOC content
toc_lines = lines[toc_start:toc_end]
new_toc_lines = []

def get_sort_key(item):
    """Extract sort key from a TOC item line."""
    match = re.search(r'\[([^\]]+)\]', item)
    if match:
        text = match.group(1)
        # Remove backslash escapes for sorting
        text = text.replace('\\_', '_').replace('\\*', '*').replace('\\&', '&')
        # Convert to lowercase for case-insensitive sorting
        return text.lower()
    return item.lower()

i = 0
section_count = 0
while i < len(toc_lines):
    line = toc_lines[i]
    
    # Check if this is a section header (starts with "- [" and is NOT indented with 4 spaces)
    # Section headers have 2 spaces of indentation
    if line.strip().startswith("- [") and not line.startswith("    "):
        # Check if next line is a sub-item (indented with 4 spaces)
        if i + 1 < len(toc_lines) and toc_lines[i + 1].startswith("    - ["):
            # This is a section with sub-items - collect them all
            section_header = line
            sub_items = []
            
            j = i + 1
            while j < len(toc_lines) and toc_lines[j].startswith("    - ["):
                sub_items.append(toc_lines[j])
                j += 1
            
            if len(sub_items) > 0:
                section_count += 1
            
            # Sort sub-items alphabetically by the text between [ and ](
            sub_items_sorted = sorted(sub_items, key=get_sort_key)
            
            # Add header and sorted sub-items
            new_toc_lines.append(section_header)
            new_toc_lines.extend(sub_items_sorted)
            
            i = j
            continue
    
    # Regular line (not a section header with sub-items), just add it
    new_toc_lines.append(line)
    i += 1

print(f"Processed {section_count} sections with sub-items")

# Replace TOC section
new_lines = lines[:toc_start] + new_toc_lines + lines[toc_end:]

# Write back
with open(nss_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Sorted TOC alphabetically within each section")

