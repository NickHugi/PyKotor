#!/usr/bin/env python3
"""Update 2DA-File-Format.md by replacing extracted sections with links."""

import re
from pathlib import Path

wiki_dir = Path("wiki")
twoda_file = wiki_dir / "2DA-File-Format.md"

# Read the file
with open(twoda_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_content = []
i = 0
in_known_files_section = False

# Map of section titles to file names
section_to_file = {}

# Build map by reading all the generated files
for file_path in sorted(wiki_dir.glob("2DA-*.md")):
    if file_path.name == "2DA-File-Format.md":
        continue
    
    # Read first line to get title
    with open(file_path, "r", encoding="utf-8") as f:
        first_lines = f.readlines()[:5]
        for line in first_lines:
            if line.strip().startswith("# ") and not line.strip().startswith("# Part"):
                title = line.strip().replace("# ", "").strip()
                section_to_file[title] = file_path.name.replace(".md", "")
                break

while i < len(lines):
    line = lines[i]
    
    # Check if we're entering the "Known 2DA Files" section
    if "## Known 2DA Files" in line:
        in_known_files_section = True
        new_content.append(line)
        i += 1
        continue
    
    # Check if we're leaving the "Known 2DA Files" section (Implementation Details)
    if in_known_files_section and line.strip().startswith("## Implementation Details"):
        in_known_files_section = False
        new_content.append("\n")
        new_content.append(line)
        i += 1
        continue
    
    if in_known_files_section:
        # Check if this is a category header (##)
        if line.strip().startswith("## ") and not line.strip().startswith("###"):
            # Category header - keep it
            new_content.append(line)
            i += 1
            # Add a blank line after category
            if i < len(lines) and lines[i].strip() != "":
                new_content.append("\n")
            continue
        
        # Check if this is a 2DA file section (### filename.2da)
        match = re.match(r"^### ([a-zA-Z_][a-zA-Z0-9_/ \*\.]+\.2da)", line.strip())
        if match:
            section_title = match.group(1)
            
            # Find end of this section
            start_idx = i
            end_idx = len(lines)
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if (next_line.startswith("### ") and not next_line.startswith("#### ")) or next_line.startswith("## "):
                    end_idx = j
                    break
            
            # Handle "/" in title - create entries for both files
            if "/" in section_title:
                parts = [p.strip() for p in section_title.split("/")]
                for part in parts:
                    if part.endswith(".2da"):
                        file_key = part
                        if file_key in section_to_file:
                            filename = section_to_file[file_key]
                            display_name = part.replace(".2da", "")
                            new_content.append(f"### {display_name}.2da\n")
                            new_content.append("\n")
                            new_content.append(f"See [{display_name}.2da]({filename}) for detailed documentation.\n")
                            new_content.append("\n")
            elif "*" in section_title:
                # Pattern-based section - use the pattern name
                display_name = section_title.replace("*.2da", "_*").replace(".2da", "")
                pattern_name = section_title.replace(".2da", "_pattern")
                if pattern_name in section_to_file:
                    filename = section_to_file[pattern_name]
                    new_content.append(f"### {section_title}\n")
                    new_content.append("\n")
                    new_content.append(f"See [{section_title}]({filename}) for detailed documentation.\n")
                    new_content.append("\n")
                else:
                    # Just create a simple link
                    filename = pattern_name.replace("*", "_pattern")
                    new_content.append(f"### {section_title}\n")
                    new_content.append("\n")
                    new_content.append(f"See [{section_title}]({filename}) for detailed documentation.\n")
                    new_content.append("\n")
            else:
                # Regular file
                if section_title in section_to_file:
                    filename = section_to_file[section_title]
                    display_name = section_title.replace(".2da", "")
                    new_content.append(f"### {display_name}.2da\n")
                    new_content.append("\n")
                    new_content.append(f"See [{display_name}.2da]({filename}) for detailed documentation.\n")
                    new_content.append("\n")
                else:
                    # Fallback - create link anyway
                    filename = section_title.replace(".2da", "").replace(" ", "_")
                    new_content.append(f"### {section_title}\n")
                    new_content.append("\n")
                    new_content.append(f"See [{section_title}](2DA-{filename}) for detailed documentation.\n")
                    new_content.append("\n")
            
            # Skip to end of section
            i = end_idx
            continue
    
    # Not in known files section or not a 2DA file section - keep the line
    new_content.append(line)
    i += 1

# Write the updated file
with open(twoda_file, "w", encoding="utf-8") as f:
    f.writelines(new_content)

print("Updated 2DA-File-Format.md with links to extracted files")

