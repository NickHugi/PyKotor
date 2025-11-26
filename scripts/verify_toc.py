#!/usr/bin/env python3
"""Verify that all sections are in the TOC."""

import re
from pathlib import Path

md_path = Path(__file__).parent.parent / "wiki" / "NSS-File-Format.md"

with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all sections
sections = re.findall(r'^###? (.+)$', content, re.MULTILINE)

# Extract TOC entries
toc_entries = re.findall(r'^\s*- \[(.+?)\]\(#', content, re.MULTILINE)

print(f"Total sections: {len(sections)}")
print(f"Total TOC entries: {len(toc_entries)}")
print(f"Difference: {len(sections) - len(toc_entries)}")

# Find missing sections
section_set = set(sections)
toc_set = set(toc_entries)
missing = section_set - toc_set

if missing:
    print(f"\nMissing from TOC ({len(missing)}):")
    for section in sorted(missing):
        print(f"  - {section}")
else:
    print("\n✓ All sections are in the TOC!")

# Find extra TOC entries
extra = toc_set - section_set
if extra:
    print(f"\nExtra TOC entries ({len(extra)}):")
    for entry in sorted(extra):
        print(f"  - {entry}")

