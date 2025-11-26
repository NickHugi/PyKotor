#!/usr/bin/env python3
"""Update NSS-File-Format.md by replacing extracted sections with links."""

import re
from pathlib import Path

wiki_dir = Path("wiki")
nss_file = wiki_dir / "NSS-File-Format.md"

# Read the file
with open(nss_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Build map of section titles to file names, considering parent context
section_to_file = {}
for file_path in sorted(wiki_dir.glob("NSS-*.md")):
    if file_path.name == "NSS-File-Format.md":
        continue
    
    # Read first few lines to get title and category
    with open(file_path, "r", encoding="utf-8") as f:
        first_lines = f.readlines()[:15]
        title = None
        category = None
        for line in first_lines:
            if line.strip().startswith("# ") and not line.strip().startswith("# Part"):
                title = line.strip().replace("# ", "").strip()
            if "**Category:**" in line:
                category_match = re.search(r'\*\*Category:\*\* (.+)', line)
                if category_match:
                    category = category_match.group(1).strip()
                    break
        
        if title and category:
            # Create a unique key combining category and title
            key = f"{category}|{title}"
            section_to_file[key] = file_path.name.replace(".md", "")

# Track current parent section
current_parent = None

new_content = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check for parent sections (## level)
    parent_match = re.match(r"^## (.+)$", line.strip())
    if parent_match:
        parent_name = parent_match.group(1)
        # Skip certain sections that aren't function/constant sections
        if parent_name not in ["Table of Contents", "PyKotor Implementation", "Commented-Out Elements in nwscript.nss", "Reference Implementations", "Cross-References"]:
            current_parent = parent_name
        else:
            current_parent = None
        new_content.append(line)
        i += 1
        continue
    
    # Check if this is a ### section header that we extracted
    match = re.match(r"^### (.+)$", line.strip())
    if match and current_parent:
        section_title = match.group(1)
        
        # Skip sections we don't extract
        if section_title in ["Data Structures", "Compilation Integration"]:
            new_content.append(line)
            i += 1
            continue
        
        # Create unique key
        key = f"{current_parent}|{section_title}"
        
        # Check if this section was extracted
        if key in section_to_file:
            # Find end of this section
            start_idx = i
            end_idx = len(lines)
            
            # Look for next ### or ## section
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith("### ") or lines[j].strip().startswith("## "):
                    end_idx = j
                    break
            
            filename = section_to_file[key]
            display_name = section_title
            
            # Replace with link
            new_content.append(f"### {display_name}\n")
            new_content.append("\n")
            new_content.append(f"See [{display_name}]({filename}) for detailed documentation.\n")
            new_content.append("\n")
            
            # Skip to end of section
            i = end_idx
            continue
    
    # Not an extracted section - keep the line
    new_content.append(line)
    i += 1

# Write the updated file
with open(nss_file, "w", encoding="utf-8") as f:
    f.writelines(new_content)

print("Updated NSS-File-Format.md with links to extracted files")
