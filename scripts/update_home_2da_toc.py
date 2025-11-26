#!/usr/bin/env python3
"""Update Home.md to add all 2DA files to the TOC under the 2DA File Format entry."""

import re
from pathlib import Path

wiki_dir = Path("wiki")
home_file = wiki_dir / "Home.md"

# Get all 2DA file names (sorted, excluding the main file)
twoda_files = sorted([f.name.replace("2DA-", "").replace(".md", "") 
                     for f in wiki_dir.glob("2DA-*.md") 
                     if f.name != "2DA-File-Format.md"])

# Read Home.md
with open(home_file, "r", encoding="utf-8") as f:
    content = f.read()

# Find the 2DA File Format line
pattern = r"(- \*\*\[2DA File Format\]\(2DA-File-Format\)\*\*.*?\n)"
match = re.search(pattern, content)

if match:
    # Get the line
    twoda_line = match.group(1)
    
    # Check if it's already indented (has sub-items)
    lines = content.split("\n")
    twoda_index = None
    for i, line in enumerate(lines):
        if "2DA File Format" in line and "File Formats" in content[max(0, i-10):i]:
            twoda_index = i
            break
    
    if twoda_index is not None:
        # Check if sub-items already exist
        next_line_index = twoda_index + 1
        has_sub_items = (next_line_index < len(lines) and 
                        lines[next_line_index].startswith("  -"))
        
        if not has_sub_items:
            # Need to indent the main line and add sub-items
            # First, indent the main line
            lines[twoda_index] = "  " + lines[twoda_index].lstrip()
            
            # Now add all 2DA file entries
            twoda_entries = []
            for twoda_file in twoda_files:
                # Convert file name to display name (add .2da extension where appropriate)
                display_name = twoda_file
                
                # Handle special cases
                if twoda_file.endswith("_pattern"):
                    # Pattern files like cls_atk__pattern
                    if "cls_atk" in twoda_file:
                        display_name = "cls_atk_*.2da"
                    elif "cls_savthr" in twoda_file:
                        display_name = "cls_savthr_*.2da"
                    else:
                        display_name = twoda_file.replace("_pattern", "*.2da")
                elif not twoda_file.endswith(".2da"):
                    # Add .2da extension
                    display_name = twoda_file + ".2da"
                
                # Clean up display name
                display_name = display_name.replace("_", " ")
                
                twoda_entries.append(f"  - [{display_name}](2DA-{twoda_file})")
            
            # Insert entries after the indented 2DA line
            lines = lines[:twoda_index + 1] + twoda_entries + lines[twoda_index + 1:]
        else:
            # Sub-items already exist, replace them
            # Find where they end
            end_index = next_line_index
            while end_index < len(lines):
                if lines[end_index].startswith("  -") and "2DA-" in lines[end_index]:
                    end_index += 1
                else:
                    break
            
            # Replace with new entries
            twoda_entries = []
            for twoda_file in twoda_files:
                # Convert file name to display name
                display_name = twoda_file
                
                # Handle special cases
                if twoda_file.endswith("_pattern"):
                    if "cls_atk" in twoda_file:
                        display_name = "cls_atk_*.2da"
                    elif "cls_savthr" in twoda_file:
                        display_name = "cls_savthr_*.2da"
                    else:
                        display_name = twoda_file.replace("_pattern", "*.2da")
                elif not twoda_file.endswith(".2da"):
                    display_name = twoda_file + ".2da"
                
                # Clean up display name
                display_name = display_name.replace("_", " ")
                
                twoda_entries.append(f"  - [{display_name}](2DA-{twoda_file})")
            
            lines = lines[:next_line_index] + twoda_entries + lines[end_index:]
        
        # Write back
        with open(home_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"Updated Home.md with {len(twoda_files)} 2DA file entries")
    else:
        print("Could not find 2DA File Format line in Home.md")
else:
    print("Could not find 2DA File Format entry in Home.md")

