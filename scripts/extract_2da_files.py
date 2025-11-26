#!/usr/bin/env python3
"""Extract individual 2DA file sections from 2DA-File-Format.md into separate files."""

import re
from pathlib import Path

wiki_dir = Path("wiki")
twoda_file = wiki_dir / "2DA-File-Format.md"

# Map section headers to their start lines and determine file names
# Read the file to find all 2DA file sections
with open(twoda_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find all 2DA file sections (### filename.2da pattern)
sections = []
i = 0
while i < len(lines):
    line = lines[i].strip()
    # Match ### filename.2da or ### filename.2da / other.2da or similar patterns
    match = re.match(r"^### ([a-zA-Z_][a-zA-Z0-9_/ \*\.]+\.2da)", line)
    if match:
        section_title = match.group(1)
        start_line = i
        # Find end of section (next ### or ## that isn't a subsection)
        end_line = len(lines)
        for j in range(i + 1, len(lines)):
            next_line = lines[j].strip()
            # Stop at next ### (2DA file) or ## (category) but not #### (subsection)
            if (next_line.startswith("### ") and not next_line.startswith("#### ")) or next_line.startswith("## "):
                end_line = j
                break
        
        # Determine file name - handle special cases
        if "/" in section_title:
            # Handle "genericdoors.2da / doortypes.2da" - create two separate files
            parts = [p.strip() for p in section_title.split("/")]
            for part in parts:
                if part.endswith(".2da"):
                    filename = part.replace(".2da", "").replace(" ", "_")
                    sections.append({
                        "title": part,
                        "start": start_line,
                        "end": end_line,
                        "filename": f"2DA-{filename}.md",
                        "full_title": section_title
                    })
        elif "*" in section_title:
            # Handle pattern-based like "cls_atk_*.2da" - use base name
            filename = section_title.replace("*.2da", "_pattern").replace(".2da", "").replace(" ", "_")
            sections.append({
                "title": section_title,
                "start": start_line,
                "end": end_line,
                "filename": f"2DA-{filename}.md",
                "full_title": section_title
            })
        else:
            # Regular file
            filename = section_title.replace(".2da", "").replace(" ", "_")
            sections.append({
                "title": section_title,
                "start": start_line,
                "end": end_line,
                "filename": f"2DA-{filename}.md",
                "full_title": section_title
            })
        
        i = end_line
    else:
        i += 1

print(f"Found {len(sections)} 2DA file sections to extract")

# Extract and create files for each section
for section in sections:
    start_line = section["start"]
    end_line = section["end"]
    
    # Extract section content
    section_lines = lines[start_line:end_line]
    section_content = "".join(section_lines)
    
    # Remove "Implementation Details" section if it exists
    if "## Implementation Details" in section_content:
        section_content = section_content.split("## Implementation Details")[0].rstrip()
        section_content = re.sub(r"\n---+?\s*$", "", section_content, flags=re.MULTILINE)
    
    # Extract the title from the first line
    lines_list = section_content.split("\n")
    first_header_line = None
    for i, line in enumerate(lines_list):
        if line.strip().startswith("### "):
            first_header_line = i
            break
    
    if first_header_line is not None:
        title_line = lines_list[first_header_line]
        full_title = re.match(r"^### (.+)$", title_line).group(1)
        
        # Handle "/" in title - extract just the first part for this file
        if "/" in full_title:
            # This is for files like "genericdoors.2da / doortypes.2da"
            # Extract the part we want for this file
            target_part = section["title"]
            # Keep only content related to this specific file
            # For now, just use the title as-is
            full_title = target_part
        
        # Change the first ### header to # for page title
        lines_list[first_header_line] = f"# {full_title}"
        
        # Change all other headers: #### becomes ##, ### becomes ##
        for i in range(len(lines_list)):
            if i != first_header_line:
                if lines_list[i].strip().startswith("#### "):
                    lines_list[i] = lines_list[i].replace("#### ", "## ", 1)
                elif lines_list[i].strip().startswith("### "):
                    lines_list[i] = lines_list[i].replace("### ", "## ", 1)
        
        # Rebuild content
        section_content = "\n".join(lines_list)
        
        # Add link back to main 2DA file right after the title
        section_content = section_content.replace(
            f"# {full_title}\n",
            f"# {full_title}\n\nPart of the [2DA File Format Documentation](2DA-File-Format).\n\n",
            1
        )
    
    output_file = wiki_dir / section["filename"]
    
    # Write the file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(section_content)
    
    print(f"Created {section['filename']} (lines {start_line+1}-{end_line}, title: {section['title']})")

print(f"\nExtracted {len(sections)} 2DA file documentation files")

