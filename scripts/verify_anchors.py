#!/usr/bin/env python3
"""Verify that all functions and constants have anchors."""

import re
from pathlib import Path

md_path = Path(__file__).parent.parent / "wiki" / "NSS-File-Format.md"

with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all functions (may have content before/after the **`...`** pattern)
funcs = set()
for match in re.finditer(r'\*\*`(\w+)\([^)]*\)`\*\*', content):
    funcs.add(match.group(1))
print(f"Total functions: {len(funcs)}")

# Extract all constants (must start with - at beginning of line after stripping)
consts = set()
for line in content.split('\n'):
    line_stripped = line.strip()
    const_match = re.match(r'^- `(\w+)`\s*\([^)]+\):', line_stripped)
    if const_match:
        consts.add(const_match.group(1))
print(f"Total constants: {len(consts)}")

# Extract all anchors
anchors = set(re.findall(r'<a id="([^"]+)">', content))
print(f"Total anchors: {len(anchors)}")

# Check title_to_anchor function logic
def title_to_anchor(title: str) -> str:
    anchor = title.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'[-\s]+', '-', anchor)
    return anchor.strip('-')

# Check which functions/constants are missing anchors
missing_funcs = []
for func in funcs:
    anchor = title_to_anchor(func)
    if anchor not in anchors:
        missing_funcs.append((func, anchor))

missing_consts = []
for const in consts:
    anchor = title_to_anchor(const)
    if anchor not in anchors:
        missing_consts.append((const, anchor))

print(f"\nMissing function anchors: {len(missing_funcs)}")
if missing_funcs:
    print("First 10 missing:")
    for func, anchor in missing_funcs[:10]:
        print(f"  {func} -> {anchor}")

print(f"\nMissing constant anchors: {len(missing_consts)}")
if missing_consts:
    print("First 10 missing:")
    for const, anchor in missing_consts[:10]:
        print(f"  {const} -> {anchor}")

# Check TOC entries
toc_funcs = set(re.findall(r'^\s{4}- \[`(\w+)`\]\(#', content, re.MULTILINE))
toc_consts = set(re.findall(r'^\s{4}- \[`(\w+)`\]\(#', content, re.MULTILINE))
print(f"\nTOC function entries: {len(toc_funcs)}")
print(f"TOC constant entries: {len(toc_funcs)}")  # Same pattern for both

if len(missing_funcs) == 0 and len(missing_consts) == 0:
    print("\n✓ All functions and constants have anchors!")
else:
    print(f"\n✗ Missing {len(missing_funcs) + len(missing_consts)} anchors total")

