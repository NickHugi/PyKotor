#!/usr/bin/env python3
"""Extract individual NSS function/constant category sections from NSS-File-Format.md into separate files."""

import re
from pathlib import Path

wiki_dir = Path("wiki")
nss_file = wiki_dir / "NSS-File-Format.md"

# Read the file
with open(nss_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find all ### sections that are function/constant categories
# We want to skip implementation sections like "Data Structures", "Compilation Integration"
sections_to_extract = []

# Track current parent section (## level)
current_parent = None

i = 0
while i < len(lines):
    line = lines[i]
    
    # Check for parent sections (## level)
    parent_match = re.match(r"^## (.+)$", line.strip())
    if parent_match:
        parent_name = parent_match.group(1)
        # Skip certain sections
        if parent_name not in ["Table of Contents", "PyKotor Implementation", "Commented-Out Elements in nwscript.nss", "Reference Implementations", "Cross-References"]:
            current_parent = parent_name
        else:
            current_parent = None
    
    # Check for ### sections (sub-categories)
    if current_parent and line.strip().startswith("### "):
        section_match = re.match(r"^### (.+)$", line.strip())
        if section_match:
            section_title = section_match.group(1)
            
            # Skip certain sub-sections we don't want to extract
            if section_title not in ["Data Structures", "Compilation Integration", 
                                      "Reasons for Commented-Out Elements", "Key Examples of Commented Elements",
                                      "Common Modder Workarounds", "Forum Discussions and Community Knowledge",
                                      "Attempts to Uncomment or Modify", "Key Citations"]:
                
                # Find the end of this section
                start_line = i
                end_line = len(lines)
                
                # Look for next ### or ## section
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("### ") or lines[j].strip().startswith("## "):
                        # Check if it's the end of this parent section
                        if lines[j].strip().startswith("## "):
                            end_line = j
                            break
                        elif lines[j].strip().startswith("### "):
                            # Check if it's a new category (not a sub-subsection like ####)
                            next_match = re.match(r"^### (.+)$", lines[j].strip())
                            if next_match:
                                end_line = j
                                break
                
                # Create filename from parent and section title
                parent_clean = current_parent.replace(" (K1 & TSL)", "").replace(" (K1)", "-K1").replace(" (TSL)", "-TSL").replace(" ", "-")
                section_clean = section_title.replace(" ", "-").replace("/", "-")
                filename = f"NSS-{parent_clean}-{section_clean}.md"
                
                # Handle duplicate names (e.g., "Actions" appears in both Shared and TSL-Only)
                # But since we're including parent in filename, this should be unique
                
                sections_to_extract.append({
                    "title": section_title,
                    "parent": current_parent,
                    "start": start_line,
                    "end": end_line,
                    "filename": filename,
                    "full_title": f"{current_parent} - {section_title}"
                })
    
    i += 1

print(f"Found {len(sections_to_extract)} NSS sections to extract")

# Extract and create files
for section in sections_to_extract:
    start_line = section["start"]
    end_line = section["end"]
    
    # Extract section content
    section_lines = lines[start_line:end_line]
    section_content = "".join(section_lines)
    
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
        
        # Change the first ### header to # for page title
        lines_list[first_header_line] = f"# {full_title}"
        
        # Adjust header levels: #### becomes ##, ### becomes ##
        for i in range(len(lines_list)):
            if i != first_header_line:
                if lines_list[i].strip().startswith("#### "):
                    lines_list[i] = lines_list[i].replace("#### ", "## ", 1)
                elif lines_list[i].strip().startswith("### "):
                    lines_list[i] = lines_list[i].replace("### ", "## ", 1)
        
        # Rebuild content
        section_content = "\n".join(lines_list)
        
        # Add link back to main NSS file and parent section info
        section_content = section_content.replace(
            f"# {full_title}\n",
            f"# {full_title}\n\nPart of the [NSS File Format Documentation](NSS-File-Format).\n\n**Category:** {section['parent']}\n\n",
            1
        )
    
    output_file = wiki_dir / section["filename"]
    
    # Write the file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(section_content)
    
    print(f"Created {section['filename']} (lines {start_line+1}-{end_line}, title: {section['full_title']})")

print(f"\nExtracted {len(sections_to_extract)} NSS section documentation files")

